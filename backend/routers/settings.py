"""
Settings router: endpoints to retrieve and update user preferences and risk profile.

These endpoints manage per‑user configuration such as risk tolerance, investment
horizon and default display preferences.  In a real implementation the settings
would be stored in a database keyed by the authenticated user.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body
from pydantic import BaseModel

router = APIRouter()


class RiskProfile(BaseModel):
    risk_type: str
    investment_horizon: str
    defensive_ratio: Optional[float] = None
    offensive_ratio: Optional[float] = None


class Preferences(BaseModel):
    market_view: str
    time_window: str
    research_mode: str
    default_export_format: list[str]


@router.get("/profile")
async def get_risk_profile() -> Dict[str, Any]:
    """Return the current risk profile settings (placeholder)."""
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    profile = RiskProfile(risk_type="平衡型", investment_horizon="3Y", defensive_ratio=0.4, offensive_ratio=0.6)
    return {
        "success": True,
        "message": "ok",
        "data": profile.dict(),
        "meta": {"timestamp": timestamp, "version": "v1"},
    }


@router.put("/profile")
async def update_risk_profile(profile: RiskProfile = Body(...)) -> Dict[str, Any]:
    """Update the risk profile settings (placeholder)."""
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    # In a real implementation we would persist the updated profile here
    return {
        "success": True,
        "message": "ok",
        "data": profile.dict(),
        "meta": {"timestamp": timestamp, "version": "v1"},
    }


@router.get("/preferences")
async def get_preferences() -> Dict[str, Any]:
    """Return the current user preferences (placeholder)."""
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    prefs = Preferences(
        market_view="A股主视角",
        time_window="20D",
        research_mode="轻量模式",
        default_export_format=["JSON", "Markdown"],
    )
    return {
        "success": True,
        "message": "ok",
        "data": prefs.dict(),
        "meta": {"timestamp": timestamp, "version": "v1"},
    }


@router.put("/preferences")
async def update_preferences(prefs: Preferences = Body(...)) -> Dict[str, Any]:
    """Update user preferences (placeholder)."""
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    return {
        "success": True,
        "message": "ok",
        "data": prefs.dict(),
        "meta": {"timestamp": timestamp, "version": "v1"},
    }