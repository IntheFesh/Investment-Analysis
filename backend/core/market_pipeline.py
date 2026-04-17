"""Asynchronous market snapshot pipeline with layered cache reads.

Read path (API): L1 memory -> L2 redis -> L3 sqlite snapshot.
Write path (scheduler): async refresh jobs -> normalize -> write L3/L2/L1.

Design invariants (2026-04 rewrite)
-----------------------------------
1. ``start()`` NEVER blocks the FastAPI startup lifecycle. Initial snapshot
   warm-up runs in a background task so the HTTP server accepts connections
   immediately.
2. ``get_snapshot`` is read-only and always returns in <50ms. If no
   cache layer has data yet, it enqueues a single-key background refresh
   (deduplicated by ``_inflight``) and returns ``(None, meta, 'miss')``
   to the caller; the router turns that into a last-good deterministic
   fallback so the frontend never sees a timeout.
3. Per-snapshot refresh uses ``asyncio.wait_for`` with a bounded timeout
   so a hanging upstream fetch never stalls the refresh cycle.
4. One bad upstream symbol (e.g. ^HSTECH 404) must not fail the snapshot —
   that is enforced upstream in ``DataSourceAdapter.index_price_data``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple

from ..analytics.market import build_overview
from .data_source import DemoSnapshotAdapter, get_data_source


logger = logging.getLogger(__name__)

VIEWS = ("cn_a", "hk", "global")
WINDOWS = ("5D", "20D", "60D", "120D", "YTD", "1Y")

_REFRESH_TIMEOUT = float(os.getenv("MARKET_REFRESH_TIMEOUT_SECONDS", "6"))
# Prioritise the default view/window during initial warmup so the very first
# user click resolves from a real (not seeded) snapshot. The remainder is
# filled in the next ``_loop_task`` cycle.
_PRIORITY_VIEW = os.getenv("MARKET_PRIORITY_VIEW", "cn_a")
_PRIORITY_WINDOW = os.getenv("MARKET_PRIORITY_WINDOW", "20D")


@dataclass
class PipelineStats:
    l1_hits: int = 0
    l2_hits: int = 0
    l3_hits: int = 0
    misses: int = 0
    refresh_ok: int = 0
    refresh_failed: int = 0
    fallback_served: int = 0
    api_latency_total_ms: float = 0.0
    api_count: int = 0
    upstream_latency_total_ms: float = 0.0
    upstream_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        avg_api = self.api_latency_total_ms / self.api_count if self.api_count else 0.0
        avg_upstream = self.upstream_latency_total_ms / self.upstream_count if self.upstream_count else 0.0
        hit_total = self.l1_hits + self.l2_hits + self.l3_hits + self.misses
        hit_rate = (self.l1_hits + self.l2_hits + self.l3_hits) / hit_total if hit_total else 0.0
        return {
            "cache": {
                "l1_hits": self.l1_hits,
                "l2_hits": self.l2_hits,
                "l3_hits": self.l3_hits,
                "misses": self.misses,
                "hit_rate": round(hit_rate, 4),
            },
            "refresh": {
                "ok": self.refresh_ok,
                "failed": self.refresh_failed,
                "fallback_served": self.fallback_served,
                "avg_upstream_latency_ms": round(avg_upstream, 2),
            },
            "api": {
                "avg_response_ms": round(avg_api, 2),
                "count": self.api_count,
            },
        }


class RedisLayer:
    def __init__(self, ttl_seconds: int = 90) -> None:
        self._ttl = ttl_seconds
        self._client = None
        url = os.getenv("REDIS_URL", "").strip()
        if not url:
            return
        try:
            import redis  # type: ignore

            self._client = redis.Redis.from_url(url, socket_connect_timeout=0.3, socket_timeout=0.3, decode_responses=True)
            self._client.ping()
            logger.info("market pipeline redis enabled")
        except Exception as exc:  # noqa: BLE001
            logger.warning("market pipeline redis disabled: %s", exc)
            self._client = None

    def get(self, key: str) -> Optional[Tuple[Dict[str, Any], Dict[str, Any], float]]:
        if self._client is None:
            return None
        try:
            raw = self._client.get(key)
            if not raw:
                return None
            data = json.loads(raw)
            return data["payload"], data["meta"], float(data.get("stored_at", 0.0))
        except Exception:  # noqa: BLE001
            return None

    def set(self, key: str, payload: Dict[str, Any], meta: Dict[str, Any], stored_at: float) -> None:
        if self._client is None:
            return
        try:
            self._client.setex(key, self._ttl, json.dumps({"payload": payload, "meta": meta, "stored_at": stored_at}, ensure_ascii=False))
        except Exception:  # noqa: BLE001
            return


class SQLiteLayer:
    def __init__(self, db_path: str) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS market_snapshots (
                snapshot_key TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                meta_json TEXT NOT NULL,
                updated_at REAL NOT NULL
            )
            """
        )
        self._conn.commit()

    def get(self, key: str) -> Optional[Tuple[Dict[str, Any], Dict[str, Any], float]]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT payload_json, meta_json, updated_at FROM market_snapshots WHERE snapshot_key = ?",
                (key,),
            )
            row = cur.fetchone()
        if not row:
            return None
        try:
            return json.loads(row[0]), json.loads(row[1]), float(row[2])
        except Exception:  # noqa: BLE001
            return None

    def set(self, key: str, payload: Dict[str, Any], meta: Dict[str, Any], updated_at: float) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO market_snapshots (snapshot_key, payload_json, meta_json, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(snapshot_key) DO UPDATE SET
                  payload_json=excluded.payload_json,
                  meta_json=excluded.meta_json,
                  updated_at=excluded.updated_at
                """,
                (key, json.dumps(payload, ensure_ascii=False), json.dumps(meta, ensure_ascii=False), updated_at),
            )
            self._conn.commit()


class MarketSnapshotPipeline:
    def __init__(self) -> None:
        self._l1: Dict[str, Tuple[float, Dict[str, Any], Dict[str, Any], float]] = {}
        self._l1_lock = threading.Lock()
        self._l1_ttl = float(os.getenv("MARKET_L1_TTL_SECONDS", "15"))
        self._l2 = RedisLayer(ttl_seconds=int(os.getenv("MARKET_L2_TTL_SECONDS", "120")))
        self._l3 = SQLiteLayer(os.getenv("MARKET_SNAPSHOT_DB", "backend/data/market_snapshots.db"))
        self._stats = PipelineStats()
        self._stats_lock = threading.Lock()
        self._task: Optional[asyncio.Task[None]] = None
        self._bootstrap_task: Optional[asyncio.Task[None]] = None
        self._stop = asyncio.Event()
        self._interval = float(os.getenv("MARKET_PIPELINE_INTERVAL_SECONDS", "45"))
        self._semaphore = asyncio.Semaphore(int(os.getenv("MARKET_PIPELINE_CONCURRENCY", "4")))
        self._inflight: Set[str] = set()
        self._inflight_lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    @staticmethod
    def _key(view: str, window: str, adapter_name: str) -> str:
        return f"market:{view}:{window}:{adapter_name}"

    async def start(self) -> None:
        """Non-blocking startup. Returns immediately; warm-up runs in BG."""
        if self._task and not self._task.done():
            return
        self._stop.clear()
        self._loop = asyncio.get_running_loop()
        # Eagerly seed deterministic snapshots so cold reads never return miss.
        await asyncio.to_thread(self._seed_fallback_snapshots)
        self._bootstrap_task = asyncio.create_task(self._initial_warmup())
        self._task = asyncio.create_task(self._loop_task())

    async def stop(self) -> None:
        self._stop.set()
        for t in (self._bootstrap_task, self._task):
            if t and not t.done():
                t.cancel()
                try:
                    await t
                except (asyncio.CancelledError, Exception):  # noqa: BLE001
                    pass

    def _seed_fallback_snapshots(self) -> None:
        """Compute a deterministic demo snapshot for every (view,window) so the
        first API call always returns data even if the real upstream is slow
        or down. Seeding uses DemoSnapshotAdapter directly so it never touches
        the network and completes in <1s."""
        adapter_name = get_data_source().name
        demo = DemoSnapshotAdapter()
        for view in VIEWS:
            for window in WINDOWS:
                key = self._key(view, window, adapter_name)
                # Skip if L3 already has a real value
                if self._l3.get(key) is not None:
                    continue
                try:
                    payload, src_meta, ev_count = build_overview(demo, window, view)
                    src_meta["evidence_count"] = ev_count
                    src_meta["snapshot_mode"] = "seed"
                    src_meta["freshness_label"] = "seed"
                    src_meta["snapshot_updated_at"] = datetime.now(tz=timezone.utc).isoformat()
                    src_meta["fallback_reason"] = "startup_seed"
                    stored_at = time.monotonic()
                    self._l3.set(key, payload, src_meta, stored_at)
                    with self._l1_lock:
                        self._l1[key] = (stored_at, payload, src_meta, stored_at)
                except Exception as exc:  # noqa: BLE001
                    logger.info("seed snapshot skipped for %s/%s: %s", view, window, exc)

    async def _initial_warmup(self) -> None:
        """Warm up in priority order: default (view, window) first, then the
        rest. This avoids the 18-job thundering herd that starves the event
        loop during the first ~30s of uptime and lets the user's first click
        land on a real refreshed snapshot even before the full cycle finishes.
        """
        adapter_name = get_data_source().name
        try:
            await self._refresh_one(adapter_name, _PRIORITY_VIEW, _PRIORITY_WINDOW)
        except Exception as exc:  # noqa: BLE001
            logger.warning("priority warmup failed for %s/%s: %s", _PRIORITY_VIEW, _PRIORITY_WINDOW, exc)
        # Run the rest in groups of 4 so we never exceed semaphore concurrency
        # by a large margin — that keeps per-job elapsed close to the expected
        # ~2s (eastmoney + tencent fast path) rather than piling up against
        # the yahoo rate limiter.
        rest = [
            (v, w)
            for v in VIEWS
            for w in WINDOWS
            if not (v == _PRIORITY_VIEW and w == _PRIORITY_WINDOW)
        ]
        batch = 4
        for i in range(0, len(rest), batch):
            group = rest[i : i + batch]
            try:
                await asyncio.gather(
                    *(self._refresh_one(adapter_name, v, w) for v, w in group),
                    return_exceptions=True,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("warmup batch %d failed: %s", i // batch, exc)

    async def _loop_task(self) -> None:
        # First cycle: wait a bit to let warmup make progress
        try:
            await asyncio.wait_for(self._stop.wait(), timeout=self._interval)
            return
        except asyncio.TimeoutError:
            pass
        while not self._stop.is_set():
            started = time.perf_counter()
            try:
                await self.refresh_all()
            except Exception as exc:  # noqa: BLE001
                logger.warning("market pipeline refresh cycle failed: %s", exc)
            elapsed = time.perf_counter() - started
            sleep_for = max(2.0, self._interval - elapsed) + random.uniform(0.0, 0.7)
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=sleep_for)
            except asyncio.TimeoutError:
                continue

    async def refresh_all(self) -> None:
        adapter = get_data_source()
        jobs = [self._refresh_one(adapter.name, v, w) for v in VIEWS for w in WINDOWS]
        await asyncio.gather(*jobs, return_exceptions=True)

    async def _refresh_one(self, adapter_name: str, view: str, window: str) -> None:
        key = self._key(view, window, adapter_name)
        with self._inflight_lock:
            if key in self._inflight:
                return
            self._inflight.add(key)
        try:
            async with self._semaphore:
                started = time.perf_counter()
                try:
                    payload, meta = await asyncio.wait_for(
                        asyncio.to_thread(self._build_snapshot, view, window),
                        timeout=_REFRESH_TIMEOUT,
                    )
                    latency_ms = (time.perf_counter() - started) * 1000
                    meta["snapshot_updated_at"] = datetime.now(tz=timezone.utc).isoformat()
                    meta["snapshot_latency_ms"] = round(latency_ms, 2)
                    stored_at = time.monotonic()
                    self._l3.set(key, payload, meta, stored_at)
                    self._l2.set(key, payload, meta, stored_at)
                    with self._l1_lock:
                        self._l1[key] = (stored_at, payload, meta, stored_at)
                    with self._stats_lock:
                        self._stats.refresh_ok += 1
                        self._stats.upstream_count += 1
                        self._stats.upstream_latency_total_ms += latency_ms
                except asyncio.TimeoutError:
                    logger.info("market snapshot refresh timed out for %s/%s (>%.1fs)", view, window, _REFRESH_TIMEOUT)
                    with self._stats_lock:
                        self._stats.refresh_failed += 1
                except Exception as exc:  # noqa: BLE001
                    logger.info("market snapshot refresh failed for %s/%s: %s", view, window, exc)
                    with self._stats_lock:
                        self._stats.refresh_failed += 1
        finally:
            with self._inflight_lock:
                self._inflight.discard(key)

    @staticmethod
    def _build_snapshot(view: str, window: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        adapter = get_data_source()
        payload, src_meta, ev_count = build_overview(adapter, window, view)
        src_meta["evidence_count"] = ev_count
        src_meta["snapshot_mode"] = "async_precomputed"
        tier = src_meta.get("source_tier")
        if tier == "production_authorized":
            src_meta["freshness_label"] = "realtime"
        elif tier == "production_delayed":
            src_meta["freshness_label"] = "delayed"
        elif tier in {"research_only", "derived"}:
            src_meta["freshness_label"] = "research"
        else:
            src_meta["freshness_label"] = "fallback"
        return payload, src_meta

    def _schedule_bg_refresh(self, view: str, window: str) -> None:
        """Fire-and-forget single-key refresh from a sync context."""
        adapter = get_data_source()
        loop = self._loop
        if loop is None or loop.is_closed():
            return
        try:
            asyncio.run_coroutine_threadsafe(self._refresh_one(adapter.name, view, window), loop)
        except Exception:  # noqa: BLE001
            return

    _STALE_AFTER_SECONDS = float(os.getenv("MARKET_STALE_AFTER_SECONDS", "180"))

    def _stamp_freshness(self, meta: Dict[str, Any], stored_at: float, now: float, layer: str) -> Dict[str, Any]:
        out = dict(meta)
        age = max(0.0, now - stored_at)
        out["age_seconds"] = round(age, 2)
        out["cache_layer"] = layer
        is_stale = age > self._STALE_AFTER_SECONDS
        out["is_stale"] = bool(is_stale)
        # Preserve seed / fallback labels; only relabel when actually stale.
        existing = out.get("freshness_label")
        if is_stale and existing not in {"seed", "fallback"}:
            out["freshness_label"] = "stale"
        return out

    def get_snapshot(self, view: str, window: str) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any], str]:
        started = time.perf_counter()
        adapter = get_data_source()
        key = self._key(view, window, adapter.name)
        now = time.monotonic()

        with self._l1_lock:
            l1 = self._l1.get(key)
            if l1 and (now - l1[0]) <= self._l1_ttl:
                with self._stats_lock:
                    self._stats.l1_hits += 1
                self._record_api_latency(started)
                return l1[1], self._stamp_freshness(l1[2], l1[3], now, "l1"), "l1"

        l2 = self._l2.get(key)
        if l2:
            payload, meta, stored_at = l2
            with self._l1_lock:
                self._l1[key] = (now, payload, meta, stored_at)
            with self._stats_lock:
                self._stats.l2_hits += 1
            self._record_api_latency(started)
            self._schedule_bg_refresh(view, window)
            return payload, self._stamp_freshness(meta, stored_at, now, "l2"), "l2"

        l3 = self._l3.get(key)
        if l3:
            payload, meta, stored_at = l3
            self._l2.set(key, payload, meta, stored_at)
            with self._l1_lock:
                self._l1[key] = (now, payload, meta, stored_at)
            with self._stats_lock:
                self._stats.l3_hits += 1
            self._record_api_latency(started)
            self._schedule_bg_refresh(view, window)
            return payload, self._stamp_freshness(meta, stored_at, now, "l3"), "l3"

        with self._stats_lock:
            self._stats.misses += 1
        self._record_api_latency(started)
        # Kick off a background refresh so the next call sees populated cache.
        self._schedule_bg_refresh(view, window)
        return None, {
            "source_name": adapter.name,
            "source_tier": adapter.tier,
            "truth_grade": adapter.truth_grade,
            "is_realtime": False,
            "is_stale": True,
            "age_seconds": -1,
            "fallback_reason": "snapshot_not_ready",
            "snapshot_mode": "cache_only",
            "freshness_label": "fallback",
        }, "miss"

    def _record_api_latency(self, started: float) -> None:
        duration_ms = (time.perf_counter() - started) * 1000
        with self._stats_lock:
            self._stats.api_count += 1
            self._stats.api_latency_total_ms += duration_ms

    def register_fallback_served(self) -> None:
        with self._stats_lock:
            self._stats.fallback_served += 1

    def stats(self) -> Dict[str, Any]:
        with self._stats_lock:
            return self._stats.to_dict()


_PIPELINE: Optional[MarketSnapshotPipeline] = None


def get_market_pipeline() -> MarketSnapshotPipeline:
    global _PIPELINE
    if _PIPELINE is None:
        _PIPELINE = MarketSnapshotPipeline()
    return _PIPELINE
