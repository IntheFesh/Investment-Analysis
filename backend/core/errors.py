"""Structured error codes shared across routers, envelope and frontend.

Keeping the taxonomy in one place lets the frontend map codes to
user-facing copy and lets log aggregators group incidents stably.
"""

from __future__ import annotations

from enum import Enum


class ErrorCode(str, Enum):
    # Upstream vendor failures
    VENDOR_TIMEOUT = "ERR_VENDOR_TIMEOUT"
    VENDOR_HTTP_ERROR = "ERR_VENDOR_HTTP_ERROR"
    VENDOR_EMPTY_PAYLOAD = "ERR_VENDOR_EMPTY_PAYLOAD"
    VENDOR_CIRCUIT_OPEN = "ERR_VENDOR_CIRCUIT_OPEN"
    VENDOR_RATE_LIMITED = "ERR_VENDOR_RATE_LIMITED"

    # Cache / pipeline
    CACHE_REBUILD_FAIL = "ERR_CACHE_REBUILD_FAIL"
    CACHE_DEADLINE_EXCEEDED = "ERR_CACHE_DEADLINE_EXCEEDED"
    SNAPSHOT_NOT_READY = "ERR_SNAPSHOT_NOT_READY"

    # Symbol / universe
    UNIVERSE_EMPTY = "ERR_UNIVERSE_EMPTY"
    SYMBOL_UNMAPPED = "ERR_SYMBOL_UNMAPPED"
    TIMESTAMP_UNPARSEABLE = "ERR_TIMESTAMP_UNPARSEABLE"

    # Sentiment / simulation
    SENTIMENT_INSUFFICIENT_DATA = "ERR_SENTIMENT_INSUFFICIENT_DATA"
    SIMULATION_TIMEOUT = "ERR_SIMULATION_TIMEOUT"

    # News
    NEWS_ON_DEMAND_TIMEOUT = "ERR_NEWS_ON_DEMAND_TIMEOUT"
    NEWS_STORE_UNAVAILABLE = "ERR_NEWS_STORE_UNAVAILABLE"

    # Catch-all
    INVALID_INPUT = "ERR_INVALID_INPUT"
    UNEXPECTED = "ERR_UNEXPECTED"
    DEPENDENCY_DOWN = "ERR_DEPENDENCY_DOWN"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value
