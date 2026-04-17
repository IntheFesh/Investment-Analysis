"""Persistent user settings store (file-backed).

Single-user local deployment; swap for a DB once auth lands.

Persists to ``$DATA_DIR/user_settings.json`` (defaults to
``./backend/data/user_settings.json``). Thread-safe with a coarse lock.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


DATA_DIR = Path(os.getenv("DATA_DIR", str(Path(__file__).resolve().parent.parent / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

_SETTINGS_PATH = DATA_DIR / "user_settings.json"


# Canonical enums. One language-neutral id + human label mapping per enum.
RISK_TYPES = [
    {"id": "conservative", "label_zh": "稳健型",  "target_vol": (0.04, 0.10), "defensive_ratio": 0.70},
    {"id": "balanced",     "label_zh": "平衡型",  "target_vol": (0.10, 0.16), "defensive_ratio": 0.45},
    {"id": "growth",       "label_zh": "进取型",  "target_vol": (0.14, 0.22), "defensive_ratio": 0.30},
    {"id": "aggressive",   "label_zh": "激进型",  "target_vol": (0.20, 0.32), "defensive_ratio": 0.15},
]

INVESTMENT_HORIZONS = [
    {"id": "short", "label_zh": "短期", "years": 0.5, "drawdown_tolerance": 0.08},
    {"id": "mid",   "label_zh": "中期", "years": 2.0, "drawdown_tolerance": 0.18},
    {"id": "long",  "label_zh": "长期", "years": 5.0, "drawdown_tolerance": 0.30},
]

MARKET_VIEWS = ["cn_a", "hk", "global"]
RESEARCH_MODES = ["light", "research"]
THEMES = ["dark", "light", "system"]
EXPORT_FORMATS = ["JSON", "Markdown", "CSV", "PNG"]
LIQUIDITY_PREFS = [
    {"id": "high", "label_zh": "高流动性"},
    {"id": "mid",  "label_zh": "平衡流动性"},
    {"id": "low",  "label_zh": "可接受低流动性"},
]


DEFAULT_PROFILE: Dict[str, Any] = {
    "risk_type": "balanced",
    "investment_horizon": "mid",
    "drawdown_tolerance": 0.18,
    "return_expectation": 0.10,
    "liquidity_preference": "mid",
    "defensive_ratio": 0.45,
    "offensive_ratio": 0.55,
    "questionnaire_score": None,
}

DEFAULT_PREFERENCES: Dict[str, Any] = {
    "market_view": "cn_a",
    "research_mode": "research",
    "theme": "dark",
    "default_export_format": ["JSON", "Markdown"],
    "include_global_events": True,
    "include_charts_in_export": True,
}


@dataclass
class UserSettings:
    profile: Dict[str, Any]
    preferences: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {"profile": self.profile, "preferences": self.preferences}


class UserStore:
    def __init__(self, path: Path = _SETTINGS_PATH) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._cache: Optional[UserSettings] = None

    def _load_raw(self) -> Dict[str, Any]:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("corrupt settings file, ignoring: %s", exc)
            return {}

    def _write_raw(self, payload: Dict[str, Any]) -> None:
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self) -> UserSettings:
        with self._lock:
            if self._cache is not None:
                return self._cache
            raw = self._load_raw()
            profile = {**DEFAULT_PROFILE, **(raw.get("profile") or {})}
            prefs = {**DEFAULT_PREFERENCES, **(raw.get("preferences") or {})}
            self._cache = UserSettings(profile=profile, preferences=prefs)
            return self._cache

    def update_profile(self, patch: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            current = self.get()
            merged = {**current.profile, **patch}
            # derive drawdown_tolerance from horizon if caller did not set it
            horizon = next((h for h in INVESTMENT_HORIZONS if h["id"] == merged.get("investment_horizon")), None)
            if horizon and patch.get("drawdown_tolerance") is None and "drawdown_tolerance" not in patch:
                merged.setdefault("drawdown_tolerance", horizon["drawdown_tolerance"])
            self._cache = UserSettings(profile=merged, preferences=current.preferences)
            self._write_raw(self._cache.to_dict())
            return merged

    def update_preferences(self, patch: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            current = self.get()
            merged = {**current.preferences, **patch}
            self._cache = UserSettings(profile=current.profile, preferences=merged)
            self._write_raw(self._cache.to_dict())
            return merged


_STORE: Optional[UserStore] = None


def get_user_store() -> UserStore:
    global _STORE
    if _STORE is None:
        _STORE = UserStore()
    return _STORE


def risk_profile_target(risk_type: str) -> Dict[str, Any]:
    for r in RISK_TYPES:
        if r["id"] == risk_type:
            return r
    return RISK_TYPES[1]  # balanced fallback


def horizon_spec(horizon: str) -> Dict[str, Any]:
    for h in INVESTMENT_HORIZONS:
        if h["id"] == horizon:
            return h
    return INVESTMENT_HORIZONS[1]
