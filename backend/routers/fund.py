"""Single-fund research endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Path, Query

from ..analytics.fund import build_analysis, build_overview
from ..core.data_source import get_data_source
from ..core.envelope import ok


router = APIRouter()


@router.get("/")
async def list_funds() -> Dict[str, Any]:
    adapter = get_data_source()
    funds = [
        {"code": code, "name": meta["name"], "type": meta["type"], "manager": meta["manager"]}
        for code, meta in adapter.fund_metadata().items()
    ]
    return ok(funds, meta=adapter.meta())


@router.get("/{fund_code}/overview")
async def fund_overview(fund_code: str = Path(...)) -> Dict[str, Any]:
    adapter = get_data_source()
    return ok(build_overview(adapter, fund_code), meta=adapter.meta())


@router.get("/{fund_code}/analysis")
async def fund_analysis(
    fund_code: str = Path(...),
    portfolio_id: str = Query("pf_default"),
) -> Dict[str, Any]:
    adapter = get_data_source()
    return ok(build_analysis(adapter, fund_code, portfolio_id), meta=adapter.meta())
