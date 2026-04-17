"""System-level endpoints (bootstrap, health)."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from ..analytics.portfolio import DEFAULT_PORTFOLIOS
from ..core.data_source import get_data_source
from ..core.envelope import ok


router = APIRouter()


@router.get("/bootstrap")
async def bootstrap() -> Dict[str, Any]:
    adapter = get_data_source()
    portfolios = [
        {"id": "pf_default", "label": "默认组合", "is_default": True},
        {"id": "pf_growth", "label": "成长激进组合", "is_default": False},
        {"id": "pf_balanced", "label": "平衡配置组合", "is_default": False},
        {"id": "all", "label": "全部组合汇总", "is_default": False},
    ]
    # keep only portfolios we actually know how to resolve
    portfolios = [p for p in portfolios if p["id"] in DEFAULT_PORTFOLIOS or p["id"] == "all"]

    data = {
        "markets": [
            {"id": "cn_a", "label": "A股主视角"},
            {"id": "hk", "label": "港股补充视角"},
            {"id": "global", "label": "全球联动视角"},
        ],
        "time_windows": ["5D", "20D", "60D", "120D", "YTD", "1Y", "CUSTOM"],
        "research_modes": [
            {"id": "light", "label": "轻量模式", "density": "comfortable"},
            {"id": "research", "label": "研究模式", "density": "compact"},
        ],
        "themes": [
            {"id": "dark", "label": "深色模式"},
            {"id": "light", "label": "浅色模式"},
            {"id": "system", "label": "跟随系统"},
        ],
        "portfolios": portfolios,
        "default_settings": {
            "market_view": "cn_a",
            "time_window": "20D",
            "research_mode": "research",
            "theme": "dark",
            "default_export_format": ["JSON", "Markdown"],
        },
        "funds": [
            {"code": code, "name": meta["name"], "type": meta["type"]}
            for code, meta in adapter.fund_metadata().items()
        ],
        "scenario_presets": [
            {"id": "hk_tech_drawdown", "label": "港股科技回撤"},
            {"id": "semi_recovery", "label": "半导体修复"},
            {"id": "pharma_rebound", "label": "医药反弹"},
            {"id": "global_risk_off", "label": "全球风险偏好下降"},
            {"id": "usd_strengthen", "label": "美元走强"},
        ],
    }
    return ok(data, meta=adapter.meta())


@router.get("/health")
async def health() -> Dict[str, Any]:
    adapter = get_data_source()
    return ok({"status": "ok"}, meta=adapter.meta())
