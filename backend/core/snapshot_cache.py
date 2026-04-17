"""Layered snapshot cache with last-good semantics.

Two tiers:

- ``hot``: short TTL (default 30s) for frequently polled preview cards.
- ``warm``: longer TTL (default 10 minutes) for heavy aggregates.

Both tiers keep the last successful value. If a ``rebuild()`` call fails,
the store returns the stale value stamped with ``fallback_reason`` so the
frontend can show "缓存" instead of an empty page.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple


logger = logging.getLogger(__name__)


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
                return entry.value, entry.meta, True

        try:
            value, meta = rebuild()
            with self._lock:
                self._entries[key] = CacheEntry(value=value, meta=meta, computed_at=now, is_stale=False)
            return value, meta, False
        except Exception as exc:  # noqa: BLE001
            logger.warning("snapshot rebuild failed for %s: %s", key, exc)
            with self._lock:
                entry = self._entries.get(key)
            if entry is not None:
                stale_meta = dict(entry.meta)
                stale_meta["fallback_reason"] = f"last-good-cache: {exc}"
                stale_meta["is_realtime"] = False
                return entry.value, stale_meta, True
            raise

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
