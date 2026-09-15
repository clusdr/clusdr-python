"""In-process gRPC daemon used by SDK tests."""

from __future__ import annotations

import queue
import threading
import time
from collections.abc import Iterator
from concurrent import futures
from dataclasses import dataclass

import grpc

from clusdr.v1alpha1 import (
    events_pb2,
    events_pb2_grpc,
    health_pb2,
    health_pb2_grpc,
    leases_pb2,
    leases_pb2_grpc,
    locks_pb2,
    locks_pb2_grpc,
    membership_pb2,
    membership_pb2_grpc,
    watch_pb2,
    watch_pb2_grpc,
)


@dataclass
class _Grant:
    name: str
    holder: str
    token: int
    deadline: float
    ttl: float


class CoordTable:
    def __init__(self) -> None:
        self.cv = threading.Condition()
        self.locks: dict[str, _Grant] = {}
        self.leases: dict[str, _Grant] = {}
        self.next_lock = 0
        self.next_lease = 0

    def acquire_lock(self, name: str, holder: str, ttl: float) -> tuple[_Grant, bool]:
        with self.cv:
            self._expire_locked(self.locks)
            rec = self.locks.get(name)
            if rec is not None:
                if rec.holder == holder:
                    rec.deadline = time.time() + ttl
                    rec.ttl = ttl
                    self.cv.notify_all()
                    return rec, True
                return rec, False
            self.next_lock += 1
            rec = _Grant(name, holder, self.next_lock, time.time() + ttl, ttl)
            self.locks[name] = rec
            self.cv.notify_all()
            return rec, True

    def release_lock(self, name: str, holder: str, token: int) -> None:
        with self.cv:
            rec = self.locks.get(name)
            if rec is None or rec.holder != holder or rec.token != token:
                raise PermissionError("fencing token mismatch")
            del self.locks[name]
            self.cv.notify_all()

    def renew_lock(self, name: str, holder: str, token: int, ttl: float) -> _Grant:
        with self.cv:
            rec = self.locks.get(name)
            if rec is None or rec.holder != holder or rec.token != token:
                raise PermissionError("fencing token mismatch")
            rec.deadline = time.time() + ttl
            rec.ttl = ttl
            return rec

    def grant_lease(self, name: str, owner: str, ttl: float) -> tuple[_Grant, bool]:
        with self.cv:
            self._expire_locked(self.leases)
            rec = self.leases.get(name)
            if rec is not None:
                if rec.holder == owner:
                    rec.deadline = time.time() + ttl
                    rec.ttl = ttl
                    return rec, True
                return rec, False
            self.next_lease += 1
            rec = _Grant(name, owner, self.next_lease, time.time() + ttl, ttl)
            self.leases[name] = rec
            return rec, True

    def revoke_lease(self, name: str, owner: str, token: int) -> None:
        with self.cv:
            rec = self.leases.get(name)
            if rec is None or rec.holder != owner or rec.token != token:
                raise PermissionError("fencing token mismatch")
            del self.leases[name]

    def renew_lease(self, name: str, owner: str, token: int, ttl: float) -> _Grant:
        with self.cv:
            rec = self.leases.get(name)
            if rec is None or rec.holder != owner or rec.token != token:
                raise PermissionError("fencing token mismatch")
            rec.deadline = time.time() + ttl
            rec.ttl = ttl
            return rec

    def expire_due(self) -> None:
        with self.cv:
            self._expire_locked(self.locks)
            self._expire_locked(self.leases)
            self.cv.notify_all()

    def _expire_locked(self, table: dict[str, _Grant]) -> None:
        now = time.time()
        for name in [n for n, rec in table.items() if rec.deadline <= now]:
            del table[name]


class FakeState:
    def __init__(self) -> None:
        self.members = [
            membership_pb2.Member(id="node-a", address="127.0.0.1:1", status="alive", leader=True),
        ]
        self.events: queue.Queue[watch_pb2.WatchResponse] = queue.Queue()
        self.published: list[events_pb2.PublishEventRequest] = []
        self.coord = CoordTable()


class Health(health_pb2_grpc.HealthServiceServicer):
    def Health(self, request: health_pb2.HealthRequest, context: grpc.ServicerContext) -> health_pb2.HealthResponse:
        return health_pb2.HealthResponse(
            node_id="node-a", cluster_id="c1", role="leader", healthy=True
        )


class Membership(membership_pb2_grpc.MembershipServiceServicer):
    def __init__(self, state: FakeState) -> None:
        self.state = state

    def ListMembers(
        self, request: membership_pb2.ListMembersRequest, context: grpc.ServicerContext
    ) -> membership_pb2.ListMembersResponse:
        return membership_pb2.ListMembersResponse(members=self.state.members)

    def GetLeader(
        self, request: membership_pb2.GetLeaderRequest, context: grpc.ServicerContext
    ) -> membership_pb2.GetLeaderResponse:
        for m in self.state.members:
            if m.leader:
                return membership_pb2.GetLeaderResponse(leader_id=m.id, address=m.address)
        return membership_pb2.GetLeaderResponse()


class Events(events_pb2_grpc.EventServiceServicer):
    def __init__(self, state: FakeState) -> None:
        self.state = state

    def PublishEvent(
        self, request: events_pb2.PublishEventRequest, context: grpc.ServicerContext
    ) -> events_pb2.PublishEventResponse:
        self.state.published.append(request)
        ev = watch_pb2.WatchResponse(
            type=f"custom.{request.topic}",
            source="node-a",
            payload=request.payload,
            timestamp_unix_ms=1,
            seq=len(self.state.published),
        )
        self.state.events.put(ev)
        return events_pb2.PublishEventResponse(accepted=True, type=ev.type)


class Watch(watch_pb2_grpc.WatchServiceServicer):
    def __init__(self, state: FakeState) -> None:
        self.state = state

    def Watch(
        self, request: watch_pb2.WatchRequest, context: grpc.ServicerContext
    ) -> Iterator[watch_pb2.WatchResponse]:
        topics = [t[7:] if t.startswith("custom.") else t for t in request.topics]
        types = list(request.event_types)
        snap = watch_pb2.WatchResponse(
            type="member.join", source="node-a", timestamp_unix_ms=1, seq=0
        )
        if _watch_match(snap.type, topics, types):
            yield snap
        while context.is_active():
            try:
                ev = self.state.events.get(timeout=0.05)
            except queue.Empty:
                continue
            if not _watch_match(ev.type, topics, types):
                continue
            yield ev


def _watch_match(event_type: str, topics: list[str], types: list[str]) -> bool:
    if event_type in ("watch.sync", "watch.gap"):
        return True
    if topics:
        if not event_type.startswith("custom.") or event_type[7:] not in topics:
            return False
    if types and event_type not in types:
        return False
    return True


def _ttl_s(ttl_ms: int, reuse: float = 15.0) -> float:
    if ttl_ms > 0:
        return ttl_ms / 1000.0
    return reuse


def _deadline_ms(rec: _Grant) -> int:
    return int(rec.deadline * 1000)


class Locks(locks_pb2_grpc.LockServiceServicer):
    def __init__(self, table: CoordTable) -> None:
        self.table = table

    def Lock(self, request: locks_pb2.LockRequest, context: grpc.ServicerContext) -> locks_pb2.LockResponse:
        ttl = _ttl_s(request.ttl_ms)
        while context.is_active():
            rec, ok = self.table.acquire_lock(request.name, request.holder, ttl)
            if ok:
                return locks_pb2.LockResponse(
                    acquired=True,
                    fencing_token=rec.token,
                    holder=rec.holder,
                    deadline_unix_ms=_deadline_ms(rec),
                )
            with self.table.cv:
                self.table.cv.wait(timeout=0.05)
        context.abort(grpc.StatusCode.CANCELLED, "cancelled")

    def TryLock(self, request: locks_pb2.LockRequest, context: grpc.ServicerContext) -> locks_pb2.LockResponse:
        rec, ok = self.table.acquire_lock(request.name, request.holder, _ttl_s(request.ttl_ms))
        if not ok:
            return locks_pb2.LockResponse(
                acquired=False,
                message="held",
                fencing_token=rec.token,
                holder=rec.holder,
                deadline_unix_ms=_deadline_ms(rec),
            )
        return locks_pb2.LockResponse(
            acquired=True,
            fencing_token=rec.token,
            holder=rec.holder,
            deadline_unix_ms=_deadline_ms(rec),
        )

    def Unlock(self, request: locks_pb2.UnlockRequest, context: grpc.ServicerContext) -> locks_pb2.UnlockResponse:
        try:
            self.table.release_lock(request.name, request.holder, request.fencing_token)
        except PermissionError as exc:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(exc))
        return locks_pb2.UnlockResponse(released=True)

    def Renew(self, request: locks_pb2.RenewLockRequest, context: grpc.ServicerContext) -> locks_pb2.RenewLockResponse:
        try:
            with self.table.cv:
                cur = self.table.locks.get(request.name)
            reuse = cur.ttl if cur is not None else 15.0
            rec = self.table.renew_lock(request.name, request.holder, request.fencing_token, _ttl_s(request.ttl_ms, reuse))
        except PermissionError as exc:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(exc))
        return locks_pb2.RenewLockResponse(
            renewed=True,
            fencing_token=request.fencing_token,
            deadline_unix_ms=_deadline_ms(rec),
        )


class Leases(leases_pb2_grpc.LeaseServiceServicer):
    def __init__(self, table: CoordTable) -> None:
        self.table = table

    def Grant(self, request: leases_pb2.GrantLeaseRequest, context: grpc.ServicerContext) -> leases_pb2.GrantLeaseResponse:
        rec, ok = self.table.grant_lease(request.name, request.owner, _ttl_s(request.ttl_ms))
        if not ok:
            return leases_pb2.GrantLeaseResponse(
                granted=False,
                message="held",
                fencing_token=rec.token,
                owner=rec.holder,
                deadline_unix_ms=_deadline_ms(rec),
            )
        return leases_pb2.GrantLeaseResponse(
            granted=True,
            fencing_token=rec.token,
            owner=rec.holder,
            deadline_unix_ms=_deadline_ms(rec),
        )

    def Renew(self, request: leases_pb2.RenewLeaseRequest, context: grpc.ServicerContext) -> leases_pb2.RenewLeaseResponse:
        try:
            with self.table.cv:
                cur = self.table.leases.get(request.name)
            reuse = cur.ttl if cur is not None else 15.0
            rec = self.table.renew_lease(request.name, request.owner, request.fencing_token, _ttl_s(request.ttl_ms, reuse))
        except PermissionError as exc:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(exc))
        return leases_pb2.RenewLeaseResponse(
            renewed=True,
            fencing_token=request.fencing_token,
            deadline_unix_ms=_deadline_ms(rec),
        )

    def Revoke(self, request: leases_pb2.RevokeLeaseRequest, context: grpc.ServicerContext) -> leases_pb2.RevokeLeaseResponse:
        try:
            self.table.revoke_lease(request.name, request.owner, request.fencing_token)
        except PermissionError as exc:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(exc))
        return leases_pb2.RevokeLeaseResponse(revoked=True)


def start_fake_server(bind: str = "127.0.0.1:0") -> tuple[str, FakeState, grpc.Server]:
    state = FakeState()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    health_pb2_grpc.add_HealthServiceServicer_to_server(Health(), server)
    membership_pb2_grpc.add_MembershipServiceServicer_to_server(Membership(state), server)
    events_pb2_grpc.add_EventServiceServicer_to_server(Events(state), server)
    watch_pb2_grpc.add_WatchServiceServicer_to_server(Watch(state), server)
    locks_pb2_grpc.add_LockServiceServicer_to_server(Locks(state.coord), server)
    leases_pb2_grpc.add_LeaseServiceServicer_to_server(Leases(state.coord), server)
    port = server.add_insecure_port(bind)
    server.start()
    host = bind.rsplit(":", 1)[0]
    return f"{host}:{port}", state, server
