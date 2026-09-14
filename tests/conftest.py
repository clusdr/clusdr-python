from __future__ import annotations

from collections.abc import Iterator

import pytest

from tests.fake import FakeState, start_fake_server


@pytest.fixture
def fake_daemon() -> Iterator[tuple[str, FakeState]]:
    addr, state, server = start_fake_server()
    try:
        yield addr, state
    finally:
        server.stop(grace=0)
