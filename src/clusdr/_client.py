"""gRPC client for the local daemon."""

from __future__ import annotations

import json
import threading
import time
import uuid
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import grpc

from clusdr._coord import CoordMixin, Lease, Lock
from clusdr._errors import ClusdrError
from clusdr._options import (
    DEFAULT_READY_TIMEOUT,
    DEFAULT_REQUEST_TIMEOUT,
    MAX_PAYLOAD,
    Options,
    env_addr,
    env_insecure,
)
from clusdr._retry import retry, transient
from clusdr._tls import open_channel
from clusdr.v1alpha1 import (
    events_pb2,
    events_pb2_grpc,
    health_pb2,
    health_pb2_grpc,
    leases_pb2_grpc,
    locks_pb2_grpc,
    membership_pb2,
    membership_pb2_grpc,
    watch_pb2,
    watch_pb2_grpc,
)


@dataclass(frozen=True)
class Member:
    """A cluster node as seen by the local daemon."""

    id: str
    address: str
    status: str
    leader: bool
    role: str = "voter"


@dataclass(frozen=True)
class Event:
    """A cluster or custom event from the Watch stream."""

    type: str
    source: str
    payload: bytes
    timestamp: datetime
    seq: int


class Cluster(CoordMixin):
    """Application view of the local Clusdr daemon."""

    def __init__(self, channel: grpc.Channel, opts: Options) -> None:
        self._channel = channel
        self._opts = opts
        self._closed = threading.Event()
        self._watch_lock = threading.Lock()
        self._watch_call: Any = None
        self._mem = membership_pb2_grpc.MembershipServiceStub(channel)
        self._watch = watch_pb2_grpc.WatchServiceStub(channel)
        self._ev = events_pb2_grpc.EventServiceStub(channel)
        self._health = health_pb2_grpc.HealthServiceStub(channel)
        self._lock = locks_pb2_grpc.LockServiceStub(channel)
        self._lease = leases_pb2_grpc.LeaseServiceStub(channel)
        self._holder = opts.holder or f"sdk-{uuid.uuid4()}"
        self._coord = threading.Lock()
        self._held: dict[str, Lock] = {}
        self._leased: dict[str, Lease] = {}

    def members(self, timeout: float | None = None) -> list[Member]:
        deadline = self._deadline(timeout)

        def call() -> membership_pb2.ListMembersResponse:
            return self._mem.ListMembers(
                membership_pb2.ListMembersRequest(),
                timeout=self._remaining(deadline),
            )

        try:
            resp = retry(call, deadline=deadline)
        except (grpc.RpcError, TimeoutError) as exc:
            raise ClusdrError(f"clusdr: members: {exc}") from exc
        return [
            Member(
                id=m.id,
                address=m.address,
                status=m.status,
                leader=m.leader,
                role=m.role or "voter",
            )
            for m in resp.members
        ]

    def leader(self, timeout: float | None = None) -> Member:
        deadline = self._deadline(timeout)

        def call() -> membership_pb2.GetLeaderResponse:
            return self._mem.GetLeader(
                membership_pb2.GetLeaderRequest(),
                timeout=self._remaining(deadline),
            )

        try:
            resp = retry(call, deadline=deadline)
        except (grpc.RpcError, TimeoutError) as exc:
            raise ClusdrError(f"clusdr: leader: {exc}") from exc
        return Member(
            id=resp.leader_id,
            address=resp.address,
            status="alive",
            leader=True,
            role="voter",
        )

    def publish(
        self,
        topic: str,
        payload: bytes | str | dict[str, Any] | list[Any] | None = None,
        timeout: float | None = None,
    ) -> None:
        body = encode_payload(payload)
        if len(body) > MAX_PAYLOAD:
            raise ClusdrError(f"clusdr: publish payload exceeds {MAX_PAYLOAD} bytes")
        deadline = self._deadline(timeout)

        def call() -> events_pb2.PublishEventResponse:
            return self._ev.PublishEvent(
                events_pb2.PublishEventRequest(topic=topic, payload=body),
                timeout=self._remaining(deadline),
            )

        try:
            resp = retry(call, deadline=deadline)
        except (grpc.RpcError, TimeoutError) as exc:
            raise ClusdrError(f"clusdr: publish: {exc}") from exc
        if resp is not None and not resp.accepted:
            raise ClusdrError(f"clusdr: publish rejected: {resp.message}")

    def watch(
        self,
        topics: Sequence[str] | None = None,
        event_types: Sequence[str] | None = None,
    ) -> Iterator[Event]:
        """Stream events. Empty topics/event_types is the full bus.

        Non-empty *topics* (keys, with or without a ``custom.`` prefix) restrict
        the stream to those custom events. The membership snapshot is omitted.
        Custom events are not replayed on reconnect. The same filter is reused
        after a drop. *event_types* matches full type strings; ``watch.sync``
        and ``watch.gap`` always pass.
        """
        topic_list = _normalize_watch_topics(topics)
        type_list = _normalize_watch_types(event_types)
        last_seq = 0
        backoff = 0.05
        while not self._closed.is_set():
            try:
                call = self._watch.Watch(
                    watch_pb2.WatchRequest(
                        last_seq=last_seq,
                        topics=topic_list,
                        event_types=type_list,
                    )
                )
            except grpc.RpcError as exc:
                if self._closed.is_set() or exc.code() == grpc.StatusCode.CANCELLED:
                    return
                if exc.code() == grpc.StatusCode.INVALID_ARGUMENT:
                    raise ClusdrError(f"clusdr: watch: {exc}") from exc
                if not self._sleep(backoff):
                    return
                backoff = min(backoff * 2, 2.0)
                continue
            with self._watch_lock:
                self._watch_call = call
            backoff = 0.05
            try:
                for resp in call:
                    if self._closed.is_set():
                        return
                    if resp.seq > last_seq:
                        last_seq = resp.seq
                    yield Event(
                        type=resp.type,
                        source=resp.source,
                        payload=bytes(resp.payload),
                        timestamp=_ts(resp.timestamp_unix_ms),
                        seq=resp.seq,
                    )
            except grpc.RpcError as exc:
                if self._closed.is_set() or exc.code() == grpc.StatusCode.CANCELLED:
                    return
                if exc.code() == grpc.StatusCode.INVALID_ARGUMENT:
                    raise ClusdrError(f"clusdr: watch: {exc}") from exc
            finally:
                with self._watch_lock:
                    if self._watch_call is call:
                        self._watch_call = None
            if not self._sleep(backoff):
                return
            backoff = min(backoff * 2, 2.0)

    def close(self) -> None:
        self._closed.set()
        self._release_grants()
        with self._watch_lock:
            if self._watch_call is not None:
                self._watch_call.cancel()
                self._watch_call = None
        self._channel.close()

    def __enter__(self) -> Cluster:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _deadline(self, timeout: float | None) -> float:
        if timeout is None:
            timeout = self._opts.request_timeout
        return time.monotonic() + timeout

    def _remaining(self, deadline: float) -> float:
        left = deadline - time.monotonic()
        if left <= 0:
            raise TimeoutError("clusdr: request timeout")
        return left

    def _sleep(self, seconds: float) -> bool:
        return not self._closed.wait(seconds)


def local(
    *,
    insecure: bool = False,
    data_dir: str = "",
    holder: str = "",
    request_timeout: float = DEFAULT_REQUEST_TIMEOUT,
    ready_timeout: float = DEFAULT_READY_TIMEOUT,
    server_name: str = "",
) -> Cluster:
    """Connect to the daemon on this host (CLUSDR_GRPC_ADDR or 127.0.0.1:7947)."""
    return connect(
        Options(
            addr=env_addr(),
            insecure=insecure,
            data_dir=data_dir,
            holder=holder.strip(),
            request_timeout=request_timeout,
            ready_timeout=ready_timeout,
            server_name=server_name,
        )
    )


def dial(
    addr: str,
    *,
    insecure: bool = False,
    data_dir: str = "",
    holder: str = "",
    request_timeout: float = DEFAULT_REQUEST_TIMEOUT,
    ready_timeout: float = DEFAULT_READY_TIMEOUT,
    server_name: str = "",
) -> Cluster:
    """Connect to addr. Tests and operators use this; applications use local()."""
    if not addr.strip():
        raise ClusdrError("clusdr: empty dial address")
    return connect(
        Options(
            addr=addr.strip(),
            insecure=insecure,
            data_dir=data_dir,
            holder=holder.strip(),
            request_timeout=request_timeout,
            ready_timeout=ready_timeout,
            server_name=server_name,
        )
    )


def connect(opts: Options) -> Cluster:
    if not opts.insecure and env_insecure() and not opts.data_dir:
        opts.insecure = True
    if not opts.addr:
        raise ClusdrError("clusdr: empty dial address")
    channel = open_channel(opts)
    cluster = Cluster(channel, opts)
    if opts.ready_timeout > 0:
        deadline = time.monotonic() + opts.ready_timeout
        try:
            retry(
                lambda: cluster._health.Health(
                    health_pb2.HealthRequest(),
                    timeout=min(0.5, max(0.05, deadline - time.monotonic())),
                ),
                deadline=deadline,
                is_transient=_ready_transient,
            )
        except (grpc.RpcError, TimeoutError) as exc:
            cluster.close()
            raise ClusdrError(f"clusdr: daemon not ready at {opts.addr}: {exc}") from exc
    return cluster


def _ready_transient(exc: BaseException) -> bool:
    if transient(exc):
        return True
    return isinstance(exc, grpc.RpcError) and exc.code() == grpc.StatusCode.DEADLINE_EXCEEDED


def encode_payload(payload: bytes | str | dict[str, Any] | list[Any] | None) -> bytes:
    if payload is None:
        return b""
    if isinstance(payload, bytes):
        return payload
    if isinstance(payload, str):
        return payload.encode("utf-8")
    if isinstance(payload, (dict, list)):
        return json.dumps(payload, separators=(",", ":")).encode("utf-8")
    raise TypeError(f"clusdr: payload must be bytes, str, dict, or list; got {type(payload).__name__}")


def _ts(unix_ms: int) -> datetime:
    return datetime.fromtimestamp(unix_ms / 1000.0, tz=timezone.utc)


_MAX_WATCH_TOPIC = 128


def _normalize_watch_topics(topics: Sequence[str] | None) -> list[str]:
    if not topics:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for raw in topics:
        t = raw.strip()
        if t.startswith("custom."):
            t = t[7:]
        if not t:
            continue
        if len(t) > _MAX_WATCH_TOPIC or not all(ch.isalnum() or ch in "._-" for ch in t):
            raise ClusdrError(f"clusdr: watch topic {raw!r} is invalid")
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def _normalize_watch_types(types: Sequence[str] | None) -> list[str]:
    if not types:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for raw in types:
        t = raw.strip()
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out
