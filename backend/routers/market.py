"""Market-overview endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from ..analytics.market import build_overview
from ..core.data_source import get_data_source
from ..core.envelope import ok


router = APIRouter()


@router.get("/overview")
async def market_overview(
    market_view: str = Query("cn_a"),
    time_window: str = Query("20D"),
    fields: Optional[List[str]] = Query(None),
) -> Dict[str, Any]:
    adapter = get_data_source()
    payload = build_overview(adapter, time_window, market_view)
    if fields:
        payload = {k: v for k, v in payload.items() if k in set(fields) | {"market_view", "time_window"}}
    return ok(payload, meta=adapter.meta())


@router.get("/indices")
async def indices(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    adapter = get_data_source()
    payload = build_overview(adapter, time_window, market_view)
    return ok(payload["indices"], meta=adapter.meta())


@router.get("/sector-rotation")
async def sector_rotation(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    adapter = get_data_source()
    payload = build_overview(adapter, time_window, market_view)
    return ok(payload["signals"]["sector_rotation"], meta=adapter.meta())


@router.get("/fund-flows")
async def fund_flows(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    adapter = get_data_source()
    payload = build_overview(adapter, time_window, market_view)
    return ok(payload["signals"]["fund_flows"], meta=adapter.meta())


@router.get("/breadth")
async def breadth(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    adapter = get_data_source()
    payload = build_overview(adapter, time_window, market_view)
    return ok(payload["signals"]["breadth"], meta=adapter.meta())


@router.get("/explanations")
async def explanations(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    adapter = get_data_source()
    payload = build_overview(adapter, time_window, market_view)
    return ok(
        {"explanations": payload["explanations"], "summary": payload["summary"]},
        meta=adapter.meta(),
    )
