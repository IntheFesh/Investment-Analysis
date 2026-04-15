"""
data_analysis
=============

This module contains a collection of functions for computing common risk and performance
metrics from financial time series.  It is designed to operate on `pandas` DataFrames
containing price or return data indexed by date.  The resulting statistics can be
used for comparing assets, assessing risk and building portfolio optimisation routines.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


def compute_daily_returns(price_data: pd.DataFrame) -> pd.DataFrame:
    """Compute simple daily returns from a price series.

    The return on day *t* is calculated as ``(P_t / P_{t-1}) - 1``.  The first
    observation is dropped because it has no preceding price.

    Parameters
    ----------
    price_data: pandas.DataFrame
        A DataFrame where each column corresponds to a ticker and the index is a
        DateTimeIndex of closing prices.

    Returns
    -------
    pandas.DataFrame
        A DataFrame of the same shape with daily return values.
    """
    returns = price_data.pct_change().dropna(how="all")
    return returns


def compute_volatility(returns: pd.DataFrame, trading_days: int = 252) -> pd.Series:
    """Annualised volatility of returns.

    Parameters
    ----------
    returns: pandas.DataFrame
        Daily return series for one or more assets.
    trading_days: int, default 252
        Number of trading days per year to annualise the standard deviation.

    Returns
    -------
    pandas.Series
        A series mapping each column in the input to its annualised volatility.
    """
    # Standard deviation of daily returns scaled by square root of trading days
    vol = returns.std() * np.sqrt(trading_days)
    return vol


def compute_correlation(returns: pd.DataFrame) -> pd.DataFrame:
    """Compute the correlation matrix of asset returns."""
    return returns.corr()


def compute_sharpe_ratio(
    returns: pd.DataFrame,
    risk_free_rate: float = 0.0,
    trading_days: int = 252,
) -> pd.Series:
    """Calculate the annualised Sharpe ratio for each asset.

    The Sharpe ratio is defined as ``(mean_return - risk_free_rate) / volatility``.
    Returns are annualised by multiplying the mean daily return by the number of
    trading days.

    Parameters
    ----------
    returns: pandas.DataFrame
        Daily returns for one or more assets.
    risk_free_rate: float, default 0.0
        The annual risk‑free rate expressed as a decimal fraction (e.g. 0.02 for 2%).
    trading_days: int, default 252
        Number of trading days per year.

    Returns
    -------
    pandas.Series
        A series containing the Sharpe ratio of each asset.
    """
    mean_daily = returns.mean()
    std_daily = returns.std()
    excess_daily = mean_daily - (risk_free_rate / trading_days)
    sharpe_daily = excess_daily / std_daily
    # Annualise the ratio
    sharpe_annual = sharpe_daily * np.sqrt(trading_days)
    return sharpe_annual


def compute_max_drawdown(price_data: pd.DataFrame) -> Dict[str, float]:
    """Compute the maximum drawdown for each asset.

    The drawdown at time *t* is the percentage loss from the historical peak up to
    that point.  The maximum drawdown is the minimum value of the drawdown series.

    Parameters
    ----------
    price_data: pandas.DataFrame
        Price series with tickers as columns.

    Returns
    -------
    dict[str, float]
        A mapping from ticker to its maximum drawdown (expressed as a negative value).
    """
    max_drawdowns: Dict[str, float] = {}
    for col in price_data.columns:
        series = price_data[col].dropna()
        running_max = series.cummax()
        drawdown = (series / running_max) - 1.0
        max_drawdowns[col] = drawdown.min()
    return max_drawdowns