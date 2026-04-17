"""Portfolio-level analytics.

Encapsulates look-through, diagnosis, export-pack, and fund overlap/correlation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from ..core.data_source import DataSourceAdapter
from .risk import annualised_volatility, max_drawdown


DEFAULT_PORTFOLIOS: Dict[str, Dict[str, float]] = {
    "pf_default": {
        "FUND001": 0.25,
        "FUND002": 0.25,
        "FUND003": 0.20,
        "FUND004": 0.20,
        "FUND005": 0.10,
    },
    "pf_growth": {
        "FUND001": 0.35,
        "FUND004": 0.35,
        "FUND002": 0.20,
        "FUND005": 0.10,
    },
    "pf_balanced": {
        "FUND001": 0.15,
        "FUND002": 0.20,
        "FUND003": 0.25,
        "FUND004": 0.15,
        "FUND005": 0.25,
    },
}


def resolve_weights(adapter: DataSourceAdapter, portfolio_id: str) -> Tuple[str, Dict[str, float]]:
    if portfolio_id in DEFAULT_PORTFOLIOS:
        return portfolio_id, DEFAULT_PORTFOLIOS[portfolio_id]
    if portfolio_id == "all":
        # aggregate of all portfolios
        agg: Dict[str, float] = {}
        for w in DEFAULT_PORTFOLIOS.values():
            for k, v in w.items():
                agg[k] = agg.get(k, 0.0) + v
        total = sum(agg.values()) or 1.0
        return portfolio_id, {k: v / total for k, v in agg.items()}
    # unknown: equal weight across all known funds
    funds = list(adapter.fund_holdings().keys())
    return portfolio_id, {code: 1.0 / len(funds) for code in funds} if funds else (portfolio_id, {})


def _fund_return_series(adapter: DataSourceAdapter) -> pd.DataFrame:
    """Proxy each fund with a deterministic index, return daily returns DataFrame."""
    index_data = adapter.index_price_data()
    symbols = list(index_data.keys())
    fund_codes = list(adapter.fund_holdings().keys())
    cols: Dict[str, pd.Series] = {}
    for i, code in enumerate(fund_codes):
        symbol = symbols[i % len(symbols)]
        cols[code] = index_data[symbol]["Adj Close"].pct_change().fillna(0)
    df = pd.DataFrame(cols)
    return df


def portfolio_return_series(adapter: DataSourceAdapter, weights: Dict[str, float]) -> pd.Series:
    fund_returns = _fund_return_series(adapter)
    codes = [c for c in weights.keys() if c in fund_returns.columns]
    if not codes:
        return pd.Series(dtype=float)
    aligned = fund_returns[codes].fillna(0)
    w = np.array([weights[c] for c in codes])
    return aligned.dot(w).rename("portfolio")


def combine_exposure(mapping: Dict[str, Dict[str, float]], weights: Dict[str, float]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for code, w in weights.items():
        for key, v in mapping.get(code, {}).items():
            out[key] = out.get(key, 0.0) + v * w
    total = sum(out.values())
    if total:
        out = {k: v / total for k, v in out.items()}
    return dict(sorted(out.items(), key=lambda x: x[1], reverse=True))


def build_overview(adapter: DataSourceAdapter, portfolio_id: str) -> Dict[str, Any]:
    portfolio_id, weights = resolve_weights(adapter, portfolio_id)
    meta = adapter.fund_metadata()
    returns = portfolio_return_series(adapter, weights)
    price = (1 + returns).cumprod()
    vol = float(annualised_volatility(pd.DataFrame({"r": returns})).iloc[0]) if not returns.empty else 0.0
    mdd = float(max_drawdown(pd.DataFrame({"r": price})).get("r", 0.0))
    ann_ret = float(returns.mean() * 252) if len(returns) else 0.0
    base = 1_000_000.0
    total_assets = base * (1 + ann_ret)

    summary = {
        "total_assets": round(total_assets, 2),
        "total_cost": round(base, 2),
        "profit_loss": round(total_assets - base, 2),
        "return_percent": round(ann_ret * 100, 2),
        "volatility": round(vol * 100, 2),
        "max_drawdown": round(mdd * 100, 2),
        "fund_count": len(weights),
    }

    holdings_view = []
    for code, w in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        m = meta.get(code, {})
        holdings_view.append(
            {
                "code": code,
                "name": m.get("name", code),
                "type": m.get("type", "—"),
                "weight": round(w * 100, 2),
                "manager": m.get("manager", "—"),
            }
        )

    exposures = {
        "industry": combine_exposure(adapter.fund_holdings(), weights),
        "style": combine_exposure(adapter.fund_styles(), weights),
        "market": _market_exposure(adapter, weights),
    }

    # fund overlap heatmap (correlation of proxied returns) — restricted to
    # funds in this portfolio only so the matrix matches the weights
    fund_returns = _fund_return_series(adapter)
    codes = [c for c in weights.keys() if c in fund_returns.columns]
    corr = fund_returns[codes].corr().round(3).fillna(0).values.tolist() if codes else []
    overlap = {
        "funds": codes,
        "matrix": corr,
    }

    target_profile = {
        "risk_profile": "平衡型",
        "recommended_risk_range": [0.12, 0.22],
        "actual_risk": round(vol, 4),
        "deviation": round(max(0.0, vol - 0.22) if vol > 0.22 else max(0.0, 0.12 - vol), 4),
    }

    return {
        "portfolio_id": portfolio_id,
        "summary": summary,
        "holdings": holdings_view,
        "exposures": exposures,
        "overlap": overlap,
        "target_deviation": target_profile,
    }


def _market_exposure(adapter: DataSourceAdapter, weights: Dict[str, float]) -> Dict[str, float]:
    # Rough mapping from style → market slice so the UI has three exposure charts
    style = combine_exposure(adapter.fund_styles(), weights)
    return {
        "A股成长": round(style.get("成长", 0.0), 4),
        "A股价值": round(style.get("价值", 0.0), 4),
        "A股红利": round(style.get("红利", 0.0), 4),
        "防御/现金": round(style.get("防御", 0.0), 4),
    }


def build_diagnosis(adapter: DataSourceAdapter, portfolio_id: str) -> Dict[str, Any]:
    portfolio_id, weights = resolve_weights(adapter, portfolio_id)
    returns = portfolio_return_series(adapter, weights)
    vol = float(annualised_volatility(pd.DataFrame({"r": returns})).iloc[0]) if not returns.empty else 0.0
    industry = combine_exposure(adapter.fund_holdings(), weights)

    if vol < 0.15:
        risk_type = "稳健型"
    elif vol < 0.22:
        risk_type = "平衡型"
    else:
        risk_type = "进攻型"

    risk_warnings: List[Dict[str, str]] = []
    for sector, w in industry.items():
        if w > 0.30:
            risk_warnings.append({"kind": "concentration", "message": f"{sector} 暴露 {w * 100:.1f}%，超过 30% 阈值"})
        elif w > 0.25:
            risk_warnings.append({"kind": "watch", "message": f"{sector} 暴露 {w * 100:.1f}%，接近集中度警戒"})
    if vol > 0.25:
        risk_warnings.append({"kind": "volatility", "message": f"组合年化波动 {vol * 100:.1f}%，回撤风险偏高"})
    if not risk_warnings:
        risk_warnings.append({"kind": "ok", "message": "暂未发现明显结构性风险"})

    if vol > 0.25:
        environment_fit = {
            "tone": "进攻",
            "message": f"当前市场波动窗口下组合偏进攻（vol {vol * 100:.1f}%），需关注回撤控制。",
        }
    elif vol < 0.15:
        environment_fit = {
            "tone": "防御",
            "message": f"组合波动 {vol * 100:.1f}% 偏低，若市场回暖存在收益弹性不足风险。",
        }
    else:
        environment_fit = {
            "tone": "均衡",
            "message": f"组合波动 {vol * 100:.1f}% 处于平衡区间，适配当前震荡环境。",
        }

    sorted_exp = sorted(industry.items(), key=lambda x: x[1], reverse=True)
    optimization: List[str] = []
    if sorted_exp:
        optimization.append(f"降低 {sorted_exp[0][0]} 暴露，替换为相关性更低的行业")
    optimization.append("适度增加防御型资产（红利/现金）比例，增强回撤控制")
    optimization.append("核查基金重叠矩阵，剔除高相关持仓")

    evidence = {
        "market_status": "广度与板块轮动指标见 /market/overview",
        "sector_rotation": "使用当日板块轮动 strongest/crowded 输出",
        "global_events": "参考 /market/explanations 中 cross-market 标签",
    }

    return {
        "portfolio_id": portfolio_id,
        "risk_profile": {
            "risk_type": risk_type,
            "investment_horizon": "3Y",
        },
        "risk_warnings": risk_warnings,
        "environment_fit": environment_fit,
        "optimization": optimization,
        "evidence": evidence,
    }


def build_export_preview(adapter: DataSourceAdapter, portfolio_id: str) -> Dict[str, Any]:
    overview = build_overview(adapter, portfolio_id)
    diagnosis = build_diagnosis(adapter, portfolio_id)
    json_content = {"overview": overview, "diagnosis": diagnosis}
    summary = overview["summary"]
    lines = [
        f"# 组合导出预览 · {portfolio_id}",
        "",
        "## 组合摘要",
        f"- 总资产：{summary['total_assets']}",
        f"- 浮动盈亏：{summary['profit_loss']}",
        f"- 年化收益：{summary['return_percent']}%",
        f"- 年化波动：{summary['volatility']}%",
        f"- 最大回撤：{summary['max_drawdown']}%",
        "",
        "## 核心诊断",
        f"- 风险类型：{diagnosis['risk_profile']['risk_type']}",
        f"- 环境适配：{diagnosis['environment_fit']['message']}",
        "",
        "## 优化方向",
    ] + [f"- {item}" for item in diagnosis["optimization"]]
    markdown_content = "\n".join(lines)
    csv_rows = ["code,name,weight,type"] + [
        f"{h['code']},{h['name']},{h['weight']},{h['type']}" for h in overview["holdings"]
    ]
    csv_content = "\n".join(csv_rows)
    return {
        "portfolio_id": portfolio_id,
        "formats": {
            "json": json_content,
            "markdown": markdown_content,
            "csv": csv_content,
        },
        "recommendation_prompt": (
            "你是一名资深组合投资顾问。请依据上文数据，拆解该组合当前的核心风险、"
            "环境适配度与优化方向。区分已知事实与推断，给出至少三条可执行建议。"
        ),
    }
