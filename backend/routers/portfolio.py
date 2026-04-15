"""
Portfolio router: endpoints for portfolio analysis and diagnostics.

Each endpoint returns high‑level data about a portfolio given its identifier.  In
the absence of a persistent database this placeholder implementation uses
synthetic data structures.  To connect this to a real portfolio store you
should retrieve portfolio holdings, call into the analysis modules, and build
response objects accordingly.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

import numpy as np
import pandas as pd
from fastapi import APIRouter, Path

from ..sample_data import (
    combine_holdings,
    combine_styles,
    get_fund_holdings,
    get_index_price_data,
    get_user_portfolio,
    get_return_series_for_portfolio,
)
from ...data_analysis import compute_max_drawdown, compute_volatility

router = APIRouter()


@router.get("/{portfolio_id}/overview")
async def portfolio_overview(portfolio_id: str = Path(..., description="Unique portfolio identifier")) -> Dict[str, Any]:
    """Return an overview of a portfolio including exposures and summary statistics.

    The portfolio is retrieved from synthetic data.  Metrics such as
    volatility, maximum drawdown and return are computed from the
    portfolio's daily return series.  Exposures are aggregated from
    constituent funds using the provided weights.  A correlation matrix
    among the funds is also included.
    """
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    # Determine portfolio weights.  Use the default sample if the ID matches
    default_portfolio_id, default_weights = get_user_portfolio()
    if portfolio_id == default_portfolio_id or portfolio_id.startswith("pf"):
        weights = default_weights
    else:
        # For unknown IDs allocate equal weight across all sample funds
        holdings = get_fund_holdings()
        fund_codes = list(holdings.keys())
        equal_weight = 1.0 / len(fund_codes)
        weights = {code: equal_weight for code in fund_codes}
    # Compute return series and derived statistics
    portfolio_returns = get_return_series_for_portfolio(weights)
    # Price series normalised to 1
    price_series = (1 + portfolio_returns).cumprod()
    returns_df = pd.DataFrame({"portfolio": portfolio_returns})
    vol = float(compute_volatility(returns_df)[0]) if not returns_df.empty else 0.0
    mdd_dict = compute_max_drawdown(pd.DataFrame({"portfolio": price_series}))
    mdd = float(mdd_dict.get("portfolio", 0.0))
    annual_return = float(portfolio_returns.mean() * 252) if len(portfolio_returns) > 0 else 0.0
    base_amount = 1_000_000.0
    total_assets = base_amount * (1 + annual_return)
    total_cost = base_amount
    profit_loss = total_assets - total_cost
    return_percent = profit_loss / total_cost if total_cost else 0.0
    fund_count = len(weights)
    summary = {
        "total_assets": round(total_assets, 2),
        "total_cost": round(total_cost, 2),
        "profit_loss": round(profit_loss, 2),
        "return_percent": round(return_percent, 4),
        "max_drawdown": round(mdd, 4),
        "volatility": round(vol, 4),
        "fund_count": fund_count,
        "updated_at": timestamp,
    }
    # Aggregate exposures
    industry_exposures = combine_holdings(weights)
    style_exposures = combine_styles(weights)
    market_exposures = {"A股" + k: v for k, v in style_exposures.items()}
    exposures = {
        "industry": industry_exposures,
        "style": style_exposures,
        "market": market_exposures,
    }
    # Build overlap (correlation) matrix among funds
    index_data = get_index_price_data()
    fund_codes = list(weights.keys())
    # Map each fund to an index (cyclic)
    symbols = list(index_data.keys())
    fund_returns_list = []
    for i, fund_code in enumerate(fund_codes):
        symbol = symbols[i % len(symbols)]
        series = index_data[symbol]["Adj Close"].pct_change().fillna(0)
        fund_returns_list.append(series)
    fund_returns_df = pd.concat(fund_returns_list, axis=1)
    fund_returns_df.columns = fund_codes
    corr = fund_returns_df.corr().fillna(0)
    overlap_matrix = corr.to_numpy().round(3).tolist()
    # Risk profile deviation: recommended range depends on a balanced profile
    recommended_range = (0.2, 0.4)
    actual_risk = vol
    deviation = 0.0
    if actual_risk > recommended_range[1]:
        deviation = actual_risk - recommended_range[1]
    elif actual_risk < recommended_range[0]:
        deviation = recommended_range[0] - actual_risk
    target_profile_deviation = {
        "risk_profile": "平衡型",
        "recommended_risk_range": recommended_range,
        "actual_risk": round(actual_risk, 4),
        "deviation": round(deviation, 4),
    }
    data = {
        "summary": summary,
        "exposures": exposures,
        "overlap_matrix": overlap_matrix,
        "target_deviation": target_profile_deviation,
    }
    return {
        "success": True,
        "message": "ok",
        "data": data,
        "meta": {"timestamp": timestamp, "version": "v1"},
    }


@router.get("/{portfolio_id}/diagnosis")
async def portfolio_diagnosis(portfolio_id: str = Path(...)) -> Dict[str, Any]:
    """Provide diagnostic conclusions and suggestions for a portfolio.

    The diagnosis uses the portfolio's volatility and sector exposures to
    determine a risk type, highlight concentration risks and offer
    optimisation suggestions.  Evidence is summarised from the synthetic
    market environment.
    """
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    # Retrieve portfolio data to diagnose
    default_portfolio_id, default_weights = get_user_portfolio()
    if portfolio_id == default_portfolio_id or portfolio_id.startswith("pf"):
        weights = default_weights
    else:
        holdings = get_fund_holdings()
        fund_codes = list(holdings.keys())
        equal_weight = 1.0 / len(fund_codes)
        weights = {code: equal_weight for code in fund_codes}
    portfolio_returns = get_return_series_for_portfolio(weights)
    returns_df = pd.DataFrame({"ret": portfolio_returns})
    vol = float(compute_volatility(returns_df)[0]) if not returns_df.empty else 0.0
    # Determine risk type based on volatility
    if vol < 0.15:
        risk_type = "稳健型"
    elif vol < 0.25:
        risk_type = "平衡型"
    else:
        risk_type = "进攻型"
    industry_exposures = combine_holdings(weights)
    # Identify concentrated sectors (>30%)
    risk_warnings: List[str] = []
    for sector, w in industry_exposures.items():
        if w > 0.3:
            risk_warnings.append(f"行业集中度高，{sector}占比超过30%")
    # Identify high correlation sectors (we approximate by exposures >0.25)
    for sector, w in industry_exposures.items():
        if 0.25 <= w <= 0.3:
            risk_warnings.append(f"{sector}暴露较高，需注意相关性风险")
    # Environment fit message
    if vol > 0.25:
        environment_fit = "当前市场波动较大，组合风险偏高，需注意回撤"
    elif vol < 0.15:
        environment_fit = "市场稳健，组合风险较低，可适当增加进攻型资产"
    else:
        environment_fit = "市场震荡，组合风险中等，建议保持均衡配置"
    # Optimisation suggestions: reduce top concentrated sectors and diversify
    sorted_exposures = sorted(industry_exposures.items(), key=lambda x: x[1], reverse=True)
    optimisation = []
    if sorted_exposures:
        top_sector, _ = sorted_exposures[0]
        optimisation.append(f"降低{top_sector}暴露，增配其他行业")
    optimisation.append("增加现金或防御型资产比例")
    optimisation.append("适度增加消费和医药类基金比例")
    # Evidence summary
    evidence = {
        "market_status": "合成市场数据波动变化反映当前行情",
        "sector_rotation": "强势板块和弱势板块根据模拟表现得出",
        "global_events": "港股与全球指数走势模拟反映海外影响",
    }
    diagnosis = {
        "risk_type": risk_type,
        "investment_horizon": "5Y",
        "risk_warnings": risk_warnings or ["暂无明显集中风险"],
        "environment_fit": environment_fit,
        "optimization": optimisation,
        "evidence": evidence,
    }
    data = {
        "diagnosis": diagnosis,
    }
    return {
        "success": True,
        "message": "ok",
        "data": data,
        "meta": {"timestamp": timestamp, "version": "v1"},
    }


@router.get("/{portfolio_id}/export-pack")
async def portfolio_export_pack(
    portfolio_id: str = Path(...),
    format: str | None = None,
) -> Dict[str, Any]:
    """Return a structured export package for a portfolio.

    In a real implementation this would trigger an asynchronous job to
    prepare the export and then return a task identifier or download link.
    Here we synchronously return a small preview of each format.
    """
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    # Placeholder export content
    json_content = {"portfolio_id": portfolio_id, "data": {"message": "export preview"}}
    markdown_content = f"# 组合导出\n\n组合 {portfolio_id} 的导出预览。"
    csv_content = "id,value\n1,10\n2,20\n"
    data = {
        "formats": {
            "json": json_content,
            "markdown": markdown_content,
            "csv": csv_content,
        },
        "recommendation_prompt": "请分析当前组合的风险暴露、市场适配度和优化方向。区分已知事实与推断。",
    }
    return {
        "success": True,
        "message": "ok",
        "data": data,
        "meta": {"timestamp": timestamp, "version": "v1"},
    }