"""Layered snapshot cache with last-good semantics.

Two tiers:

- ``hot``: short TTL (default 30s) for frequently polled preview cards.
- ``warm``: longer TTL (default 10 minutes) for heavy aggregates.

Both tiers keep the last successful value. If a ``rebuild()`` call fails,
the store returns the stale value stamped with ``fallback_reason`` so the
frontend can show "缓存" instead of an empty page.

The cache also supports stale-while-revalidate: ``get_fresh_or_stale``
returns ``(value, meta, is_stale)`` without blocking on a rebuild when a
stale entry exists — callers (typically the async refresher) are
responsible for the rebuild side-channel.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple


logger = logging.getLogger(__name__)

# Shared thread pool for async cache rebuilds — keeps rebuild work off the
# event loop and lets the request handler race it against a deadline.
_REBUILD_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="snapshot-rebuild")


@dataclass
class CacheEntry:
    value: Any
    meta: Dict[str, Any]
    computed_at: float
    is_stale: bool = False


class SnapshotCache:
    def __init__(self, default_ttl: float = 30.0) -> None:
        self._entries: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self._ttl = default_ttl
        self._inflight: Dict[str, Any] = {}

    def peek(self, key: str) -> Optional[Tuple[Any, Dict[str, Any], float]]:
        """Return ``(value, meta, age_seconds)`` without triggering a rebuild.

        Returns ``None`` if no entry is present.
        """
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            age = time.monotonic() - entry.computed_at
            return entry.value, dict(entry.meta), age

    def put(self, key: str, value: Any, meta: Dict[str, Any]) -> None:
        with self._lock:
            self._entries[key] = CacheEntry(
                value=value, meta=dict(meta), computed_at=time.monotonic(), is_stale=False
            )

    def get(
        self,
        key: str,
        *,
        ttl: Optional[float] = None,
        rebuild: Callable[[], Tuple[Any, Dict[str, Any]]],
    ) -> Tuple[Any, Dict[str, Any], bool]:
        """Return ``(value, meta, was_cache_hit)``.

        If the rebuild callback raises, the last known good value is returned
        with a ``fallback_reason`` stamped into the meta.
        """

        ttl_s = ttl if ttl is not None else self._ttl
        now = time.monotonic()
        with self._lock:
            entry = self._entries.get(key)
            if entry and (now - entry.computed_at) <= ttl_s and not entry.is_stale:
                return entry.value, self._stamp_age(entry, now, was_cache_hit=True), True

        try:
            value, meta = rebuild()
            with self._lock:
                self._entries[key] = CacheEntry(value=value, meta=meta, computed_at=now, is_stale=False)
            return value, self._stamp_fresh(meta), False
        except Exception as exc:  # noqa: BLE001
            logger.warning("snapshot rebuild failed for %s: %s", key, exc)
            with self._lock:
                entry = self._entries.get(key)
            if entry is not None:
                stale_meta = dict(entry.meta)
                stale_meta["fallback_reason"] = f"last-good-cache: {exc}"
                stale_meta["is_realtime"] = False
                stale_meta["is_stale"] = True
                stale_meta["age_seconds"] = round(max(0.0, now - entry.computed_at), 2)
                return entry.value, stale_meta, True
            raise

    def get_fresh_or_stale(
        self,
        key: str,
        *,
        ttl: Optional[float] = None,
    ) -> Optional[Tuple[Any, Dict[str, Any], bool]]:
        """Non-blocking read.

        Returns ``(value, meta, is_stale)`` or ``None`` if no entry exists.
        A caller (typically an async refresher) is expected to rebuild the
        entry out-of-band when ``is_stale`` is True.
        """
        ttl_s = ttl if ttl is not None else self._ttl
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            age = time.monotonic() - entry.computed_at
            is_stale = age > ttl_s or entry.is_stale
            return entry.value, dict(entry.meta), is_stale

    def get_with_deadline(
        self,
        key: str,
        *,
        ttl: Optional[float] = None,
        deadline_seconds: float = 4.0,
        rebuild: Callable[[], Tuple[Any, Dict[str, Any]]],
    ) -> Tuple[Any, Dict[str, Any], bool]:
        """Like :meth:`get`, but if the rebuild exceeds ``deadline_seconds``
        return the last cached value (stamped stale) without cancelling the
        rebuild — the rebuild keeps running and will populate the cache for
        the next caller.
        """

        ttl_s = ttl if ttl is not None else self._ttl
        now = time.monotonic()
        with self._lock:
            entry = self._entries.get(key)
            cached_fresh = entry and (now - entry.computed_at) <= ttl_s and not entry.is_stale
        if cached_fresh and entry is not None:
            return entry.value, self._stamp_age(entry, now, was_cache_hit=True), True

        # Only one rebuild at a time per key, but callers racing against the
        # deadline may still return the last-good value.
        with self._lock:
            if key not in self._inflight:
                self._inflight[key] = _REBUILD_POOL.submit(self._rebuild_and_store, key, rebuild)
            future = self._inflight[key]
        try:
            value, meta = future.result(timeout=deadline_seconds)
            return value, self._stamp_fresh(meta), False
        except FutureTimeoutError:
            with self._lock:
                fallback = self._entries.get(key)
            if fallback is not None:
                stale_meta = dict(fallback.meta)
                stale_meta["fallback_reason"] = "rebuild_in_progress"
                stale_meta["is_stale"] = True
                stale_meta["partial"] = True
                stale_meta["age_seconds"] = round(max(0.0, now - fallback.computed_at), 2)
                logger.info("snapshot %s deadline exceeded (%.1fs) — serving stale", key, deadline_seconds)
                return fallback.value, stale_meta, True
            raise
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                fallback = self._entries.get(key)
            if fallback is not None:
                stale_meta = dict(fallback.meta)
                stale_meta["fallback_reason"] = f"rebuild_error: {exc}"
                stale_meta["is_stale"] = True
                stale_meta["age_seconds"] = round(max(0.0, now - fallback.computed_at), 2)
                return fallback.value, stale_meta, True
            raise

    def _rebuild_and_store(
        self,
        key: str,
        rebuild: Callable[[], Tuple[Any, Dict[str, Any]]],
    ) -> Tuple[Any, Dict[str, Any]]:
        try:
            value, meta = rebuild()
            with self._lock:
                self._entries[key] = CacheEntry(
                    value=value, meta=meta, computed_at=time.monotonic(), is_stale=False
                )
            return value, meta
        finally:
            with self._lock:
                self._inflight.pop(key, None)

    @staticmethod
    def _stamp_age(entry: "CacheEntry", now: float, *, was_cache_hit: bool) -> Dict[str, Any]:
        meta = dict(entry.meta)
        age = max(0.0, now - entry.computed_at)
        meta["age_seconds"] = round(age, 2)
        meta["is_stale"] = bool(entry.is_stale)
        meta["cache_hit"] = was_cache_hit
        return meta

    @staticmethod
    def _stamp_fresh(meta: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(meta)
        out["age_seconds"] = 0.0
        out["is_stale"] = False
        out["cache_hit"] = False
        return out

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._entries.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> int:
        with self._lock:
            victims = [k for k in self._entries if k.startswith(prefix)]
            for k in victims:
                self._entries.pop(k, None)
            return len(victims)

    def keys(self) -> list[str]:
        with self._lock:
            return sorted(self._entries.keys())

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


_HOT: Optional[SnapshotCache] = None
_WARM: Optional[SnapshotCache] = None


def hot_cache() -> SnapshotCache:
    global _HOT
    if _HOT is None:
        _HOT = SnapshotCache(default_ttl=30.0)
    return _HOT


def warm_cache() -> SnapshotCache:
    global _WARM
    if _WARM is None:
        _WARM = SnapshotCache(default_ttl=600.0)
    return _WARM
