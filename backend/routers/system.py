"""
System router: endpoints relating to application bootstrapping and global configuration.

This router exposes a single endpoint used by the front‑end to obtain a base
configuration when the application first loads.  It returns available market
views, time windows, research modes, user portfolio summaries and default
preferences.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter()


@router.get("/bootstrap")
async def bootstrap() -> Dict[str, Any]:
    """Return base configuration data required during application start.

    The payload includes lists of selectable options and default preferences.
    In a full implementation these values would be loaded from a database
    or configuration file and customised per user.
    """
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    data = {
        "market_views": ["A股主视角", "港股补充视角", "全球联动视角"],
        "time_windows": ["5D", "20D", "60D", "120D", "YTD", "1Y"],
        "research_modes": ["轻量模式", "研究模式"],
        "default_settings": {
            "market_view": "A股主视角",
            "time_window": "20D",
            "research_mode": "轻量模式",
            "default_export_format": ["JSON", "Markdown"],
        },
        "portfolios": [],
    }
    return {
        "success": True,
        "message": "ok",
        "data": data,
        "meta": {"timestamp": timestamp, "version": "v1"},
    }