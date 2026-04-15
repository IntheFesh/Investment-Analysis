"""
Market router: endpoints providing market overview data.

This router aggregates data across multiple markets and returns a concise
snapshot of the current market environment.  The endpoint currently returns
placeholder data.  In a full implementation the data would be pulled from
market data providers and computed via the analysis modules.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

import numpy as np
from fastapi import APIRouter, Query

from ..sample_data import get_index_price_data

router = APIRouter()


def _parse_time_window(window: str) -> int:
    """Convert a window string like '20D' into an integer number of trading days."""
    if not window:
        return 20
    try:
        if window.upper().endswith("D"):
            return int(window[:-1])
        elif window.upper().endswith("Y"):
            years = float(window[:-1])
            return int(years * 252)
        else:
            # Default to 20 days
            return 20
    except Exception:
        return 20


@router.get("/overview")
async def market_overview(
    market_view: str = Query("A股主视角", description="Market perspective"),
    time_window: str = Query("20D", description="Calculation window"),
    fields: List[str] | None = Query(None, description="Optional list of fields to include"),
) -> Dict[str, Any]:
    """Return market overview data for the selected market view and time window.

    This implementation derives basic statistics from synthetic index price
    data (see ``sample_data.get_index_price_data``).  The results include
    current price, daily change, turnover and short trend for each index,
    along with simple signals and explanation cards derived from the data.

    Parameters
    ----------
    market_view: str
        The market perspective (unused in this synthetic implementation).
    time_window: str
        The time window for calculations (e.g. ``20D``).  Only the numeric
        component is used to determine the number of days.
    fields: list[str], optional
        Optional field filter; include only specific sections to reduce payload size.
    """
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    window_days = _parse_time_window(time_window)

    index_data = get_index_price_data()
    # Mapping of symbols to human‑readable names
    name_map = {
        "000001.SS": "上证指数",
        "399001.SZ": "深证成指",
        "HSI": "恒生指数",
        "SPX": "标普500",
    }
    indices: List[Dict[str, Any]] = []
    for symbol, df in index_data.items():
        close = df["Adj Close"]
        last = float(close.iloc[-1])
        prev = float(close.iloc[-2]) if len(close) >= 2 else last
        change = last - prev
        change_percent = change / prev if prev != 0 else 0.0
        # Use last business day's volume as turnover (scaled by 1000 for readability)
        turnover = int(df["Volume"].iloc[-1])
        # Short trend: last 10 observations within the chosen window
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
            }
        )

    # Derive simple signals from price movement over the window
    advancers_ratio = 0.0
    total_advancers = 0
    total_decliners = 0
    for df in index_data.values():
        close = df["Adj Close"]
        window = close.tail(window_days)
        returns = window.pct_change().dropna()
        advancers = (returns > 0).sum()
        decliners = (returns < 0).sum()
        total_advancers += advancers
        total_decliners += decliners
    total = total_advancers + total_decliners
    if total > 0:
        advancers_ratio = total_advancers / total
    # Identify sectors with strongest and weakest performance using synthetic returns
    # We arbitrarily map sectors to indices for demonstration
    sector_map = {
        "半导体": "000001.SS",
        "医药": "399001.SZ",
        "新能源": "HSI",
        "消费": "SPX",
    }
    sector_perf: Dict[str, float] = {}
    for sector, sym in sector_map.items():
        close = index_data[sym]["Adj Close"]
        window = close.tail(window_days)
        sector_perf[sector] = float(window.iloc[-1] / window.iloc[0] - 1.0)
    # Sort sectors by performance
    sorted_sectors = sorted(sector_perf.items(), key=lambda x: x[1], reverse=True)
    strongest_sectors = [s[0] for s in sorted_sectors[:2]]
    candidate_sectors = [s[0] for s in sorted_sectors[2:4]]
    high_crowding_sectors = [s for s, perf in sector_perf.items() if perf < 0]

    signals = {
        "sector_rotation": {
            "strongest_sectors": strongest_sectors,
            "candidate_sectors": candidate_sectors,
            "high_crowding_sectors": high_crowding_sectors or [],
        },
        "fund_flows": {
            # Simulate fund flows proportional to performance
            "top_inflows": [{"sector": s, "value": round(perf * 1e9, 2)} for s, perf in sorted_sectors[:2]],
            "top_outflows": [{"sector": s, "value": round(perf * 1e9, 2)} for s, perf in sorted_sectors[-2:]],
        },
        "breadth": {
            "advancers_ratio": round(advancers_ratio, 2),
            "limit_up": int(total_advancers * 0.05),
            "limit_down": int(total_decliners * 0.03),
            # Turnover change approximated by average absolute daily return
            "turnover_change": round(np.mean([abs(p) for p in sector_perf.values()]), 2),
            "market_heat": round(advancers_ratio * 1.2, 2),
        },
    }
    explanations = [
        {
            "event": "市场波动与政策预期",
            "impact": "强势板块持续领涨，弱势板块承压",
            "evidence": "合成指数走势与模拟资金流向",
        },
        {
            "event": "全球宏观因素",
            "impact": "港股科技受压制，A股稳中有升",
            "evidence": "恒生指数表现弱于A股指数",
        },
    ]
    summary = "根据合成数据推算，主要指数短期内涨跌互现，强势板块表现优于弱势板块。"
    data = {
        "indices": indices,
        "signals": signals,
        "explanations": explanations,
        "summary": summary,
    }
    if fields:
        data = {k: v for k, v in data.items() if k in fields}
    return {
        "success": True,
        "message": "ok",
        "data": data,
        "meta": {"timestamp": timestamp, "version": "v1"},
    }