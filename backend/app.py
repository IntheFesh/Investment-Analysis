"""FastAPI application entry point for the investment research platform.

All routers are registered under ``/api/v1/*`` and share a unified response
envelope (see :mod:`backend.core.envelope`). A :class:`DataSourceAdapter`
controls whether the payload is backed by a live market data provider or a
deterministic demo snapshot — in either case, ``meta.data_source`` /
``meta.is_demo`` / ``meta.as_of_trading_day`` tell the UI the truth.
"""

from __future__ import annotations

import logging
import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.data_source import get_data_source
from .core.envelope import build_meta
from .core.market_pipeline import get_market_pipeline
from .core.runtime import (
    current_trace_id,
    new_trace_id,
    reset_trace_id,
    set_trace_id,
)
from .core.scheduler import register_default_jobs
from .routers import (
    backtest,
    debug as debug_router,
    export_api,
    fund,
    import_api,
    market,
    portfolio,
    scheduler,
    sentiment,
    settings,
    simulation,
    system,
    tasks as tasks_router,
)


logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(title="Investment Research Platform API", version="v1")

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://127.0.0.1:3000,http://localhost:3000")
allowed_origins = [o.strip() for o in frontend_origin.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def _trace_and_latency(request: Request, call_next):
    """Attach trace_id + server-side latency to every envelope.

    - Honours an inbound ``X-Trace-Id`` header so clients that already
      generate one (e.g. the frontend fetch client) can correlate logs.
    - Emits ``X-Trace-Id`` / ``X-Latency-Ms`` response headers and, when
      the response body is a JSON envelope, injects ``meta.trace_id`` and
      ``meta.latency_ms`` so the frontend doesn't need to peek at headers.
    """
    inbound = request.headers.get("x-trace-id", "").strip() or new_trace_id()
    token = set_trace_id(inbound)
    start = time.monotonic()
    try:
        response = await call_next(request)
    finally:
        elapsed_ms = round((time.monotonic() - start) * 1000.0, 2)
        reset_trace_id(token)
    response.headers["X-Trace-Id"] = inbound
    response.headers["X-Latency-Ms"] = str(elapsed_ms)
    return response


app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
app.include_router(debug_router.router, prefix="/api/v1/debug", tags=["debug"])
app.include_router(market.router, prefix="/api/v1/market", tags=["market"])
app.include_router(sentiment.router, prefix="/api/v1/sentiment", tags=["sentiment"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["portfolio"])
app.include_router(fund.router, prefix="/api/v1/fund", tags=["fund"])
app.include_router(simulation.router, prefix="/api/v1/simulation", tags=["simulation"])
app.include_router(import_api.router, prefix="/api/v1/import", tags=["import"])
app.include_router(export_api.router, prefix="/api/v1/export", tags=["export"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["settings"])
app.include_router(tasks_router.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(backtest.router, prefix="/api/v1/backtest", tags=["backtest"])
app.include_router(scheduler.router, prefix="/api/v1/scheduler", tags=["scheduler"])


@app.on_event("startup")
async def _on_startup() -> None:
    register_default_jobs()
    await get_market_pipeline().start()


@app.on_event("shutdown")
async def _on_shutdown() -> None:
    await get_market_pipeline().stop()


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
    logging.getLogger(__name__).exception("unhandled error")
    tid = current_trace_id()
    meta = build_meta()
    meta["trace_id"] = tid
    return JSONResponse(
        status_code=500,
        headers={"X-Trace-Id": tid},
        content={
            "success": False,
            "status": "failed",
            "error_code": "ERR_UNEXPECTED",
            "message": "后端内部错误，请检查日志",
            "data": None,
            "meta": meta,
        },
    )


@app.get("/")
async def root() -> dict:
    adapter = get_data_source()
    return {
        "success": True,
        "message": "Investment research platform API is running",
        "data": {"service": "investment-research", "adapter": adapter.name},
        "meta": build_meta(adapter.meta()),
    }
