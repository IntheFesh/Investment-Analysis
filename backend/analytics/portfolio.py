"""Portfolio analytics (v2).

Multi-dimensional penetration + explainable diagnosis. Integrates:
- User settings (:mod:`backend.core.user_store`) to set the target risk
  profile, drawdown tolerance and liquidity preference.
- Live risk-sentiment (:mod:`backend.analytics.sentiment`) to drive
  environment-fit commentary and adjust suggested rebalancing pressure.

Outputs are bundled with :class:`Evidence` blocks so the frontend panel
can open each recommendation and inspect which primitives drove it.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Mapping, Optional, Tuple

import numpy as np
import pandas as pd

from ..core.data_source import DataSourceAdapter
from ..core.evidence import stamp_evidence
from ..core.user_store import get_user_store, horizon_spec, risk_profile_target
from .risk import annualised_volatility, max_drawdown


METHOD_VERSION = "pf.v2"


DEFAULT_PORTFOLIOS: Dict[str, Dict[str, float]] = {
    "pf_default": {"FUND001": 0.22, "FUND002": 0.22, "FUND003": 0.18, "FUND004": 0.18, "FUND005": 0.10, "FUND006": 0.10},
    "pf_growth":  {"FUND001": 0.30, "FUND004": 0.30, "FUND002": 0.20, "FUND007": 0.10, "FUND005": 0.10},
    "pf_balanced": {"FUND001": 0.12, "FUND002": 0.15, "FUND003": 0.25, "FUND005": 0.25, "FUND006": 0.13, "FUND007": 0.10},
}


# ---------------------------------------------------------------------------
# Weight resolution & watermark
# ---------------------------------------------------------------------------


def resolve_weights(adapter: DataSourceAdapter, portfolio_id: str) -> Tuple[str, Dict[str, float]]:
    if portfolio_id in DEFAULT_PORTFOLIOS:
        return portfolio_id, DEFAULT_PORTFOLIOS[portfolio_id]
    if portfolio_id == "all":
        agg: Dict[str, float] = {}
        for w in DEFAULT_PORTFOLIOS.values():
            for k, v in w.items():
                agg[k] = agg.get(k, 0.0) + v
        total = sum(agg.values()) or 1.0
        return portfolio_id, {k: v / total for k, v in agg.items()}
    funds = list(adapter.fund_holdings().keys())
    return portfolio_id, ({code: 1.0 / len(funds) for code in funds} if funds else {})


def portfolio_watermark(portfolio_id: str, weights: Mapping[str, float]) -> str:
    serial = json.dumps({"id": portfolio_id, "w": sorted(weights.items())}, ensure_ascii=False)
    return hashlib.sha1(serial.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Return series (proxy via index mapping). Honest about being a proxy.
# ---------------------------------------------------------------------------


_FUND_PROXY_MAP: Dict[str, str] = {
    "FUND001": "399006.SZ",
    "FUND002": "000905.SS",
    "FUND003": "000300.SS",
    "FUND004": "000688.SS",
    "FUND005": "000300.SS",
    "FUND006": "HSTECH",
    "FUND007": "NDX",
}


def _fund_return_series(adapter: DataSourceAdapter) -> pd.DataFrame:
    index_data = adapter.index_price_data()
    cols: Dict[str, pd.Series] = {}
    for code in adapter.fund_holdings().keys():
        proxy = _FUND_PROXY_MAP.get(code) or next(iter(index_data.keys()), None)
        if not proxy or proxy not in index_data:
            continue
        cols[code] = index_data[proxy]["Adj Close"].pct_change().fillna(0)
    return pd.DataFrame(cols)


def portfolio_return_series(adapter: DataSourceAdapter, weights: Dict[str, float]) -> pd.Series:
    fund_returns = _fund_return_series(adapter)
    codes = [c for c in weights if c in fund_returns.columns]
    if not codes:
        return pd.Series(dtype=float)
    aligned = fund_returns[codes].fillna(0)
    w = np.array([weights[c] for c in codes])
    return aligned.dot(w).rename("portfolio")


# ---------------------------------------------------------------------------
# Exposure composition
# ---------------------------------------------------------------------------


def combine_exposure(mapping: Dict[str, Dict[str, float]], weights: Dict[str, float]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for code, w in weights.items():
        for key, v in mapping.get(code, {}).items():
            out[key] = out.get(key, 0.0) + v * w
    total = sum(out.values())
    if total:
        out = {k: v / total for k, v in out.items()}
    return dict(sorted(out.items(), key=lambda x: x[1], reverse=True))


def _factor_exposure(style: Dict[str, float], region: Dict[str, float]) -> Dict[str, float]:
    """Lightweight factor mapping: growth/value/quality/defensive/overseas."""
    return {
        "成长": round(style.get("成长", 0.0), 4),
        "价值": round(style.get("价值", 0.0), 4),
        "红利": round(style.get("红利", 0.0), 4),
        "防御": round(style.get("防御", 0.0), 4),
        "海外": round(region.get("海外", 0.0) + region.get("港股", 0.0), 4),
    }


# ---------------------------------------------------------------------------
# Overlap clustering
# ---------------------------------------------------------------------------


def _overlap_clusters(codes: List[str], matrix: List[List[float]], threshold: float = 0.75) -> List[List[str]]:
    n = len(codes)
    visited = [False] * n
    clusters: List[List[str]] = []
    for i in range(n):
        if visited[i]:
            continue
        members = [codes[i]]
        visited[i] = True
        for j in range(i + 1, n):
            if visited[j]:
                continue
            if matrix[i][j] >= threshold:
                members.append(codes[j])
                visited[j] = True
        if len(members) > 1:
            clusters.append(members)
    return clusters


# ---------------------------------------------------------------------------
# Build overview
# ---------------------------------------------------------------------------


def build_overview(adapter: DataSourceAdapter, portfolio_id: str) -> Tuple[Dict[str, Any], Dict[str, Any], int]:
    portfolio_id, weights = resolve_weights(adapter, portfolio_id)
    watermark = portfolio_watermark(portfolio_id, weights)

    meta_fund = adapter.fund_metadata()
    returns = portfolio_return_series(adapter, weights)
    price = (1 + returns).cumprod() if not returns.empty else pd.Series(dtype=float)
    vol = float(annualised_volatility(pd.DataFrame({"r": returns})).iloc[0]) if not returns.empty else 0.0
    mdd = float(max_drawdown(pd.DataFrame({"p": price})).get("p", 0.0)) if not price.empty else 0.0
    ann_ret = float(returns.mean() * 252) if len(returns) else 0.0

    base_capital = 1_000_000.0
    total_assets = base_capital * (1 + ann_ret)

    summary = {
        "total_assets": round(total_assets, 2),
        "total_cost": round(base_capital, 2),
        "profit_loss": round(total_assets - base_capital, 2),
        "return_percent": round(ann_ret * 100, 2),
        "volatility": round(vol * 100, 2),
        "max_drawdown": round(mdd * 100, 2),
        "fund_count": len(weights),
    }

    holdings_view: List[Dict[str, Any]] = []
    for code, w in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        m = meta_fund.get(code, {})
        holdings_view.append({
            "code": code,
            "name": m.get("name", code),
            "type": m.get("type", "—"),
            "region": m.get("region", "—"),
            "weight": round(w * 100, 2),
            "manager": m.get("manager", "—"),
            "proxy_symbol": _FUND_PROXY_MAP.get(code, "—"),
        })

    industry = combine_exposure(adapter.fund_holdings(), weights)
    style = combine_exposure(adapter.fund_styles(), weights)
    region = combine_exposure(adapter.fund_regions(), weights)
    cap = combine_exposure(adapter.fund_caps(), weights)
    factor = _factor_exposure(style, region)

    exposures = {
        "industry": industry,
        "style": style,
        "region": region,
        "cap": cap,
        "factor": factor,
        # legacy "market" bucket retained for existing UI tiles
        "market": {
            "A股": round(region.get("A股", 0.0), 4),
            "港股": round(region.get("港股", 0.0), 4),
            "海外": round(region.get("海外", 0.0), 4),
            "现金/防御": round(region.get("现金", 0.0) + style.get("防御", 0.0) * 0.3, 4),
        },
    }

    fund_returns = _fund_return_series(adapter)
    codes = [c for c in weights if c in fund_returns.columns]
    matrix = fund_returns[codes].corr().round(3).fillna(0).values.tolist() if codes else []
    overlap = {
        "funds": codes,
        "matrix": matrix,
        "clusters": _overlap_clusters(codes, matrix, threshold=0.8),
        "threshold": 0.8,
    }

    user = get_user_store().get()
    target = risk_profile_target(user.profile.get("risk_type", "balanced"))
    target_lo, target_hi = target["target_vol"]

    deviation = 0.0
    if vol > target_hi:
        deviation = vol - target_hi
    elif vol < target_lo:
        deviation = target_lo - vol

    target_profile = {
        "risk_profile_id": target["id"],
        "risk_profile_label": target["label_zh"],
        "recommended_risk_range": [target_lo, target_hi],
        "actual_risk": round(vol, 4),
        "deviation": round(deviation, 4),
        "defensive_target": target["defensive_ratio"],
        "defensive_actual": round(style.get("防御", 0.0) + region.get("现金", 0.0) * 0.5, 4),
    }

    # Simple liquidity / redemption fragility metric: share of illiquid or
    # concentrated buckets - proxy only.
    liquidity_fragility = round(
        0.4 * max(0.0, industry.get(list(industry)[0], 0.0) - 0.35) +
        0.3 * max(0.0, 1 - region.get("A股", 0.0)) +
        0.3 * max(0.0, mdd * -1 - 0.15),
        3,
    ) if industry else 0.0

    payload = {
        "portfolio_id": portfolio_id,
        "watermark": watermark,
        "summary": summary,
        "holdings": holdings_view,
        "exposures": exposures,
        "overlap": overlap,
        "target_deviation": target_profile,
        "liquidity": {
            "fragility_score": liquidity_fragility,
            "note": "代理口径：基金净值未接入实时申赎数据。数值 > 0.3 建议人工复核。",
        },
        "method_version": METHOD_VERSION,
    }

    src = adapter.meta(universe="portfolio").to_dict()
    src["calculation_method_version"] = METHOD_VERSION
    src["evidence_count"] = 3
    return payload, src, 3


# ---------------------------------------------------------------------------
# Diagnosis with settings + sentiment integration
# ---------------------------------------------------------------------------


def build_diagnosis(
    adapter: DataSourceAdapter,
    portfolio_id: str,
    sentiment_snapshot: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any], int]:
    portfolio_id, weights = resolve_weights(adapter, portfolio_id)
    watermark = portfolio_watermark(portfolio_id, weights)

    returns = portfolio_return_series(adapter, weights)
    vol = float(annualised_volatility(pd.DataFrame({"r": returns})).iloc[0]) if not returns.empty else 0.0
    industry = combine_exposure(adapter.fund_holdings(), weights)
    style = combine_exposure(adapter.fund_styles(), weights)
    region = combine_exposure(adapter.fund_regions(), weights)

    user = get_user_store().get()
    profile = user.profile
    target = risk_profile_target(profile.get("risk_type", "balanced"))
    h_spec = horizon_spec(profile.get("investment_horizon", "mid"))
    target_lo, target_hi = target["target_vol"]

    # --- Risk warnings with evidence ---
    warnings: List[Dict[str, Any]] = []
    for sector, w in list(industry.items())[:5]:
        if w > 0.30:
            warnings.append({
                "kind": "concentration",
                "severity": "high",
                "message": f"{sector} 暴露 {w*100:.1f}% 超过 30% 阈值",
                "evidence": stamp_evidence(
                    adapter.meta(universe="portfolio").to_dict(),
                    conclusion=f"{sector} 集中度预警",
                    method="industry_concentration",
                    indicators={"sector": sector, "weight": round(w, 4)},
                    confidence=0.8,
                ),
            })
        elif w > 0.25:
            warnings.append({
                "kind": "watch",
                "severity": "mid",
                "message": f"{sector} 暴露 {w*100:.1f}% 接近警戒",
            })

    if vol > target_hi:
        warnings.append({
            "kind": "volatility",
            "severity": "high",
            "message": f"年化波动 {vol*100:.1f}% 超出 {target['label_zh']} 区间 {target_hi*100:.0f}%",
            "evidence": stamp_evidence(
                adapter.meta(universe="portfolio").to_dict(),
                conclusion="组合波动超出画像",
                method="vol_vs_profile",
                indicators={"actual_vol": round(vol, 4), "target_range": [target_lo, target_hi]},
                confidence=0.85,
                risks=["若风险偏好改善，超出区间的组合可能放大收益；需动态评估"],
            ),
        })
    elif vol < target_lo * 0.7:
        warnings.append({
            "kind": "underexposed",
            "severity": "mid",
            "message": f"年化波动 {vol*100:.1f}% 低于画像下限 {target_lo*100:.0f}%，可能错失上行弹性",
        })
    if not warnings:
        warnings.append({"kind": "ok", "severity": "low", "message": "暂未发现明显结构性风险"})

    # --- Environment fit driven by live sentiment snapshot ---
    short_score = None
    short_state = "neutral"
    if sentiment_snapshot:
        short_score = sentiment_snapshot.get("short_term_score")
        short_state = sentiment_snapshot.get("short_term_state", "neutral")

    tone, env_message = _environment_fit(vol, target, short_score, short_state, profile)

    # --- Attribution (coarse, proxied) ---
    price = (1 + returns).cumprod() if not returns.empty else pd.Series(dtype=float)
    attribution = []
    for code, w in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        fund_ret = _fund_return_series(adapter).get(code)
        if fund_ret is None or fund_ret.empty:
            continue
        contribution = float(fund_ret.mean() * 252 * w)
        attribution.append({
            "code": code,
            "name": adapter.fund_metadata().get(code, {}).get("name", code),
            "weight": round(w, 4),
            "contribution_return": round(contribution, 4),
            "proxy_symbol": _FUND_PROXY_MAP.get(code, "—"),
            "is_proxy": True,
        })

    # --- Minimal adjustment path ---
    adjustments: List[Dict[str, Any]] = []
    if industry and list(industry.values())[0] > 0.30:
        top_sector, top_w = next(iter(industry.items()))
        adjustments.append({
            "action": f"将 {top_sector} 暴露从 {top_w*100:.1f}% 降至 28%",
            "expected_effect": "降低集中度，改善广度参与",
            "preconditions": "替换持仓与现有相关性 < 0.5",
            "side_effects": "短期若该板块强势可能降低相对收益",
            "evidence": stamp_evidence(
                adapter.meta(universe="portfolio").to_dict(),
                conclusion=f"降低 {top_sector} 集中度",
                method="rebalance_concentration",
                indicators={"sector": top_sector, "current": top_w, "target": 0.28},
                confidence=0.75,
            ),
        })
    if vol > target_hi:
        adjustments.append({
            "action": f"将防御/红利仓位提升至 {int(target['defensive_ratio']*100)}%",
            "expected_effect": "压缩年化波动至画像区间内",
            "preconditions": f"配合 {h_spec['label_zh']} 持有目标",
            "side_effects": "牺牲部分上行弹性",
            "evidence": stamp_evidence(
                adapter.meta(universe="portfolio").to_dict(),
                conclusion="提升防御仓位",
                method="defensive_lift",
                indicators={"target_defensive": target["defensive_ratio"], "current_style_defensive": style.get("防御", 0.0)},
                confidence=0.7,
            ),
        })
    if short_state in ("lean_risk_off", "stress") and style.get("成长", 0.0) > 0.45:
        adjustments.append({
            "action": "短期情绪偏弱，减持成长风格 5-8 个百分点",
            "expected_effect": "降低尾部风险暴露",
            "preconditions": "已确认情绪读数为结构性而非单日脉冲",
            "side_effects": "若情绪迅速修复可能踏空",
            "evidence": stamp_evidence(
                adapter.meta(universe="portfolio").to_dict(),
                conclusion="情绪驱动风格再平衡",
                method="sentiment_style_rebalance",
                indicators={"short_state": short_state, "growth_weight": style.get("成长", 0.0)},
                confidence=0.6,
            ),
        })

    payload = {
        "portfolio_id": portfolio_id,
        "watermark": watermark,
        "risk_profile": {
            "risk_type": target["id"],
            "risk_type_label": target["label_zh"],
            "investment_horizon": h_spec["id"],
            "investment_horizon_label": h_spec["label_zh"],
            "target_vol_range": [target_lo, target_hi],
            "drawdown_tolerance": profile.get("drawdown_tolerance", h_spec["drawdown_tolerance"]),
            "liquidity_preference": profile.get("liquidity_preference"),
            "return_expectation": profile.get("return_expectation"),
        },
        "risk_warnings": warnings,
        "environment_fit": {
            "tone": tone,
            "message": env_message,
            "sentiment_short_score": short_score,
            "sentiment_short_state": short_state,
        },
        "attribution": attribution,
        "adjustments": adjustments,
        "optimization": [a["action"] for a in adjustments] or ["当前诊断未发现强制调整项"],
        "evidence": {
            "market_status": "参见 /api/v1/market/overview 的 signals 与 explanations",
            "sector_rotation": "参见 market.signals.sector_rotation.ranked",
            "risk_sentiment": "参见 /api/v1/sentiment/overview 的短期/中期状态",
        },
        "method_version": METHOD_VERSION,
    }

    src = adapter.meta(universe="portfolio").to_dict()
    src["calculation_method_version"] = METHOD_VERSION
    evidence_count = sum(1 for w in warnings if w.get("evidence")) + len(adjustments)
    src["evidence_count"] = evidence_count
    return payload, src, evidence_count


def _environment_fit(
    vol: float,
    target: Dict[str, Any],
    short_score: Optional[float],
    short_state: str,
    profile: Dict[str, Any],
) -> Tuple[str, str]:
    low, high = target["target_vol"]
    label = target["label_zh"]
    parts: List[str] = []
    if vol > high:
        tone = "进攻"
        parts.append(f"组合波动 {vol*100:.1f}% 高于{label}区间（{high*100:.0f}%），偏进攻")
    elif vol < low:
        tone = "防御"
        parts.append(f"组合波动 {vol*100:.1f}% 低于{label}区间（{low*100:.0f}%），偏防御")
    else:
        tone = "均衡"
        parts.append(f"组合波动 {vol*100:.1f}% 处于{label}区间内")

    if short_score is not None:
        parts.append(f"当前短期情绪评分 {short_score:.0f}（{short_state}）")
        if tone == "进攻" and short_state in ("lean_risk_off", "stress"):
            parts.append("情绪偏弱叠加进攻型配置，建议关注回撤控制")
        elif tone == "防御" and short_state in ("risk_on", "lean_risk_on"):
            parts.append("市场偏多而组合偏防御，关注弹性不足风险")
    else:
        parts.append("情绪快照暂不可用，仅基于波动做判断")

    return tone, "；".join(parts) + "。"


# ---------------------------------------------------------------------------
# Export preview consuming settings
# ---------------------------------------------------------------------------


def build_export_preview(
    adapter: DataSourceAdapter,
    portfolio_id: str,
    sentiment_snapshot: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    overview, _, _ = build_overview(adapter, portfolio_id)
    diagnosis, _, _ = build_diagnosis(adapter, portfolio_id, sentiment_snapshot=sentiment_snapshot)

    user = get_user_store().get()
    formats = user.preferences.get("default_export_format", ["JSON", "Markdown"])

    json_content = {"overview": overview, "diagnosis": diagnosis}
    summary = overview["summary"]

    lines = [
        f"# 组合导出预览 · {portfolio_id}",
        f"水位线: {overview['watermark']}",
        "",
        "## 组合摘要",
        f"- 总资产：{summary['total_assets']}",
        f"- 浮动盈亏：{summary['profit_loss']}",
        f"- 年化收益：{summary['return_percent']}%",
        f"- 年化波动：{summary['volatility']}%",
        f"- 最大回撤：{summary['max_drawdown']}%",
        "",
        "## 画像与环境",
        f"- 风险画像：{diagnosis['risk_profile']['risk_type_label']}",
        f"- 持有期：{diagnosis['risk_profile']['investment_horizon_label']}",
        f"- 环境适配：{diagnosis['environment_fit']['message']}",
        "",
        "## 调整建议",
    ]
    for adj in diagnosis["adjustments"] or [{"action": "当前无强制调整"}]:
        lines.append(f"- {adj['action']}")
        if "expected_effect" in adj:
            lines.append(f"  - 预期改善: {adj['expected_effect']}")
        if "preconditions" in adj:
            lines.append(f"  - 适用前提: {adj['preconditions']}")
        if "side_effects" in adj:
            lines.append(f"  - 潜在副作用: {adj['side_effects']}")

    markdown_content = "\n".join(lines)
    csv_rows = ["code,name,weight,type,region"] + [
        f"{h['code']},{h['name']},{h['weight']},{h['type']},{h['region']}" for h in overview["holdings"]
    ]
    csv_content = "\n".join(csv_rows)

    prompt_tone = diagnosis["risk_profile"]["risk_type_label"]
    return {
        "portfolio_id": portfolio_id,
        "watermark": overview["watermark"],
        "configured_formats": formats,
        "formats": {
            "json": json_content,
            "markdown": markdown_content,
            "csv": csv_content,
        },
        "recommendation_prompt": (
            f"你是一名资深组合投资顾问，用户画像为{prompt_tone}。请针对上文数据，"
            f"严格区分事实/推断/证据/风险，给出至少三条可执行建议，并在每条建议"
            f"下方标注：预期改善项、适用前提、潜在副作用。"
        ),
    }
