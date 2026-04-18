"""Risk sentiment endpoints (v2) with last-good cache and deadline reads."""

from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import APIRouter, Query

from ..analytics.greed import build_greed_index
from ..analytics.sentiment import build_empty_payload, build_overview
from ..core.data_source import get_data_source
from ..core.envelope import ok
from ..core.snapshot_cache import hot_cache


router = APIRouter()


_SENTIMENT_DEADLINE = float(os.getenv("SENTIMENT_READ_DEADLINE_SECONDS", "4.0"))
_SENTIMENT_TTL = float(os.getenv("SENTIMENT_CACHE_TTL", "60.0"))
_GREED_DEADLINE = float(os.getenv("GREED_READ_DEADLINE_SECONDS", "4.0"))
_GREED_TTL = float(os.getenv("GREED_CACHE_TTL", "60.0"))


def _sentiment_key(market_view: str, time_window: str, adapter_name: str) -> str:
    return f"sentiment:{market_view}:{time_window}:{adapter_name}"


def _read_sentiment(market_view: str, time_window: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
    adapter = get_data_source()
    key = _sentiment_key(market_view, time_window, adapter.name)

    def rebuild():
        payload, src_meta, ev_count = build_overview(adapter, time_window, market_view)
        src_meta["evidence_count"] = ev_count
        return payload, src_meta

    try:
        payload, meta, _ = hot_cache().get_with_deadline(
            key, ttl=_SENTIMENT_TTL, deadline_seconds=_SENTIMENT_DEADLINE, rebuild=rebuild,
        )
        return payload, meta
    except Exception as exc:  # noqa: BLE001
        # No cached value and rebuild failed — return a schema-valid skeleton
        # so the UI renders an explicit "计算中" state instead of a timeout.
        empty_payload = build_empty_payload(market_view, time_window)
        empty_meta = adapter.meta(universe=market_view, fallback_reason=f"sentiment_unavailable: {exc}").to_dict()
        empty_meta["partial"] = True
        empty_meta["is_stale"] = True
        return empty_payload, empty_meta


@router.get("/overview")
async def sentiment_overview(
    market_view: str = Query("cn_a"),
    time_window: str = Query("20D"),
) -> Dict[str, Any]:
    payload, meta = _read_sentiment(market_view, time_window)
    return ok(payload, meta=meta)


@router.get("/snapshot-light")
async def sentiment_snapshot_light(
    market_view: str = Query("cn_a"),
    time_window: str = Query("20D"),
) -> Dict[str, Any]:
    """Lightweight read used by other pages (portfolio diagnosis, simulation).

    Returns only scores + stress_parameters so callers avoid pulling the full
    payload. Backed by the same hot cache with deadline semantics.
    """
    payload, meta = _read_sentiment(market_view, time_window)
    slim = {
        "short_term_score": payload.get("short_term_score", 50.0),
        "mid_term_score": payload.get("mid_term_score", 50.0),
        "short_term_state": payload.get("short_term_state", "neutral"),
        "mid_term_state": payload.get("mid_term_state", "neutral"),
        "state_transition": payload.get("state_transition", {"direction": "stable", "delta": 0.0}),
        "stress_parameters": payload.get("stress_parameters", {
            "equity_shock_multiplier": 1.0,
            "volatility_scale": 1.0,
            "cross_asset_spillover": 0.3,
        }),
    }
    return ok(slim, meta=meta)


def _read_greed(market_view: str) -> tuple[Dict[str, Any], Dict[str, Any]]:
    adapter = get_data_source()
    key = f"greed:{market_view}:{adapter.name}"

    def rebuild():
        payload, src_meta = build_greed_index(adapter, market_view)
        return payload, src_meta

    try:
        payload, meta, _ = hot_cache().get_with_deadline(
            key, ttl=_GREED_TTL, deadline_seconds=_GREED_DEADLINE, rebuild=rebuild,
        )
        return payload, meta
    except Exception as exc:  # noqa: BLE001
        empty_payload = {
            "market_view": market_view,
            "score": 50.0,
            "state": "neutral",
            "state_label": "中性",
            "as_of": None,
            "components": {
                "volume": {"score": 50.0, "weight": 0.5, "evidence": {"reason": "unavailable"}},
                "breadth": {"score": 50.0, "weight": 0.5, "evidence": {"reason": "unavailable"}},
            },
            "method_version": "greed.v1",
        }
        empty_meta = adapter.meta(universe=market_view, fallback_reason=f"greed_unavailable: {exc}").to_dict()
        empty_meta["partial"] = True
        empty_meta["is_stale"] = True
        return empty_payload, empty_meta


@router.get("/greed-index")
async def sentiment_greed_index(
    market_view: str = Query("cn_a"),
) -> Dict[str, Any]:
    """A 股贪婪指数（初版）——成交量 + 涨跌家数合成 0-100 分。"""
    payload, meta = _read_greed(market_view)
    return ok(payload, meta=meta)
