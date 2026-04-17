"""Settings endpoints backed by the persistent user store.

Unifies enums (risk type, horizon, market view, research mode, theme,
export format, liquidity preference) so front and back never disagree on
what ``growth`` means vs ``进取型``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body
from pydantic import BaseModel, Field, field_validator

from ..core.data_source import get_data_source
from ..core.envelope import ok
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


_RISK_IDS = {r["id"] for r in RISK_TYPES}
_HORIZON_IDS = {h["id"] for h in INVESTMENT_HORIZONS}
_LIQ_IDS = {l["id"] for l in LIQUIDITY_PREFS}


class RiskProfile(BaseModel):
    risk_type: str = Field(..., description=" | ".join(sorted(_RISK_IDS)))
    investment_horizon: str = Field(..., description=" | ".join(sorted(_HORIZON_IDS)))
    drawdown_tolerance: Optional[float] = Field(None, ge=0.0, le=0.9)
    return_expectation: Optional[float] = Field(None, ge=-0.5, le=1.0)
    liquidity_preference: Optional[str] = Field(None, description=" | ".join(sorted(_LIQ_IDS)))
    defensive_ratio: Optional[float] = Field(None, ge=0.0, le=1.0)
    offensive_ratio: Optional[float] = Field(None, ge=0.0, le=1.0)
    questionnaire_score: Optional[int] = Field(None, ge=0, le=100)

    @field_validator("risk_type")
    @classmethod
    def _check_risk(cls, v: str) -> str:
        if v not in _RISK_IDS:
            raise ValueError(f"risk_type must be one of {sorted(_RISK_IDS)}")
        return v

    @field_validator("investment_horizon")
    @classmethod
    def _check_horizon(cls, v: str) -> str:
        if v not in _HORIZON_IDS:
            raise ValueError(f"investment_horizon must be one of {sorted(_HORIZON_IDS)}")
        return v

    @field_validator("liquidity_preference")
    @classmethod
    def _check_liq(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _LIQ_IDS:
            raise ValueError(f"liquidity_preference must be one of {sorted(_LIQ_IDS)}")
        return v


class Preferences(BaseModel):
    market_view: str = Field("cn_a")
    research_mode: str = Field("research")
    theme: str = Field("dark")
    default_export_format: List[str] = Field(default_factory=lambda: ["JSON", "Markdown"])
    include_global_events: bool = True
    include_charts_in_export: bool = True

    @field_validator("market_view")
    @classmethod
    def _v_market(cls, v: str) -> str:
        if v not in MARKET_VIEWS:
            raise ValueError(f"market_view must be one of {MARKET_VIEWS}")
        return v

    @field_validator("research_mode")
    @classmethod
    def _v_mode(cls, v: str) -> str:
        if v not in RESEARCH_MODES:
            raise ValueError(f"research_mode must be one of {RESEARCH_MODES}")
        return v

    @field_validator("theme")
    @classmethod
    def _v_theme(cls, v: str) -> str:
        if v not in THEMES:
            raise ValueError(f"theme must be one of {THEMES}")
        return v

    @field_validator("default_export_format")
    @classmethod
    def _v_formats(cls, v: List[str]) -> List[str]:
        for f in v:
            if f not in EXPORT_FORMATS:
                raise ValueError(f"format {f!r} not in {EXPORT_FORMATS}")
        return v


@router.get("/enums")
async def get_enums() -> Dict[str, Any]:
    """Return the canonical enum catalogue for frontend consumption."""
    adapter = get_data_source()
    meta = adapter.meta(universe="settings").to_dict()
    return ok(
        {
            "risk_types": RISK_TYPES,
            "investment_horizons": INVESTMENT_HORIZONS,
            "market_views": MARKET_VIEWS,
            "research_modes": RESEARCH_MODES,
            "themes": THEMES,
            "export_formats": EXPORT_FORMATS,
            "liquidity_preferences": LIQUIDITY_PREFS,
        },
        meta=meta,
    )


@router.get("/profile")
async def get_profile() -> Dict[str, Any]:
    adapter = get_data_source()
    store = get_user_store()
    return ok(store.get().profile, meta=adapter.meta(universe="settings").to_dict())


@router.put("/profile")
async def update_profile(profile: RiskProfile = Body(...)) -> Dict[str, Any]:
    adapter = get_data_source()
    store = get_user_store()
    updated = store.update_profile(profile.model_dump())
    # Invalidate portfolio / simulation caches since risk target changed.
    from ..core.snapshot_cache import hot_cache, warm_cache
    hot_cache().clear()
    warm_cache().clear()
    return ok(updated, meta=adapter.meta(universe="settings").to_dict())


@router.get("/preferences")
async def get_preferences() -> Dict[str, Any]:
    adapter = get_data_source()
    store = get_user_store()
    return ok(store.get().preferences, meta=adapter.meta(universe="settings").to_dict())


@router.put("/preferences")
async def update_preferences(prefs: Preferences = Body(...)) -> Dict[str, Any]:
    adapter = get_data_source()
    store = get_user_store()
    updated = store.update_preferences(prefs.model_dump())
    return ok(updated, meta=adapter.meta(universe="settings").to_dict())
