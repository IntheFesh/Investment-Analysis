"""Single-fund research analytics."""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

from ..core.data_source import DataSourceAdapter
from .portfolio import DEFAULT_PORTFOLIOS, portfolio_return_series, resolve_weights
from .risk import annualised_volatility, max_drawdown, window_return


def _proxy_index(adapter: DataSourceAdapter, fund_code: str) -> str:
    symbols = list(adapter.index_price_data().keys())
    funds = list(adapter.fund_holdings().keys())
    if fund_code not in funds or not symbols:
        return symbols[0] if symbols else ""
    return symbols[funds.index(fund_code) % len(symbols)]


def build_overview(adapter: DataSourceAdapter, fund_code: str) -> Dict[str, Any]:
    meta = adapter.fund_metadata().get(fund_code)
    if meta is None:
        meta = {"name": "未知基金", "type": "股票型", "manager": "未定义", "aum": 0.0, "inception_date": "—"}
    proxy = _proxy_index(adapter, fund_code)
    close = adapter.index_price_data()[proxy]["Adj Close"] if proxy else pd.Series(dtype=float)
    return {
        "code": fund_code,
        "name": meta["name"],
        "type": meta["type"],
        "manager": meta["manager"],
        "aum": meta["aum"],
        "inception_date": meta["inception_date"],
        "returns": {
            "20D": round(window_return(close, 20) * 100, 2),
            "60D": round(window_return(close, 60) * 100, 2),
            "120D": round(window_return(close, 120) * 100, 2),
        },
        "proxy_index": proxy,
    }


def build_analysis(adapter: DataSourceAdapter, fund_code: str, portfolio_id: str = "pf_default") -> Dict[str, Any]:
    proxy = _proxy_index(adapter, fund_code)
    index_data = adapter.index_price_data()
    close = index_data[proxy]["Adj Close"] if proxy else pd.Series(dtype=float)
    ret = close.pct_change().fillna(0)
    vol = float(annualised_volatility(pd.DataFrame({"r": ret})).iloc[0]) if not ret.empty else 0.0
    nav = (1 + ret).cumprod().tail(120)
    drawdown = (nav / nav.cummax() - 1).round(4)
    mdd = float(drawdown.min()) if len(drawdown) else 0.0

    # Rolling rank against all other funds
    peer_scores_20: List[float] = []
    peer_scores_60: List[float] = []
    for other in adapter.fund_holdings().keys():
        sym = _proxy_index(adapter, other)
        s = index_data[sym]["Adj Close"].pct_change().fillna(0)
        peer_scores_20.append(float(s.tail(20).mean()) * 252)
        peer_scores_60.append(float(s.tail(60).mean()) * 252)

    def _rank(target: float, peers: List[float]) -> float:
        peers_sorted = sorted(peers)
        idx = int(np.searchsorted(peers_sorted, target))
        return round(idx / max(1, len(peers_sorted)), 3)

    ret_20 = float(ret.tail(20).mean()) * 252
    ret_60 = float(ret.tail(60).mean()) * 252

    industry_exposure = adapter.fund_holdings().get(fund_code, {})
    style = adapter.fund_styles().get(fund_code, {})

    # correlation to user's current portfolio
    _, weights = resolve_weights(adapter, portfolio_id)
    port_ret = portfolio_return_series(adapter, weights)
    common = port_ret.index.intersection(ret.index)
    if len(common) > 2:
        corr = float(np.corrcoef(ret.loc[common], port_ret.loc[common])[0, 1])
    else:
        corr = 0.0

    overlap = 0.0
    holdings = adapter.fund_holdings()
    if fund_code in holdings:
        fund_holdings = holdings[fund_code]
        port_industry = {}
        for c, w in weights.items():
            for sector, sw in holdings.get(c, {}).items():
                port_industry[sector] = port_industry.get(sector, 0) + sw * w
        overlap = sum(min(fund_holdings.get(s, 0), port_industry.get(s, 0)) for s in set(fund_holdings) | set(port_industry))

    return {
        "code": fund_code,
        "nav_curve": [
            {"date": d.strftime("%Y-%m-%d"), "nav": round(float(v), 4)} for d, v in nav.items()
        ],
        "drawdown_curve": [
            {"date": d.strftime("%Y-%m-%d"), "drawdown": round(float(v) * 100, 2)} for d, v in drawdown.items()
        ],
        "metrics": {
            "volatility": round(vol * 100, 2),
            "max_drawdown": round(mdd * 100, 2),
            "benchmark_deviation": round(corr - 1.0, 3),
            "rolling_rank": {
                "20D": _rank(ret_20, peer_scores_20),
                "60D": _rank(ret_60, peer_scores_60),
            },
        },
        "exposures": {
            "industry": industry_exposure,
            "style": style,
            "style_drift_flag": "稳定" if abs(style.get("成长", 0) - 0.5) < 0.25 else "可能漂移",
        },
        "top_holdings": [
            {"ticker": f"PX{i + 1:04d}.SZ", "name": sector, "weight": round(w * 100, 2)}
            for i, (sector, w) in enumerate(sorted(industry_exposure.items(), key=lambda x: x[1], reverse=True)[:5])
        ],
        "portfolio_relation": {
            "portfolio_id": portfolio_id,
            "overlap_score": round(overlap, 3),
            "correlation": round(corr, 3),
            "if_added": "组合成长暴露 +",
            "if_removed": "组合成长暴露 -",
        },
        "conclusion": {
            "suitable_scenarios": "适合对成长与波动有承受力的投资者，需关注中期拥挤度",
            "advantages": "行业主线清晰，近 60D 收益分位处于中上",
            "risks": f"年化波动 {vol * 100:.1f}%，行业集中度较高",
        },
    }
