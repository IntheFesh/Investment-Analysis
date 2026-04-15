"""
Sample data generation and helper functions.

This module provides in‑memory data sets for indices, funds and portfolios
used throughout the API.  Since the environment does not allow external
network access, these functions simulate plausible financial time series
and holdings so that the analysis routines can operate on them.  The
intention is not to reflect real market prices but to produce numbers that
behave similarly (i.e. trending up and down with some volatility).

The sample data covers a handful of major Chinese and global indices
(`000001.SS`, `399001.SZ`, `HSI`, `SPX`), a few mutual funds with basic
metadata and holdings exposures, and a default user portfolio comprised
of these funds.  Each price series spans roughly one year of daily
observations.  Random seeds are fixed so that generated data is
deterministic across invocations.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


def _generate_price_series(
    start: datetime,
    end: datetime,
    base_price: float,
    volatility: float,
    trend: float = 0.0,
    seed: int | None = None,
) -> pd.DataFrame:
    """Generate a synthetic daily price series.

    Parameters
    ----------
    start: datetime
        Start date of the series.
    end: datetime
        End date of the series (inclusive).
    base_price: float
        Starting price at the beginning of the series.
    volatility: float
        Standard deviation of the daily return distribution (e.g. 0.02 for 2%).
    trend: float, default 0.0
        Drift component of the daily return (positive for up‑trend).
    seed: int, optional
        Random seed for reproducibility.

    Returns
    -------
    pandas.DataFrame
        A DataFrame with a DatetimeIndex and columns ``['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']``.
    """
    if seed is not None:
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()
    dates = pd.date_range(start=start, end=end, freq="B")  # Business days
    num_days = len(dates)
    # Generate daily log returns with drift and volatility
    log_returns = rng.normal(loc=trend, scale=volatility, size=num_days)
    prices = base_price * np.exp(np.cumsum(log_returns))
    # Build OHLC approximations: assume open == prior close and intraday range ±1% of close
    close = pd.Series(prices, index=dates)
    open_ = close.shift(1).fillna(close.iloc[0])
    high = close * (1 + 0.01)
    low = close * (1 - 0.01)
    volume = rng.integers(low=1e5, high=5e5, size=num_days)
    df = pd.DataFrame(
        {
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Adj Close": close,
            "Volume": volume,
        }
    )
    df.index.name = "Date"
    return df


def get_index_price_data() -> Dict[str, pd.DataFrame]:
    """Return synthetic price data for several indices.

    The time span covers the last 252 trading days (approx. one year).

    Returns
    -------
    dict[str, pd.DataFrame]
        Mapping of ticker symbols to their price DataFrames.
    """
    end = datetime.today()
    start = end - timedelta(days=365)
    indices = {
        "000001.SS": (3000.0, 0.012, 0.0002),  # Shanghai Composite
        "399001.SZ": (11000.0, 0.013, 0.00015),  # Shenzhen Component
        "HSI": (18000.0, 0.015, -0.0001),  # Hang Seng Index (slight downtrend)
        "SPX": (4500.0, 0.01, 0.00025),  # S&P 500
    }
    data: Dict[str, pd.DataFrame] = {}
    seed_base = 42
    for i, (symbol, (base_price, vol, drift)) in enumerate(indices.items()):
        data[symbol] = _generate_price_series(start, end, base_price, vol, drift, seed=seed_base + i)
    return data


def get_fund_holdings() -> Dict[str, Dict[str, float]]:
    """Return sample fund holdings as sector weights.

    The keys are fund codes; the values map sector names to weight percentages.
    """
    return {
        "FUND001": {"半导体": 0.35, "医药": 0.25, "消费": 0.20, "银行": 0.10, "现金": 0.10},
        "FUND002": {"新能源": 0.30, "医药": 0.30, "消费": 0.25, "原材料": 0.10, "现金": 0.05},
        "FUND003": {"金融": 0.40, "地产": 0.20, "消费": 0.20, "能源": 0.10, "现金": 0.10},
        "FUND004": {"科技": 0.50, "医药": 0.20, "消费": 0.15, "防御": 0.10, "现金": 0.05},
        "FUND005": {"消费": 0.40, "红利": 0.30, "医药": 0.20, "现金": 0.10},
    }


def get_fund_metadata() -> Dict[str, Dict[str, str | float]]:
    """Return basic metadata for the sample funds."""
    return {
        "FUND001": {
            "name": "半导体成长混合",
            "type": "股票型",
            "manager": "李四",
            "aum": 8.5e9,
            "inception_date": "2019-05-10",
        },
        "FUND002": {
            "name": "新能源先锋",
            "type": "股票型",
            "manager": "王五",
            "aum": 6.2e9,
            "inception_date": "2021-01-15",
        },
        "FUND003": {
            "name": "金融地产优选",
            "type": "混合型",
            "manager": "赵六",
            "aum": 4.7e9,
            "inception_date": "2018-09-01",
        },
        "FUND004": {
            "name": "科技创新先锋",
            "type": "股票型",
            "manager": "张三",
            "aum": 7.8e9,
            "inception_date": "2020-03-20",
        },
        "FUND005": {
            "name": "消费红利精选",
            "type": "混合型",
            "manager": "钱七",
            "aum": 5.3e9,
            "inception_date": "2017-11-05",
        },
    }


def get_user_portfolio() -> Tuple[str, Dict[str, float]]:
    """Return a default user portfolio identifier and its fund weights.

    The weights sum to 1.

    Returns
    -------
    (str, dict[str, float])
        A tuple of portfolio ID and a mapping of fund codes to weights.
    """
    return "pf_default", {"FUND001": 0.25, "FUND002": 0.25, "FUND003": 0.20, "FUND004": 0.20, "FUND005": 0.10}


def combine_holdings(weights: Dict[str, float]) -> Dict[str, float]:
    """Aggregate sector weights from individual fund holdings given portfolio weights.

    Parameters
    ----------
    weights: dict[str, float]
        Mapping of fund codes to portfolio weights.

    Returns
    -------
    dict[str, float]
        Combined sector exposures normalized to sum to 1.
    """
    holdings = get_fund_holdings()
    combined: Dict[str, float] = {}
    for fund_code, fund_weight in weights.items():
        sectors = holdings.get(fund_code, {})
        for sector, sector_weight in sectors.items():
            combined[sector] = combined.get(sector, 0.0) + sector_weight * fund_weight
    # Normalize to sum to 1
    total = sum(combined.values())
    if total > 0:
        combined = {sector: weight / total for sector, weight in combined.items()}
    return combined


def get_style_exposures() -> Dict[str, Dict[str, float]]:
    """Return sample style exposures for funds.

    Style exposures reflect factor bets such as growth, value, dividend or defensive.
    """
    return {
        "FUND001": {"成长": 0.60, "价值": 0.25, "红利": 0.10, "防御": 0.05},
        "FUND002": {"成长": 0.50, "价值": 0.20, "红利": 0.20, "防御": 0.10},
        "FUND003": {"成长": 0.30, "价值": 0.40, "红利": 0.20, "防御": 0.10},
        "FUND004": {"成长": 0.70, "价值": 0.15, "红利": 0.10, "防御": 0.05},
        "FUND005": {"成长": 0.35, "价值": 0.25, "红利": 0.30, "防御": 0.10},
    }


def combine_styles(weights: Dict[str, float]) -> Dict[str, float]:
    """Aggregate style exposures from individual funds given portfolio weights."""
    styles = get_style_exposures()
    combined: Dict[str, float] = {}
    for fund_code, fund_weight in weights.items():
        fund_styles = styles.get(fund_code, {})
        for style, style_weight in fund_styles.items():
            combined[style] = combined.get(style, 0.0) + style_weight * fund_weight
    total = sum(combined.values())
    if total > 0:
        combined = {style: weight / total for style, weight in combined.items()}
    return combined


def get_return_series_for_portfolio(weights: Dict[str, float]) -> pd.Series:
    """Compute the portfolio return series given fund weights.

    Uses the synthetic index price data as proxy for fund performance.  Each fund
    is mapped to one of the synthetic indices to derive a representative return
    series.  The mapping is arbitrary but consistent.

    Returns
    -------
    pandas.Series
        Daily return series for the portfolio.
    """
    index_data = get_index_price_data()
    # Map funds to indices (cyclical assignment)
    symbols = list(index_data.keys())
    fund_codes = list(weights.keys())
    returns_list: List[pd.Series] = []
    fund_weights: List[float] = []
    for i, fund_code in enumerate(fund_codes):
        symbol = symbols[i % len(symbols)]
        price_df = index_data[symbol]["Adj Close"]
        returns = price_df.pct_change().fillna(0)
        returns_list.append(returns)
        fund_weights.append(weights[fund_code])
    # Align series and compute weighted sum
    aligned = pd.concat(returns_list, axis=1).fillna(0)
    weight_array = np.array(fund_weights)
    portfolio_returns = aligned.dot(weight_array)
    portfolio_returns.name = "portfolio"
    return portfolio_returns