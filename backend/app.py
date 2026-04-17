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

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.data_source import get_data_source
from .core.envelope import build_meta
from .core.market_pipeline import get_market_pipeline
from .core.scheduler import register_default_jobs
from .routers import (
    backtest,
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

app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
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
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "UNEXPECTED_ERROR",
            "message": "后端内部错误，请检查日志",
            "data": None,
            "meta": build_meta(),
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
