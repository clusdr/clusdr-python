"""Lock and lease methods on Cluster. Same surface as the Go SDK."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import grpc

from clusdr._errors import ClusdrError
from clusdr._retry import retry
from clusdr.v1alpha1 import leases_pb2, locks_pb2

if TYPE_CHECKING:
    from clusdr._client import Cluster


class Lock:
    """A held exclusive lock.

    ``token`` is the fencing token — store it with any write that must be
    fenced. Background renew runs until :meth:`Cluster.unlock` or
    :meth:`Cluster.close`.
    """

    def __init__(self, name: str, holder: str, token: int, deadline: datetime | None) -> None:
        self.name = name
        self.holder = holder
        self.token = token
        self._deadline = deadline
        self._mu = threading.Lock()
        self._stop = threading.Event()
        self._cluster: Cluster | None = None

    @property
    def deadline(self) -> datetime | None:
        with self._mu:
            return self._deadline

    def _set_deadline(self, value: datetime | None) -> None:
        with self._mu:
            self._deadline = value


class Lease:
    """A held TTL grant.

    ``token`` is the fencing token. ``stop_renew()`` (or the ``stop`` event
    passed to :meth:`Cluster.lease`) stops background renew; the grant then
    expires. :meth:`Cluster.close` revokes.
    """

    def __init__(self, name: str, owner: str, token: int, deadline: datetime | None) -> None:
        self.name = name
        self.owner = owner
        self.token = token
        self._deadline = deadline
        self._mu = threading.Lock()
        self._stop = threading.Event()
        self._cluster: Cluster | None = None

    @property
    def deadline(self) -> datetime | None:
        with self._mu:
            return self._deadline

    def _set_deadline(self, value: datetime | None) -> None:
        with self._mu:
            self._deadline = value

    def stop_renew(self) -> None:
        """Stop background renewal; the grant then expires at its deadline."""
        self._stop.set()


class CoordMixin:
    def lock(self: Cluster, name: str, ttl: float | None = None, timeout: float | None = None) -> Lock:
        existing = self._held_lock(name)
        if existing is not None:
            return existing
        deadline = self._deadline(timeout)

        def call() -> locks_pb2.LockResponse:
            return self._lock.Lock(
                locks_pb2.LockRequest(name=name, holder=self._holder, ttl_ms=_ttl_ms(ttl)),
                timeout=self._remaining(deadline),
            )

        try:
            resp = retry(call, deadline=deadline)
        except (grpc.RpcError, TimeoutError) as exc:
            raise ClusdrError(f"clusdr: lock {name!r}: {exc}") from exc
        if resp is None or not resp.acquired:
            msg = resp.message if resp is not None and resp.message else "not acquired"
            raise ClusdrError(f"clusdr: lock {name!r}: {msg}")
        return self._adopt_lock(resp, name, ttl)

    def try_lock(self: Cluster, name: str, ttl: float | None = None, timeout: float | None = None) -> Lock | None:
        existing = self._held_lock(name)
        if existing is not None:
            return existing
        deadline = self._deadline(timeout)

        def call() -> locks_pb2.LockResponse:
            return self._lock.TryLock(
                locks_pb2.LockRequest(name=name, holder=self._holder, ttl_ms=_ttl_ms(ttl)),
                timeout=self._remaining(deadline),
            )

        try:
            resp = retry(call, deadline=deadline)
        except (grpc.RpcError, TimeoutError) as exc:
            raise ClusdrError(f"clusdr: trylock {name!r}: {exc}") from exc
        if resp is None or not resp.acquired:
            return None
        return self._adopt_lock(resp, name, ttl)

    def unlock(self: Cluster, name: str, timeout: float | None = None) -> None:
        lk = self._held_lock(name)
        if lk is None:
            raise ClusdrError(f"clusdr: lock {name!r} is not held by this client")
        self._release_lock(lk, timeout)

    def lease(
        self: Cluster,
        name: str,
        ttl: float | None = None,
        *,
        stop: threading.Event | None = None,
        timeout: float | None = None,
    ) -> Lease:
        existing = self._held_lease(name)
        if existing is not None:
            return existing
        deadline = self._deadline(timeout)

        def call() -> leases_pb2.GrantLeaseResponse:
            return self._lease.Grant(
                leases_pb2.GrantLeaseRequest(name=name, owner=self._holder, ttl_ms=_ttl_ms(ttl)),
                timeout=self._remaining(deadline),
            )

        try:
            resp = retry(call, deadline=deadline)
        except (grpc.RpcError, TimeoutError) as exc:
            raise ClusdrError(f"clusdr: lease {name!r}: {exc}") from exc
        if resp is None or not resp.granted:
            msg = resp.message if resp is not None and resp.message else "not granted"
            owner = resp.owner if resp is not None else ""
            if owner:
                raise ClusdrError(f"clusdr: lease {name!r}: {msg} (owner {owner})")
            raise ClusdrError(f"clusdr: lease {name!r}: {msg}")
        return self._adopt_lease(resp, name, ttl, stop)

    def renew(self: Cluster, name: str, timeout: float | None = None) -> None:
        ls = self._held_lease(name)
        if ls is None:
            raise ClusdrError(f"clusdr: lease {name!r} is not held by this client")
        deadline = self._deadline(timeout)

        def call() -> leases_pb2.RenewLeaseResponse:
            return self._lease.Renew(
                leases_pb2.RenewLeaseRequest(name=ls.name, owner=ls.owner, fencing_token=ls.token),
                timeout=self._remaining(deadline),
            )

        try:
            resp = retry(call, deadline=deadline)
        except (grpc.RpcError, TimeoutError) as exc:
            raise ClusdrError(f"clusdr: renew {name!r}: {exc}") from exc
        if resp is not None and not resp.renewed:
            raise ClusdrError(f"clusdr: renew {name!r}: {resp.message}")
        if resp is not None and resp.deadline_unix_ms:
            ls._set_deadline(_from_ms(resp.deadline_unix_ms))

    def revoke(self: Cluster, name: str, timeout: float | None = None) -> None:
        ls = self._held_lease(name)
        if ls is None:
            raise ClusdrError(f"clusdr: lease {name!r} is not held by this client")
        self._drop_lease(ls, timeout)

    def _held_lock(self: Cluster, name: str) -> Lock | None:
        with self._coord:
            return self._held.get(name)

    def _held_lease(self: Cluster, name: str) -> Lease | None:
        with self._coord:
            return self._leased.get(name)

    def _adopt_lock(self: Cluster, resp: locks_pb2.LockResponse, name: str, ttl: float | None) -> Lock:
        lk = Lock(name, resp.holder or self._holder, resp.fencing_token, _from_ms(resp.deadline_unix_ms))
        lk._cluster = self
        with self._coord:
            existing = self._held.get(name)
            if existing is not None and existing.token == lk.token:
                return existing
            self._held[name] = lk
        self._start_lock_renew(lk, ttl)
        return lk

    def _adopt_lease(
        self: Cluster,
        resp: leases_pb2.GrantLeaseResponse,
        name: str,
        ttl: float | None,
        stop: threading.Event | None,
    ) -> Lease:
        ls = Lease(name, resp.owner or self._holder, resp.fencing_token, _from_ms(resp.deadline_unix_ms))
        ls._cluster = self
        if stop is not None:
            ls._stop = stop
        with self._coord:
            existing = self._leased.get(name)
            if existing is not None and existing.token == ls.token:
                return existing
            self._leased[name] = ls
        self._start_lease_renew(ls, ttl)
        return ls

    def _release_lock(self: Cluster, lk: Lock, timeout: float | None) -> None:
        lk._stop.set()
        deadline = self._deadline(timeout)

        def call() -> locks_pb2.UnlockResponse:
            return self._lock.Unlock(
                locks_pb2.UnlockRequest(name=lk.name, holder=lk.holder, fencing_token=lk.token),
                timeout=self._remaining(deadline),
            )

        try:
            resp = retry(call, deadline=deadline)
        except grpc.RpcError as exc:
            if exc.code() == grpc.StatusCode.FAILED_PRECONDITION:
                self._forget_lock(lk.name, lk.token)
            raise ClusdrError(f"clusdr: unlock {lk.name!r}: {exc}") from exc
        except TimeoutError as exc:
            raise ClusdrError(f"clusdr: unlock {lk.name!r}: {exc}") from exc
        if resp is not None and not resp.released:
            raise ClusdrError(f"clusdr: unlock {lk.name!r}: {resp.message}")
        self._forget_lock(lk.name, lk.token)

    def _drop_lease(self: Cluster, ls: Lease, timeout: float | None) -> None:
        ls._stop.set()
        deadline = self._deadline(timeout)

        def call() -> leases_pb2.RevokeLeaseResponse:
            return self._lease.Revoke(
                leases_pb2.RevokeLeaseRequest(name=ls.name, owner=ls.owner, fencing_token=ls.token),
                timeout=self._remaining(deadline),
            )

        try:
            resp = retry(call, deadline=deadline)
        except grpc.RpcError as exc:
            if exc.code() == grpc.StatusCode.FAILED_PRECONDITION:
                self._forget_lease(ls.name, ls.token)
            raise ClusdrError(f"clusdr: revoke {ls.name!r}: {exc}") from exc
        except TimeoutError as exc:
            raise ClusdrError(f"clusdr: revoke {ls.name!r}: {exc}") from exc
        if resp is not None and not resp.revoked:
            raise ClusdrError(f"clusdr: revoke {ls.name!r}: {resp.message}")
        self._forget_lease(ls.name, ls.token)

    def _forget_lock(self: Cluster, name: str, token: int) -> None:
        with self._coord:
            cur = self._held.get(name)
            if cur is not None and cur.token == token:
                del self._held[name]

    def _forget_lease(self: Cluster, name: str, token: int) -> None:
        with self._coord:
            cur = self._leased.get(name)
            if cur is not None and cur.token == token:
                del self._leased[name]

    def _release_grants(self: Cluster) -> None:
        with self._coord:
            locks = list(self._held.values())
            leases = list(self._leased.values())
        for lk in locks:
            try:
                self._release_lock(lk, None)
            except ClusdrError:
                pass
        for ls in leases:
            try:
                self._drop_lease(ls, None)
            except ClusdrError:
                pass

    def _start_lock_renew(self: Cluster, lk: Lock, ttl: float | None) -> None:
        interval = _renew_interval(ttl, lk.deadline)
        thread = threading.Thread(target=self._renew_lock_loop, args=(lk, interval), daemon=True)
        thread.start()

    def _start_lease_renew(self: Cluster, ls: Lease, ttl: float | None) -> None:
        interval = _renew_interval(ttl, ls.deadline)
        thread = threading.Thread(target=self._renew_lease_loop, args=(ls, interval), daemon=True)
        thread.start()

    def _renew_lock_loop(self: Cluster, lk: Lock, interval: float) -> None:
        while not lk._stop.wait(interval):
            if self._closed.is_set():
                return
            try:
                resp = self._lock.Renew(
                    locks_pb2.RenewLockRequest(name=lk.name, holder=lk.holder, fencing_token=lk.token),
                    timeout=self._opts.request_timeout,
                )
            except grpc.RpcError as exc:
                if exc.code() in (grpc.StatusCode.FAILED_PRECONDITION, grpc.StatusCode.CANCELLED):
                    return
                continue
            if resp is not None and resp.deadline_unix_ms:
                lk._set_deadline(_from_ms(resp.deadline_unix_ms))

    def _renew_lease_loop(self: Cluster, ls: Lease, interval: float) -> None:
        while not ls._stop.wait(interval):
            if self._closed.is_set():
                return
            try:
                resp = self._lease.Renew(
                    leases_pb2.RenewLeaseRequest(name=ls.name, owner=ls.owner, fencing_token=ls.token),
                    timeout=self._opts.request_timeout,
                )
            except grpc.RpcError as exc:
                if exc.code() in (grpc.StatusCode.FAILED_PRECONDITION, grpc.StatusCode.CANCELLED):
                    return
                continue
            if resp is not None and resp.deadline_unix_ms:
                ls._set_deadline(_from_ms(resp.deadline_unix_ms))


def _ttl_ms(ttl: float | None) -> int:
    if ttl is None or ttl <= 0:
        return 0
    return max(1, int(ttl * 1000))


def _from_ms(unix_ms: int) -> datetime | None:
    if not unix_ms:
        return None
    return datetime.fromtimestamp(unix_ms / 1000.0, tz=timezone.utc)


def _renew_interval(ttl: float | None, deadline: datetime | None) -> float:
    d = ttl
    if d is None or d <= 0:
        if deadline is not None:
            d = (deadline - datetime.now(timezone.utc)).total_seconds()
    if d is None or d <= 0:
        d = 15.0
    return max(0.05, d / 3.0)
