"""Settings endpoints: risk profile + preferences.

Values are held in an in-memory dict keyed by a static ``default`` user; this
is the right shape for a local / demo deployment without auth. Swap for a
database-backed store once identity is wired in.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body
from pydantic import BaseModel, Field

from ..core.data_source import get_data_source
from ..core.envelope import ok


router = APIRouter()


class RiskProfile(BaseModel):
    risk_type: str = Field(..., description="保守型 | 平衡型 | 进攻型")
    investment_horizon: str = Field("3Y")
    defensive_ratio: Optional[float] = 0.4
    offensive_ratio: Optional[float] = 0.6
    questionnaire_score: Optional[int] = None


class Preferences(BaseModel):
    market_view: str = "cn_a"
    time_window: str = "20D"
    research_mode: str = "research"
    theme: str = "dark"
    default_export_format: List[str] = Field(default_factory=lambda: ["JSON", "Markdown"])
    include_global_events: bool = True
    include_charts_in_export: bool = True


_STORE: Dict[str, Any] = {
    "profile": RiskProfile(risk_type="平衡型", investment_horizon="3Y", defensive_ratio=0.4, offensive_ratio=0.6).model_dump(),
    "preferences": Preferences().model_dump(),
}


@router.get("/profile")
async def get_profile() -> Dict[str, Any]:
    adapter = get_data_source()
    return ok(_STORE["profile"], meta=adapter.meta())


@router.put("/profile")
async def update_profile(profile: RiskProfile = Body(...)) -> Dict[str, Any]:
    adapter = get_data_source()
    _STORE["profile"] = profile.model_dump()
    return ok(_STORE["profile"], meta=adapter.meta())


@router.get("/preferences")
async def get_preferences() -> Dict[str, Any]:
    adapter = get_data_source()
    return ok(_STORE["preferences"], meta=adapter.meta())


@router.put("/preferences")
async def update_preferences(prefs: Preferences = Body(...)) -> Dict[str, Any]:
    adapter = get_data_source()
    _STORE["preferences"] = prefs.model_dump()
    return ok(_STORE["preferences"], meta=adapter.meta())
