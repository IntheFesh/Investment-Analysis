"""Market-overview endpoints (v2).

Request handling policy
-----------------------
These endpoints are cache-first and never block on external data fetches.

1. Try the hot snapshot cache populated by
   :mod:`backend.core.market_pipeline`. A fresh or slightly-stale entry is
   returned immediately (single-digit-ms response time).
2. On a genuine cold miss, run ``build_overview`` inside a thread with a
   short deadline (``MARKET_REQUEST_DEADLINE_SECONDS``, default 3 s) so we
   never propagate upstream timeouts to the frontend.
3. If even the deadline path fails, return an empty skeleton with
   ``fallback_reason=warming`` so the UI renders its empty-state rather
   than 500ing.

A stale entry served from the cache is additionally asked to be
refreshed by the background pipeline via :func:`schedule_refresh`.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Query

from ..analytics.market import build_overview
from ..core.data_source import get_data_source
from ..core.envelope import ok
from ..core.market_pipeline import _cache_key, refresh_one
from ..core.snapshot_cache import hot_cache
from ..core.universe import get_universe


logger = logging.getLogger(__name__)
router = APIRouter()


HOT_TTL = float(os.getenv("MARKET_HOT_TTL_SECONDS", "120"))
REQUEST_DEADLINE = float(os.getenv("MARKET_REQUEST_DEADLINE_SECONDS", "3"))


def _empty_payload(market_view: str, time_window: str, reason: str) -> Dict[str, Any]:
    universe = get_universe(market_view)
    return {
        "market_view": market_view,
        "universe_id": universe.id,
        "universe_label": universe.label,
        "time_window": time_window,
        "indices": [],
        "signals": {
            "sector_rotation": {
                "ranked": [], "strongest": [], "candidate": [], "high_crowding": [],
                "method": "composite_sector_score", "method_version": "mkt.v2",
            },
            "liquidity_proxy": {
                "label": "流动性偏好代理",
                "disclaimer": "缓存预热中，尚无可用数据。",
                "top_inflows": [], "top_outflows": [],
                "universe_turnover_momentum": 0.0, "view": "sector_proxy",
            },
            "fund_flows": {
                "label": "流动性偏好代理", "disclaimer": "缓存预热中，尚无可用数据。",
                "top_inflows": [], "top_outflows": [],
                "universe_turnover_momentum": 0.0, "view": "liquidity_proxy",
            },
            "breadth": {
                "coverage": 0, "advancers_ratio": 0.0,
                "above_ma20_ratio": 0.0, "above_ma60_ratio": 0.0,
                "new_highs_60d": 0, "new_lows_60d": 0, "hotspot_concentration": 0.0,
                "limit_up": 0, "limit_down": 0, "turnover_change": 0.0, "market_heat": 0.0,
            },
            "cross_asset": [],
        },
        "explanations": [],
        "summary": "缓存预热中，请稍候。",
        "meta_hint": {"calculation_method_version": "mkt.v2", "evidence_count": 0},
        "_warming": True,
        "_fallback_reason": reason,
    }


def _empty_meta(reason: str) -> Dict[str, Any]:
    adapter = get_data_source()
    m = adapter.meta().to_dict()
    m["fallback_reason"] = reason
    m["is_realtime"] = False
    m["evidence_count"] = 0
    return m


async def _build_with_deadline(market_view: str, time_window: str) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    adapter = get_data_source()
    try:
        payload, src_meta, ev_count = await asyncio.wait_for(
            asyncio.to_thread(build_overview, adapter, time_window, market_view),
            timeout=REQUEST_DEADLINE,
        )
    except asyncio.TimeoutError:
        logger.info("market request deadline exceeded: %s/%s", market_view, time_window)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("market on-demand build failed for %s/%s: %s", market_view, time_window, exc)
        return None
    src_meta = dict(src_meta)
    src_meta["evidence_count"] = ev_count
    return payload, src_meta


def _schedule_background_refresh(market_view: str, time_window: str) -> None:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return
    asyncio.create_task(refresh_one(market_view, time_window))


async def _get_overview(market_view: str, time_window: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Return ``(payload, meta)``. Never raises, never blocks on upstream data."""
    adapter = get_data_source()
    key = _cache_key(market_view, time_window, adapter.name)

    cached = hot_cache().get_fresh_or_stale(key, ttl=HOT_TTL)
    if cached is not None:
        payload, meta, is_stale = cached
        if is_stale:
            _schedule_background_refresh(market_view, time_window)
        return payload, meta

    # Cold cache. Try to build with a short deadline so we don't stall.
    built = await _build_with_deadline(market_view, time_window)
    if built is not None:
        payload, meta = built
        hot_cache().put(key, payload, meta)
        return payload, meta

    # Deadline missed — trigger background refresh and hand back a
    # skeleton so the UI can render its empty states instead of 500.
    _schedule_background_refresh(market_view, time_window)
    return _empty_payload(market_view, time_window, "warming"), _empty_meta("warming")


@router.get("/overview")
async def market_overview(
    market_view: str = Query("cn_a"),
    time_window: str = Query("20D"),
    fields: Optional[List[str]] = Query(None),
) -> Dict[str, Any]:
    payload, meta = await _get_overview(market_view, time_window)
    if fields:
        keep = set(fields) | {"market_view", "time_window", "universe_id"}
        payload = {k: v for k, v in payload.items() if k in keep}
    return ok(payload, meta=meta)


@router.get("/indices")
async def indices(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    payload, meta = await _get_overview(market_view, time_window)
    return ok(payload.get("indices", []), meta=meta)


@router.get("/sector-rotation")
async def sector_rotation(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    payload, meta = await _get_overview(market_view, time_window)
    return ok(payload.get("signals", {}).get("sector_rotation", {}), meta=meta)


@router.get("/fund-flows")
async def fund_flows(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    payload, meta = await _get_overview(market_view, time_window)
    return ok(payload.get("signals", {}).get("liquidity_proxy", {}), meta=meta)


@router.get("/breadth")
async def breadth(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    payload, meta = await _get_overview(market_view, time_window)
    return ok(payload.get("signals", {}).get("breadth", {}), meta=meta)


@router.get("/cross-asset")
async def cross_asset(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    payload, meta = await _get_overview(market_view, time_window)
    return ok(payload.get("signals", {}).get("cross_asset", []), meta=meta)


@router.get("/explanations")
async def explanations(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    payload, meta = await _get_overview(market_view, time_window)
    return ok(
        {
            "explanations": payload.get("explanations", []),
            "summary": payload.get("summary", ""),
        },
        meta=meta,
    )
