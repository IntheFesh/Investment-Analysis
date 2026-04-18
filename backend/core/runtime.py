"""Unified wrapper for blocking / vendor calls.

Every router that needs to call a synchronous adapter method must route
through :func:`run_blocking` (or its async variant :func:`run_blocking_async`).
Centralising this gives us a single place to add:

- ``asyncio.to_thread`` dispatch so handlers never block the event loop;
- hard deadline enforcement (``asyncio.wait_for``);
- per-vendor circuit breaker (open after N consecutive failures, auto
  half-open after a cool-down);
- per-vendor success/failure/latency counters surfaced by the debug
  panel and the request envelope;
- request-scoped ``trace_id`` propagation so logs & the data-probe line
  up end-to-end.

The circuit breaker is intentionally tiny (one dict + a lock per vendor)
so it stays easy to reason about. We are not trying to replicate Hystrix.
"""

from __future__ import annotations

import asyncio
import contextvars
import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, TypeVar


logger = logging.getLogger(__name__)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Request-scoped trace id
# ---------------------------------------------------------------------------

_trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "trace_id", default=""
)


def new_trace_id() -> str:
    return uuid.uuid4().hex[:16]


def current_trace_id() -> str:
    tid = _trace_id_var.get()
    return tid or "-"


def set_trace_id(trace_id: str) -> contextvars.Token:
    return _trace_id_var.set(trace_id or new_trace_id())


def reset_trace_id(token: contextvars.Token) -> None:
    _trace_id_var.reset(token)


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------


@dataclass
class BreakerState:
    vendor: str
    failure_threshold: int = 3
    open_cooldown_s: float = 20.0
    # mutable counters
    consecutive_failures: int = 0
    opened_at: Optional[float] = None
    # metrics
    success_count: int = 0
    failure_count: int = 0
    latency_total_ms: float = 0.0
    last_error: Optional[str] = None
    last_success_at: Optional[float] = None

    def is_open(self, now: float) -> bool:
        if self.opened_at is None:
            return False
        if now - self.opened_at >= self.open_cooldown_s:
            # half-open: let the next call through; we reset opened_at only
            # when it succeeds.
            return False
        return True

    def record_success(self, latency_ms: float, now: float) -> None:
        self.consecutive_failures = 0
        self.opened_at = None
        self.success_count += 1
        self.latency_total_ms += latency_ms
        self.last_success_at = now

    def record_failure(self, exc: BaseException, now: float) -> None:
        self.consecutive_failures += 1
        self.failure_count += 1
        self.last_error = f"{type(exc).__name__}: {exc}"[:200]
        if self.consecutive_failures >= self.failure_threshold:
            self.opened_at = now

    def snapshot(self) -> Dict[str, Any]:
        total = self.success_count + self.failure_count
        avg_latency = (self.latency_total_ms / self.success_count) if self.success_count else 0.0
        return {
            "vendor": self.vendor,
            "state": "open" if self.is_open(time.monotonic()) else "closed",
            "success": self.success_count,
            "failure": self.failure_count,
            "success_rate": round(self.success_count / total, 4) if total else None,
            "avg_success_latency_ms": round(avg_latency, 2),
            "consecutive_failures": self.consecutive_failures,
            "opened_at_monotonic": self.opened_at,
            "last_error": self.last_error,
        }


class CircuitBreakerRegistry:
    _DEFAULT_THRESHOLD = int(os.getenv("VENDOR_BREAKER_THRESHOLD", "3"))
    _DEFAULT_COOLDOWN = float(os.getenv("VENDOR_BREAKER_COOLDOWN_SECONDS", "20"))

    def __init__(self) -> None:
        self._states: Dict[str, BreakerState] = {}
        self._lock = threading.Lock()

    def state(self, vendor: str) -> BreakerState:
        with self._lock:
            st = self._states.get(vendor)
            if st is None:
                st = BreakerState(
                    vendor=vendor,
                    failure_threshold=self._DEFAULT_THRESHOLD,
                    open_cooldown_s=self._DEFAULT_COOLDOWN,
                )
                self._states[vendor] = st
            return st

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {v: st.snapshot() for v, st in self._states.items()}


class CircuitOpenError(RuntimeError):
    """Raised by run_blocking when a vendor's breaker is open."""

    def __init__(self, vendor: str) -> None:
        super().__init__(f"circuit open for vendor={vendor}")
        self.vendor = vendor


_REGISTRY = CircuitBreakerRegistry()


def breaker_registry() -> CircuitBreakerRegistry:
    return _REGISTRY


# ---------------------------------------------------------------------------
# Blocking-call wrapper
# ---------------------------------------------------------------------------


@dataclass
class CallResult:
    value: Any = None
    ok: bool = False
    vendor: str = "unknown"
    latency_ms: float = 0.0
    error: Optional[str] = None
    trace_id: str = "-"
    circuit_open: bool = False


async def run_blocking_async(
    fn: Callable[..., T],
    *args: Any,
    timeout: float,
    vendor: str = "internal",
    trace_id: Optional[str] = None,
    **kwargs: Any,
) -> CallResult:
    """Run a synchronous ``fn`` off the event loop with full observability.

    Returns a :class:`CallResult` — never raises. Callers inspect ``ok``
    and ``error`` / ``circuit_open`` to decide what envelope to emit.
    """
    tid = trace_id or current_trace_id()
    now = time.monotonic()
    state = _REGISTRY.state(vendor)
    if state.is_open(now):
        logger.info("run_blocking vendor=%s trace=%s circuit_open", vendor, tid)
        return CallResult(
            ok=False, vendor=vendor, latency_ms=0.0,
            error="circuit_open", trace_id=tid, circuit_open=True,
        )
    start = time.monotonic()
    try:
        value = await asyncio.wait_for(
            asyncio.to_thread(fn, *args, **kwargs),
            timeout=timeout,
        )
        elapsed_ms = (time.monotonic() - start) * 1000.0
        state.record_success(elapsed_ms, time.monotonic())
        return CallResult(value=value, ok=True, vendor=vendor, latency_ms=elapsed_ms, trace_id=tid)
    except asyncio.TimeoutError as exc:
        elapsed_ms = (time.monotonic() - start) * 1000.0
        state.record_failure(exc, time.monotonic())
        logger.info("run_blocking vendor=%s trace=%s timeout after %.0fms", vendor, tid, elapsed_ms)
        return CallResult(ok=False, vendor=vendor, latency_ms=elapsed_ms, error=f"timeout:{timeout:.1f}s", trace_id=tid)
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = (time.monotonic() - start) * 1000.0
        state.record_failure(exc, time.monotonic())
        logger.info("run_blocking vendor=%s trace=%s failed: %s", vendor, tid, exc)
        return CallResult(ok=False, vendor=vendor, latency_ms=elapsed_ms, error=f"{type(exc).__name__}: {exc}"[:200], trace_id=tid)


def run_blocking(
    fn: Callable[..., T],
    *args: Any,
    timeout: float,
    vendor: str = "internal",
    trace_id: Optional[str] = None,
    **kwargs: Any,
) -> CallResult:
    """Synchronous variant for code paths that are already off the event loop.

    Enforces the same deadline + breaker semantics. Uses a worker thread
    with ``Future.result(timeout=...)``; on timeout the worker keeps
    running in the background so we never leak event-loop threads.
    """
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

    tid = trace_id or current_trace_id()
    now = time.monotonic()
    state = _REGISTRY.state(vendor)
    if state.is_open(now):
        return CallResult(ok=False, vendor=vendor, error="circuit_open", trace_id=tid, circuit_open=True)

    with ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"blk-{vendor}") as pool:
        start = time.monotonic()
        future = pool.submit(fn, *args, **kwargs)
        try:
            value = future.result(timeout=timeout)
            elapsed_ms = (time.monotonic() - start) * 1000.0
            state.record_success(elapsed_ms, time.monotonic())
            return CallResult(value=value, ok=True, vendor=vendor, latency_ms=elapsed_ms, trace_id=tid)
        except FutureTimeoutError as exc:
            elapsed_ms = (time.monotonic() - start) * 1000.0
            state.record_failure(exc, time.monotonic())
            return CallResult(ok=False, vendor=vendor, latency_ms=elapsed_ms, error=f"timeout:{timeout:.1f}s", trace_id=tid)
        except Exception as exc:  # noqa: BLE001
            elapsed_ms = (time.monotonic() - start) * 1000.0
            state.record_failure(exc, time.monotonic())
            return CallResult(ok=False, vendor=vendor, latency_ms=elapsed_ms, error=f"{type(exc).__name__}: {exc}"[:200], trace_id=tid)
