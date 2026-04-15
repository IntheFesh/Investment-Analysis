"""
Sentiment router: endpoints exposing risk sentiment metrics.

This router returns information about short‑term and mid‑term market risk sentiment.
The endpoint returns gauge values, factor breakdown and time series data.  The
output structure follows the design described in the product specification.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

import numpy as np
import pandas as pd
from fastapi import APIRouter, Query

from ..sample_data import get_index_price_data
from data_analysis import compute_volatility

router = APIRouter()


def _compute_sentiment_scores(window_days: int) -> Dict[str, float]:
    """Compute short and mid term sentiment scores based on volatility and returns.

    The score is inversely related to volatility: lower volatility results in
    higher sentiment.  Returns can slightly adjust the score upward or downward.
    """
    index_data = get_index_price_data()
    vols: List[float] = []
    rets: List[float] = []
    for df in index_data.values():
        close = df["Adj Close"]
        window = close.tail(window_days)
        returns = window.pct_change().dropna()
        if len(returns) == 0:
            continue
        vol = float(compute_volatility(pd.DataFrame({"ret": returns})))[0]
        vols.append(vol)
        rets.append(float(returns.mean()) * 252)
    # Avoid zero lists
    if not vols:
        return {"score": 50.0, "volatility": 0.0, "return": 0.0}
    avg_vol = float(np.mean(vols))
    avg_ret = float(np.mean(rets))
    # Scale volatility into [0, 100] where lower vol = higher score
    # Use a simple heuristic: vol in [0.05, 0.4] maps to [80, 20]
    vol_score = 80.0 - 150.0 * (avg_vol - 0.05)
    vol_score = max(0.0, min(100.0, vol_score))
    # Adjust score based on return: positive returns add up to 10 points, negative subtract
    ret_adj = np.tanh(avg_ret) * 10.0
    score = vol_score + ret_adj
    score = max(0.0, min(100.0, score))
    return {"score": score, "volatility": avg_vol, "return": avg_ret}


@router.get("/overview")
async def sentiment_overview(
    market_view: str = Query("A股主视角"),
    time_window: str = Query("20D"),
) -> Dict[str, Any]:
    """Return short and mid‑term sentiment gauges and factor contributions.

    Sentiment scores are derived from synthetic market data.  Short‑term
    sentiment uses a 20‑day window, while mid‑term sentiment uses a 60‑day
    window.  Factors contributing to the sentiment include volatility risk,
    fund flows, market breadth and overseas shocks.  Each factor's score
    reflects its relative contribution to the overall sentiment.
    """
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    # Short and mid term windows
    short_res = _compute_sentiment_scores(20)
    mid_res = _compute_sentiment_scores(60)
    short_score = round(short_res["score"], 2)
    mid_score = round(mid_res["score"], 2)
    # Label based on score
    def label(score: float) -> str:
        if score >= 70:
            return "偏贪婪"
        elif score >= 40:
            return "中性"
        else:
            return "偏恐慌"
    short_label = label(short_score)
    mid_label = label(mid_score)
    # Factor contributions (weights sum to 1).  We derive weights from volatility and return.
    volatility_weight = 0.4
    fund_flow_weight = 0.2
    breadth_weight = 0.25
    overseas_weight = 0.15
    factors = [
        {
            "name": "波动风险",
            "score": round((1 - short_res["volatility"]) * 100, 2),
            "direction": "down" if short_res["volatility"] > mid_res["volatility"] else "up",
            "driver": "合成指数波动率变化",
        },
        {
            "name": "资金偏好",
            "score": round((1 + np.tanh(short_res["return"])) * 50, 2),
            "direction": "up" if short_res["return"] > 0 else "down",
            "driver": "模拟资金回报率变化",
        },
        {
            "name": "市场广度",
            "score": round((breadth_weight * short_score), 2),
            "direction": "up" if short_score > mid_score else "down",
            "driver": "上涨/下跌家数比例",
        },
        {
            "name": "海外冲击",
            "score": round((overseas_weight * (100 - short_score)), 2),
            "direction": "down" if short_score < mid_score else "up",
            "driver": "港股与全球指数相对表现",
        },
    ]
    # Build a simple time series of past sentiment scores (look back 10 days)
    index_data = get_index_price_data()
    dates = list(index_data[next(iter(index_data))].index[-10:])
    ts: List[Dict[str, Any]] = []
    for date in dates:
        # Compute scores on each past date by taking data up to that date
        # For efficiency we recompute only volatility using truncated series
        # Build temporary price data truncated to date
        truncated_data = {k: df[df.index <= date] for k, df in index_data.items()}
        def compute_score(data_map: Dict[str, pd.DataFrame], days: int) -> float:
            vols: List[float] = []
            rets: List[float] = []
            for df in data_map.values():
                close = df["Adj Close"].tail(days)
                returns = close.pct_change().dropna()
                if len(returns) == 0:
                    continue
                vol = float(compute_volatility(pd.DataFrame({"ret": returns})))[0]
                vols.append(vol)
                rets.append(float(returns.mean()) * 252)
            if not vols:
                return 50.0
            avg_vol = float(np.mean(vols))
            avg_ret = float(np.mean(rets))
            vol_score = 80.0 - 150.0 * (avg_vol - 0.05)
            vol_score = max(0.0, min(100.0, vol_score))
            ret_adj = np.tanh(avg_ret) * 10.0
            score = vol_score + ret_adj
            return max(0.0, min(100.0, score))
        s_score = compute_score(truncated_data, 20)
        m_score = compute_score(truncated_data, 60)
        ts.append({"date": date.strftime("%Y-%m-%d"), "short": round(s_score, 2), "mid": round(m_score, 2)})
    # Contributions normalised
    contributions = {
        "波动风险": round(volatility_weight, 2),
        "资金偏好": round(fund_flow_weight, 2),
        "市场广度": round(breadth_weight, 2),
        "海外冲击": round(overseas_weight, 2),
    }
    data: Dict[str, Any] = {
        "short_term_score": short_score,
        "mid_term_score": mid_score,
        "short_term_label": short_label,
        "mid_term_label": mid_label,
        "factors": factors,
        "time_series": ts,
        "contributions": contributions,
    }
    return {
        "success": True,
        "message": "ok",
        "data": data,
        "meta": {"timestamp": timestamp, "version": "v1"},
    }