from __future__ import annotations

import threading
import time

import pytest

from clusdr import ClusdrError, dial


def test_lock_acquire_unlock(fake_daemon: tuple) -> None:
    addr, state = fake_daemon
    a = dial(addr, insecure=True, holder="worker-a")
    b = dial(addr, insecure=True, holder="worker-b")
    try:
        lk = a.lock("scheduler", ttl=1.0)
        assert lk.token > 0
        assert lk.holder == "worker-a"
        assert lk.deadline is not None

        assert b.try_lock("scheduler", ttl=1.0) is None

        a.unlock("scheduler")
        assert "scheduler" not in state.coord.locks

        won = b.try_lock("scheduler", ttl=1.0)
        assert won is not None
        assert won.token > lk.token
        b.unlock("scheduler")
    finally:
        a.close()
        b.close()


def test_lock_waits_for_unlock(fake_daemon: tuple) -> None:
    addr, _ = fake_daemon
    a = dial(addr, insecure=True, holder="worker-a")
    b = dial(addr, insecure=True, holder="worker-b")
    try:
        first = a.try_lock("job", ttl=1.0)
        assert first is not None
        got: list = []

        def waiter() -> None:
            got.append(b.lock("job", ttl=1.0, timeout=3.0))

        t = threading.Thread(target=waiter)
        t.start()
        time.sleep(0.05)
        a.unlock("job")
        t.join(3)
        assert got and got[0].holder == "worker-b"
    finally:
        a.close()
        b.close()


def test_unlock_requires_acquire(fake_daemon: tuple) -> None:
    addr, _ = fake_daemon
    c = dial(addr, insecure=True)
    try:
        with pytest.raises(ClusdrError, match="not held"):
            c.unlock("missing")
    finally:
        c.close()


def test_close_releases_lock(fake_daemon: tuple) -> None:
    addr, state = fake_daemon
    a = dial(addr, insecure=True, holder="worker-a")
    a.lock("job", ttl=1.0)
    a.close()
    assert "job" not in state.coord.locks


def test_lock_renew_keeps_grant(fake_daemon: tuple) -> None:
    addr, state = fake_daemon
    c = dial(addr, insecure=True, holder="worker-a")
    try:
        lk = c.lock("job", ttl=0.15)
        first = state.coord.locks["job"].deadline
        time.sleep(0.2)
        state.coord.expire_due()
        assert "job" in state.coord.locks
        assert state.coord.locks["job"].deadline > first
        assert lk.token > 0
    finally:
        c.close()


def test_lease_grant_revoke(fake_daemon: tuple) -> None:
    addr, state = fake_daemon
    a = dial(addr, insecure=True, holder="worker-a")
    b = dial(addr, insecure=True, holder="worker-b")
    try:
        ls = a.lease("worker-1", ttl=1.0)
        assert ls.token > 0
        assert ls.owner == "worker-a"
        with pytest.raises(ClusdrError, match="held"):
            b.lease("worker-1", ttl=1.0)
        a.revoke("worker-1")
        assert "worker-1" not in state.coord.leases
        won = b.lease("worker-1", ttl=1.0)
        assert won.token > ls.token
        b.revoke("worker-1")
    finally:
        a.close()
        b.close()


def test_lease_renew_and_cancel(fake_daemon: tuple) -> None:
    addr, state = fake_daemon
    c = dial(addr, insecure=True, holder="worker-a")
    try:
        stop = threading.Event()
        ls = c.lease("worker-1", ttl=0.08, stop=stop)
        first = state.coord.leases["worker-1"].deadline
        c.renew("worker-1")
        assert state.coord.leases["worker-1"].deadline > first
        stop.set()
        deadline = time.time() + 2
        expired = False
        while time.time() < deadline:
            state.coord.expire_due()
            if "worker-1" not in state.coord.leases:
                expired = True
                break
            time.sleep(0.01)
        assert expired
        assert ls.token > 0
    finally:
        c.close()


def test_close_revokes_lease(fake_daemon: tuple) -> None:
    addr, state = fake_daemon
    c = dial(addr, insecure=True, holder="worker-a")
    c.lease("worker-1", ttl=1.0)
    c.close()
    assert "worker-1" not in state.coord.leases


def test_revoke_requires_grant(fake_daemon: tuple) -> None:
    addr, _ = fake_daemon
    c = dial(addr, insecure=True)
    try:
        with pytest.raises(ClusdrError, match="not held"):
            c.revoke("missing")
        with pytest.raises(ClusdrError, match="not held"):
            c.renew("missing")
    finally:
        c.close()
