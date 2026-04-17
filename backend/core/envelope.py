"""Unified response envelope with full data-truth metadata.

Every router returns ``{success, message, data, meta, error_code?}``.

``meta`` carries a full honesty contract — the frontend uses it to display
exactly what the user is looking at:

- ``timestamp``: ISO8601 UTC of response build time (``computed_at`` alias)
- ``version``: "v1"
- ``source_name``: concrete adapter id (e.g. "demo-snapshot", "akshare-delayed15m")
- ``source_tier``: one of ``production_authorized`` | ``research_only`` |
                   ``fallback_demo`` | ``derived``
- ``truth_grade``: ``A`` (live, authorized)  | ``B`` (delayed live) |
                   ``C`` (research/open-source, non-commercial) |
                   ``D`` (proxy / derived) | ``E`` (demo / synthetic)
- ``is_demo``: True when data is synthetic
- ``is_proxy``: True when a surrogate stands in for the target universe
- ``is_realtime``: True when snapshot is < 60s old
- ``delay_seconds``: provider's disclosed delay (0 if not disclosed)
- ``license_scope``: "commercial" | "research_only" | "internal_preview"
- ``fallback_reason``: reason string if source degraded, else None
- ``trading_day``: the trading day the snapshot represents (YYYY-MM-DD)
- ``computed_at``: same as ``timestamp`` (kept explicit for audit)
- ``coverage_universe``: id of the universe (e.g. "cn_a_all", "hs300")
- ``calculation_method_version``: versioned hash of algorithm
- ``evidence_count``: number of traceable evidence items in this payload
- ``market_session``: "pre" | "open" | "close" | "after" | "snapshot"
- ``tz``: timezone of as_of

Backwards-compat: ``data_source`` / ``as_of_trading_day`` / ``as_of`` are
kept as aliases so frontend code that already reads them keeps working.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional


DEFAULT_META: Dict[str, Any] = {
    "source_name": "unknown",
    "source_tier": "fallback_demo",
    "truth_grade": "E",
    "is_demo": True,
    "is_proxy": False,
    "is_realtime": False,
    "delay_seconds": 0,
    "license_scope": "internal_preview",
    "fallback_reason": None,
    "trading_day": None,
    "coverage_universe": "unknown",
    "calculation_method_version": "v0",
    "evidence_count": 0,
    "market_session": "snapshot",
    "tz": "UTC",
}


def _coerce(source_meta: Any) -> Optional[Mapping[str, Any]]:
    if source_meta is None:
        return None
    if hasattr(source_meta, "to_dict"):
        return source_meta.to_dict()
    if isinstance(source_meta, Mapping):
        return source_meta
    return dict(source_meta)


def build_meta(source_meta: Any = None) -> Dict[str, Any]:
    now = datetime.now(tz=timezone.utc)
    meta: Dict[str, Any] = {
        "timestamp": now.isoformat(),
        "computed_at": now.isoformat(),
        "version": "v1",
    }
    meta.update(DEFAULT_META)
    source = _coerce(source_meta)
    if source:
        meta.update({k: v for k, v in source.items() if v is not None or k in DEFAULT_META})
    # Legacy aliases - keep so existing frontends work unchanged.
    meta.setdefault("data_source", meta.get("source_name"))
    meta.setdefault("as_of_trading_day", meta.get("trading_day"))
    meta.setdefault("as_of", meta.get("computed_at"))
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
    return {
        "success": False,
        "message": message,
        "error_code": error_code,
        "data": data,
        "meta": build_meta(meta),
        "_http_status": http_status,
    }


def merge_meta(base: Optional[Mapping[str, Any]], extra: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """Merge two meta dicts with ``extra`` taking precedence."""

    out: Dict[str, Any] = {}
    if base:
        out.update(base)
    if extra:
        out.update({k: v for k, v in extra.items() if v is not None})
    return out
