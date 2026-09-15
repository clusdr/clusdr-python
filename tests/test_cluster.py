from __future__ import annotations

import threading
import time
from concurrent import futures

import grpc
import pytest

from clusdr import ClusdrError, dial, local
from clusdr._client import encode_payload
from clusdr.v1alpha1 import (
    events_pb2_grpc,
    health_pb2_grpc,
    membership_pb2_grpc,
    watch_pb2_grpc,
)
from tests.fake import Events, FakeState, Health, Membership, Watch


def test_members_leader_watch_publish(fake_daemon: tuple) -> None:
    addr, state = fake_daemon
    cluster = dial(addr, insecure=True)
    try:
        members = cluster.members()
        assert len(members) == 1
        assert members[0].id == "node-a"
        assert members[0].leader

        leader = cluster.leader()
        assert leader.id == "node-a"
        assert leader.leader

        events = []
        done = threading.Event()

        def consume() -> None:
            for ev in cluster.watch():
                events.append(ev)
                if ev.type == "custom.deployment":
                    done.set()
                    return

        t = threading.Thread(target=consume, daemon=True)
        t.start()
        deadline = time.time() + 3
        while time.time() < deadline and not any(e.type == "member.join" for e in events):
            time.sleep(0.02)
        assert any(e.type == "member.join" and e.source == "node-a" for e in events)

        cluster.publish("deployment", {"sha": "abc"})
        assert done.wait(3)
        ev = next(e for e in events if e.type == "custom.deployment")
        assert ev.payload == b'{"sha":"abc"}'
        assert state.published[0].topic == "deployment"
    finally:
        cluster.close()


def test_watch_topics(fake_daemon: tuple) -> None:
    addr, _ = fake_daemon
    cluster = dial(addr, insecure=True)
    try:
        events = []
        done = threading.Event()

        def consume() -> None:
            for ev in cluster.watch(topics=["deployment"]):
                events.append(ev)
                if ev.type == "custom.deployment":
                    done.set()
                    return

        t = threading.Thread(target=consume, daemon=True)
        t.start()
        time.sleep(0.05)
        cluster.publish("noise", "x")
        cluster.publish("deployment", {"sha": "abc"})
        assert done.wait(3)
        assert not any(e.type == "member.join" for e in events)
        assert not any(e.type == "custom.noise" for e in events)
        assert any(e.type == "custom.deployment" for e in events)
    finally:
        cluster.close()


def test_watch_event_types(fake_daemon: tuple) -> None:
    addr, _ = fake_daemon
    cluster = dial(addr, insecure=True)
    try:
        events = []
        done = threading.Event()

        def consume() -> None:
            for ev in cluster.watch(event_types=["custom.deployment"]):
                events.append(ev)
                if ev.type == "custom.deployment":
                    done.set()
                    return

        t = threading.Thread(target=consume, daemon=True)
        t.start()
        time.sleep(0.05)
        cluster.publish("noise", "x")
        cluster.publish("deployment", {"sha": "abc"})
        assert done.wait(3)
        assert not any(e.type == "member.join" for e in events)
        assert not any(e.type == "custom.noise" for e in events)
    finally:
        cluster.close()


def test_watch_bad_topic(fake_daemon: tuple) -> None:
    addr, _ = fake_daemon
    cluster = dial(addr, insecure=True)
    try:
        with pytest.raises(ClusdrError, match="topic"):
            next(cluster.watch(topics=["bad topic"]))
    finally:
        cluster.close()


def test_local_uses_env_addr(fake_daemon: tuple, monkeypatch: pytest.MonkeyPatch) -> None:
    addr, _ = fake_daemon
    monkeypatch.setenv("CLUSDR_GRPC_ADDR", addr)
    monkeypatch.setenv("CLUSDR_TLS", "disabled")
    cluster = local()
    try:
        members = cluster.members()
        assert len(members) == 1
        assert members[0].id == "node-a"
    finally:
        cluster.close()


def test_retry_until_ready() -> None:
    state = FakeState()
    health = _FlakyHealth(failures=2)
    srv = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    health_pb2_grpc.add_HealthServiceServicer_to_server(health, srv)
    membership_pb2_grpc.add_MembershipServiceServicer_to_server(Membership(state), srv)
    events_pb2_grpc.add_EventServiceServicer_to_server(Events(state), srv)
    watch_pb2_grpc.add_WatchServiceServicer_to_server(Watch(state), srv)
    port = srv.add_insecure_port("127.0.0.1:0")
    srv.start()
    try:
        cluster = dial(f"127.0.0.1:{port}", insecure=True, ready_timeout=5)
        try:
            assert cluster.members()[0].id == "node-a"
            assert health.calls >= 3
        finally:
            cluster.close()
    finally:
        srv.stop(grace=0)


class _FlakyHealth(Health):
    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.calls = 0

    def Health(self, request, context):  # noqa: ANN001
        self.calls += 1
        if self.calls <= self.failures:
            context.abort(grpc.StatusCode.UNAVAILABLE, "wait")
        return super().Health(request, context)


def test_empty_dial() -> None:
    with pytest.raises(ClusdrError, match="empty"):
        dial("  ", insecure=True)


def test_publish_too_large(fake_daemon: tuple) -> None:
    addr, _ = fake_daemon
    cluster = dial(addr, insecure=True)
    try:
        with pytest.raises(ClusdrError, match="exceeds"):
            cluster.publish("deployment", b"x" * (64 * 1024 + 1))
    finally:
        cluster.close()


def test_encode_payload() -> None:
    assert encode_payload(None) == b""
    assert encode_payload(b"raw") == b"raw"
    assert encode_payload("hi") == b"hi"
    assert encode_payload({"sha": "abc"}) == b'{"sha":"abc"}'
    with pytest.raises(TypeError):
        encode_payload(1)  # type: ignore[arg-type]
