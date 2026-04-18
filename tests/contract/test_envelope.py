"""Round-0 contract tests for the response envelope.

These tests pin the honesty contract every endpoint must honour so later
rounds can't regress it silently. They only exercise the pure envelope +
status helpers; full HTTP contract tests land in Round 6.
"""

from __future__ import annotations

import pytest

from backend.core.envelope import (
    ALL_STATUSES,
    DEFAULT_META,
    STATUS_DEGRADED,
    STATUS_FAILED,
    STATUS_PARTIAL,
    STATUS_SUCCESS,
    build_meta,
    degraded,
    failure,
    ok,
    partial,
)
from backend.core.errors import ErrorCode


REQUIRED_META_KEYS = {
    "timestamp",
    "computed_at",
    "version",
    "source_name",
    "source_tier",
    "truth_grade",
    "is_demo",
    "is_proxy",
    "is_realtime",
    "delay_seconds",
    "license_scope",
    "fallback_reason",
    "trading_day",
    "coverage_universe",
    "calculation_method_version",
    "evidence_count",
    "market_session",
    "tz",
    # Round-0 additions the frontend relies on
    "source_vendor",
    "is_stale",
    "cache_hit",
    "fallback_used",
    "degraded_reason",
    "market_phase",
    "schema_version",
    "latency_ms",
    "trace_id",
}


def test_build_meta_has_all_round0_keys() -> None:
    meta = build_meta()
    missing = REQUIRED_META_KEYS - set(meta.keys())
    assert not missing, f"build_meta missing required keys: {sorted(missing)}"


def test_build_meta_defaults_include_all_honesty_badges() -> None:
    # Every honesty field present in DEFAULT_META must survive build_meta,
    # so frontends that key off these fields never encounter ``undefined``.
    meta = build_meta()
    for key in DEFAULT_META.keys():
        assert key in meta, f"default meta key {key!r} lost in build_meta"


def test_ok_status_success_by_default_for_clean_meta() -> None:
    resp = ok({"value": 1}, meta={
        "source_name": "eastmoney",
        "source_tier": "research_only",
        "truth_grade": "C",
        "is_demo": False,
    })
    assert resp["status"] == STATUS_SUCCESS
    assert resp["success"] is True
    assert resp["data"] == {"value": 1}
    assert "meta" in resp


def test_ok_status_infers_degraded_when_fallback_used() -> None:
    resp = ok({"value": 1}, meta={"fallback_used": True, "fallback_reason": "snapshot_not_ready"})
    assert resp["status"] == STATUS_DEGRADED
    assert resp["success"] is False


def test_ok_status_infers_partial_when_partial_flag_set() -> None:
    resp = ok({"value": 1}, meta={"partial": True, "is_demo": False, "source_tier": "research_only"})
    assert resp["status"] == STATUS_PARTIAL


def test_ok_status_infers_degraded_for_demo_snapshot() -> None:
    resp = ok({"value": 1}, meta={"is_demo": True, "source_tier": "fallback_demo"})
    assert resp["status"] == STATUS_DEGRADED


def test_partial_helper_flags_partial_and_keeps_reason() -> None:
    resp = partial({"value": 1}, degraded_reason=str(ErrorCode.SENTIMENT_INSUFFICIENT_DATA))
    assert resp["status"] == STATUS_PARTIAL
    assert resp["meta"]["partial"] is True
    assert resp["meta"]["degraded_reason"] == "ERR_SENTIMENT_INSUFFICIENT_DATA"


def test_degraded_helper_marks_fallback_and_reason() -> None:
    resp = degraded({"value": 1}, degraded_reason=str(ErrorCode.CACHE_REBUILD_FAIL))
    assert resp["status"] == STATUS_DEGRADED
    assert resp["meta"]["fallback_used"] is True
    assert resp["meta"]["degraded_reason"] == "ERR_CACHE_REBUILD_FAIL"
    # fallback_reason alias is populated for backwards compat.
    assert resp["meta"]["fallback_reason"] == "ERR_CACHE_REBUILD_FAIL"


def test_failure_returns_failed_status_and_http_hint() -> None:
    resp = failure(str(ErrorCode.VENDOR_TIMEOUT), "upstream timed out")
    assert resp["status"] == STATUS_FAILED
    assert resp["error_code"] == "ERR_VENDOR_TIMEOUT"
    assert resp["_http_status"] >= 500


def test_all_statuses_are_the_documented_four() -> None:
    assert ALL_STATUSES == (STATUS_SUCCESS, STATUS_PARTIAL, STATUS_DEGRADED, STATUS_FAILED)


def test_ok_does_not_emit_failed_status() -> None:
    # Guard against callers accidentally producing a FAILED 200 body.
    resp = ok({"value": 1}, status=STATUS_FAILED)
    assert resp["status"] == STATUS_DEGRADED  # coerced down to 200-valid status
