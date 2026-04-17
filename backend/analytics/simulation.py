"""Scenario / statistical simulation analytics."""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

from ..core.data_source import DataSourceAdapter
from .portfolio import portfolio_return_series, resolve_weights, combine_exposure
from .risk import max_drawdown


SCENARIO_PRESETS: Dict[str, Dict[str, Any]] = {
    "hk_tech_drawdown": {
        "label": "港股科技回撤",
        "shock": {"港股科技": -0.15, "半导体": -0.05},
    },
    "semi_recovery": {
        "label": "半导体修复",
        "shock": {"半导体": 0.12, "电子": 0.05},
    },
    "pharma_rebound": {
        "label": "医药反弹",
        "shock": {"医药": 0.10, "消费": 0.03},
    },
    "global_risk_off": {
        "label": "全球风险偏好下降",
        "shock": {"海外科技": -0.10, "港股科技": -0.08, "新能源": -0.05},
    },
    "usd_strengthen": {
        "label": "美元走强",
        "shock": {"海外科技": -0.04, "金融": 0.02, "能源": 0.03},
    },
}


def _buckets(sims: np.ndarray) -> Dict[str, float]:
    bins = [-1.0, -0.3, -0.1, 0.0, 0.1, 0.3, 1.0]
    labels = ["<-30%", "-30%~-10%", "-10%~0%", "0%~10%", "10%~30%", ">30%"]
    counts, _ = np.histogram(sims, bins=bins)
    total = max(1, counts.sum())
    return {label: round(float(c) / total, 3) for label, c in zip(labels, counts)}


def statistical_run(
    adapter: DataSourceAdapter,
    portfolio_id: str,
    horizon_days: int,
    num_paths: int,
    confidence: float,
    bootstrap: bool,
) -> Dict[str, Any]:
    _, weights = resolve_weights(adapter, portfolio_id)
    returns = portfolio_return_series(adapter, weights).dropna().to_numpy()
    if returns.size == 0:
        returns = np.zeros(1)
    rng = np.random.default_rng(1337)

    horizons = sorted(set([10, 30, max(10, horizon_days)]))
    heatmap: Dict[str, Dict[str, float]] = {}
    extreme_curve: List[Dict[str, Any]] = []

    for horizon in horizons:
        sims = np.empty(num_paths)
        for i in range(num_paths):
            if bootstrap:
                sampled = rng.choice(returns, size=horizon, replace=True)
            else:
                sampled = rng.choice(returns, size=min(horizon, returns.size), replace=False)
            sims[i] = float(np.prod(1 + sampled) - 1)
        heatmap[f"{horizon}D"] = _buckets(sims)
        extreme_curve.append(
            {
                "horizon": horizon,
                "best_return": round(float(np.quantile(sims, confidence)), 4),
                "worst_return": round(float(np.quantile(sims, 1 - confidence)), 4),
                "median": round(float(np.median(sims)), 4),
            }
        )

    exposures = combine_exposure(adapter.fund_holdings(), weights)
    sensitivity = [
        {
            "factor": f"{sector}±1σ",
            "expected_change": round(-w * 0.1, 4),
            "loss_risk": round(w, 3),
            "affected_exposure": sector,
        }
        for sector, w in list(exposures.items())[:5]
    ]

    price = (1 + portfolio_return_series(adapter, weights)).cumprod()
    mdd = float(max_drawdown(pd.DataFrame({"p": price})).get("p", 0.0))

    return {
        "mode": "statistical",
        "portfolio_id": portfolio_id,
        "horizons": horizons,
        "heatmap": heatmap,
        "extreme_curve": extreme_curve,
        "sensitivity": sensitivity,
        "max_drawdown": round(mdd * 100, 2),
        "confidence_interval": confidence,
        "num_paths": num_paths,
        "bootstrap": bootstrap,
    }


def scenario_run(adapter: DataSourceAdapter, portfolio_id: str, scenario_ids: List[str]) -> Dict[str, Any]:
    _, weights = resolve_weights(adapter, portfolio_id)
    industry = combine_exposure(adapter.fund_holdings(), weights)
    table: List[Dict[str, Any]] = []
    heatmap: Dict[str, Dict[str, float]] = {}
    for sid in scenario_ids:
        preset = SCENARIO_PRESETS.get(sid)
        if preset is None:
            continue
        expected = sum(industry.get(sector, 0) * shock for sector, shock in preset["shock"].items())
        worst = expected * 1.4
        table.append(
            {
                "scenario_id": sid,
                "label": preset["label"],
                "expected_return": round(expected, 4),
                "worst_return": round(worst, 4),
                "max_exposure_factor": max(preset["shock"].items(), key=lambda kv: abs(industry.get(kv[0], 0))),
            }
        )
        heatmap[preset["label"]] = {"expected": round(expected, 4), "worst": round(worst, 4)}

    return {
        "mode": "scenario",
        "portfolio_id": portfolio_id,
        "scenarios": table,
        "heatmap": heatmap,
        "presets": [{"id": sid, "label": p["label"]} for sid, p in SCENARIO_PRESETS.items()],
    }
