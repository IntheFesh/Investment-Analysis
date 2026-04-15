"""
Fund router: endpoints for single fund analysis.

These endpoints provide summary and detailed analysis for individual funds.
In a real implementation the fund metadata and holdings would be pulled from
financial data providers.  Here we return placeholder values.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from fastapi import APIRouter, Path

from ..sample_data import (
    get_fund_holdings,
    get_fund_metadata,
    get_index_price_data,
    get_style_exposures,
    get_return_series_for_portfolio,
    get_user_portfolio,
)
from data_analysis import compute_max_drawdown, compute_volatility

router = APIRouter()


def _map_fund_to_index(fund_code: str) -> str:
    """Map a fund code to one of the synthetic index symbols (cyclic mapping)."""
    index_symbols = list(get_index_price_data().keys())
    fund_codes = list(get_fund_holdings().keys())
    if fund_code not in fund_codes:
        # Assign unknown funds arbitrarily to the first index
        return index_symbols[0]
    idx = fund_codes.index(fund_code)
    return index_symbols[idx % len(index_symbols)]


@router.get("/{fund_code}/overview")
async def fund_overview(fund_code: str = Path(..., description="Fund code")) -> Dict[str, Any]:
    """Return basic information about a fund.

    Uses synthetic metadata and price data to compute returns over several
    horizons.  If the requested fund is unknown, a placeholder entry is
    returned.
    """
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    meta = get_fund_metadata().get(fund_code)
    if meta is None:
        meta = {
            "name": "未知基金",
            "type": "股票型",
            "manager": "未定义",
            "aum": 1.0e9,
            "inception_date": "2020-01-01",
        }
    # Determine returns by mapping the fund to a synthetic index
    symbol = _map_fund_to_index(fund_code)
    index_data = get_index_price_data()[symbol]
    close = index_data["Adj Close"]
    def horizon_return(days: int) -> float:
        if len(close) < days:
            return 0.0
        start = close.iloc[-days]
        end = close.iloc[-1]
        return float(end / start - 1.0)
    returns = {
        "20D": round(horizon_return(20), 4),
        "60D": round(horizon_return(60), 4),
        "120D": round(horizon_return(120), 4),
    }
    overview = {
        "code": fund_code,
        "name": meta["name"],
        "type": meta["type"],
        "manager": meta["manager"],
        "assets_under_management": meta["aum"],
        "inception_date": meta["inception_date"],
        "returns": returns,
    }
    return {
        "success": True,
        "message": "ok",
        "data": overview,
        "meta": {"timestamp": timestamp, "version": "v1"},
    }


@router.get("/{fund_code}/analysis")
async def fund_analysis(fund_code: str = Path(...)) -> Dict[str, Any]:
    """Return risk/return profile, holdings and correlation with user's portfolio.

    The analysis includes the fund's net asset value curve, maximum drawdown,
    volatility, rolling return percentile relative to peers, sector and style
    exposures, major holdings and correlation with the default portfolio.
    """
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    # Retrieve price series for the fund
    symbol = _map_fund_to_index(fund_code)
    index_data = get_index_price_data()[symbol]
    close = index_data["Adj Close"]
    returns = close.pct_change().fillna(0)
    nav_curve = (1 + returns).cumprod().tail(60)  # last 60 business days
    nav_list = [round(float(v), 4) for v in nav_curve.tolist()]
    # Compute risk metrics
    returns_df = pd.DataFrame({"ret": returns})
    vol = float(compute_volatility(returns_df)[0]) if not returns_df.empty else 0.0
    mdd_dict = compute_max_drawdown(pd.DataFrame({"price": (1 + returns).cumprod()}))
    mdd = float(mdd_dict.get("price", 0.0))
    # Rolling return percentile vs peers
    # Compute fund's returns for 20D and 60D and compare to peer distribution
    def compute_percentile(window: int) -> float:
        r = returns.tail(window)
        fund_ret = float(r.mean() * 252) if len(r) > 0 else 0.0
        # Build peer distribution from other funds
        peers = []
        for other_code in get_fund_holdings().keys():
            sym = _map_fund_to_index(other_code)
            other_returns = get_index_price_data()[sym]["Adj Close"].pct_change().fillna(0)
            rr = other_returns.tail(window)
            peers.append(float(rr.mean() * 252) if len(rr) > 0 else 0.0)
        # Percentile rank within peers
        peers_sorted = sorted(peers)
        rank_idx = np.searchsorted(peers_sorted, fund_ret)
        percentile = rank_idx / len(peers_sorted)
        return percentile
    rolling_returns = [
        {"window": "20D", "rank": round(compute_percentile(20), 4)},
        {"window": "60D", "rank": round(compute_percentile(60), 4)},
    ]
    # Exposures
    industry_exposure = get_fund_holdings().get(fund_code, {})
    style_drift = get_style_exposures().get(fund_code, {})
    # Major holdings: list top 2 sectors by weight as proxies for underlying securities
    sorted_industry = sorted(industry_exposure.items(), key=lambda x: x[1], reverse=True) if industry_exposure else []
    major_holdings = [
        {"ticker": f"{i+1:06d}.SZ", "name": sector, "weight": round(weight, 4)}
        for i, (sector, weight) in enumerate(sorted_industry[:2])
    ]
    # Correlation with the default portfolio
    default_portfolio_id, default_weights = get_user_portfolio()
    portfolio_returns = get_return_series_for_portfolio(default_weights)
    # Align fund returns and portfolio returns
    common_index = portfolio_returns.index.intersection(returns.index)
    if len(common_index) > 1:
        fund_r = returns.loc[common_index]
        port_r = portfolio_returns.loc[common_index]
        corr = np.corrcoef(fund_r, port_r)[0, 1]
    else:
        corr = 0.0
    conclusion = {
        "suitable_scenarios": "长期成长配置，适合风险偏好较高的投资者",
        "advantages": "成长风格明显，行业集中度适中",
        "risks": "行业波动可能加大组合回撤",
    }
    analysis = {
        "nav_curve": nav_list,
        "max_drawdown": round(mdd, 4),
        "volatility": round(vol, 4),
        "rolling_returns": rolling_returns,
        "industry_exposure": industry_exposure,
        "style_drift": style_drift,
        "major_holdings": major_holdings,
        "correlation_with_portfolio": round(float(corr), 4),
        "conclusion": conclusion,
    }
    return {
        "success": True,
        "message": "ok",
        "data": analysis,
        "meta": {"timestamp": timestamp, "version": "v1"},
    }