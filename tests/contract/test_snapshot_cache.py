"""Round-0 contract tests for the snapshot cache.

Pins: singleflight, stale-while-revalidate, jittered TTL, and last-good
fallback when rebuild fails.
"""

from __future__ import annotations

import threading
import time

import pytest

from backend.core import snapshot_cache as sc


def _meta(**kw):
    base = {"source_name": "test", "source_tier": "research_only", "truth_grade": "C"}
    base.update(kw)
    return base


def test_get_returns_cached_value_within_ttl() -> None:
    cache = sc.SnapshotCache(default_ttl=5.0)
    calls = {"n": 0}

    def rebuild():
        calls["n"] += 1
        return {"v": calls["n"]}, _meta()

    v1, _, hit1 = cache.get("k", rebuild=rebuild)
    v2, _, hit2 = cache.get("k", rebuild=rebuild)
    assert v1 == {"v": 1}
    assert v2 == {"v": 1}
    assert calls["n"] == 1
    assert hit1 is False
    assert hit2 is True


def test_get_returns_last_good_when_rebuild_fails() -> None:
    cache = sc.SnapshotCache(default_ttl=0.01)
    cache.put("k", {"v": 1}, _meta())
    time.sleep(0.02)

    def broken_rebuild():
        raise RuntimeError("upstream down")

    value, meta, hit = cache.get("k", rebuild=broken_rebuild)
    assert value == {"v": 1}
    assert meta["is_stale"] is True
    assert "fallback_reason" in meta
    assert hit is True


def test_swr_returns_stale_value_and_schedules_rebuild() -> None:
    cache = sc.SnapshotCache(default_ttl=0.01)
    cache.put("k", {"v": 0}, _meta())
    time.sleep(0.02)

    rebuild_done = threading.Event()
    calls = {"n": 0}

    def rebuild():
        calls["n"] += 1
        time.sleep(0.05)
        rebuild_done.set()
        return {"v": 99}, _meta()

    value, meta, state = cache.swr_get_or_rebuild("k", rebuild=rebuild)
    # Must return stale value immediately — not block on rebuild.
    assert value == {"v": 0}
    assert state in {"stale", "rebuild"}
    assert meta["is_stale"] is True

    # Rebuild eventually completes in background and updates cache.
    assert rebuild_done.wait(1.0)
    time.sleep(0.02)
    fresh, _, hit = cache.get("k", rebuild=lambda: (_ for _ in ()).throw(AssertionError("should not be called")))
    assert fresh == {"v": 99}
    assert hit is True


def test_swr_miss_when_nothing_cached() -> None:
    cache = sc.SnapshotCache(default_ttl=5.0)

    def rebuild():
        return {"v": 1}, _meta()

    value, meta, state = cache.swr_get_or_rebuild("missing", rebuild=rebuild)
    assert state == "miss"
    assert value is None
    assert meta is None


def test_ttl_jitter_applied_to_effective_ttl(monkeypatch) -> None:
    cache = sc.SnapshotCache(default_ttl=10.0)
    # Force deterministic jitter so we can assert non-zero spread.
    monkeypatch.setattr(sc, "_TTL_JITTER_FRAC", 0.3)
    cache.put("a", {}, _meta(), ttl=10.0)
    cache.put("b", {}, _meta(), ttl=10.0)
    ea = cache._entries["a"].effective_ttl
    eb = cache._entries["b"].effective_ttl
    assert 7.0 <= ea <= 13.0
    assert 7.0 <= eb <= 13.0


def test_get_with_deadline_serves_stale_when_rebuild_too_slow() -> None:
    cache = sc.SnapshotCache(default_ttl=0.01)
    cache.put("k", {"v": "old"}, _meta())
    time.sleep(0.02)

    def slow_rebuild():
        time.sleep(0.3)
        return {"v": "new"}, _meta()

    value, meta, hit = cache.get_with_deadline("k", deadline_seconds=0.05, rebuild=slow_rebuild)
    assert value == {"v": "old"}
    assert meta["is_stale"] is True
    assert meta.get("fallback_reason") in {"rebuild_in_progress", "rebuild_error"} or "rebuild" in meta.get("fallback_reason", "")
