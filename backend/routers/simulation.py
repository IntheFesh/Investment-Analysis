"""
Simulation router: endpoints to run scenario and statistical simulations.

The run endpoint triggers an asynchronous simulation based on provided parameters
and returns a task identifier.  For demonstration purposes we compute a small
synthetic result synchronously and return it directly.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..sample_data import combine_holdings, get_user_portfolio, get_return_series_for_portfolio
from data_analysis import compute_max_drawdown

router = APIRouter()


class StatisticalSimulationRequest(BaseModel):
    mode: str = Field("statistical", const=True)
    horizon_days: int = 60
    num_paths: int = 1000
    confidence_interval: float = 0.95
    bootstrap: bool = False


class ScenarioSimulationRequest(BaseModel):
    mode: str = Field("scenario", const=True)
    scenario_ids: list[str]


def _monte_carlo_simulation(returns: pd.Series, horizon: int, num_paths: int, bootstrap: bool) -> np.ndarray:
    """Generate Monte Carlo sample cumulative returns over a given horizon.

    Returns
    -------
    numpy.ndarray
        Array of simulated total returns for each path.
    """
    returns = returns.dropna().to_numpy()
    if len(returns) == 0:
        return np.zeros(num_paths)
    rng = np.random.default_rng(42)
    sims = np.zeros(num_paths)
    for i in range(num_paths):
        if bootstrap:
            sampled = rng.choice(returns, size=horizon, replace=True)
        else:
            sampled = rng.choice(returns, size=horizon, replace=False)
        sims[i] = np.prod(1 + sampled) - 1
    return sims


@router.post("/run")
async def run_simulation(request: StatisticalSimulationRequest | ScenarioSimulationRequest) -> Dict[str, Any]:
    """Run a portfolio simulation and return results or a task identifier.

    When ``mode`` is ``statistical`` the function performs a simple Monte Carlo
    simulation using the portfolio's historical daily returns.  Distributions
    of returns across several horizons (10, 30, 60 days) are summarised into
    discrete probability buckets.  The extreme curve shows the best and worst
    outcomes from the simulated paths.  Sensitivity analysis highlights
    exposures that may contribute to downside risk.
    """
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    if isinstance(request, StatisticalSimulationRequest):
        # Retrieve portfolio returns
        _, weights = get_user_portfolio()
        portfolio_returns = get_return_series_for_portfolio(weights)
        horizons = [10, 30, request.horizon_days]
        heatmap: Dict[str, Dict[str, float]] = {}
        extreme_curve: List[Dict[str, Any]] = []
        for horizon in horizons:
            sims = _monte_carlo_simulation(portfolio_returns, horizon, request.num_paths, request.bootstrap)
            # Define buckets based on percentile bands
            bins = [-0.3, -0.1, 0.0, 0.1, 0.3, np.inf]
            labels = ["<-30%", "-30%~-10%", "-10%~0%", "0%~10%", ">10%"]
            counts, _ = np.histogram(sims, bins=bins)
            probs = (counts / request.num_paths).tolist()
            heatmap[f"{horizon}D"] = {label: round(prob, 3) for label, prob in zip(labels, probs)}
            extreme_curve.append({
                "day": horizon,
                "best_return": round(float(np.max(sims)), 4),
                "worst_return": round(float(np.min(sims)), 4),
            })
        # Sensitivity: highlight sectors with highest exposures
        exposures = combine_holdings(weights)
        sorted_exposures = sorted(exposures.items(), key=lambda x: x[1], reverse=True)
        sensitivity = []
        for sector, weight in sorted_exposures[:3]:
            sensitivity.append({
                "factor": f"{sector}波动",
                "expected_change": round(-weight * 0.1, 4),
                "loss_risk": round(weight, 2),
                "affected_exposure": sector,
            })
        # Calculate max drawdown from the price series
        price_series = (1 + portfolio_returns).cumprod()
        mdd_dict = compute_max_drawdown(pd.DataFrame({"price": price_series}))
        max_drawdown = round(float(mdd_dict.get("price", 0.0)), 4)
        data = {
            "heatmap": heatmap,
            "extreme_curve": extreme_curve,
            "sensitivity": sensitivity,
            "max_drawdown": max_drawdown,
        }
    else:
        # Scenario mode returns empty placeholders for now
        data = {
            "heatmap": {},
            "extreme_curve": [],
            "sensitivity": [],
            "max_drawdown": 0.0,
        }
    return {
        "success": True,
        "message": "ok",
        "data": data,
        "meta": {"timestamp": timestamp, "version": "v1"},
    }