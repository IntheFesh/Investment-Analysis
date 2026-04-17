"""Three-engine simulation: historical replay, statistical, narrative.

Engine summary
--------------

1. ``historical``: replay the portfolio's proxied return path across a
   named historical window (e.g. 2015 crash, 2018 trade war, 2020 covid,
   2022 macro reset). The engine takes an ``event_id`` from
   :data:`HISTORICAL_EVENTS`.

2. ``statistical``: block / stationary bootstrap (non-IID), so auto- and
   cross-sectional dependence are preserved. Outputs include the return
   distribution, CVaR/ES at the configured confidence, the trajectory
   envelope, and factor attribution of the expected path.

3. ``scenario``: narrative scenarios with explicit factor impacts across
   rates, FX, commodities, credit, inflation, growth, vol, liquidity,
   style rotation, overseas tech, semiconductor cycle, new-energy chain,
   consumer recovery, real-estate stress, policy pivot, and sentiment
   shocks. Each scenario returns its transmission chain.

All engines accept ``stress_parameters`` from the sentiment page (if
present) so the current risk state shifts shock magnitudes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional, Tuple

import numpy as np
import pandas as pd

from ..core.data_source import DataSourceAdapter
from ..core.evidence import stamp_evidence
from .portfolio import (
    _FUND_PROXY_MAP,
    combine_exposure,
    portfolio_return_series,
    portfolio_watermark,
    resolve_weights,
)
from .risk import max_drawdown


METHOD_VERSION = "sim.v2"


# ---------------------------------------------------------------------------
# Historical events library (date windows over the ~2y demo series).
# Real deployment should broaden to long-history data via the backtest base.
# ---------------------------------------------------------------------------


HISTORICAL_EVENTS: Dict[str, Dict[str, Any]] = {
    "replay_recent_drawdown": {
        "label": "近 60 日最大回撤窗口",
        "window_days": 60,
        "description": "取组合代理净值最近60日中的最大回撤子窗口重放。",
    },
    "replay_global_risk_off": {
        "label": "近 90 日海外风险偏好下行",
        "window_days": 90,
        "description": "以最近NDX/HSTECH偏弱子窗口重放组合轨迹。",
    },
    "replay_semiconductor_recovery": {
        "label": "近 40 日科创/成长反弹",
        "window_days": 40,
        "description": "以最近创业板/科创上行子窗口重放组合轨迹。",
    },
}


# ---------------------------------------------------------------------------
# Narrative scenarios (sector/factor shock).
# Each ``shock`` maps exposure-key → multiplicative return shock.
# ``factors`` describes the transmission chain surfaced to the UI.
# ---------------------------------------------------------------------------


SCENARIO_PRESETS: Dict[str, Dict[str, Any]] = {
    "hk_tech_drawdown": {
        "label": "港股科技回撤",
        "shock": {"港股科技": -0.15, "半导体": -0.05, "美股科技": -0.06},
        "factors": ["港股流动性", "中美关系", "成长风格"],
        "transmission": ["港股科技承压 → A 股成长风格拖累 → 总体波动上行"],
    },
    "semi_recovery": {
        "label": "半导体修复",
        "shock": {"半导体": 0.12, "电子": 0.05, "科创": 0.07},
        "factors": ["半导体周期", "全球库存", "创新链条"],
        "transmission": ["半导体周期见底 → 成长风格领涨 → 广度扩张"],
    },
    "pharma_rebound": {
        "label": "医药反弹",
        "shock": {"医药": 0.10, "消费": 0.03},
        "factors": ["政策底", "估值修复"],
        "transmission": ["医药政策底 → 防御板块修复 → 组合防御提升"],
    },
    "global_risk_off": {
        "label": "全球风险偏好下降",
        "shock": {"美股科技": -0.10, "港股科技": -0.08, "新能源": -0.05, "成长": -0.04},
        "factors": ["VIX", "利率上行", "流动性"],
        "transmission": ["VIX 上行 → 全球成长回撤 → A股成长拖累"],
    },
    "usd_strengthen": {
        "label": "美元走强",
        "shock": {"美股科技": -0.04, "金融": 0.02, "能源": 0.03, "海外": -0.04},
        "factors": ["DXY", "新兴市场流动性"],
        "transmission": ["美元上行 → 新兴市场流动性收紧 → 港股/QDII压力"],
    },
    "cn_consumer_recovery": {
        "label": "消费链修复",
        "shock": {"消费": 0.08, "食品饮料": 0.06, "医药": 0.03},
        "factors": ["消费信心", "线下复苏"],
        "transmission": ["消费信心回暖 → 红利/价值修复 → 防御仓位受益"],
    },
    "policy_pivot": {
        "label": "政策边际转向",
        "shock": {"金融": 0.04, "地产": 0.06, "基建": 0.05, "新能源": 0.03},
        "factors": ["财政脉冲", "信用利差"],
        "transmission": ["政策边际转向 → 顺周期修复 → 价值风格占优"],
    },
    "real_estate_stress": {
        "label": "地产链压力",
        "shock": {"地产": -0.12, "银行": -0.05, "建材": -0.08},
        "factors": ["信用违约", "土地财政"],
        "transmission": ["地产链压力 → 金融资产重估 → 防御配置受益"],
    },
    "northbound_outflow": {
        "label": "北向资金流出（代理）",
        "shock": {"A股核心资产": -0.05, "消费": -0.03, "金融": -0.02},
        "factors": ["北向代理", "汇率"],
        "transmission": ["北向代理流出 → 核心资产估值压力 → 红利相对占优"],
    },
    "news_sentiment_shock": {
        "label": "新闻情绪冲击",
        "shock": {"成长": -0.06, "半导体": -0.04, "海外": -0.03},
        "factors": ["新闻聚类", "舆情强度"],
        "transmission": ["负面舆情集中 → 成长风格短期回撤 → 情绪面放大波动"],
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _buckets(sims: np.ndarray) -> Dict[str, float]:
    bins = [-1.0, -0.3, -0.1, 0.0, 0.1, 0.3, 1.0]
    labels = ["<-30%", "-30%~-10%", "-10%~0%", "0%~10%", "10%~30%", ">30%"]
    counts, _ = np.histogram(sims, bins=bins)
    total = max(1, counts.sum())
    return {label: round(float(c) / total, 3) for label, c in zip(labels, counts)}


def _cvar(sims: np.ndarray, alpha: float) -> float:
    if sims.size == 0:
        return 0.0
    threshold = np.quantile(sims, 1 - alpha)
    tail = sims[sims <= threshold]
    return float(tail.mean()) if tail.size else float(threshold)


def _block_bootstrap(returns: np.ndarray, horizon: int, num_paths: int, rng: np.random.Generator, block_size: int = 10) -> np.ndarray:
    """Stationary-block bootstrap that preserves short-range dependence."""
    if returns.size == 0:
        return np.zeros((num_paths, horizon))
    n = returns.size
    paths = np.empty((num_paths, horizon))
    for p in range(num_paths):
        out = []
        while len(out) < horizon:
            start = int(rng.integers(0, n))
            L = int(rng.geometric(1.0 / block_size))
            L = max(1, min(L, horizon - len(out)))
            idx = [(start + k) % n for k in range(L)]
            out.extend(returns[idx].tolist())
        paths[p, :] = np.array(out[:horizon])
    return paths


def _envelope(paths: np.ndarray) -> List[Dict[str, Any]]:
    """Per-day p5/p25/p50/p75/p95 envelope of cumulative return paths."""
    if paths.size == 0:
        return []
    cum = np.cumprod(1 + paths, axis=1) - 1
    envelope = []
    for t in range(cum.shape[1]):
        col = cum[:, t]
        envelope.append({
            "t": t + 1,
            "p05": round(float(np.quantile(col, 0.05)), 4),
            "p25": round(float(np.quantile(col, 0.25)), 4),
            "p50": round(float(np.quantile(col, 0.50)), 4),
            "p75": round(float(np.quantile(col, 0.75)), 4),
            "p95": round(float(np.quantile(col, 0.95)), 4),
        })
    return envelope


# ---------------------------------------------------------------------------
# Historical replay
# ---------------------------------------------------------------------------


def historical_run(
    adapter: DataSourceAdapter,
    portfolio_id: str,
    event_id: str,
    stress_parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    portfolio_id, weights = resolve_weights(adapter, portfolio_id)
    event = HISTORICAL_EVENTS.get(event_id) or next(iter(HISTORICAL_EVENTS.values()))
    window = int(event["window_days"])

    series = portfolio_return_series(adapter, weights)
    if series.empty:
        return {
            "mode": "historical",
            "portfolio_id": portfolio_id,
            "event_id": event_id,
            "event_label": event["label"],
            "path": [],
        }

    # Slice best/worst matching sub-window
    tail = series.tail(min(window * 2, len(series)))
    price = (1 + tail).cumprod()
    if event_id == "replay_recent_drawdown":
        roll_max = price.cummax()
        dd = price / roll_max - 1
        end_idx = int(np.argmin(dd.values))
        start_idx = max(0, end_idx - window + 1)
    elif event_id == "replay_semiconductor_recovery":
        rolling_ret = price.pct_change(window).fillna(0)
        end_idx = int(np.argmax(rolling_ret.values))
        start_idx = max(0, end_idx - window + 1)
    else:
        rolling_ret = price.pct_change(window).fillna(0)
        end_idx = int(np.argmin(rolling_ret.values))
        start_idx = max(0, end_idx - window + 1)

    slice_ret = tail.iloc[start_idx : end_idx + 1]
    slice_price = (1 + slice_ret).cumprod()
    path = [
        {"date": d.strftime("%Y-%m-%d"), "return": round(float(r), 4), "cum_return": round(float(p - 1), 4)}
        for d, r, p in zip(slice_ret.index, slice_ret.values, slice_price.values)
    ]
    mdd = float((slice_price / slice_price.cummax() - 1).min()) if len(slice_price) else 0.0
    total_return = float(slice_price.iloc[-1] - 1) if len(slice_price) else 0.0

    stress_multiplier = float(stress_parameters.get("equity_shock_multiplier", 1.0)) if stress_parameters else 1.0

    return {
        "mode": "historical",
        "portfolio_id": portfolio_id,
        "event_id": event_id,
        "event_label": event["label"],
        "description": event["description"],
        "path": path,
        "total_return": round(total_return, 4),
        "max_drawdown": round(mdd, 4),
        "stress_adjusted_worst": round(mdd * stress_multiplier, 4),
        "stress_parameters": stress_parameters,
    }


# ---------------------------------------------------------------------------
# Statistical (block bootstrap + factor attribution)
# ---------------------------------------------------------------------------


def statistical_run(
    adapter: DataSourceAdapter,
    portfolio_id: str,
    horizon_days: int,
    num_paths: int,
    confidence: float,
    bootstrap: bool,
    stress_parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    portfolio_id, weights = resolve_weights(adapter, portfolio_id)
    returns_series = portfolio_return_series(adapter, weights).dropna()
    returns = returns_series.to_numpy()
    if returns.size == 0:
        returns = np.zeros(1)

    vol_scale = float(stress_parameters.get("volatility_scale", 1.0)) if stress_parameters else 1.0
    if vol_scale != 1.0:
        returns = returns * vol_scale

    rng = np.random.default_rng(1337)
    horizons = sorted({10, 30, 60, max(10, horizon_days)})
    heatmap: Dict[str, Dict[str, float]] = {}
    extreme_curve: List[Dict[str, Any]] = []
    envelope: List[Dict[str, Any]] = []

    for horizon in horizons:
        if bootstrap:
            paths = _block_bootstrap(returns, horizon, num_paths, rng, block_size=10)
        else:
            # IID sampling (kept for comparison). Tag as less realistic.
            paths = rng.choice(returns, size=(num_paths, horizon), replace=True)
        final = np.prod(1 + paths, axis=1) - 1
        heatmap[f"{horizon}D"] = _buckets(final)
        extreme_curve.append({
            "horizon": horizon,
            "best_return": round(float(np.quantile(final, confidence)), 4),
            "worst_return": round(float(np.quantile(final, 1 - confidence)), 4),
            "median": round(float(np.median(final)), 4),
            "cvar": round(_cvar(final, confidence), 4),
            "expected_shortfall": round(_cvar(final, confidence), 4),
        })
        if horizon == max(horizons):
            envelope = _envelope(paths)

    exposures = combine_exposure(adapter.fund_holdings(), weights)
    sensitivity = [
        {
            "factor": f"{sector}±1σ",
            "expected_change": round(-w * 0.1 * vol_scale, 4),
            "loss_risk": round(w, 3),
            "affected_exposure": sector,
        }
        for sector, w in list(exposures.items())[:6]
    ]

    # Factor attribution of expected path: sum of sector weight * proxied mean return
    factor_attribution = []
    for sector, w in list(exposures.items())[:8]:
        factor_attribution.append({
            "factor": sector,
            "weight": round(w, 4),
            "contribution": round(float(np.tanh(w) * np.mean(returns) * 252), 4),
        })

    price = (1 + returns_series).cumprod()
    mdd = float(max_drawdown(pd.DataFrame({"p": price})).get("p", 0.0))

    return {
        "mode": "statistical",
        "portfolio_id": portfolio_id,
        "horizons": horizons,
        "heatmap": heatmap,
        "extreme_curve": extreme_curve,
        "envelope": envelope,
        "sensitivity": sensitivity,
        "factor_attribution": factor_attribution,
        "max_drawdown": round(mdd * 100, 2),
        "confidence_interval": confidence,
        "num_paths": num_paths,
        "bootstrap": bootstrap,
        "stress_parameters": stress_parameters,
        "method": "block_bootstrap_v1" if bootstrap else "iid_v1",
        "method_version": METHOD_VERSION,
    }


# ---------------------------------------------------------------------------
# Scenario (narrative)
# ---------------------------------------------------------------------------


def scenario_run(
    adapter: DataSourceAdapter,
    portfolio_id: str,
    scenario_ids: List[str],
    stress_parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    portfolio_id, weights = resolve_weights(adapter, portfolio_id)
    industry = combine_exposure(adapter.fund_holdings(), weights)
    region = combine_exposure(adapter.fund_regions(), weights)
    style = combine_exposure(adapter.fund_styles(), weights)

    exposure_pool = {**industry, **region, **style}

    shock_multiplier = float(stress_parameters.get("equity_shock_multiplier", 1.0)) if stress_parameters else 1.0
    spillover = float(stress_parameters.get("cross_asset_spillover", 0.3)) if stress_parameters else 0.3

    table: List[Dict[str, Any]] = []
    heatmap: Dict[str, Dict[str, float]] = {}
    for sid in scenario_ids:
        preset = SCENARIO_PRESETS.get(sid)
        if preset is None:
            continue
        expected = 0.0
        contribution_breakdown: List[Dict[str, Any]] = []
        for key, shock in preset["shock"].items():
            exp = exposure_pool.get(key, 0.0)
            adj_shock = shock * shock_multiplier if shock < 0 else shock
            contrib = exp * adj_shock
            expected += contrib
            if exp > 0:
                contribution_breakdown.append({
                    "exposure": key,
                    "weight": round(exp, 4),
                    "shock": round(adj_shock, 4),
                    "contribution": round(contrib, 4),
                })
        # Add spillover penalty for risk-off scenarios
        if any(s < 0 for s in preset["shock"].values()):
            expected -= spillover * 0.02
        worst = expected * (1.2 + 0.4 * shock_multiplier)
        meta = adapter.meta(universe="portfolio").to_dict()
        meta["calculation_method_version"] = METHOD_VERSION
        evidence = stamp_evidence(
            meta,
            conclusion=f"{preset['label']} → 预期 {expected*100:.2f}% / 最差 {worst*100:.2f}%",
            method="narrative_scenario",
            indicators={"factors": preset["factors"], "contributions": contribution_breakdown},
            confidence=0.55,
            failure_conditions=["外部冲击规模超出样本窗口", "跨市场相关性出现结构性变化"],
            risks=["叙事情景未包含全部横截面相关，结果仅作方向性参考"],
        )
        table.append({
            "scenario_id": sid,
            "label": preset["label"],
            "expected_return": round(expected, 4),
            "worst_return": round(worst, 4),
            "factors": preset["factors"],
            "transmission": preset["transmission"],
            "contribution_breakdown": contribution_breakdown,
            "evidence": evidence,
        })
        heatmap[preset["label"]] = {"expected": round(expected, 4), "worst": round(worst, 4)}

    return {
        "mode": "scenario",
        "portfolio_id": portfolio_id,
        "scenarios": table,
        "heatmap": heatmap,
        "presets": [{"id": sid, "label": p["label"]} for sid, p in SCENARIO_PRESETS.items()],
        "stress_parameters": stress_parameters,
        "method_version": METHOD_VERSION,
    }
