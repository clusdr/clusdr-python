from __future__ import annotations

import time

import grpc
import pytest

from clusdr._retry import retry, transient


class _RpcError(grpc.RpcError):
    def __init__(self, code: grpc.StatusCode, details: str = "x") -> None:
        super().__init__()
        self._code = code
        self._details = details

    def code(self) -> grpc.StatusCode:
        return self._code

    def details(self) -> str:
        return self._details


def test_transient() -> None:
    assert not transient(RuntimeError("x"))
    assert transient(_RpcError(grpc.StatusCode.UNAVAILABLE))
    assert transient(_RpcError(grpc.StatusCode.ABORTED))
    assert transient(_RpcError(grpc.StatusCode.RESOURCE_EXHAUSTED))
    assert not transient(_RpcError(grpc.StatusCode.INVALID_ARGUMENT))


def test_retry_succeeds_after_transient() -> None:
    n = 0

    def fn() -> str:
        nonlocal n
        n += 1
        if n < 3:
            raise _RpcError(grpc.StatusCode.UNAVAILABLE, "wait")
        return "ok"

    assert retry(fn, deadline=time.monotonic() + 2, sleep=lambda _: None) == "ok"
    assert n == 3


def test_retry_stops_on_deadline() -> None:
    def fn() -> None:
        raise _RpcError(grpc.StatusCode.UNAVAILABLE, "down")

    with pytest.raises(grpc.RpcError):
        retry(fn, deadline=time.monotonic() + 0.15)


def test_retry_does_not_retry_invalid_argument() -> None:
    def fn() -> None:
        raise _RpcError(grpc.StatusCode.INVALID_ARGUMENT, "bad")

    with pytest.raises(grpc.RpcError) as ei:
        retry(fn, deadline=time.monotonic() + 2)
    assert ei.value.code() == grpc.StatusCode.INVALID_ARGUMENT
