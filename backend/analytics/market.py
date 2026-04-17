"""Market-overview analytics (v2).

Built around :mod:`backend.core.universe`. Every piece of output carries
evidence pointing back to the raw indicator and the data source tier, so
the frontend's EvidencePanel can open any conclusion.

Algorithms
----------

- Sector rotation: composite score = 0.35 · RS + 0.25 · volume-z +
  0.20 · breadth + 0.10 · cross-beta − 0.10 · crowding, where RS is
  relative strength vs the market's composite, volume-z is the z-score of
  sector-basket turnover vs 60d mean, breadth proxies the within-basket
  spread, cross-beta captures sensitivity to global risk-on/off, crowding
  is the sector's share of total universe turnover.

- Liquidity / fund flows: explicitly named ``liquidity_proxy`` because
  the demo tier has no true fund-flow data. Built from the dollar-volume
  momentum of each sector basket relative to the universe's breadth pool.

- Breadth: universe-based. For the configured ``breadth_pool``, we
  compute advance ratio, % above 20/60d MA, new 60d highs, new lows,
  sector-level breadth concentration.

- Today's explanation: four-bucket structure
  ``fact → inference → evidence → risk`` — every tile shows those four
  blocks and an evidence pointer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..core.data_source import DataSourceAdapter
from ..core.evidence import stamp_evidence
from ..core.universe import (
    SectorBasket,
    UniverseConfig,
    get_universe,
    name_of,
    required_symbols_for,
)
from .risk import annualised_volatility


METHOD_VERSION = "mkt.v2"


def _window(time_window: str) -> int:
    from .risk import parse_time_window
    return max(5, parse_time_window(time_window))


def _rank_pct(value: float, series: pd.Series) -> float:
    if series.empty:
        return 0.5
    ranked = float((series < value).mean())
    return ranked


def _rolling_percentile(series: pd.Series, lookback: int = 252) -> float:
    if series.empty:
        return 0.5
    recent = series.tail(lookback)
    latest = series.iloc[-1]
    return float((recent <= latest).mean())


def _sector_score(
    basket: SectorBasket,
    df: pd.DataFrame,
    market_ret_window: pd.Series,
    window: int,
    total_turnover: float,
    cross_asset_returns: Dict[str, pd.Series],
) -> Dict[str, Any]:
    close = df["Adj Close"]
    volume = df["Volume"]
    ret_window = close.pct_change().dropna().tail(window)
    if ret_window.empty:
        return {
            "sector": basket.sector,
            "proxy_symbol": basket.proxy_symbol,
            "score": 0.0,
            "components": {},
            "note": basket.caveat,
        }

    # Relative strength vs market composite
    sector_cum = float((1 + ret_window).prod() - 1)
    market_cum = float((1 + market_ret_window).prod() - 1) if not market_ret_window.empty else 0.0
    rs = sector_cum - market_cum

    # Volume z-score on dollar-turnover
    dollar_turnover = (close.tail(window) * volume.tail(window)).astype(float)
    base = (close.tail(252) * volume.tail(252)).astype(float) if len(close) > 60 else dollar_turnover
    mu = float(base.mean()) if not base.empty else 0.0
    sd = float(base.std()) if not base.empty and float(base.std()) > 0 else 1.0
    vol_z = (float(dollar_turnover.mean()) - mu) / sd

    # Within-basket breadth proxy: fraction of positive days in window
    within_breadth = float((ret_window > 0).mean())

    # Cross-market beta (against global risk-on, proxied by SPX if present)
    cross_beta = 0.0
    spx_ret = cross_asset_returns.get("SPX")
    if spx_ret is not None and not spx_ret.empty:
        aligned = pd.concat([ret_window, spx_ret.tail(window)], axis=1, join="inner").dropna()
        if len(aligned) >= 5 and aligned.iloc[:, 1].std() > 0:
            cov = float(np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])[0, 1])
            var = float(np.var(aligned.iloc[:, 1]))
            cross_beta = cov / var if var else 0.0

    # Crowding: fraction of universe-wide dollar turnover captured by sector
    crowding = 0.0
    if total_turnover > 0:
        crowding = float(dollar_turnover.mean()) / total_turnover

    composite = (
        0.35 * np.tanh(rs * 5)
        + 0.25 * np.tanh(vol_z / 2)
        + 0.20 * (within_breadth - 0.5) * 2
        + 0.10 * np.tanh(cross_beta)
        - 0.10 * np.tanh((crowding - 0.25) * 4)
    )
    # Map to 0-100
    score = float((composite + 1) / 2 * 100)

    return {
        "sector": basket.sector,
        "proxy_symbol": basket.proxy_symbol,
        "score": round(score, 2),
        "components": {
            "relative_strength": round(rs, 4),
            "volume_z": round(vol_z, 3),
            "within_breadth": round(within_breadth, 3),
            "cross_beta": round(cross_beta, 3),
            "crowding": round(crowding, 3),
        },
        "return_window": round(sector_cum * 100, 2),
        "note": basket.caveat,
        "is_proxy": basket.is_proxy,
    }


def _breadth(universe: UniverseConfig, data: Dict[str, pd.DataFrame], window: int) -> Dict[str, Any]:
    pool = [s for s in universe.breadth_pool if s in data]
    if not pool:
        return {
            "coverage": 0,
            "advancers_ratio": 0.0,
            "above_ma20_ratio": 0.0,
            "above_ma60_ratio": 0.0,
            "new_highs_60d": 0,
            "new_lows_60d": 0,
            "hotspot_concentration": 0.0,
        }
    advancers = 0
    total_days = 0
    above_ma20 = 0
    above_ma60 = 0
    new_highs = 0
    new_lows = 0
    for s in pool:
        close = data[s]["Adj Close"]
        if len(close) < 60:
            continue
        rets = close.tail(window).pct_change().dropna()
        advancers += int((rets > 0).sum())
        total_days += len(rets)
        ma20 = close.tail(20).mean()
        ma60 = close.tail(60).mean()
        latest = close.iloc[-1]
        if latest > ma20:
            above_ma20 += 1
        if latest > ma60:
            above_ma60 += 1
        high60 = close.tail(60).max()
        low60 = close.tail(60).min()
        if latest >= high60 * 0.995:
            new_highs += 1
        if latest <= low60 * 1.005:
            new_lows += 1
    total = max(1, len(pool))
    # hotspot concentration: turnover share captured by top-2 pool symbols
    turnovers = []
    for s in pool:
        v = float((data[s]["Adj Close"].tail(window) * data[s]["Volume"].tail(window)).mean())
        turnovers.append(v)
    turnovers.sort(reverse=True)
    denom = sum(turnovers) or 1.0
    top2 = sum(turnovers[:2]) / denom if turnovers else 0.0

    return {
        "coverage": total,
        "advancers_ratio": round(advancers / max(1, total_days), 3),
        "above_ma20_ratio": round(above_ma20 / total, 3),
        "above_ma60_ratio": round(above_ma60 / total, 3),
        "new_highs_60d": int(new_highs),
        "new_lows_60d": int(new_lows),
        "hotspot_concentration": round(float(top2), 3),
    }


def _liquidity_proxy(
    universe: UniverseConfig,
    sector_scored: List[Dict[str, Any]],
    data: Dict[str, pd.DataFrame],
    window: int,
) -> Dict[str, Any]:
    # Ranked by volume-z component — this is a LIQUIDITY PREFERENCE proxy,
    # NOT a fund-flow read. The UI must label it as such.
    ranked = sorted(sector_scored, key=lambda x: x["components"].get("volume_z", 0), reverse=True)
    inflows = [
        {
            "sector": r["sector"],
            "value": r["components"].get("volume_z", 0.0),
            "note": r["note"],
            "is_proxy": True,
        }
        for r in ranked[:3]
    ]
    outflows = [
        {
            "sector": r["sector"],
            "value": r["components"].get("volume_z", 0.0),
            "note": r["note"],
            "is_proxy": True,
        }
        for r in ranked[-3:]
    ]
    # universe-wide turnover momentum
    liq_syms = [s for s in universe.liquidity_proxy_symbols if s in data]
    momentum = []
    for s in liq_syms:
        dv = (data[s]["Adj Close"].tail(window) * data[s]["Volume"].tail(window)).astype(float)
        base = (data[s]["Adj Close"].tail(252) * data[s]["Volume"].tail(252)).astype(float)
        mu = float(base.mean()) or 1.0
        momentum.append(float(dv.mean()) / mu - 1)
    universe_liq = float(np.mean(momentum)) if momentum else 0.0
    return {
        "label": "流动性偏好代理",
        "disclaimer": "非真实资金流数据：基于板块代理指数成交额的 z 分数，仅作方向性参考。",
        "top_inflows": inflows,
        "top_outflows": outflows,
        "universe_turnover_momentum": round(universe_liq, 3),
        "view": "sector_proxy",
    }


def _cross_asset_snapshot(universe: UniverseConfig, data: Dict[str, pd.DataFrame], window: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for s in universe.cross_asset:
        if s not in data:
            continue
        close = data[s]["Adj Close"]
        last = float(close.iloc[-1]) if len(close) else 0.0
        w_ret = float(close.iloc[-1] / close.iloc[-window] - 1) if len(close) > window else 0.0
        percentile = _rolling_percentile(close.tail(252))
        out.append(
            {
                "symbol": s,
                "name": name_of(s),
                "last": round(last, 4),
                "window_return": round(w_ret, 4),
                "52w_percentile": round(percentile, 3),
            }
        )
    return out


def _explanations(
    meta: Dict[str, Any],
    universe: UniverseConfig,
    time_window: str,
    ranked_sectors: List[Dict[str, Any]],
    breadth: Dict[str, Any],
    cross_asset: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    if ranked_sectors:
        top = ranked_sectors[0]
        out.append({
            "id": "top_sector",
            "fact": f"{top['sector']}板块评分 {top['score']:.1f}（{time_window}），在{universe.label}下居首。",
            "inference": "短期相对强度与流动性同时改善，资金偏好明显倾斜该方向。",
            "evidence": stamp_evidence(
                meta,
                conclusion=f"{top['sector']} 领先",
                method="composite_sector_score",
                indicators=top["components"],
                confidence=0.7 if not top.get("is_proxy") else 0.55,
                failure_conditions=[
                    "代理指数与真实行业净值偏离扩大",
                    "总成交额集中度突破 0.45 时信号失真",
                ],
                risks=["若次日大盘转向，首板块反倒可能因拥挤度高而补跌"],
            ),
            "risk": "代理指数口径下的板块强度并非真实行业 ETF 净值；关注后续是否延续。",
            "tag": "sector-rotation",
        })

    if ranked_sectors and ranked_sectors[-1]["score"] < 40:
        weak = ranked_sectors[-1]
        out.append({
            "id": "weak_sector",
            "fact": f"{weak['sector']}板块综合评分 {weak['score']:.1f} 最低。",
            "inference": "资金回避该方向，短期可能继续弱势。",
            "evidence": stamp_evidence(
                meta,
                conclusion=f"{weak['sector']} 承压",
                method="composite_sector_score",
                indicators=weak["components"],
                confidence=0.6,
            ),
            "risk": "若出现超跌反弹，评分排名会短期翻转；仅作方向提示。",
            "tag": "sector-rotation",
        })

    adv = breadth.get("advancers_ratio", 0.0)
    if adv >= 0.55:
        out.append({
            "id": "breadth_up",
            "fact": f"广度样本中 {adv*100:.1f}% 日内上涨。",
            "inference": "参与度扩散，风险偏好改善。",
            "evidence": stamp_evidence(
                meta,
                conclusion="广度扩张",
                method="universe_breadth",
                indicators=breadth,
                confidence=0.65,
            ),
            "risk": "广度样本（{}只指数）仍有限，需配合真实成分股数据验证。".format(breadth.get("coverage", 0)),
            "tag": "breadth",
        })
    elif adv <= 0.45:
        out.append({
            "id": "breadth_down",
            "fact": f"广度样本中仅 {adv*100:.1f}% 日内上涨。",
            "inference": "参与度收敛，赚钱效应下降。",
            "evidence": stamp_evidence(
                meta,
                conclusion="广度收敛",
                method="universe_breadth",
                indicators=breadth,
                confidence=0.65,
            ),
            "risk": "短期超跌可能出现反抽，但结构性修复需广度回升。",
            "tag": "breadth",
        })

    if cross_asset:
        snap = ", ".join(f"{c['name']}窗口 {c['window_return']*100:+.2f}%" for c in cross_asset)
        out.append({
            "id": "cross_asset",
            "fact": f"跨资产读数：{snap}。",
            "inference": "跨资产信号为风险情绪与流动性提供外部背景。",
            "evidence": stamp_evidence(
                meta,
                conclusion="跨资产联动",
                method="cross_asset_snapshot",
                indicators={c["symbol"]: c for c in cross_asset},
                confidence=0.55,
            ),
            "risk": "跨资产代理数据受汇率/利率工具口径影响较大。",
            "tag": "cross-market",
        })

    return out


def build_overview(adapter: DataSourceAdapter, time_window: str, market_view: str) -> Dict[str, Any]:
    universe = get_universe(market_view)
    window = _window(time_window)
    syms = required_symbols_for(market_view)
    data = adapter.index_price_data(syms)

    source_meta = adapter.meta(universe=universe.id).to_dict()
    source_meta["calculation_method_version"] = METHOD_VERSION

    # Headline indices rows
    indices: List[Dict[str, Any]] = []
    for symbol in universe.headline_indices + universe.supporting_indices:
        df = data.get(symbol)
        if df is None or df.empty:
            continue
        close = df["Adj Close"]
        last = float(close.iloc[-1])
        prev = float(close.iloc[-2]) if len(close) >= 2 else last
        change = last - prev
        change_pct = (change / prev * 100.0) if prev else 0.0
        indices.append({
            "symbol": symbol,
            "name": name_of(symbol),
            "last": round(last, 2),
            "change": round(change, 2),
            "change_percent": round(change_pct, 2),
            "turnover": round(float(df["Volume"].iloc[-1]), 0),
            "trend": [round(float(v), 2) for v in close.tail(10).tolist()],
            "as_of": df.index[-1].strftime("%Y-%m-%d"),
            "role": "headline" if symbol in universe.headline_indices else "support",
        })

    # Market composite return series (equal-weighted of headline indices)
    rets_list = []
    for s in universe.headline_indices:
        df = data.get(s)
        if df is not None and not df.empty:
            rets_list.append(df["Adj Close"].pct_change().dropna().tail(window))
    if rets_list:
        market_ret = pd.concat(rets_list, axis=1).mean(axis=1).dropna()
    else:
        market_ret = pd.Series(dtype=float)

    # Cross-asset returns cached for use in sector beta
    cross_asset_returns: Dict[str, pd.Series] = {}
    for s in ("SPX", "NDX", "VIX"):
        df = data.get(s)
        if df is not None:
            cross_asset_returns[s] = df["Adj Close"].pct_change().dropna()

    # Per-sector composite score
    total_turnover = 0.0
    for b in universe.sector_baskets:
        df = data.get(b.proxy_symbol)
        if df is not None:
            total_turnover += float((df["Adj Close"].tail(window) * df["Volume"].tail(window)).mean())

    sector_scored: List[Dict[str, Any]] = []
    for b in universe.sector_baskets:
        df = data.get(b.proxy_symbol)
        if df is None or df.empty:
            continue
        sector_scored.append(_sector_score(b, df, market_ret, window, total_turnover, cross_asset_returns))
    sector_scored.sort(key=lambda x: x["score"], reverse=True)

    strongest = sector_scored[:3]
    candidate = sector_scored[3:5] if len(sector_scored) > 3 else []
    crowded = sorted(sector_scored, key=lambda x: x["components"].get("crowding", 0), reverse=True)[:2]

    breadth = _breadth(universe, data, window)
    liquidity = _liquidity_proxy(universe, sector_scored, data, window)
    cross_asset = _cross_asset_snapshot(universe, data, window)

    explanations = _explanations(source_meta, universe, time_window, sector_scored, breadth, cross_asset)

    evidence_count = len(explanations) + len(sector_scored) + 1

    summary_bits = [
        f"视角：{universe.label}",
        f"广度上涨比 {breadth['advancers_ratio']*100:.1f}%",
        f"MA20 上方 {breadth['above_ma20_ratio']*100:.0f}%",
    ]
    if sector_scored:
        summary_bits.append(f"最强 {sector_scored[0]['sector']}（{sector_scored[0]['score']:.1f}）")
        summary_bits.append(f"最弱 {sector_scored[-1]['sector']}（{sector_scored[-1]['score']:.1f}）")
    if cross_asset:
        hot = max(cross_asset, key=lambda c: abs(c["window_return"]))
        summary_bits.append(f"{hot['name']}{hot['window_return']*100:+.2f}%")

    payload = {
        "market_view": market_view,
        "universe_id": universe.id,
        "universe_label": universe.label,
        "time_window": time_window,
        "indices": indices,
        "signals": {
            "sector_rotation": {
                "ranked": sector_scored,
                "strongest": strongest,
                "candidate": candidate,
                "high_crowding": [
                    {
                        "sector": c["sector"],
                        "score": c["score"],
                        "crowding": c["components"].get("crowding", 0.0),
                        "note": c["note"],
                    }
                    for c in crowded
                ],
                "method": "composite_sector_score",
                "method_version": METHOD_VERSION,
            },
            "liquidity_proxy": liquidity,
            # keep legacy key but with honest label
            "fund_flows": {
                **liquidity,
                "top_inflows": liquidity["top_inflows"],
                "top_outflows": liquidity["top_outflows"],
                "view": "liquidity_proxy",
            },
            "breadth": breadth,
            "cross_asset": cross_asset,
        },
        "explanations": explanations,
        "summary": "；".join(summary_bits),
        "meta_hint": {
            "calculation_method_version": METHOD_VERSION,
            "evidence_count": evidence_count,
        },
    }

    return payload, source_meta, evidence_count
