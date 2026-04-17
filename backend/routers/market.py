"""Market-overview endpoints (v2)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from ..analytics.market import build_overview
from ..core.data_source import get_data_source
from ..core.envelope import ok
from ..core.snapshot_cache import hot_cache


router = APIRouter()


def _get_overview(market_view: str, time_window: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
    adapter = get_data_source()
    key = f"market:{market_view}:{time_window}:{adapter.name}"

    def rebuild():
        payload, src_meta, ev_count = build_overview(adapter, time_window, market_view)
        src_meta["evidence_count"] = ev_count
        return payload, src_meta

    payload, meta, _ = hot_cache().get(key, ttl=30.0, rebuild=rebuild)
    return payload, meta


@router.get("/overview")
async def market_overview(
    market_view: str = Query("cn_a"),
    time_window: str = Query("20D"),
    fields: Optional[List[str]] = Query(None),
) -> Dict[str, Any]:
    payload, meta = _get_overview(market_view, time_window)
    if fields:
        payload = {k: v for k, v in payload.items() if k in set(fields) | {"market_view", "time_window", "universe_id"}}
    return ok(payload, meta=meta)


@router.get("/indices")
async def indices(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    payload, meta = _get_overview(market_view, time_window)
    return ok(payload["indices"], meta=meta)


@router.get("/sector-rotation")
async def sector_rotation(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    payload, meta = _get_overview(market_view, time_window)
    return ok(payload["signals"]["sector_rotation"], meta=meta)


@router.get("/fund-flows")
async def fund_flows(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    payload, meta = _get_overview(market_view, time_window)
    return ok(payload["signals"]["liquidity_proxy"], meta=meta)


@router.get("/breadth")
async def breadth(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    payload, meta = _get_overview(market_view, time_window)
    return ok(payload["signals"]["breadth"], meta=meta)


@router.get("/cross-asset")
async def cross_asset(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    payload, meta = _get_overview(market_view, time_window)
    return ok(payload["signals"]["cross_asset"], meta=meta)


@router.get("/explanations")
async def explanations(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    payload, meta = _get_overview(market_view, time_window)
    return ok(
        {"explanations": payload["explanations"], "summary": payload["summary"]},
        meta=meta,
    )
