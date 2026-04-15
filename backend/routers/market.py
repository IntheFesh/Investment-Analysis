"""
Market router: endpoints providing market overview data.

This router aggregates synthetic data across multiple markets and also exposes
sub-endpoints for partial refreshes (indices/sector-rotation/fund-flows/
breadth/explanations) as described in the product specification.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

import numpy as np
from fastapi import APIRouter, Query

from ..sample_data import get_index_price_data

router = APIRouter()


def _parse_time_window(window: str) -> int:
    """Convert a window string into business days, with support for CUSTOM."""
    if not window:
        return 20
    window = window.upper()
    try:
        if window == "YTD":
            return 120
        if window == "CUSTOM":
            return 20
        if window.endswith("D"):
            return max(1, int(window[:-1]))
        if window.endswith("Y"):
            years = float(window[:-1])
            return max(1, int(years * 252))
    except (TypeError, ValueError):
        pass
    return 20


def _build_market_data(time_window: str) -> Dict[str, Any]:
    """Build the full market payload once for reuse by all market endpoints."""
    window_days = _parse_time_window(time_window)
    index_data = get_index_price_data()
    name_map = {
        "000001.SS": "上证指数",
        "399001.SZ": "深证成指",
        "399006.SZ": "创业板指",
        "000300.SS": "沪深300",
        "000852.SS": "中证1000",
        "HSI": "恒生指数",
        "HSTECH": "恒生科技",
        "NDX": "纳斯达克100",
        "SPX": "标普500",
    }

    indices: List[Dict[str, Any]] = []
    for symbol, df in index_data.items():
        close = df["Adj Close"]
        last = float(close.iloc[-1])
        prev = float(close.iloc[-2]) if len(close) >= 2 else last
        change = last - prev
        change_percent = change / prev if prev else 0.0
        turnover = int(df["Volume"].iloc[-1])
        trend_series = close.tail(min(10, window_days)).tolist()
        indices.append(
            {
                "symbol": symbol,
                "name": name_map.get(symbol, symbol),
                "last": round(last, 2),
                "change": round(change, 2),
                "change_percent": round(change_percent * 100, 2),
                "turnover": turnover,
                "trend": [round(float(v), 2) for v in trend_series],
                "updated_at": datetime.now(tz=timezone.utc).isoformat(),
            }
        )

    total_advancers = total_decliners = 0
    for df in index_data.values():
        returns = df["Adj Close"].tail(window_days).pct_change().dropna()
        total_advancers += int((returns > 0).sum())
        total_decliners += int((returns < 0).sum())
    total = total_advancers + total_decliners
    advancers_ratio = total_advancers / total if total else 0.0

    sector_map = {
        "半导体": "399006.SZ",
        "医药": "000300.SS",
        "消费": "SPX",
        "银行": "000001.SS",
        "港股科技": "HSTECH",
        "新能源": "399001.SZ",
    }
    sector_perf: Dict[str, float] = {}
    for sector, sym in sector_map.items():
        window = index_data[sym]["Adj Close"].tail(window_days)
        sector_perf[sector] = float(window.iloc[-1] / window.iloc[0] - 1.0)

    sorted_sectors = sorted(sector_perf.items(), key=lambda x: x[1], reverse=True)
    strongest = [{"sector": s, "score": round(v * 100, 2)} for s, v in sorted_sectors[:2]]
    candidate = [{"sector": s, "score": round(v * 100, 2)} for s, v in sorted_sectors[2:4]]
    crowded = [{"sector": s, "score": round(v * 100, 2)} for s, v in sorted_sectors[-2:]]

    sector_rotation = {
        "strongest": strongest,
        "candidate": candidate,
        "high_crowding": crowded,
    }
    fund_flows = {
        "top_inflows": [{"sector": s, "value": round(v * 1e9, 2)} for s, v in sorted_sectors[:3]],
        "top_outflows": [{"sector": s, "value": round(v * 1e9, 2)} for s, v in sorted_sectors[-3:]],
        "view": "industry",
    }
    breadth = {
        "advancers_ratio": round(advancers_ratio, 2),
        "limit_up": int(total_advancers * 0.05),
        "limit_down": int(total_decliners * 0.03),
        "turnover_change": round(float(np.mean([abs(v) for v in sector_perf.values()])), 4),
        "market_heat": round(advancers_ratio * 1.2, 2),
    }
    explanations = [
        {
            "event": "海外科技风险偏好修复",
            "impact": "港股科技与A股成长出现共振",
            "evidence": "HSTECH 与 创业板近窗口涨幅领先",
        },
        {
            "event": "资金回流高景气赛道",
            "impact": "半导体、新能源得到增量资金关注",
            "evidence": "sector_rotation strongest + top_inflows",
        },
        {
            "event": "防御板块相对走弱",
            "impact": "短期组合需关注波动回升风险",
            "evidence": "高拥挤板块得分回落",
        },
    ]
    summary = "合成样本显示：跨市场指数分化，成长风格短期占优，建议控制高波动暴露。"
    return {
        "indices": indices,
        "signals": {
            "sector_rotation": sector_rotation,
            "fund_flows": fund_flows,
            "breadth": breadth,
        },
        "explanations": explanations,
        "summary": summary,
    }


@router.get("/overview")
async def market_overview(
    market_view: str = Query("A股主视角", description="Market perspective"),
    time_window: str = Query("20D", description="Calculation window"),
    fields: List[str] | None = Query(None, description="Optional list of fields to include"),
) -> Dict[str, Any]:
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    data = _build_market_data(time_window)
    if fields:
        data = {k: v for k, v in data.items() if k in fields}
    return {
        "success": True,
        "message": "ok",
        "data": {"market_view": market_view, **data},
        "meta": {"timestamp": timestamp, "version": "v1"},
    }


@router.get("/indices")
async def market_indices(time_window: str = Query("20D")) -> Dict[str, Any]:
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    data = _build_market_data(time_window)
    return {"success": True, "message": "ok", "data": data["indices"], "meta": {"timestamp": timestamp, "version": "v1"}}


@router.get("/sector-rotation")
async def market_sector_rotation(time_window: str = Query("20D")) -> Dict[str, Any]:
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    data = _build_market_data(time_window)
    return {
        "success": True,
        "message": "ok",
        "data": data["signals"]["sector_rotation"],
        "meta": {"timestamp": timestamp, "version": "v1"},
    }


@router.get("/fund-flows")
async def market_fund_flows(time_window: str = Query("20D")) -> Dict[str, Any]:
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    data = _build_market_data(time_window)
    return {
        "success": True,
        "message": "ok",
        "data": data["signals"]["fund_flows"],
        "meta": {"timestamp": timestamp, "version": "v1"},
    }


@router.get("/breadth")
async def market_breadth(time_window: str = Query("20D")) -> Dict[str, Any]:
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    data = _build_market_data(time_window)
    return {"success": True, "message": "ok", "data": data["signals"]["breadth"], "meta": {"timestamp": timestamp, "version": "v1"}}


@router.get("/explanations")
async def market_explanations(time_window: str = Query("20D")) -> Dict[str, Any]:
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    data = _build_market_data(time_window)
    return {"success": True, "message": "ok", "data": data["explanations"], "meta": {"timestamp": timestamp, "version": "v1"}}
