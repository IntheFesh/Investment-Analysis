"""Risk / return primitives.

Moved here from the root ``data_analysis.py`` so that routers never import
from outside the ``backend`` package.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


def daily_returns(price: pd.DataFrame) -> pd.DataFrame:
    return price.pct_change().dropna(how="all")


def annualised_volatility(returns: pd.DataFrame, trading_days: int = 252) -> pd.Series:
    return returns.std() * np.sqrt(trading_days)


def sharpe_ratio(returns: pd.DataFrame, risk_free: float = 0.0, trading_days: int = 252) -> pd.Series:
    mean_daily = returns.mean()
    std_daily = returns.std()
    excess = mean_daily - (risk_free / trading_days)
    return (excess / std_daily) * np.sqrt(trading_days)


def max_drawdown(price: pd.DataFrame) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for col in price.columns:
        s = price[col].dropna()
        peak = s.cummax()
        dd = (s / peak) - 1.0
        out[col] = float(dd.min()) if len(dd) else 0.0
    return out


def window_return(series: pd.Series, days: int) -> float:
    if len(series) < days + 1:
        return 0.0
    s = series.tail(days + 1)
    return float(s.iloc[-1] / s.iloc[0] - 1.0)


def parse_time_window(window: str) -> int:
    if not window:
        return 20
    window = window.upper()
    try:
        if window == "YTD":
            return 120
        if window == "CUSTOM":
            return 20
        if window.endswith("D"):
            return max(1, int(window[:-1]))
        if window.endswith("Y"):
            return max(1, int(float(window[:-1]) * 252))
    except (TypeError, ValueError):
        pass
    return 20
