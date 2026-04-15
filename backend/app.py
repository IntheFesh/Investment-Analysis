"""
FastAPI application for the investment research platform.

This module instantiates the main `FastAPI` app and registers routers for
different resource groups.  The API is versioned under the ``/api/v1`` prefix.
"""

from __future__ import annotations

from fastapi import FastAPI

from .routers import (
    system,
    market,
    sentiment,
    portfolio,
    fund,
    simulation,
    import_api,
    export_api,
    settings,
)

app = FastAPI(title="Investment Research Platform API", version="v1")

# Register routers under the /api/v1 prefix
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
app.include_router(market.router, prefix="/api/v1/market", tags=["market"])
app.include_router(sentiment.router, prefix="/api/v1/sentiment", tags=["sentiment"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["portfolio"])
app.include_router(fund.router, prefix="/api/v1/fund", tags=["fund"])
app.include_router(simulation.router, prefix="/api/v1/simulation", tags=["simulation"])
app.include_router(import_api.router, prefix="/api/v1/import", tags=["import"])
app.include_router(export_api.router, prefix="/api/v1/export", tags=["export"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["settings"])

# Generic root endpoint to verify server status
@app.get("/")
async def root() -> dict:
    return {
        "success": True,
        "message": "Investment research platform API is running",
        "data": {},
        "meta": {"version": "v1"},
    }