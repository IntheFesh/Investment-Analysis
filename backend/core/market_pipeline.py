"""Background refresher for market overview snapshots.

Problem
-------
``/market/*`` endpoints used to call ``build_overview`` synchronously on
every cache miss. The builder in turn reaches out to yfinance with no
deadline. When a single vendor call stalls (Yahoo 404 on ^HSTECH is the
current recurring failure), every inbound request blocks on it and
eventually hits the 15s client timeout — which is what produces the
"market snapshot refresh failed for cn_a/hk/global + all windows" flood
in the backend logs and the cascading "暂无可用行情 / 无轮动数据" tiles
on the frontend.

Design
------
* A single ``asyncio.Task`` loop runs on FastAPI startup.
* The loop rebuilds every ``(market_view, time_window)`` slot on an
  interval (default 60 s) using ``asyncio.to_thread`` so the blocking
  pandas/yfinance work never runs on the event loop thread.
* Each rebuild is bounded by ``REFRESH_DEADLINE_SECONDS`` (default 8s).
  A timeout stamps ``fallback_reason=refresh_timeout`` onto the current
  cache meta so the UI can still render *something* while we wait for
  the next tick to heal.
* The cache stores *last-good* results so transient upstream failures
  never erase the user's view.

The pipeline is best-effort: if there is nothing to refresh (e.g. during
tests, offline) it silently backs off.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Iterable, List, Tuple

from .data_source import get_data_source
from .snapshot_cache import hot_cache


logger = logging.getLogger(__name__)


DEFAULT_MARKET_VIEWS: Tuple[str, ...] = ("cn_a", "hk", "global")
DEFAULT_TIME_WINDOWS: Tuple[str, ...] = ("20D", "1M", "3M", "1Y")

REFRESH_INTERVAL = float(os.getenv("MARKET_REFRESH_INTERVAL_SECONDS", "60"))
REFRESH_DEADLINE = float(os.getenv("MARKET_REFRESH_DEADLINE_SECONDS", "8"))
HOT_TTL = float(os.getenv("MARKET_HOT_TTL_SECONDS", "120"))


def _cache_key(market_view: str, time_window: str, adapter_name: str) -> str:
    return f"market:{market_view}:{time_window}:{adapter_name}"


def _build_sync(market_view: str, time_window: str) -> Tuple[dict, dict]:
    # Imported lazily to avoid circular imports at module load time.
    from ..analytics.market import build_overview

    adapter = get_data_source()
    payload, src_meta, ev_count = build_overview(adapter, time_window, market_view)
    src_meta = dict(src_meta)
    src_meta["evidence_count"] = ev_count
    return payload, src_meta


async def refresh_one(market_view: str, time_window: str) -> bool:
    """Rebuild a single snapshot slot. Returns True on success."""
    adapter = get_data_source()
    key = _cache_key(market_view, time_window, adapter.name)
    start = time.monotonic()
    try:
        payload, meta = await asyncio.wait_for(
            asyncio.to_thread(_build_sync, market_view, time_window),
            timeout=REFRESH_DEADLINE,
        )
    except asyncio.TimeoutError:
        logger.warning(
            "market snapshot refresh timeout for %s/%s after %.1fs",
            market_view, time_window, REFRESH_DEADLINE,
        )
        _mark_timeout(key)
        return False
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "market snapshot refresh failed for %s/%s: %s",
            market_view, time_window, exc,
        )
        _mark_error(key, str(exc))
        return False

    elapsed = time.monotonic() - start
    logger.debug("market snapshot refreshed %s/%s in %.2fs", market_view, time_window, elapsed)
    hot_cache().put(key, payload, meta)
    return True


def _mark_timeout(key: str) -> None:
    existing = hot_cache().peek(key)
    if existing is None:
        return
    value, meta, _age = existing
    meta = dict(meta)
    meta["fallback_reason"] = "refresh_timeout"
    meta["is_realtime"] = False
    hot_cache().put(key, value, meta)


def _mark_error(key: str, reason: str) -> None:
    existing = hot_cache().peek(key)
    if existing is None:
        return
    value, meta, _age = existing
    meta = dict(meta)
    meta["fallback_reason"] = f"refresh_error: {reason}"[:200]
    meta["is_realtime"] = False
    hot_cache().put(key, value, meta)


async def refresh_all(
    market_views: Iterable[str] = DEFAULT_MARKET_VIEWS,
    time_windows: Iterable[str] = DEFAULT_TIME_WINDOWS,
) -> None:
    """Refresh every configured (market_view, time_window) slot concurrently."""
    tasks: List[asyncio.Task] = []
    for mv in market_views:
        for tw in time_windows:
            tasks.append(asyncio.create_task(refresh_one(mv, tw)))
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


_LOOP_TASK: asyncio.Task | None = None
_STARTED = False


async def _loop() -> None:
    # Prime the cache as fast as possible on startup so the first UI
    # paint isn't a cold miss.
    try:
        await refresh_all()
    except Exception:  # noqa: BLE001
        logger.exception("initial market refresh failed")

    while True:
        try:
            await asyncio.sleep(REFRESH_INTERVAL)
            await refresh_all()
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            logger.exception("market refresh loop iteration failed")


def start_pipeline() -> None:
    global _LOOP_TASK, _STARTED
    if _STARTED:
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop (e.g. test setup) — caller should invoke later
        # from inside an async context. We intentionally do NOT set
        # ``_STARTED`` so a subsequent call from a real startup hook
        # succeeds.
        return
    _STARTED = True
    _LOOP_TASK = loop.create_task(_loop())
    logger.info(
        "market refresh pipeline started (interval=%ss, deadline=%ss)",
        REFRESH_INTERVAL, REFRESH_DEADLINE,
    )


def stop_pipeline() -> None:
    global _LOOP_TASK, _STARTED
    _STARTED = False
    if _LOOP_TASK is not None:
        _LOOP_TASK.cancel()
        _LOOP_TASK = None


def seed_demo_snapshots(
    market_views: Iterable[str] = DEFAULT_MARKET_VIEWS,
    time_windows: Iterable[str] = DEFAULT_TIME_WINDOWS,
) -> None:
    """Populate the hot cache with a first deterministic snapshot so
    cold requests never return 500 while the async loop primes real data.

    Uses the currently-selected adapter directly (synchronous) because
    this runs exactly once at startup before ``start_pipeline``.
    """
    for mv in market_views:
        for tw in time_windows:
            try:
                payload, meta = _build_sync(mv, tw)
            except Exception as exc:  # noqa: BLE001
                logger.warning("seed snapshot failed for %s/%s: %s", mv, tw, exc)
                continue
            adapter = get_data_source()
            key = _cache_key(mv, tw, adapter.name)
            meta = dict(meta)
            meta.setdefault("fallback_reason", "cold-start-seed")
            hot_cache().put(key, payload, meta)
