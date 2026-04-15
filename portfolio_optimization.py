"""
portfolio_optimization
======================

This module implements a basic mean–variance optimisation routine.  It provides
functions to calculate portfolio performance metrics given a set of asset weights
and to optimise weights for a maximum Sharpe ratio subject to the weights
summing to one.  Only long‑only portfolios are considered.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize


def portfolio_performance(
    weights: np.ndarray,
    returns: pd.DataFrame,
    risk_free_rate: float = 0.0,
    trading_days: int = 252,
) -> Tuple[float, float, float]:
    """Compute expected annualised return, volatility and Sharpe ratio for a portfolio.

    Parameters
    ----------
    weights: np.ndarray
        Array of portfolio weights summing to 1.
    returns: pandas.DataFrame
        Daily return series for each asset.
    risk_free_rate: float, default 0.0
        Annual risk‑free rate as a decimal.
    trading_days: int, default 252
        Number of trading days per year.

    Returns
    -------
    (float, float, float)
        A tuple of (expected return, volatility, Sharpe ratio), all annualised.
    """
    mean_daily = returns.mean().values
    cov_daily = returns.cov().values
    # Annualise mean and covariance
    mean_annual = mean_daily * trading_days
    cov_annual = cov_daily * trading_days
    port_return = np.dot(weights, mean_annual)
    port_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_annual, weights)))
    sharpe = 0.0
    if port_volatility != 0:
        sharpe = (port_return - risk_free_rate) / port_volatility
    return port_return, port_volatility, sharpe


def _neg_sharpe_ratio(weights: np.ndarray, returns: pd.DataFrame, risk_free_rate: float, trading_days: int) -> float:
    """Objective function: negative Sharpe ratio for use in optimisation."""
    _, _, sharpe = portfolio_performance(weights, returns, risk_free_rate, trading_days)
    return -sharpe


def optimise_portfolio(
    returns: pd.DataFrame,
    risk_free_rate: float = 0.0,
    trading_days: int = 252,
) -> np.ndarray:
    """Optimise portfolio weights to maximise the Sharpe ratio.

    A long‑only constraint is enforced by bounding each weight between 0 and 1.
    The weights are constrained to sum to 1.  Optimisation is performed using
    the SLSQP algorithm from SciPy.

    Parameters
    ----------
    returns: pandas.DataFrame
        Daily returns for the assets in the portfolio.
    risk_free_rate: float, default 0.0
        Annual risk‑free rate.
    trading_days: int, default 252
        Number of trading days per year.

    Returns
    -------
    numpy.ndarray
        The optimised weights, one per asset.
    """
    num_assets = returns.shape[1]
    if num_assets == 0:
        raise ValueError("Returns DataFrame must contain at least one asset.")
    # Start from equal weights
    x0 = np.full(num_assets, 1.0 / num_assets)
    # Long‑only bounds for each weight
    bounds = [(0.0, 1.0) for _ in range(num_assets)]
    # Weights must sum to one
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
    result = minimize(
        _neg_sharpe_ratio,
        x0,
        args=(returns, risk_free_rate, trading_days),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints,
        options={'disp': False}
    )
    if not result.success:
        raise RuntimeError(f"Optimisation failed: {result.message}")
    return result.x