"""Historical backtest base.

Minimal, honest backtest engine aimed at regression protection and
attribution for paper portfolios. Designed for walk-forward evaluation
with transaction costs, slippage and scheduled rebalances. The engine is
intentionally small so behaviour can be reasoned about line-by-line.

Scope & honest limits
---------------------
- Uses daily close-to-close returns of the fund proxies (``_FUND_PROXY_MAP``).
  So backtest is proxied — flagged via ``is_proxy=True`` in metadata.
- No look-ahead: weights for day ``t`` are computed using data up to
  ``t-1``; returns on ``t`` apply those weights.
- Survivorship is *not* handled automatically — if a proxy vanishes the
  engine drops it from that day's cross-section. Callers must be aware
  when comparing long histories.
- Transaction costs are linear on notional turnover and slippage is
  linear on absolute weight change. Set both to 0 for a frictionless
  benchmark.
- Rebalance cadence is declared by the caller (``D``/``W``/``M``/``Q``)
  and aligned to the business calendar.
- Results carry a ``method_version`` hash so stored backtests can be
  invalidated when the engine changes.

The engine is deterministic: given the same input series and the same
weighting callable, two runs produce identical numbers.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

import numpy as np
import pandas as pd

from ..core.data_source import DataSourceAdapter
from .portfolio import _FUND_PROXY_MAP, resolve_weights


METHOD_VERSION = "bt.v1"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


_REBALANCE_CADENCES = {
    "D": "B",    # every business day
    "W": "W-FRI",
    "M": "BME",
    "Q": "BQE",
}


@dataclass
class BacktestConfig:
    start: Optional[str] = None
    end: Optional[str] = None
    rebalance: str = "M"           # D | W | M | Q
    transaction_cost_bps: float = 8.0
    slippage_bps: float = 3.0
    initial_nav: float = 1.0
    benchmark_symbol: Optional[str] = "000300.SS"
    method_version: str = METHOD_VERSION

    def cache_key(self) -> str:
        payload = f"{self.start}|{self.end}|{self.rebalance}|{self.transaction_cost_bps}|{self.slippage_bps}|{self.benchmark_symbol}|{self.method_version}"
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Data assembly (proxied)
# ---------------------------------------------------------------------------


def _load_proxy_returns(adapter: DataSourceAdapter, fund_codes: List[str]) -> pd.DataFrame:
    raw = adapter.index_price_data()
    cols: Dict[str, pd.Series] = {}
    for code in fund_codes:
        proxy = _FUND_PROXY_MAP.get(code)
        if proxy and proxy in raw:
            cols[code] = raw[proxy]["Adj Close"].pct_change().fillna(0.0)
    if not cols:
        return pd.DataFrame()
    return pd.DataFrame(cols).dropna(how="all")


def _benchmark_returns(adapter: DataSourceAdapter, symbol: Optional[str]) -> pd.Series:
    if not symbol:
        return pd.Series(dtype=float)
    raw = adapter.index_price_data()
    if symbol not in raw:
        return pd.Series(dtype=float)
    return raw[symbol]["Adj Close"].pct_change().fillna(0.0).rename("benchmark")


# ---------------------------------------------------------------------------
# Rebalance schedule
# ---------------------------------------------------------------------------


def _rebalance_dates(index: pd.DatetimeIndex, cadence: str) -> pd.DatetimeIndex:
    freq = _REBALANCE_CADENCES.get(cadence, _REBALANCE_CADENCES["M"])
    if len(index) == 0:
        return index
    if cadence == "D":
        return index
    grid = pd.date_range(start=index.min(), end=index.max(), freq=freq)
    # snap to actual trading day at or before grid point
    snapped = []
    for g in grid:
        slot = index[index <= g]
        if len(slot):
            snapped.append(slot[-1])
    out = pd.DatetimeIndex(sorted(set(snapped)))
    if len(out) == 0:
        out = pd.DatetimeIndex([index[0]])
    return out


# ---------------------------------------------------------------------------
# Core walk-forward loop
# ---------------------------------------------------------------------------


WeightFn = Callable[[pd.Timestamp, pd.DataFrame], Mapping[str, float]]


def _constant_weights(weights: Mapping[str, float]) -> WeightFn:
    frozen = dict(weights)
    def fn(_ts: pd.Timestamp, _hist: pd.DataFrame) -> Mapping[str, float]:
        return frozen
    return fn


def walk_forward(
    returns: pd.DataFrame,
    weight_fn: WeightFn,
    cfg: BacktestConfig,
    benchmark: Optional[pd.Series] = None,
) -> Dict[str, Any]:
    if returns.empty:
        return {"nav": [], "summary": {}, "method_version": cfg.method_version}

    if cfg.start:
        returns = returns.loc[returns.index >= pd.Timestamp(cfg.start)]
    if cfg.end:
        returns = returns.loc[returns.index <= pd.Timestamp(cfg.end)]
    if returns.empty:
        return {"nav": [], "summary": {}, "method_version": cfg.method_version}

    reb_dates = _rebalance_dates(returns.index, cfg.rebalance)
    reb_set = set(pd.Timestamp(d) for d in reb_dates)

    fee_rate = cfg.transaction_cost_bps * 1e-4
    slip_rate = cfg.slippage_bps * 1e-4

    current_weights = pd.Series(0.0, index=returns.columns)
    nav = cfg.initial_nav
    nav_path: List[Dict[str, Any]] = []
    turnover_series: List[float] = []
    cost_series: List[float] = []

    for ts, row in returns.iterrows():
        # realize returns with yesterday's weights, then rebalance at close
        port_ret = float((row.fillna(0.0) * current_weights).sum())
        nav = nav * (1 + port_ret)

        turnover = 0.0
        cost = 0.0
        if ts in reb_set or nav_path == []:
            hist = returns.loc[:ts].iloc[:-1]
            target_raw = weight_fn(ts, hist) or {}
            target = pd.Series({c: float(target_raw.get(c, 0.0)) for c in returns.columns})
            total = float(target.abs().sum())
            if total > 0:
                target = target / total
            else:
                target = pd.Series(0.0, index=returns.columns)
            turnover = float((target - current_weights).abs().sum())
            cost = turnover * (fee_rate + slip_rate)
            nav = nav * (1 - cost)
            current_weights = target

        turnover_series.append(turnover)
        cost_series.append(cost)
        nav_path.append({"date": ts.strftime("%Y-%m-%d"), "nav": round(nav, 6), "turnover": round(turnover, 4)})

    nav_series = pd.Series([p["nav"] for p in nav_path], index=returns.index)
    daily_ret = nav_series.pct_change().fillna(0.0)
    summary = _summary(daily_ret, nav_series, benchmark, reb_dates)
    summary["total_transaction_cost"] = round(float(sum(cost_series)), 6)
    summary["total_turnover"] = round(float(sum(turnover_series)), 4)

    return {
        "nav": nav_path,
        "summary": summary,
        "rebalance_dates": [d.strftime("%Y-%m-%d") for d in reb_dates],
        "method_version": cfg.method_version,
        "cache_key": cfg.cache_key(),
    }


def _summary(
    daily_ret: pd.Series,
    nav: pd.Series,
    benchmark: Optional[pd.Series],
    reb_dates: pd.DatetimeIndex,
) -> Dict[str, Any]:
    if daily_ret.empty:
        return {}
    total_return = float(nav.iloc[-1] / nav.iloc[0] - 1)
    ann_ret = float(daily_ret.mean() * 252)
    ann_vol = float(daily_ret.std() * np.sqrt(252))
    sharpe = float(ann_ret / ann_vol) if ann_vol else 0.0
    roll_max = nav.cummax()
    dd = nav / roll_max - 1
    mdd = float(dd.min())
    hit = float((daily_ret > 0).mean())

    out: Dict[str, Any] = {
        "total_return": round(total_return, 4),
        "annualised_return": round(ann_ret, 4),
        "annualised_volatility": round(ann_vol, 4),
        "sharpe_proxy": round(sharpe, 3),
        "max_drawdown": round(mdd, 4),
        "hit_ratio": round(hit, 3),
        "rebalance_count": len(reb_dates),
    }

    if benchmark is not None and not benchmark.empty:
        bench = benchmark.reindex(daily_ret.index).fillna(0.0)
        excess = daily_ret - bench
        te = float(excess.std() * np.sqrt(252))
        ir = float(excess.mean() * 252 / te) if te else 0.0
        out["benchmark_total_return"] = round(float((1 + bench).prod() - 1), 4)
        out["tracking_error"] = round(te, 4)
        out["information_ratio_proxy"] = round(ir, 3)
    return out


# ---------------------------------------------------------------------------
# Public entry point for router-level consumption
# ---------------------------------------------------------------------------


def backtest_portfolio(
    adapter: DataSourceAdapter,
    portfolio_id: str,
    cfg: Optional[BacktestConfig] = None,
    weight_fn: Optional[WeightFn] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Run a walk-forward backtest using the portfolio's default weights.

    Returns ``(payload, source_meta_dict)``.
    """
    cfg = cfg or BacktestConfig()
    portfolio_id, weights = resolve_weights(adapter, portfolio_id)
    returns = _load_proxy_returns(adapter, list(weights.keys()))
    if returns.empty:
        meta = adapter.meta(universe="backtest").to_dict()
        meta["calculation_method_version"] = cfg.method_version
        meta["is_proxy"] = True
        meta["fallback_reason"] = "proxy series empty"
        return {"nav": [], "summary": {}, "method_version": cfg.method_version}, meta

    fn = weight_fn or _constant_weights(weights)
    benchmark = _benchmark_returns(adapter, cfg.benchmark_symbol).reindex(returns.index).fillna(0.0)

    result = walk_forward(returns, fn, cfg, benchmark=benchmark)
    result["portfolio_id"] = portfolio_id
    result["benchmark_symbol"] = cfg.benchmark_symbol
    result["is_proxy"] = True
    result["note"] = "回测序列由指数代理构造，非真实基金净值，仅用于相对比较与回归保护。"

    meta = adapter.meta(universe="backtest").to_dict()
    meta["calculation_method_version"] = cfg.method_version
    meta["is_proxy"] = True
    meta["evidence_count"] = len(result.get("nav", []))
    return result, meta
