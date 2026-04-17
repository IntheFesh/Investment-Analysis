"""System bootstrap + health."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from ..analytics.portfolio import DEFAULT_PORTFOLIOS
from ..analytics.simulation import HISTORICAL_EVENTS, SCENARIO_PRESETS
from ..core.data_source import get_data_source
from ..core.envelope import ok
from ..core.universe import UNIVERSES
from ..core.user_store import (
    EXPORT_FORMATS,
    INVESTMENT_HORIZONS,
    LIQUIDITY_PREFS,
    MARKET_VIEWS,
    RESEARCH_MODES,
    RISK_TYPES,
    THEMES,
    get_user_store,
)


router = APIRouter()


@router.get("/bootstrap")
async def bootstrap() -> Dict[str, Any]:
    adapter = get_data_source()
    user = get_user_store().get()

    portfolios = [
        {"id": "pf_default",  "label": "默认组合",     "is_default": True},
        {"id": "pf_growth",   "label": "成长激进组合", "is_default": False},
        {"id": "pf_balanced", "label": "平衡配置组合", "is_default": False},
        {"id": "all",         "label": "全部组合汇总", "is_default": False},
    ]
    portfolios = [p for p in portfolios if p["id"] in DEFAULT_PORTFOLIOS or p["id"] == "all"]

    data = {
        "markets": [{"id": u.id, "label": u.label, "hint": u.narrative_hint} for u in UNIVERSES.values()],
        "research_modes": [
            {"id": "light",    "label": "轻量模式", "density": "comfortable"},
            {"id": "research", "label": "研究模式", "density": "compact"},
        ],
        "themes": [{"id": t, "label": {"dark": "深色模式", "light": "浅色模式", "system": "跟随系统"}[t]} for t in THEMES],
        "portfolios": portfolios,
        "enums": {
            "risk_types": RISK_TYPES,
            "investment_horizons": INVESTMENT_HORIZONS,
            "market_views": MARKET_VIEWS,
            "research_modes": RESEARCH_MODES,
            "themes": THEMES,
            "export_formats": EXPORT_FORMATS,
            "liquidity_preferences": LIQUIDITY_PREFS,
        },
        "default_settings": {
            "market_view": user.preferences.get("market_view", "cn_a"),
            "research_mode": user.preferences.get("research_mode", "research"),
            "theme": user.preferences.get("theme", "dark"),
            "default_export_format": user.preferences.get("default_export_format", ["JSON", "Markdown"]),
        },
        "profile": user.profile,
        "funds": [
            {"code": code, "name": meta["name"], "type": meta["type"], "region": meta.get("region", "CN")}
            for code, meta in adapter.fund_metadata().items()
        ],
        "scenario_presets": [{"id": sid, "label": preset["label"], "factors": preset["factors"]} for sid, preset in SCENARIO_PRESETS.items()],
        "historical_events": [{"id": eid, "label": ev["label"], "description": ev["description"]} for eid, ev in HISTORICAL_EVENTS.items()],
        "data_source": {
            "name": adapter.name,
            "tier": adapter.tier,
            "truth_grade": adapter.truth_grade,
            "license_scope": adapter.license_scope,
            "delay_seconds": adapter.delay_seconds,
            "is_realtime": adapter.is_realtime,
        },
    }
    return ok(data, meta=adapter.meta(universe="system").to_dict())


@router.get("/health")
async def health() -> Dict[str, Any]:
    adapter = get_data_source()
    return ok({"status": "ok"}, meta=adapter.meta(universe="system").to_dict())
