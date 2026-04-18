"""Unified response envelope with full data-truth metadata.

Every router returns ``{success, status, message, data, meta, error_code?}``.

``status`` is the coarse state the frontend branches on:

- ``success``  — live/delayed real data within freshness budget.
- ``partial``  — real data but with some factors/fields missing; UI should
                 still render, but explicit "partial" badges must show.
- ``degraded`` — served from stale cache, negative-cache, or a proxy that
                 the user needs to be warned about. Still HTTP 200.
- ``failed``   — no data could be produced (and no acceptable fallback
                 exists). HTTP 502/503 so monitoring pages react.

``meta`` carries the full honesty contract:

- ``timestamp`` / ``computed_at``: ISO8601 UTC of response build time.
- ``version``:             envelope schema version ("v1").
- ``schema_version``:      per-endpoint payload schema version.
- ``trace_id``:            request-scoped id, echoed in logs & debug probes.
- ``latency_ms``:          total server-side latency for this request.
- ``source_name`` / ``source_tier`` / ``truth_grade``: vendor truth badges.
- ``source_vendor``:       the concrete upstream vendor (eastmoney/tencent/
                           akshare/yahoo/cache/demo) that produced the data.
- ``as_of``:               ISO timestamp of the datum itself (not response).
- ``is_stale``:            True if payload is outside the freshness budget.
- ``cache_hit``:           True if served (fully or partially) from cache.
- ``fallback_used``:       True if any fallback path was taken.
- ``degraded_reason``:     structured reason code when status != success.
- ``market_phase``:        open|closed|holiday|preopen|postclose|snapshot.
- ``is_demo`` / ``is_proxy`` / ``is_realtime`` / ``delay_seconds``:
                           existing truth badges (retained).
- ``license_scope``:       commercial|research_only|internal_preview.
- ``trading_day``:         the trading day the snapshot represents.
- ``coverage_universe``:   id of the universe (e.g. "cn_a_all", "hs300").
- ``calculation_method_version``: versioned algorithm hash.
- ``evidence_count``:      number of traceable evidence items.

Backwards-compat: ``data_source`` / ``as_of_trading_day`` / ``as_of`` are
kept as aliases so frontend code that already reads them keeps working.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional


# ---------------------------------------------------------------------------
# Status hierarchy
# ---------------------------------------------------------------------------


STATUS_SUCCESS = "success"
STATUS_PARTIAL = "partial"
STATUS_DEGRADED = "degraded"
STATUS_FAILED = "failed"

ALL_STATUSES = (STATUS_SUCCESS, STATUS_PARTIAL, STATUS_DEGRADED, STATUS_FAILED)


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
    # Round-0 additions
    "source_vendor": None,
    "is_stale": False,
    "cache_hit": False,
    "fallback_used": False,
    "degraded_reason": None,
    "market_phase": None,
    "schema_version": "v1",
    "latency_ms": None,
    "trace_id": None,
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
    # Auto-stamp trace_id from the request-scoped contextvar if caller did
    # not already override it. Keeps routers free of boilerplate.
    try:  # pragma: no cover - trivial
        from .runtime import current_trace_id
        if not meta.get("trace_id") or meta.get("trace_id") == "-":
            tid = current_trace_id()
            if tid and tid != "-":
                meta["trace_id"] = tid
    except Exception:  # noqa: BLE001
        pass
    # Legacy aliases - keep so existing frontends work unchanged.
    meta.setdefault("data_source", meta.get("source_name"))
    meta.setdefault("as_of_trading_day", meta.get("trading_day"))
    meta.setdefault("as_of", meta.get("computed_at"))
    return meta


def _infer_status(meta: Mapping[str, Any]) -> str:
    """Infer status from meta when caller hasn't set one explicitly.

    Preserves backwards compatibility for routers that have not yet been
    migrated to the explicit status kwarg.
    """
    if meta.get("is_demo") or (meta.get("source_tier") == "fallback_demo"):
        return STATUS_DEGRADED
    if meta.get("fallback_used") or meta.get("fallback_reason"):
        return STATUS_DEGRADED
    if meta.get("is_stale"):
        return STATUS_DEGRADED
    if meta.get("partial"):
        return STATUS_PARTIAL
    return STATUS_SUCCESS


def ok(
    data: Any,
    *,
    meta: Optional[Mapping[str, Any]] = None,
    message: str = "ok",
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a success/partial/degraded envelope (HTTP 200).

    If ``status`` is not provided it is inferred from ``meta`` so legacy
    callers keep working. New code should pass ``status`` explicitly.
    """
    built = build_meta(meta)
    resolved = status if status in ALL_STATUSES else _infer_status(built)
    if resolved == STATUS_FAILED:
        # ``ok`` is reserved for 200-style responses; callers that truly
        # want FAILED must go through ``failure()``.
        resolved = STATUS_DEGRADED
    return {
        "success": resolved == STATUS_SUCCESS,
        "status": resolved,
        "message": message,
        "data": data,
        "meta": built,
    }


def partial(
    data: Any,
    *,
    meta: Optional[Mapping[str, Any]] = None,
    message: str = "partial",
    degraded_reason: Optional[str] = None,
) -> Dict[str, Any]:
    extra: Dict[str, Any] = dict(meta or {})
    extra["partial"] = True
    if degraded_reason:
        extra["degraded_reason"] = degraded_reason
    return ok(data, meta=extra, message=message, status=STATUS_PARTIAL)


def degraded(
    data: Any,
    *,
    meta: Optional[Mapping[str, Any]] = None,
    message: str = "degraded",
    degraded_reason: Optional[str] = None,
) -> Dict[str, Any]:
    extra: Dict[str, Any] = dict(meta or {})
    extra["fallback_used"] = True
    if degraded_reason:
        extra["degraded_reason"] = degraded_reason
        extra.setdefault("fallback_reason", degraded_reason)
    return ok(data, meta=extra, message=message, status=STATUS_DEGRADED)


def failure(
    error_code: str,
    message: str,
    *,
    data: Any = None,
    meta: Optional[Mapping[str, Any]] = None,
    http_status: int = 502,
) -> Dict[str, Any]:
    """Return a FAILED envelope with a non-200 http status.

    Default ``http_status`` is 502 (bad gateway) because a failed envelope
    almost always reflects upstream data-source failure we could not mask.
    """
    built = build_meta(meta)
    return {
        "success": False,
        "status": STATUS_FAILED,
        "message": message,
        "error_code": error_code,
        "data": data,
        "meta": built,
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
