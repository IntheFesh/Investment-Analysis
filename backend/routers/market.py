"""Market-overview endpoints (cache-first, async-pipeline backed)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from ..core.envelope import ok
from ..core.market_pipeline import get_market_pipeline


router = APIRouter()


def _empty_overview(market_view: str, time_window: str) -> Dict[str, Any]:
    return {
        "market_view": market_view,
        "time_window": time_window,
        "universe_id": market_view,
        "indices": [],
        "top_metrics": [],
        "signals": {
            "sector_rotation": {"ranked": [], "strongest": [], "candidate": [], "high_crowding": []},
            "fund_flows": {"top_inflows": [], "top_outflows": [], "view": "liquidity_preference"},
            "liquidity_proxy": {"top_inflows": [], "top_outflows": [], "view": "liquidity_preference"},
            "breadth": {
                "coverage": 0,
                "advancers_ratio": 0.0,
                "decliners_ratio": 0.0,
                "above_ma20_ratio": 0.0,
                "above_ma60_ratio": 0.0,
                "new_high_ratio": 0.0,
                "new_low_ratio": 0.0,
                "limit_up": 0,
                "limit_down": 0,
                "hotspot_concentration": 0.0,
                "market_heat": 0.0,
                "diffusion": 0.0,
            },
            "cross_asset": [],
            "regime": {"label": "未知", "probability": 0.0, "duration_days": 0, "switch_risk": 0.0},
            "anomalies": [],
        },
        "explanations": [],
        "news": {"domestic": [], "international": []},
        "summary": "暂无可用快照，正在后台刷新。",
    }


def _get_overview(market_view: str, time_window: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
    pipeline = get_market_pipeline()
    payload, meta, layer = pipeline.get_snapshot(market_view, time_window)
    out_meta = dict(meta)
    out_meta["cache_layer"] = layer
    out_meta["pipeline_stats"] = pipeline.stats()

    if payload is None:
        pipeline.register_fallback_served()
        payload = _empty_overview(market_view, time_window)
        out_meta["fallback_reason"] = out_meta.get("fallback_reason") or "snapshot_not_ready"
        out_meta["is_realtime"] = False
    return payload, out_meta


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
    return ok(payload.get("indices", []), meta=meta)


@router.get("/sector-rotation")
async def sector_rotation(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    payload, meta = _get_overview(market_view, time_window)
    return ok(payload.get("signals", {}).get("sector_rotation", {}), meta=meta)


@router.get("/fund-flows")
async def fund_flows(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    payload, meta = _get_overview(market_view, time_window)
    return ok(payload.get("signals", {}).get("liquidity_proxy", {}), meta=meta)


@router.get("/breadth")
async def breadth(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    payload, meta = _get_overview(market_view, time_window)
    return ok(payload.get("signals", {}).get("breadth", {}), meta=meta)


@router.get("/cross-asset")
async def cross_asset(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    payload, meta = _get_overview(market_view, time_window)
    return ok(payload.get("signals", {}).get("cross_asset", []), meta=meta)


@router.get("/explanations")
async def explanations(time_window: str = Query("20D"), market_view: str = Query("cn_a")) -> Dict[str, Any]:
    payload, meta = _get_overview(market_view, time_window)
    return ok(
        {"explanations": payload.get("explanations", []), "summary": payload.get("summary", "")},
        meta=meta,
    )
