"""Risk sentiment endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Query

from ..analytics.sentiment import build_overview
from ..core.data_source import get_data_source
from ..core.envelope import ok


router = APIRouter()


@router.get("/overview")
async def sentiment_overview(
    market_view: str = Query("cn_a"),
    time_window: str = Query("20D"),
) -> Dict[str, Any]:
    adapter = get_data_source()
    payload = build_overview(adapter, time_window, market_view)
    return ok(payload, meta=adapter.meta())
