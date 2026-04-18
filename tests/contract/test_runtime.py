"""Round-0 contract tests for the blocking-call wrapper + circuit breaker.

Guards the invariants the rest of the pipeline depends on:

- ``run_blocking_async`` never raises — it returns a :class:`CallResult`.
- A vendor that fails N times consecutively flips the breaker open and
  subsequent calls short-circuit without touching the downstream.
- trace_id propagates from the contextvar when the caller doesn't set one.
"""

from __future__ import annotations

import asyncio
import time

import pytest

from backend.core.runtime import (
    CircuitBreakerRegistry,
    breaker_registry,
    current_trace_id,
    new_trace_id,
    reset_trace_id,
    run_blocking_async,
    set_trace_id,
)


def _boom() -> None:
    raise RuntimeError("boom")


def _slow() -> None:
    time.sleep(0.2)


def _ok() -> int:
    return 42


@pytest.mark.asyncio
async def test_run_blocking_returns_result_never_raises_on_exception() -> None:
    result = await run_blocking_async(_boom, timeout=1.0, vendor="test-exc")
    assert result.ok is False
    assert "boom" in (result.error or "")
    assert result.circuit_open is False


@pytest.mark.asyncio
async def test_run_blocking_times_out_without_crashing() -> None:
    result = await run_blocking_async(_slow, timeout=0.05, vendor="test-slow")
    assert result.ok is False
    assert result.error is not None
    assert "timeout" in result.error


@pytest.mark.asyncio
async def test_run_blocking_records_success() -> None:
    result = await run_blocking_async(_ok, timeout=1.0, vendor="test-ok")
    assert result.ok is True
    assert result.value == 42
    assert result.latency_ms >= 0


@pytest.mark.asyncio
async def test_breaker_opens_after_consecutive_failures_and_short_circuits() -> None:
    vendor = "test-breaker"
    # Three consecutive failures should flip the breaker (default threshold=3).
    for _ in range(3):
        r = await run_blocking_async(_boom, timeout=1.0, vendor=vendor)
        assert r.ok is False
    # Next call must be short-circuited and NOT call the function.
    calls = {"n": 0}

    def _tracker() -> int:
        calls["n"] += 1
        return 1

    r = await run_blocking_async(_tracker, timeout=1.0, vendor=vendor)
    assert r.ok is False
    assert r.circuit_open is True
    assert calls["n"] == 0


def test_trace_id_context_propagation() -> None:
    token = set_trace_id("abcdef1234567890")
    try:
        assert current_trace_id() == "abcdef1234567890"
    finally:
        reset_trace_id(token)
    # After reset, falls back to default "-".
    assert current_trace_id() == "-"


def test_new_trace_id_is_stable_length() -> None:
    tid = new_trace_id()
    assert isinstance(tid, str)
    assert len(tid) == 16


def test_breaker_registry_is_process_singleton() -> None:
    a = breaker_registry()
    b = breaker_registry()
    assert a is b
