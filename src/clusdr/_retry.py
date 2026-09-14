"""Retry transient gRPC failures with bounded backoff."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

import grpc

from clusdr._options import INITIAL_BACKOFF, MAX_BACKOFF

T = TypeVar("T")

_TRANSIENT = (
    grpc.StatusCode.UNAVAILABLE,
    grpc.StatusCode.RESOURCE_EXHAUSTED,
    grpc.StatusCode.ABORTED,
)


def transient(exc: BaseException) -> bool:
    if not isinstance(exc, grpc.RpcError):
        return False
    return exc.code() in _TRANSIENT


def retry(
    fn: Callable[[], T],
    *,
    deadline: float,
    sleep: Callable[[float], None] = time.sleep,
    is_transient: Callable[[BaseException], bool] = transient,
) -> T:
    """Call fn until it succeeds, a non-transient error, or monotonic deadline."""
    backoff = INITIAL_BACKOFF
    last: BaseException | None = None
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            if last is not None:
                raise last
            raise TimeoutError("clusdr: retry deadline exceeded")
        try:
            return fn()
        except grpc.RpcError as exc:
            if not is_transient(exc):
                raise
            last = exc
        wait = min(backoff, max(0.0, deadline - time.monotonic()))
        if wait <= 0:
            if last is not None:
                raise last
            raise TimeoutError("clusdr: retry deadline exceeded")
        sleep(wait)
        backoff = min(backoff * 2, MAX_BACKOFF)
