"""Risk-sentiment state machine (v2).

Four factor clusters, each a composite of concrete indicators normalised
against rolling historical percentiles. Short-term (20d) and mid-term
(60d) windows have independent weights and the engine emits a state
transition (``risk_on``, ``risk_neutral``, ``risk_off``, ``stress``)
plus the dominant drivers.

Clusters:

- ``volatility_tail``: realised vol (20d/60d), vol-of-vol, VIX percentile,
  drawdown vs 60d high.
- ``liquidity_preference``: dollar-turnover momentum on liquidity proxies,
  10Y-rate change (percentile), DXY percentile — proxies!
- ``breadth_participation``: breadth_pool advance ratio, % above MA20,
  % above MA60, new_highs / new_lows ratio, hotspot concentration.
- ``external_shock``: NDX 5d return vs HSTECH 5d, VIX window change,
  USD-CNH change.

Every output carries evidence. Results are stamped with a watermark
``(universe, trading_day, method_version)`` to support last-good-cache.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ..core.data_source import DataSourceAdapter
from ..core.evidence import stamp_evidence
from ..core.universe import get_universe, required_symbols_for


METHOD_VERSION = "sent.v2"


FACTOR_WEIGHTS_SHORT = {
    "volatility_tail": 0.35,
    "liquidity_preference": 0.20,
    "breadth_participation": 0.30,
    "external_shock": 0.15,
}

FACTOR_WEIGHTS_MID = {
    "volatility_tail": 0.30,
    "liquidity_preference": 0.25,
    "breadth_participation": 0.25,
    "external_shock": 0.20,
}

STATE_THRESHOLDS = [
    (80.0, "risk_on"),
    (60.0, "lean_risk_on"),
    (40.0, "neutral"),
    (20.0, "lean_risk_off"),
    (0.0, "stress"),
]


def _state_label(score: float) -> str:
    for thr, label in STATE_THRESHOLDS:
        if score >= thr:
            return label
    return "stress"


def _label_zh(state: str) -> str:
    return {
        "risk_on": "风险偏好充分",
        "lean_risk_on": "偏乐观",
        "neutral": "中性",
        "lean_risk_off": "偏谨慎",
        "stress": "压力区间",
    }.get(state, state)


def _rolling_percentile(series: pd.Series, window: int = 252) -> float:
    if series.empty:
        return 0.5
    recent = series.tail(window)
    latest = series.iloc[-1]
    return float((recent <= latest).mean())


def _invert(p: float) -> float:
    return 1.0 - p


def _score(p: float) -> float:
    """Map a 0-1 percentile to a 0-100 score."""
    return float(max(0.0, min(100.0, p * 100)))


def _volatility_tail(data: Dict[str, pd.DataFrame], window: int, universe_pool: List[str]) -> Dict[str, Any]:
    pool = [s for s in universe_pool if s in data]
    if not pool:
        return {"score": 50.0, "indicators": {}}
    rets = []
    for s in pool:
        rets.append(data[s]["Adj Close"].pct_change().dropna())
    all_rets = pd.concat(rets, axis=1).dropna(how="any")
    if all_rets.empty:
        return {"score": 50.0, "indicators": {}}
    avg_daily = all_rets.mean(axis=1)
    roll_vol = avg_daily.rolling(window).std() * np.sqrt(252)
    vol_now = float(roll_vol.iloc[-1]) if len(roll_vol.dropna()) else 0.0
    vol_pct = _rolling_percentile(roll_vol.dropna())
    # Drawdown from rolling peak
    price_path = (1 + avg_daily).cumprod()
    dd = float(price_path.iloc[-1] / price_path.tail(60).max() - 1) if len(price_path) >= 60 else 0.0

    vix_pct = 0.5
    if "VIX" in data:
        vix_close = data["VIX"]["Adj Close"]
        vix_pct = _rolling_percentile(vix_close)

    # Lower vol & shallower drawdown → higher score (risk_on)
    score = _score(_invert(0.5 * vol_pct + 0.3 * vix_pct) * 1.0 + 0.2 * max(0.0, 1 + dd))
    indicators = {
        "realised_vol": round(vol_now, 4),
        "vol_percentile_1y": round(vol_pct, 3),
        "vix_percentile_1y": round(vix_pct, 3),
        "drawdown_from_60d_high": round(dd, 4),
    }
    return {"score": round(score, 2), "indicators": indicators}


def _liquidity_preference(data: Dict[str, pd.DataFrame], window: int, liq_symbols: List[str]) -> Dict[str, Any]:
    pool = [s for s in liq_symbols if s in data]
    if not pool:
        return {"score": 50.0, "indicators": {}}
    momentums = []
    for s in pool:
        dv = (data[s]["Adj Close"] * data[s]["Volume"]).astype(float)
        recent = dv.tail(window).mean() if len(dv) >= window else dv.mean()
        base = dv.tail(252).mean() if len(dv) >= 252 else dv.mean()
        momentums.append(float(recent / (base or 1.0) - 1))
    universe_liq = float(np.mean(momentums)) if momentums else 0.0

    # Rate / dollar proxy — higher rates or stronger USD = risk_off
    rate_pct = 0.5
    if "US10Y" in data:
        rate_pct = _rolling_percentile(data["US10Y"]["Adj Close"])
    dxy_pct = 0.5
    if "DXY" in data:
        dxy_pct = _rolling_percentile(data["DXY"]["Adj Close"])

    liquidity_score = 0.5 + 0.3 * np.tanh(universe_liq * 4)
    risk_off_tilt = 0.5 * rate_pct + 0.5 * dxy_pct
    blended = 0.6 * liquidity_score + 0.4 * (1 - risk_off_tilt)
    score = _score(blended)

    return {
        "score": round(score, 2),
        "indicators": {
            "universe_liquidity_momentum": round(universe_liq, 3),
            "us10y_percentile_1y": round(rate_pct, 3),
            "dxy_percentile_1y": round(dxy_pct, 3),
        },
    }


def _breadth_participation(data: Dict[str, pd.DataFrame], window: int, pool_syms: List[str]) -> Dict[str, Any]:
    pool = [s for s in pool_syms if s in data]
    if not pool:
        return {"score": 50.0, "indicators": {}}
    advance_days = 0
    total_days = 0
    above_ma20 = 0
    above_ma60 = 0
    new_high_count = 0
    new_low_count = 0
    for s in pool:
        close = data[s]["Adj Close"]
        if len(close) < 60:
            continue
        rets = close.tail(window).pct_change().dropna()
        advance_days += int((rets > 0).sum())
        total_days += len(rets)
        if close.iloc[-1] > close.tail(20).mean():
            above_ma20 += 1
        if close.iloc[-1] > close.tail(60).mean():
            above_ma60 += 1
        if close.iloc[-1] >= close.tail(60).max() * 0.995:
            new_high_count += 1
        if close.iloc[-1] <= close.tail(60).min() * 1.005:
            new_low_count += 1

    adv_ratio = advance_days / max(1, total_days)
    above20 = above_ma20 / max(1, len(pool))
    above60 = above_ma60 / max(1, len(pool))
    hi_lo_ratio = (new_high_count + 1) / (new_high_count + new_low_count + 2)

    score = _score(0.35 * adv_ratio + 0.25 * above20 + 0.2 * above60 + 0.2 * hi_lo_ratio)
    return {
        "score": round(score, 2),
        "indicators": {
            "advance_ratio": round(adv_ratio, 3),
            "pct_above_ma20": round(above20, 3),
            "pct_above_ma60": round(above60, 3),
            "hi_lo_ratio": round(hi_lo_ratio, 3),
        },
    }


def _external_shock(data: Dict[str, pd.DataFrame], window: int) -> Dict[str, Any]:
    ind: Dict[str, Any] = {}
    score_bits: List[float] = []

    for s in ("NDX", "HSTECH", "SPX"):
        df = data.get(s)
        if df is None:
            continue
        close = df["Adj Close"]
        if len(close) < window + 1:
            continue
        r = float(close.iloc[-1] / close.iloc[-window] - 1)
        ind[f"{s}_window_return"] = round(r, 4)
        # stronger overseas → risk_on
        score_bits.append(0.5 + 0.5 * np.tanh(r * 5))

    if "VIX" in data:
        vix = data["VIX"]["Adj Close"]
        vix_chg = float(vix.iloc[-1] / vix.iloc[-window] - 1) if len(vix) > window else 0.0
        ind["vix_window_change"] = round(vix_chg, 4)
        score_bits.append(0.5 - 0.5 * np.tanh(vix_chg * 4))

    if "CNH" in data and "DXY" in data:
        cnh = data["CNH"]["Adj Close"]
        dxy = data["DXY"]["Adj Close"]
        ind["cnh_window_change"] = round(float(cnh.iloc[-1] / cnh.iloc[-window] - 1), 4) if len(cnh) > window else 0.0
        ind["dxy_window_change"] = round(float(dxy.iloc[-1] / dxy.iloc[-window] - 1), 4) if len(dxy) > window else 0.0

    if not score_bits:
        return {"score": 50.0, "indicators": ind}
    return {"score": round(_score(float(np.mean(score_bits))), 2), "indicators": ind}


def _compose(factors: Dict[str, Dict[str, Any]], weights: Dict[str, float]) -> float:
    total = sum(factors.get(k, {}).get("score", 50.0) * w for k, w in weights.items())
    return round(float(total), 2)


def _state_transition(short_score: float, mid_score: float) -> Dict[str, Any]:
    # Simple 3-state delta: improving / stable / deteriorating
    delta = short_score - mid_score
    if delta > 8:
        direction = "improving"
    elif delta < -8:
        direction = "deteriorating"
    else:
        direction = "stable"
    return {
        "direction": direction,
        "delta": round(delta, 2),
        "short_state": _state_label(short_score),
        "mid_state": _state_label(mid_score),
    }


def _time_series(data: Dict[str, pd.DataFrame], universe_pool: List[str], liq_syms: List[str]) -> List[Dict[str, Any]]:
    pool = [s for s in universe_pool if s in data]
    if not pool:
        return []
    first = data[pool[0]]
    end_dates = list(first.index[-30:])
    ts: List[Dict[str, Any]] = []
    for d in end_dates:
        truncated = {k: df[df.index <= d] for k, df in data.items()}
        short_score = _compose(
            {
                "volatility_tail": _volatility_tail(truncated, 20, universe_pool),
                "liquidity_preference": _liquidity_preference(truncated, 20, liq_syms),
                "breadth_participation": _breadth_participation(truncated, 20, universe_pool),
                "external_shock": _external_shock(truncated, 20),
            },
            FACTOR_WEIGHTS_SHORT,
        )
        mid_score = _compose(
            {
                "volatility_tail": _volatility_tail(truncated, 60, universe_pool),
                "liquidity_preference": _liquidity_preference(truncated, 60, liq_syms),
                "breadth_participation": _breadth_participation(truncated, 60, universe_pool),
                "external_shock": _external_shock(truncated, 60),
            },
            FACTOR_WEIGHTS_MID,
        )
        ts.append({"date": d.strftime("%Y-%m-%d"), "short": short_score, "mid": mid_score})
    return ts


def build_overview(adapter: DataSourceAdapter, time_window: str, market_view: str) -> Dict[str, Any]:
    universe = get_universe(market_view)
    syms = required_symbols_for(market_view)
    data = adapter.index_price_data(syms)

    source_meta = adapter.meta(universe=universe.id).to_dict()
    source_meta["calculation_method_version"] = METHOD_VERSION

    short_factors = {
        "volatility_tail": _volatility_tail(data, 20, universe.breadth_pool),
        "liquidity_preference": _liquidity_preference(data, 20, universe.liquidity_proxy_symbols or universe.breadth_pool),
        "breadth_participation": _breadth_participation(data, 20, universe.breadth_pool),
        "external_shock": _external_shock(data, 20),
    }
    mid_factors = {
        "volatility_tail": _volatility_tail(data, 60, universe.breadth_pool),
        "liquidity_preference": _liquidity_preference(data, 60, universe.liquidity_proxy_symbols or universe.breadth_pool),
        "breadth_participation": _breadth_participation(data, 60, universe.breadth_pool),
        "external_shock": _external_shock(data, 60),
    }

    short_score = _compose(short_factors, FACTOR_WEIGHTS_SHORT)
    mid_score = _compose(mid_factors, FACTOR_WEIGHTS_MID)
    transition = _state_transition(short_score, mid_score)

    factors = []
    for key, label in [
        ("volatility_tail", "波动与尾部"),
        ("liquidity_preference", "流动性偏好（代理）"),
        ("breadth_participation", "广度与参与度"),
        ("external_shock", "外部冲击"),
    ]:
        f_short = short_factors[key]
        f_mid = mid_factors[key]
        direction = "up" if f_short["score"] >= f_mid["score"] else "down"
        factors.append({
            "id": key,
            "name": label,
            "short_score": f_short["score"],
            "mid_score": f_mid["score"],
            "direction": direction,
            "driver": _dominant_driver(key, f_short["indicators"]),
            "indicators": f_short["indicators"],
            "indicators_mid": f_mid["indicators"],
            "evidence": stamp_evidence(
                source_meta,
                conclusion=f"{label} 因子得分 {f_short['score']}",
                method=f"factor::{key}",
                indicators=f_short["indicators"],
                confidence=0.6,
                failure_conditions=["指标窗口不足 60 日", "代理口径与真实成分偏差 > 30%"],
                risks=["代理数据为主，外部冲击类需人工复核事件时间线"],
                is_proxy=bool(source_meta.get("is_proxy")) or key == "liquidity_preference",
            ),
        })

    time_series = _time_series(data, universe.breadth_pool, universe.liquidity_proxy_symbols or universe.breadth_pool)

    contributions = [
        {
            "name": factors[i]["name"],
            "weight": FACTOR_WEIGHTS_SHORT[factors[i]["id"]],
            "score": factors[i]["short_score"],
        }
        for i in range(len(factors))
    ]

    # Top drivers: sort by deviation from 50
    short_sorted = sorted(factors, key=lambda f: abs(f["short_score"] - 50), reverse=True)
    mid_sorted = sorted(factors, key=lambda f: abs(f["mid_score"] - 50), reverse=True)

    payload = {
        "market_view": market_view,
        "universe_id": universe.id,
        "universe_label": universe.label,
        "time_window": time_window,
        "short_term_score": short_score,
        "mid_term_score": mid_score,
        "short_term_label": _label_zh(_state_label(short_score)),
        "mid_term_label": _label_zh(_state_label(mid_score)),
        "short_term_state": _state_label(short_score),
        "mid_term_state": _state_label(mid_score),
        "state_transition": transition,
        "short_term_drivers": [f["driver"] for f in short_sorted[:2]],
        "mid_term_drivers": [f["driver"] for f in mid_sorted[:2]],
        "factors": factors,
        "time_series": time_series,
        "contributions": contributions,
        "stress_parameters": derive_stress_parameters(short_score, factors),
        "method_version": METHOD_VERSION,
    }

    evidence_count = len(factors) + 2
    return payload, source_meta, evidence_count


def _dominant_driver(factor_key: str, indicators: Dict[str, Any]) -> str:
    if not indicators:
        return "指标不足"
    first = next(iter(indicators.items()))
    k, v = first
    if isinstance(v, (int, float)):
        return f"{k}={v}"
    return f"{k}"


def derive_stress_parameters(short_score: float, factors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Map a sentiment read into stress-sim parameter hints.

    Consumed by ``analytics.simulation`` to align stress scenarios with the
    real-time risk state. Higher score → lighter stress. Lower score →
    heavier equity shock, wider tails.
    """
    scale = max(0.5, min(2.0, 1.8 - short_score / 80.0))
    return {
        "equity_shock_multiplier": round(float(scale), 3),
        "volatility_scale": round(float(0.8 + (100 - short_score) / 100.0), 3),
        "cross_asset_spillover": round(float(0.3 + (100 - short_score) / 200.0), 3),
        "notes": "sentiment-aware shock multipliers feed stress scenarios",
    }
