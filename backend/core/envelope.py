"""Unified response envelope.

Every router returns ``{success, message, data, meta, error_code?}``.
``meta`` always carries:
- ``timestamp``: ISO8601 UTC of response build time
- ``version``: "v1"
- ``data_source``: adapter identifier (demo / yfinance / akshare / ...)
- ``is_demo``: True when data is synthetic / snapshot / stale
- ``as_of_trading_day``: the trading day the snapshot represents (YYYY-MM-DD)
- ``market_session``: "pre" | "open" | "close" | "after" | "snapshot"
- ``tz``: timezone of as_of, e.g. "Asia/Shanghai" or "UTC"
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional


def build_meta(source_meta: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    meta: Dict[str, Any] = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "version": "v1",
    }
    if source_meta:
        meta.update(source_meta)
    return meta


def ok(data: Any, *, meta: Optional[Mapping[str, Any]] = None, message: str = "ok") -> Dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": data,
        "meta": build_meta(meta),
    }


def failure(
    error_code: str,
    message: str,
    *,
    data: Any = None,
    meta: Optional[Mapping[str, Any]] = None,
    http_status: int = 400,
) -> Dict[str, Any]:
    # Used as return value; FastAPI routes return this with a chosen status_code
    return {
        "success": False,
        "message": message,
        "error_code": error_code,
        "data": data,
        "meta": build_meta(meta),
        "_http_status": http_status,
    }
