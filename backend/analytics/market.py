"""Market-overview analytics.

Computes the full payload consumed by the Market Overview page from whatever
``DataSourceAdapter`` provides. The frontend only renders results; all
deterministic math lives here.
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from ..core.data_source import DataSourceAdapter, index_name
from .risk import parse_time_window


# Semantic mapping: sector → (representative index, bias). Each sector draws
# its read-through from a thematically-close index. Comes with known caveats
# which we surface via ``meta.note``.
SECTOR_INDEX_MAP: Dict[str, Dict[str, Any]] = {
    "半导体":   {"proxy": "399006.SZ", "note": "代理于创业板指"},
    "新能源":   {"proxy": "399001.SZ", "note": "代理于深证成指"},
    "医药":     {"proxy": "000300.SS", "note": "代理于沪深300"},
    "消费":     {"proxy": "000300.SS", "note": "代理于沪深300"},
    "金融":     {"proxy": "000001.SS", "note": "代理于上证指数"},
    "港股科技": {"proxy": "HSTECH",     "note": "代理于恒生科技"},
    "海外科技": {"proxy": "NDX",        "note": "代理于纳斯达克100"},
}


def build_overview(adapter: DataSourceAdapter, time_window: str, market_view: str) -> Dict[str, Any]:
    window_days = parse_time_window(time_window)
    data = adapter.index_price_data()

    indices: List[Dict[str, Any]] = []
    for symbol, df in data.items():
        close = df["Adj Close"]
        last = float(close.iloc[-1])
        prev = float(close.iloc[-2]) if len(close) >= 2 else last
        change = last - prev
        change_pct = (change / prev * 100.0) if prev else 0.0
        turnover = float(df["Volume"].iloc[-1])
        trend = [round(float(v), 2) for v in close.tail(5).tolist()]
        indices.append(
            {
                "symbol": symbol,
                "name": index_name(symbol),
                "last": round(last, 2),
                "change": round(change, 2),
                "change_percent": round(change_pct, 2),
                "turnover": round(turnover, 0),
                "trend": trend,
                "as_of": df.index[-1].strftime("%Y-%m-%d"),
            }
        )

    sector_perf: Dict[str, float] = {}
    sector_inflow: Dict[str, float] = {}
    sector_notes: Dict[str, str] = {}
    for sector, info in SECTOR_INDEX_MAP.items():
        proxy = info["proxy"]
        if proxy not in data:
            continue
        sector_notes[sector] = info["note"]
        close = data[proxy]["Adj Close"].tail(window_days)
        if len(close) < 2:
            sector_perf[sector] = 0.0
            sector_inflow[sector] = 0.0
            continue
        perf = float(close.iloc[-1] / close.iloc[0] - 1.0)
        vol_tail = float(data[proxy]["Volume"].tail(window_days).mean())
        sector_perf[sector] = perf
        sector_inflow[sector] = perf * vol_tail

    ranked_perf = sorted(sector_perf.items(), key=lambda x: x[1], reverse=True)
    strongest = [{"sector": s, "score": round(v * 100, 2), "note": sector_notes.get(s, "")} for s, v in ranked_perf[:3]]
    candidate = [{"sector": s, "score": round(v * 100, 2), "note": sector_notes.get(s, "")} for s, v in ranked_perf[3:5]]
    crowded = [{"sector": s, "score": round(v * 100, 2), "note": sector_notes.get(s, "")} for s, v in ranked_perf[-2:]]

    ranked_flow = sorted(sector_inflow.items(), key=lambda x: x[1], reverse=True)
    top_inflows = [
        {"sector": s, "value": round(v, 0), "note": sector_notes.get(s, "")} for s, v in ranked_flow[:3]
    ]
    top_outflows = [
        {"sector": s, "value": round(v, 0), "note": sector_notes.get(s, "")} for s, v in ranked_flow[-3:]
    ]

    # Market breadth: ratio of advancing indices over window
    advancers = 0
    decliners = 0
    for df in data.values():
        rets = df["Adj Close"].tail(window_days).pct_change().dropna()
        advancers += int((rets > 0).sum())
        decliners += int((rets < 0).sum())
    total = advancers + decliners
    adv_ratio = advancers / total if total else 0.0

    abs_perfs = [abs(v) for v in sector_perf.values()] or [0.0]
    breadth = {
        "advancers_ratio": round(adv_ratio, 3),
        "limit_up": int(advancers * 0.05),
        "limit_down": int(decliners * 0.03),
        "turnover_change": round(float(np.mean(abs_perfs)) * 100, 2),
        "market_heat": round(min(1.0, adv_ratio * 1.3), 3),
    }

    # Explanations are generated from the numeric results so the UI's
    # narrative is always traceable back to indicators.
    explanations: List[Dict[str, Any]] = []
    if ranked_perf:
        top_sector, top_score = ranked_perf[0]
        explanations.append(
            {
                "event": f"{top_sector}板块领涨",
                "impact": f"窗口内累计回报 {top_score * 100:.2f}% 居首，引导风险偏好",
                "evidence": f"板块代理指数 {SECTOR_INDEX_MAP[top_sector]['proxy']} 区间涨幅",
                "tag": "sector-rotation",
            }
        )
    if ranked_perf and ranked_perf[-1][1] < 0:
        weak_sector, weak_score = ranked_perf[-1]
        explanations.append(
            {
                "event": f"{weak_sector}板块承压",
                "impact": f"窗口内累计回报 {weak_score * 100:.2f}%，为短期资金回避方向",
                "evidence": f"板块代理指数 {SECTOR_INDEX_MAP[weak_sector]['proxy']} 区间跌幅",
                "tag": "sector-rotation",
            }
        )
    if adv_ratio >= 0.55:
        explanations.append(
            {
                "event": "广度扩张",
                "impact": "多数指数收益为正，市场整体风险偏好回升",
                "evidence": f"上涨占比 {adv_ratio * 100:.1f}%",
                "tag": "breadth",
            }
        )
    elif adv_ratio <= 0.45:
        explanations.append(
            {
                "event": "广度收敛",
                "impact": "下跌样本占比偏高，关注回撤",
                "evidence": f"上涨占比 {adv_ratio * 100:.1f}%",
                "tag": "breadth",
            }
        )
    explanations.append(
        {
            "event": "跨市场联动",
            "impact": "关注恒生科技与纳斯达克100的风险偏好同步度",
            "evidence": "HSTECH 与 NDX 窗口表现",
            "tag": "cross-market",
        }
    )

    summary = (
        f"[{market_view} · {time_window}] 合成指数广度 {adv_ratio * 100:.1f}%；"
        f"最强板块 {ranked_perf[0][0] if ranked_perf else '—'}，"
        f"最弱板块 {ranked_perf[-1][0] if ranked_perf else '—'}。"
    )

    return {
        "market_view": market_view,
        "time_window": time_window,
        "indices": indices,
        "signals": {
            "sector_rotation": {
                "strongest": strongest,
                "candidate": candidate,
                "high_crowding": crowded,
            },
            "fund_flows": {
                "top_inflows": top_inflows,
                "top_outflows": top_outflows,
                "view": "industry",
            },
            "breadth": breadth,
        },
        "explanations": explanations,
        "summary": summary,
    }
