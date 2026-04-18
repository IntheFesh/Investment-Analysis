"""Debug / observability endpoints.

Only mounted when ``DEBUG=true``. Exposes:

- ``GET /api/v1/debug/data-probe?symbols=000300.SS,HSI``
    Per-symbol diagnostic: vendor name, HTTP status, latency, row count,
    raw timestamp sample, parsed timestamp, breaker state, stale reason.
    Invaluable when the live pipeline "returns" data but the timestamps
    are wrong or the breaker silently opened.

- ``GET /api/v1/debug/vendor-health``
    Circuit-breaker snapshot for every vendor the runtime has talked to
    this process lifetime (success/failure/latency/consecutive-failures).

- ``GET /api/v1/debug/cache-stats``
    Snapshot cache key count + pipeline stats.

- ``GET /api/v1/debug/health``
    Top-level liveness probe.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..core.data_source import get_data_source
from ..core.envelope import ok
from ..core.market_pipeline import get_market_pipeline
from ..core.runtime import breaker_registry, current_trace_id
from ..core.snapshot_cache import hot_cache, warm_cache
from ..core.universe import required_symbols_for, UNIVERSES


router = APIRouter()


def _debug_enabled() -> bool:
    return os.getenv("DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}


def _guard() -> None:
    if not _debug_enabled():
        raise HTTPException(status_code=404, detail="debug endpoints disabled")


@router.get("/health")
async def debug_health() -> Dict[str, Any]:
    adapter = get_data_source()
    pipeline = get_market_pipeline()
    return ok(
        {
            "adapter": adapter.name,
            "tier": adapter.tier,
            "truth_grade": adapter.truth_grade,
            "pipeline": pipeline.stats(),
            "hot_cache_keys": len(hot_cache().keys()),
            "warm_cache_keys": len(warm_cache().keys()),
            "trace_id": current_trace_id(),
        },
        meta={
            "source_name": "debug-health",
            "source_tier": "derived",
            "truth_grade": "D",
            "is_demo": False,
            "schema_version": "debug-health.v1",
            "trace_id": current_trace_id(),
        },
    )


@router.get("/data-probe")
async def data_probe(
    symbols: Optional[str] = Query(
        None,
        description="Comma-separated symbols; defaults to the default market_view universe.",
    ),
    market_view: str = Query("cn_a"),
) -> Dict[str, Any]:
    _guard()
    adapter = get_data_source()
    if symbols:
        wanted: List[str] = [s.strip() for s in symbols.split(",") if s.strip()]
    else:
        wanted = list(required_symbols_for(market_view))

    reports: List[Dict[str, Any]] = []
    probe_fn = getattr(adapter, "probe_symbol", None)
    if probe_fn is None:
        # Fall back to a minimal probe: just call index_price_data for the
        # symbols and record row counts + last timestamp.
        for sym in wanted:
            try:
                df = adapter.index_price_data([sym]).get(sym)
                rows = int(len(df)) if df is not None else 0
                last_ts = str(df.index.max())[:19] if df is not None and not df.empty else None
                reports.append({
                    "symbol": sym,
                    "attempts": [{
                        "vendor": adapter.name,
                        "ok": rows > 0,
                        "rows": rows,
                        "last_raw_date": last_ts,
                    }],
                    "final_vendor": adapter.name if rows > 0 else None,
                    "final_rows": rows,
                    "final_last_parsed": last_ts,
                    "stale_reason": None if rows > 0 else "no_probe_support",
                })
            except Exception as exc:  # noqa: BLE001
                reports.append({
                    "symbol": sym,
                    "attempts": [],
                    "final_vendor": None,
                    "final_rows": 0,
                    "final_last_parsed": None,
                    "stale_reason": f"{type(exc).__name__}: {exc}"[:200],
                })
    else:
        for sym in wanted:
            reports.append(probe_fn(sym))

    success = sum(1 for r in reports if r.get("final_vendor"))
    return ok(
        {
            "market_view": market_view,
            "symbols_requested": wanted,
            "reports": reports,
            "summary": {
                "total": len(reports),
                "succeeded": success,
                "failed": len(reports) - success,
            },
            "breakers": breaker_registry().snapshot(),
        },
        meta={
            "source_name": "debug-data-probe",
            "source_tier": "derived",
            "truth_grade": "D",
            "is_demo": False,
            "schema_version": "debug-probe.v1",
            "trace_id": current_trace_id(),
        },
    )


@router.get("/vendor-health")
async def vendor_health() -> Dict[str, Any]:
    _guard()
    return ok(
        {"breakers": breaker_registry().snapshot()},
        meta={
            "source_name": "debug-vendor-health",
            "source_tier": "derived",
            "truth_grade": "D",
            "is_demo": False,
            "schema_version": "debug-vendor-health.v1",
            "trace_id": current_trace_id(),
        },
    )


@router.get("/cache-stats")
async def cache_stats() -> Dict[str, Any]:
    _guard()
    pipeline = get_market_pipeline()
    return ok(
        {
            "pipeline": pipeline.stats(),
            "hot_cache": {"keys": hot_cache().keys()},
            "warm_cache": {"keys": warm_cache().keys()},
        },
        meta={
            "source_name": "debug-cache-stats",
            "source_tier": "derived",
            "truth_grade": "D",
            "is_demo": False,
            "schema_version": "debug-cache-stats.v1",
            "trace_id": current_trace_id(),
        },
    )


@router.get("/universes")
async def list_universes() -> Dict[str, Any]:
    """Expose the resolved symbols per market_view. Useful when diagnosing
    why a view's kline symbols collapsed to cn_a defaults."""
    _guard()
    payload = {
        view: {
            "label": cfg.label,
            "headline": list(cfg.headline_indices),
            "supporting": list(cfg.supporting_indices),
            "breadth_pool": list(cfg.breadth_pool),
            "cross_asset": list(cfg.cross_asset),
            "sector_baskets": [b.proxy_symbol for b in cfg.sector_baskets],
            "all_symbols": required_symbols_for(view),
        }
        for view, cfg in UNIVERSES.items()
    }
    return ok(
        payload,
        meta={
            "source_name": "debug-universes",
            "source_tier": "derived",
            "truth_grade": "D",
            "is_demo": False,
            "schema_version": "debug-universes.v1",
            "trace_id": current_trace_id(),
        },
    )
