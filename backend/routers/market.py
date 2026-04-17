"""Market-overview endpoints (cache-first, async-pipeline backed).

Read path is strictly cache-first (L1 -> L2 -> L3). On a total miss we
return a deterministic demo snapshot produced inline so the frontend never
times out; a background refresh against the real adapter is enqueued by
``MarketSnapshotPipeline.get_snapshot``.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Query

from ..analytics.market import build_overview
from ..core.data_source import DemoSnapshotAdapter, get_data_source
from ..core.envelope import ok
from ..core.market_pipeline import get_market_pipeline


logger = logging.getLogger(__name__)
router = APIRouter()


def _inline_demo_overview(market_view: str, time_window: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Synchronous deterministic overview — last-resort fallback (no network)."""
    demo = DemoSnapshotAdapter()
    try:
        payload, src_meta, ev_count = build_overview(demo, time_window, market_view)
        src_meta["evidence_count"] = ev_count
        src_meta["snapshot_mode"] = "inline_demo"
        src_meta["fallback_reason"] = "snapshot_not_ready"
        src_meta["freshness_label"] = "fallback"
        return payload, src_meta
    except Exception as exc:  # noqa: BLE001
        return (
            {
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
                "news": {"domestic": [], "international": [], "status": "refreshing", "age_seconds": None},
                "summary": "暂无可用快照，正在后台刷新。",
            },
            {
                "source_name": "inline-demo",
                "source_tier": "fallback_demo",
                "truth_grade": "E",
                "is_demo": True,
                "is_realtime": False,
                "fallback_reason": f"inline_demo_error: {exc}",
                "snapshot_mode": "inline_demo",
            },
        )


def _get_overview(market_view: str, time_window: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    pipeline = get_market_pipeline()
    payload, meta, layer = pipeline.get_snapshot(market_view, time_window)
    out_meta = dict(meta)
    out_meta["cache_layer"] = layer
    out_meta["pipeline_stats"] = pipeline.stats()

    if payload is None:
        pipeline.register_fallback_served()
        payload, demo_meta = _inline_demo_overview(market_view, time_window)
        out_meta.update({k: v for k, v in demo_meta.items() if v is not None})
        out_meta["cache_layer"] = "inline_demo"
        out_meta["is_realtime"] = False
        out_meta.setdefault("fallback_reason", "snapshot_not_ready")
    return payload, out_meta


async def _upgrade_live_if_needed(
    market_view: str,
    time_window: str,
    payload: Dict[str, Any],
    meta: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """When cached data is fallback-demo, try one bounded live refresh.

    This keeps the page usable on cold start while still honoring the
    "open-source realtime" requirement whenever upstream responds quickly.
    """
    if (meta.get("source_tier") or "").lower() != "fallback_demo":
        return payload, meta

    def _build_live() -> Tuple[Dict[str, Any], Dict[str, Any]]:
        live_payload, src_meta, ev_count = build_overview(get_data_source(), time_window, market_view)
        src_meta["evidence_count"] = ev_count
        src_meta["snapshot_mode"] = "request_live_upgrade"
        tier = (src_meta.get("source_tier") or "").lower()
        if tier == "production_authorized":
            src_meta["freshness_label"] = "realtime"
        elif tier == "production_delayed":
            src_meta["freshness_label"] = "delayed"
        elif tier in {"research_only", "derived"}:
            src_meta["freshness_label"] = "research"
        else:
            src_meta["freshness_label"] = "fallback"
        return live_payload, src_meta

    try:
        live_payload, live_meta = await asyncio.wait_for(asyncio.to_thread(_build_live), timeout=6.0)
        merged_meta = dict(meta)
        merged_meta.update({k: v for k, v in live_meta.items() if v is not None})
        merged_meta["cache_layer"] = "request_live"
        return live_payload, merged_meta
    except Exception:  # noqa: BLE001
        return payload, meta


@router.get("/overview")
async def market_overview(
    market_view: str = Query("cn_a"),
    time_window: str = Query("20D"),
    fields: Optional[List[str]] = Query(None),
) -> Dict[str, Any]:
    payload, meta = _get_overview(market_view, time_window)
    payload, meta = await _upgrade_live_if_needed(market_view, time_window, payload, meta)
    if fields:
        keep = set(fields) | {"market_view", "time_window", "universe_id"}
        payload = {k: v for k, v in payload.items() if k in keep}
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
    payload, meta = await _upgrade_live_if_needed(market_view, time_window, payload, meta)
    return ok(
        {"explanations": payload.get("explanations", []), "summary": payload.get("summary", "")},
        meta=meta,
    )
