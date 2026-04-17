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
        {
            "code": code,
            "name": meta["name"],
            "type": meta["type"],
            "manager": meta["manager"],
            "region": meta.get("region", "CN"),
        }
        for code, meta in adapter.fund_metadata().items()
    ]
    m = adapter.meta(universe="funds").to_dict()
    m["evidence_count"] = len(funds)
    return ok(funds, meta=m)


@router.get("/{fund_code}/overview")
async def fund_overview(fund_code: str = Path(...)) -> Dict[str, Any]:
    adapter = get_data_source()
    m = adapter.meta(universe=f"fund:{fund_code}").to_dict()
    m["is_proxy"] = True  # fund nav is proxied from an index
    m["evidence_count"] = 1
    return ok(build_overview(adapter, fund_code), meta=m)


@router.get("/{fund_code}/analysis")
async def fund_analysis(
    fund_code: str = Path(...),
    portfolio_id: str = Query("pf_default"),
) -> Dict[str, Any]:
    adapter = get_data_source()
    m = adapter.meta(universe=f"fund:{fund_code}").to_dict()
    m["is_proxy"] = True
    m["evidence_count"] = 2
    return ok(build_analysis(adapter, fund_code, portfolio_id), meta=m)
