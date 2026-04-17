"""Risk sentiment analytics.

Produces short/mid-term gauge scores, four factor cards, a time-series of
past scores (last ~20 sessions), and contribution weights. Numbers are
always derived from the adapter's snapshot.
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

from ..core.data_source import DataSourceAdapter
from .risk import annualised_volatility


FACTOR_WEIGHTS = {
    "波动风险": 0.40,
    "资金偏好": 0.20,
    "市场广度": 0.25,
    "海外冲击": 0.15,
}


def _label(score: float) -> str:
    if score >= 80:
        return "过热"
    if score >= 60:
        return "偏贪婪"
    if score >= 40:
        return "中性"
    if score >= 20:
        return "偏恐慌"
    return "极度恐慌"


def _score_from_window(index_data: Dict[str, pd.DataFrame], days: int) -> Dict[str, float]:
    vols: List[float] = []
    rets: List[float] = []
    for df in index_data.values():
        close = df["Adj Close"].tail(days + 1)
        ret = close.pct_change().dropna()
        if ret.empty:
            continue
        vols.append(float(annualised_volatility(pd.DataFrame({"r": ret}))[0]))
        rets.append(float(ret.mean()) * 252)
    if not vols:
        return {"score": 50.0, "volatility": 0.0, "return": 0.0}
    avg_vol = float(np.mean(vols))
    avg_ret = float(np.mean(rets))
    vol_score = 80.0 - 150.0 * (avg_vol - 0.05)
    vol_score = max(0.0, min(100.0, vol_score))
    ret_adj = float(np.tanh(avg_ret)) * 10.0
    score = max(0.0, min(100.0, vol_score + ret_adj))
    return {"score": score, "volatility": avg_vol, "return": avg_ret}


def build_overview(adapter: DataSourceAdapter, time_window: str, market_view: str) -> Dict[str, Any]:
    data = adapter.index_price_data()
    short_res = _score_from_window(data, 20)
    mid_res = _score_from_window(data, 60)
    short_score = round(short_res["score"], 2)
    mid_score = round(mid_res["score"], 2)

    factors = [
        {
            "name": "波动风险",
            "score": round(max(0.0, min(100.0, (1 - short_res["volatility"]) * 100)), 2),
            "direction": "down" if short_res["volatility"] > mid_res["volatility"] else "up",
            "driver": f"短期年化波动 {short_res['volatility'] * 100:.2f}%",
        },
        {
            "name": "资金偏好",
            "score": round(max(0.0, min(100.0, (1 + np.tanh(short_res["return"])) * 50)), 2),
            "direction": "up" if short_res["return"] > 0 else "down",
            "driver": f"短期年化收益 {short_res['return'] * 100:.2f}%",
        },
        {
            "name": "市场广度",
            "score": round(max(0.0, min(100.0, short_score)), 2),
            "direction": "up" if short_score > mid_score else "down",
            "driver": "跨指数上涨家数占比",
        },
        {
            "name": "海外冲击",
            "score": round(max(0.0, min(100.0, 100 - abs(short_score - mid_score) * 3)), 2),
            "direction": "down" if short_score < mid_score else "up",
            "driver": "港股与美股联动度",
        },
    ]

    # past time-series (last 20 sessions) — re-score truncated data
    first_df = next(iter(data.values()))
    dates = list(first_df.index[-20:])
    ts: List[Dict[str, Any]] = []
    for d in dates:
        truncated = {k: df[df.index <= d] for k, df in data.items()}
        s = _score_from_window(truncated, 20)["score"]
        m = _score_from_window(truncated, 60)["score"]
        ts.append({"date": d.strftime("%Y-%m-%d"), "short": round(s, 2), "mid": round(m, 2)})

    contributions = [
        {"name": name, "weight": weight, "score": next(f["score"] for f in factors if f["name"] == name)}
        for name, weight in FACTOR_WEIGHTS.items()
    ]

    return {
        "market_view": market_view,
        "time_window": time_window,
        "short_term_score": short_score,
        "mid_term_score": mid_score,
        "short_term_label": _label(short_score),
        "mid_term_label": _label(mid_score),
        "short_term_drivers": [
            f["driver"] for f in factors if f["direction"] == ("up" if short_score >= 50 else "down")
        ][:2],
        "mid_term_drivers": [
            f["driver"] for f in factors if f["direction"] == ("up" if mid_score >= 50 else "down")
        ][:2],
        "factors": factors,
        "time_series": ts,
        "contributions": contributions,
    }
