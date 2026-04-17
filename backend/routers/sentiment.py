"""Risk sentiment endpoints (v2) with last-good cache."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Query

from ..analytics.sentiment import build_overview
from ..core.data_source import get_data_source
from ..core.envelope import ok
from ..core.snapshot_cache import hot_cache


router = APIRouter()


@router.get("/overview")
async def sentiment_overview(
    market_view: str = Query("cn_a"),
    time_window: str = Query("20D"),
) -> Dict[str, Any]:
    adapter = get_data_source()
    key = f"sentiment:{market_view}:{time_window}:{adapter.name}"

    def rebuild():
        payload, src_meta, ev_count = build_overview(adapter, time_window, market_view)
        src_meta["evidence_count"] = ev_count
        return payload, src_meta

    payload, meta, _ = hot_cache().get(key, ttl=30.0, rebuild=rebuild)
    return ok(payload, meta=meta)


@router.get("/snapshot-light")
async def sentiment_snapshot_light(
    market_view: str = Query("cn_a"),
    time_window: str = Query("20D"),
) -> Dict[str, Any]:
    """Lightweight read used by other pages (portfolio diagnosis, simulation).

    Returns only scores + stress_parameters so callers avoid pulling the full
    payload. Backed by the same hot cache.
    """
    adapter = get_data_source()
    key = f"sentiment:{market_view}:{time_window}:{adapter.name}"

    def rebuild():
        payload, src_meta, ev_count = build_overview(adapter, time_window, market_view)
        src_meta["evidence_count"] = ev_count
        return payload, src_meta

    payload, meta, _ = hot_cache().get(key, ttl=30.0, rebuild=rebuild)
    slim = {
        "short_term_score": payload["short_term_score"],
        "mid_term_score": payload["mid_term_score"],
        "short_term_state": payload["short_term_state"],
        "mid_term_state": payload["mid_term_state"],
        "state_transition": payload["state_transition"],
        "stress_parameters": payload["stress_parameters"],
    }
    return ok(slim, meta=meta)
