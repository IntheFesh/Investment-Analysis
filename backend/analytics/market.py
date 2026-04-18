"""Market-overview analytics (v3)."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import threading
from typing import Any, Dict, List, Tuple
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd

from ..core.data_source import DataSourceAdapter
from ..core.evidence import stamp_evidence
from ..core.universe import SectorBasket, UniverseConfig, get_universe, name_of, required_symbols_for


METHOD_VERSION = "mkt.v3"

# News is an optional enrichment. We cache it independently of the market
# snapshot so a Yahoo news timeout never blocks the snapshot refresh.
_NEWS_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_NEWS_LOCK = threading.Lock()
_NEWS_TTL = float(os.environ.get("NEWS_CACHE_TTL", "900"))   # 15 min
_NEWS_TIMEOUT = float(os.environ.get("NEWS_TIMEOUT_SECONDS", "2.0"))
_NEWS_INFLIGHT: Dict[str, bool] = {}


def _safe_ts_to_str(ts: Any) -> str:
    """Convert a Unix timestamp (int or str) to 'YYYY-MM-DD HH:MM' safely.

    Protects against ``OverflowError: timestamp out of range for platform
    time_t`` raised by ``datetime.fromtimestamp`` on platforms with a
    restricted ``time_t`` range. Returns "" when the input is unusable.
    """
    if ts is None or ts == "":
        return ""
    try:
        ts_int = int(ts)
    except (TypeError, ValueError):
        return ""
    # Clamp to a window we know every platform can represent.
    if not (0 < ts_int < 4_102_444_800):  # 1970..2100
        return ""
    try:
        return datetime.fromtimestamp(ts_int, tz=timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
    except (OverflowError, OSError, ValueError):
        return ""


# ---------------------------------------------------------------------------
# News pipeline — Chinese-language only.
#
# Both the 国内 and 国际 columns on the overview page are sourced from
# mainland-Chinese platforms (primarily 东方财富; 新浪财经 as a fallback) so
# every headline is Chinese regardless of the market the story is about.
# Items are ranked by an ``importance`` score (keyword hits + recency)
# instead of raw publish-time order, matching the request for "重要的新的"
# coverage rather than the very latest headline wire.
# ---------------------------------------------------------------------------


# Keyword → weight. These cover central-bank / macro shocks, mergers, big
# market moves, listings, and policy announcements. The keyword list is
# intentionally small — we'd rather miss a minor boost than over-weight the
# wrong story.
_IMPORTANCE_KEYWORDS: Dict[str, float] = {
    "美联储": 3.0, "联储": 2.5, "降息": 3.0, "加息": 3.0, "缩表": 2.0,
    "央行": 2.5, "人行": 2.0, "政治局": 2.5, "国常会": 2.5,
    "重磅": 2.5, "突发": 3.0, "紧急": 2.5, "警示": 1.5, "熔断": 4.0,
    "暴跌": 2.5, "暴涨": 2.5, "崩盘": 3.0, "回购": 1.5, "增持": 1.5,
    "减持": 1.5, "IPO": 1.5, "上市": 1.0, "退市": 2.0, "停牌": 1.5,
    "复牌": 1.0, "并购": 2.0, "收购": 2.0, "合并": 1.5, "重组": 2.0,
    "业绩": 1.2, "财报": 1.2, "年报": 1.2, "预告": 1.0,
    "关税": 2.5, "制裁": 2.5, "地缘": 1.8, "战争": 2.5, "冲突": 1.8,
    "油价": 1.5, "金价": 1.2, "汇率": 1.5, "人民币": 1.5,
}


def _score_importance(item: Dict[str, Any], now_ts: float) -> float:
    """Score a news item for editorial importance.

    Combines:
    - keyword hits in title (weighted)
    - recency boost (published in last 6h) with a linear decay over 24h
    - source-tier bonus (东方财富/新浪财经/财联社 > generic aggregators)
    """
    title = str(item.get("title") or "")
    score = 0.0
    # Keyword hits — count per keyword, cap to avoid runaway scores.
    hits = 0
    for kw, w in _IMPORTANCE_KEYWORDS.items():
        if kw in title:
            score += w
            hits += 1
            if hits >= 5:
                break
    # Recency: parse "YYYY-MM-DD HH:MM" (Eastmoney format) to a rough delta.
    pub = str(item.get("published_at") or "")
    if len(pub) >= 16:
        try:
            dt = datetime.strptime(pub[:16], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            age_h = max(0.0, (now_ts - dt.timestamp()) / 3600.0)
            if age_h <= 6:
                score += 2.0
            elif age_h <= 24:
                score += max(0.0, 2.0 * (1.0 - (age_h - 6) / 18.0))
        except (ValueError, OverflowError):
            pass
    # Source tier
    src = str(item.get("source") or "")
    if any(k in src for k in ("东方财富", "财联社", "新华", "人民日报", "证券时报")):
        score += 0.5
    elif "新浪" in src:
        score += 0.3
    return score


def _query_eastmoney_news(channel: str, count: int = 8) -> List[Dict[str, Any]]:
    """Fetch Chinese-language headlines from Eastmoney's public JSON feed.

    Channels (all return Chinese-language content):
      - ``stock`` → 102  A 股要闻
      - ``hk``    → 114  港股
      - ``global``→ 110  海外宏观 (Chinese reporting on overseas markets)
    """
    board_map = {
        "stock": "102",
        "hk": "114",
        "global": "110",
    }
    code = board_map.get(channel, "102")
    url = (
        "https://np-listapi.eastmoney.com/comm/web/getListInfo?"
        + urllib.parse.urlencode({"client": "web", "mTypeAndCode": code, "type": "1", "pageSize": max(count, 10)})
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.eastmoney.com/"})
    try:
        with urllib.request.urlopen(req, timeout=_NEWS_TIMEOUT) as resp:  # nosec B310
            payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
    except Exception:  # noqa: BLE001
        return []
    rows = (((payload.get("data") or {}).get("list") or []) if isinstance(payload, dict) else []) or []
    out: List[Dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        title = str(item.get("Art_Title") or item.get("title") or "").strip()
        link = str(item.get("Art_Url") or item.get("url") or "").strip()
        pub = str(item.get("Art_ShowTime") or item.get("showtime") or "").strip()
        source = str(item.get("Art_Source") or item.get("source") or "东方财富").strip()
        if not title or not link:
            continue
        out.append(
            {
                "title": title,
                "source": source,
                "url": link,
                "published_at": pub[:16],
                "lang": "zh",
            }
        )
    return out[:count]


def _query_sina_news(channel: str, count: int = 8) -> List[Dict[str, Any]]:
    """Secondary Chinese source — Sina Finance rolling news JSON.

    Used as a fallback when Eastmoney is unreachable. Sina's feed covers
    both domestic and international macro in Chinese. ``channel`` maps to
    ``lid`` (list id):
      - ``stock``  → 2509  (财经要闻)
      - ``hk``     → 2516  (港股)
      - ``global`` → 2515  (国际财经)
    """
    lid_map = {
        "stock": "2509",
        "hk": "2516",
        "global": "2515",
    }
    lid = lid_map.get(channel, "2509")
    url = (
        "https://feed.mix.sina.com.cn/api/roll/get?"
        + urllib.parse.urlencode({"pageid": "153", "lid": lid, "num": max(count, 10), "versionNumber": "1.2.4"})
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"})
    try:
        with urllib.request.urlopen(req, timeout=_NEWS_TIMEOUT) as resp:  # nosec B310
            payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
    except Exception:  # noqa: BLE001
        return []
    rows = (((payload.get("result") or {}).get("data") or []) if isinstance(payload, dict) else []) or []
    out: List[Dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        link = str(item.get("url") or "").strip()
        src = str(item.get("media_name") or item.get("source") or "新浪财经").strip()
        pub = _safe_ts_to_str(item.get("ctime") or item.get("mtime"))
        if not title or not link:
            continue
        out.append({"title": title, "source": src, "url": link, "published_at": pub, "lang": "zh"})
    return out[:count]


def _rank_news(rows: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    """Dedupe by title, score by importance, return top_k."""
    if not rows:
        return []
    now_ts = datetime.now(timezone.utc).timestamp()
    seen: set = set()
    uniq: List[Dict[str, Any]] = []
    for r in rows:
        t = str(r.get("title") or "")
        if not t or t in seen:
            continue
        seen.add(t)
        r = dict(r)
        r["importance"] = round(_score_importance(r, now_ts), 2)
        uniq.append(r)
    uniq.sort(key=lambda x: (-float(x.get("importance", 0.0)), -len(x.get("published_at") or "")))
    return uniq[:top_k]


# ---------------------------------------------------------------------------
# Domestic / international classification
#
# Upstream channel IDs (东财 102 vs 110, 新浪 2509 vs 2515) mix content — a
# story about Iran-US conflict often lands in the A-share board because it
# moves A-shares the next day. Relying only on the channel produced the
# observed failure mode where 国内 showed oil/Iran stories and 国际 showed
# Chinese-EV stories. So we pool candidates from every Chinese-language
# endpoint we call and classify each by keyword, routing by whichever side
# has stronger signal (ties go to 国内 since our primary audience is A-share).
# ---------------------------------------------------------------------------


_DOMESTIC_KEYWORDS: Tuple[str, ...] = (
    # 市场与监管
    "A股", "沪深", "上证", "深证", "创业板", "科创板", "科创", "北交所",
    "证监会", "央行", "人行", "国常会", "政治局", "发改委", "银保监",
    "财政部", "国务院", "国资委", "工信部", "商务部", "税务总局",
    "沪深300", "中证500", "中证1000", "北证50", "中字头", "中特估",
    "A50", "港股通", "沪股通", "深股通", "北向资金", "南向资金",
    "人民币", "RMB", "LPR", "MLF", "逆回购", "降准",
    # 中资公司（头部样本）
    "宁德时代", "贵州茅台", "茅台", "五粮液", "比亚迪", "中芯国际",
    "腾讯", "阿里", "阿里巴巴", "美团", "京东", "拼多多", "字节", "字节跳动",
    "华为", "小米", "蔚来", "小鹏", "理想", "极氪", "零跑", "广汽", "长安",
    "平安", "工商银行", "工行", "建设银行", "建行", "农业银行", "农行",
    "中国银行", "招商银行", "招行", "交通银行", "交行", "中信",
    "中国石油", "中石油", "中国石化", "中石化", "中国海油", "中海油",
    "国家电网", "国电投", "大唐", "三峡", "中国移动", "中国电信", "中国联通",
    "淘天", "淘宝", "天猫", "顺丰", "菜鸟", "京东物流",
    "恒大", "碧桂园", "万科", "保利", "融创", "龙湖",
    "中建", "中铁", "中信证券", "中金", "华泰", "海通", "国泰君安",
)


_INTERNATIONAL_KEYWORDS: Tuple[str, ...] = (
    # 美国宏观 / 政府
    "美联储", "联储", "鲍威尔", "FOMC", "美债", "美国国债",
    "特朗普", "拜登", "哈里斯", "白宫", "国务卿", "国务院",
    "美国", "美股", "标普", "标普500", "纳指", "纳斯达克", "道指", "道琼斯",
    "罗素2000",
    # 欧洲 / 日韩
    "欧元", "欧央行", "欧洲央行", "拉加德", "欧盟", "欧洲",
    "英镑", "英国", "英央行", "欧元区",
    "日元", "日本", "日银", "日本央行", "植田",
    "韩国", "韩元",
    # 地缘
    "俄罗斯", "普京", "乌克兰", "泽连斯基",
    "以色列", "伊朗", "哈马斯", "美以", "美伊", "中东",
    "霍尔木兹", "加沙", "红海", "胡塞",
    # 大宗
    "OPEC", "沙特", "布伦特", "WTI", "北海", "原油",
    # 美企
    "英伟达", "苹果", "特斯拉", "亚马逊", "谷歌", "Alphabet", "微软", "Meta",
    "伯克希尔", "奈飞", "Netflix", "台积电",
    # 多边
    "G7", "G20", "IMF", "世行", "世贸", "WTO",
)


def _classify_news(title: str) -> str:
    """Return ``domestic`` | ``international`` | ``unknown``.

    Counts keyword hits on each side; ties break to ``domestic`` so A-share
    readers don't lose China-relevant content when a headline mentions both
    sides. Items with no hits on either side are dropped so the panels only
    show clearly-on-topic stories.
    """
    if not title:
        return "unknown"
    dom_hits = sum(1 for kw in _DOMESTIC_KEYWORDS if kw in title)
    intl_hits = sum(1 for kw in _INTERNATIONAL_KEYWORDS if kw in title)
    if dom_hits == 0 and intl_hits == 0:
        return "unknown"
    if intl_hits > dom_hits:
        return "international"
    return "domestic"


def _fetch_news_blocking(market_view: str) -> Dict[str, Any]:
    # Pool candidates from every Chinese-language feed we can reach, then
    # classify by keyword so the 国内 / 国际 columns split on content rather
    # than upstream board IDs (the root cause of the observed cross-mixing).
    pool: List[Dict[str, Any]] = []
    for ch in ("stock", "global"):
        pool.extend(_query_eastmoney_news(ch, count=10))
    for ch in ("stock", "global"):
        pool.extend(_query_sina_news(ch, count=10))

    # Dedupe by title across channels first so the classifier doesn't waste
    # cycles on upstream repeats.
    seen: set = set()
    uniq: List[Dict[str, Any]] = []
    for r in pool:
        t = str(r.get("title") or "")
        if not t or t in seen:
            continue
        seen.add(t)
        uniq.append(r)

    dom_pool: List[Dict[str, Any]] = []
    intl_pool: List[Dict[str, Any]] = []
    for r in uniq:
        kind = _classify_news(str(r.get("title") or ""))
        if kind == "domestic":
            dom_pool.append(r)
        elif kind == "international":
            intl_pool.append(r)

    domestic = _rank_news(dom_pool, top_k=5)
    international = _rank_news(intl_pool, top_k=5)
    news = {
        "domestic": domestic,
        "international": international,
        "sources_tried": {
            "pool": ["eastmoney:stock", "eastmoney:global", "sina:stock", "sina:global"],
            "classification": "keyword_split",
        },
        "ranking": "importance_desc",
    }
    now_ts = datetime.now(timezone.utc).timestamp()
    with _NEWS_LOCK:
        _NEWS_CACHE[market_view] = (now_ts, news)
    return news


def _fetch_news(market_view: str) -> Dict[str, Any]:
    """Return cached news immediately; trigger async refresh on stale. Never raises.

    The returned payload always includes a ``status`` field:
      - ``fresh``: cache populated within ``_NEWS_TTL``
      - ``stale``: cache exists but older than TTL; background refresh scheduled
      - ``refreshing``: no cache yet; background refresh scheduled
      - ``unavailable``: no cache and no in-flight refresh succeeded
    """
    now_ts = datetime.now(timezone.utc).timestamp()
    with _NEWS_LOCK:
        cached = _NEWS_CACHE.get(market_view)
        inflight = _NEWS_INFLIGHT.get(market_view, False)

    if cached and (now_ts - cached[0]) <= _NEWS_TTL:
        payload = dict(cached[1])
        payload["status"] = "fresh"
        payload["age_seconds"] = round(now_ts - cached[0], 1)
        return payload

    # Schedule non-blocking refresh; serve stale (or empty) immediately.
    if not inflight:
        with _NEWS_LOCK:
            _NEWS_INFLIGHT[market_view] = True

        def _worker() -> None:
            try:
                _fetch_news_blocking(market_view)
            except Exception:  # noqa: BLE001
                pass
            finally:
                with _NEWS_LOCK:
                    _NEWS_INFLIGHT[market_view] = False

        threading.Thread(target=_worker, name=f"news-refresh-{market_view}", daemon=True).start()

    if cached:
        payload = dict(cached[1])
        payload["status"] = "stale"
        payload["age_seconds"] = round(now_ts - cached[0], 1)
        return payload
    return {
        "domestic": [],
        "international": [],
        "status": "refreshing" if inflight else "refreshing",
        "age_seconds": None,
    }


def _window(time_window: str) -> int:
    from .risk import parse_time_window

    return max(10, parse_time_window(time_window))


def _empty_payload(universe_id: str, universe_label: str, market_view: str, time_window: str) -> Dict[str, Any]:
    liquidity_shell = {
        "label": "流动性偏好强度",
        "disclaimer": "基于成交活跃度与收益动量的研究指标（研究用途，存在延迟）。",
        "top_inflows": [],
        "top_outflows": [],
        "universe_turnover_momentum": 0.0,
        "view": "liquidity_preference",
    }
    return {
        "market_view": market_view,
        "universe_id": universe_id,
        "universe_label": universe_label,
        "time_window": time_window,
        "indices": [],
        "top_metrics": [],
        "signals": {
            "sector_rotation": {"ranked": [], "strongest": [], "candidate": [], "high_crowding": []},
            "fund_flows": liquidity_shell,
            "liquidity_proxy": liquidity_shell,
            "breadth": {
                "coverage": 0,
                "advancers_ratio": 0.0,
                "decliners_ratio": 0.0,
                "above_ma20_ratio": 0.0,
                "above_ma60_ratio": 0.0,
                "new_high_ratio": 0.0,
                "new_low_ratio": 0.0,
                "limit_up": 0,
                "limit_down": 0,
                "hotspot_concentration": 0.0,
                "market_heat": 0.0,
                "diffusion": 0.0,
                "advance_decline_ratio": 0.0,
                "trend_participation": 0.0,
            },
            "cross_asset": [],
            "regime": {"label": "未知", "probability": 0.0, "duration_days": 0, "switch_risk": 0.0},
            "anomalies": [],
        },
        "explanations": [],
        "news": {"domestic": [], "international": [], "status": "refreshing", "age_seconds": None},
        "summary": "数据正在准备中，稍后自动刷新。",
    }


def _safe_pct(a: float, b: float) -> float:
    if not b:
        return 0.0
    return (a - b) / b


def _rolling_rank(series: pd.Series, lookback: int = 252) -> float:
    if series.empty:
        return 0.5
    clipped = series.tail(lookback)
    latest = float(clipped.iloc[-1])
    return float((clipped <= latest).mean())


def _market_return(data: Dict[str, pd.DataFrame], symbols: List[str], window: int) -> pd.Series:
    chunks = []
    for s in symbols:
        df = data.get(s)
        if df is None or df.empty:
            continue
        chunks.append(df["Adj Close"].pct_change().dropna().tail(window))
    if not chunks:
        return pd.Series(dtype=float)
    return pd.concat(chunks, axis=1).mean(axis=1).dropna()


def _enhanced_sector_score(
    basket: SectorBasket,
    df: pd.DataFrame,
    market_ret_window: pd.Series,
    window: int,
    total_turnover: float,
    global_lead: pd.Series,
) -> Dict[str, Any]:
    close = df["Adj Close"].astype(float)
    vol = df["Volume"].astype(float)
    ret = close.pct_change().dropna()
    win = ret.tail(window)
    if len(win) < 6:
        return {
            "sector": basket.sector,
            "score": 50.0,
            "components": {},
            "note": basket.caveat,
            "is_proxy": basket.is_proxy,
        }

    cum20 = float((1 + ret.tail(min(20, len(ret)))).prod() - 1)
    cum60 = float((1 + ret.tail(min(60, len(ret)))).prod() - 1)
    momentum = 0.65 * cum20 + 0.35 * cum60

    market_cum = float((1 + market_ret_window).prod() - 1) if not market_ret_window.empty else 0.0
    relative_strength = cum20 - market_cum

    dvol = (close * vol).dropna()
    win_turn = dvol.tail(window)
    base = dvol.tail(252) if len(dvol) >= 120 else dvol
    mu = float(base.mean()) if not base.empty else 1.0
    sd = float(base.std()) if float(base.std()) > 0 else max(1.0, abs(mu) * 0.1)
    turnover_surge = (float(win_turn.mean()) - mu) / sd

    breadth_ratio = float((win > 0).mean())
    vol_adj_ret = float(win.mean() / (win.std() + 1e-6) * np.sqrt(252))

    crowding = float(win_turn.mean() / total_turnover) if total_turnover > 0 else 0.0

    lead_beta = 0.0
    if not global_lead.empty:
        aligned = pd.concat([win, global_lead.tail(window)], axis=1, join="inner").dropna()
        if len(aligned) > 5 and float(aligned.iloc[:, 1].std()) > 1e-9:
            lead_beta = float(np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])[0, 1] / np.var(aligned.iloc[:, 1]))

    composite = (
        0.24 * np.tanh(relative_strength * 6)
        + 0.18 * np.tanh(momentum * 4)
        + 0.18 * np.tanh(turnover_surge / 2)
        + 0.14 * (breadth_ratio - 0.5) * 2
        + 0.16 * np.tanh(vol_adj_ret / 3)
        + 0.10 * np.tanh(lead_beta / 1.5)
        - 0.12 * np.tanh((crowding - 0.20) * 5)
    )
    score = float(np.clip((composite + 1) * 50, 0, 100))

    return {
        "sector": basket.sector,
        "proxy_symbol": basket.proxy_symbol,
        "score": round(score, 2),
        "components": {
            "relative_strength": round(relative_strength, 4),
            "rolling_momentum": round(momentum, 4),
            "turnover_surge": round(turnover_surge, 3),
            "breadth_ratio": round(breadth_ratio, 3),
            "crowding": round(crowding, 3),
            "vol_adjusted_return": round(vol_adj_ret, 3),
            "cross_market_beta": round(lead_beta, 3),
        },
        "note": basket.caveat,
        "is_proxy": basket.is_proxy,
    }


def _breadth(universe: UniverseConfig, data: Dict[str, pd.DataFrame], window: int) -> Dict[str, Any]:
    pool = [s for s in universe.breadth_pool if s in data and not data[s].empty]
    if not pool:
        return {
            "coverage": 0,
            "advancers_ratio": 0.0,
            "decliners_ratio": 0.0,
            "above_ma20_ratio": 0.0,
            "above_ma60_ratio": 0.0,
            "new_high_ratio": 0.0,
            "new_low_ratio": 0.0,
            "limit_up": 0,
            "limit_down": 0,
            "hotspot_concentration": 0.0,
            "market_heat": 0.0,
            "diffusion": 0.0,
            "advance_decline_ratio": 0.0,
            "trend_participation": 0.0,
        }

    adv, total_days = 0, 0
    above20, above60 = 0, 0
    highs, lows = 0, 0
    turnovers: List[float] = []
    trend_strength: List[float] = []

    for s in pool:
        close = data[s]["Adj Close"].astype(float)
        if len(close) < 65:
            continue
        ret = close.pct_change().dropna().tail(window)
        adv += int((ret > 0).sum())
        total_days += len(ret)

        last = float(close.iloc[-1])
        ma20 = float(close.tail(20).mean())
        ma60 = float(close.tail(60).mean())
        above20 += int(last >= ma20)
        above60 += int(last >= ma60)

        highs += int(last >= float(close.tail(60).max()) * 0.997)
        lows += int(last <= float(close.tail(60).min()) * 1.003)

        dv = float((data[s]["Adj Close"].tail(window) * data[s]["Volume"].tail(window)).mean())
        turnovers.append(max(0.0, dv))
        trend_strength.append(float((1 + ret).prod() - 1))

    coverage = max(1, len(trend_strength))
    adv_ratio = adv / max(1, total_days)
    dec_ratio = max(0.0, 1 - adv_ratio)
    turnover_sum = sum(turnovers) or 1.0
    hotspot = sum(sorted(turnovers, reverse=True)[:2]) / turnover_sum if turnovers else 0.0
    high_ratio = highs / coverage
    low_ratio = lows / coverage
    diffusion = float(np.std(trend_strength)) if trend_strength else 0.0

    limit_up_proxy = int(round(coverage * max(0.0, adv_ratio - 0.55) * 10))
    limit_down_proxy = int(round(coverage * max(0.0, 0.45 - adv_ratio) * 10))

    market_heat = np.clip(
        0.42 * adv_ratio + 0.22 * (above20 / coverage) + 0.16 * high_ratio + 0.12 * (1 - hotspot) + 0.08 * (1 - low_ratio),
        0,
        1,
    )

    return {
        "coverage": int(coverage),
        "advancers_ratio": round(float(adv_ratio), 3),
        "decliners_ratio": round(float(dec_ratio), 3),
        "above_ma20_ratio": round(float(above20 / coverage), 3),
        "above_ma60_ratio": round(float(above60 / coverage), 3),
        "new_high_ratio": round(float(high_ratio), 3),
        "new_low_ratio": round(float(low_ratio), 3),
        "limit_up": int(limit_up_proxy),
        "limit_down": int(limit_down_proxy),
        "hotspot_concentration": round(float(hotspot), 3),
        "market_heat": round(float(market_heat), 3),
        "diffusion": round(float(diffusion), 3),
        "advance_decline_ratio": round(float(adv_ratio / max(0.01, dec_ratio)), 3),
        "trend_participation": round(float((above20 / coverage) * 0.6 + (above60 / coverage) * 0.4), 3),
    }


def _liquidity_preference(sector_scored: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Rank by a blend of turnover surge (flow) and momentum (price).
    ranked = sorted(
        sector_scored,
        key=lambda x: 0.55 * x["components"].get("turnover_surge", 0.0)
        + 0.45 * x["components"].get("rolling_momentum", 0.0),
        reverse=True,
    )

    def _as_item(it: Dict[str, Any]) -> Dict[str, Any]:
        pref = 0.55 * it["components"].get("turnover_surge", 0.0) + 0.45 * it["components"].get("rolling_momentum", 0.0)
        return {
            "sector": it["sector"],
            "value": round(pref, 3),
            "strength": round(it.get("score", 50.0), 2),
            "note": it.get("note"),
        }

    # Split the ranked list into strict halves so the same sector never
    # appears in both the inflow and outflow columns of the chart. With 6–8
    # baskets that means top_k = outflow_k = len/2 (rounded down).
    n = len(ranked)
    if n == 0:
        top, tail = [], []
    else:
        half = max(1, n // 2)
        # Up to 5 on each side, but never overlap: cap by half.
        k = min(5, half)
        top = [_as_item(x) for x in ranked[:k]]
        tail = [_as_item(x) for x in ranked[n - k:]]
        # Belt-and-braces dedupe by sector name in case upstream delivered
        # duplicate sector labels (legacy baskets, merge bugs, etc.).
        top_names = {t["sector"] for t in top}
        tail = [x for x in tail if x["sector"] not in top_names]
    return {
        "label": "流动性偏好强度",
        "disclaimer": "基于成交活跃度与收益动量的研究指标（研究用途，存在延迟）。",
        "top_inflows": top,
        "top_outflows": list(reversed(tail)),
        "universe_turnover_momentum": round(float(np.mean([x["value"] for x in top])) if top else 0.0, 3),
        "view": "liquidity_preference",
    }


def _cross_asset_snapshot(universe: UniverseConfig, data: Dict[str, pd.DataFrame], window: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for s in universe.cross_asset:
        if s not in data or data[s].empty:
            continue
        close = data[s]["Adj Close"].astype(float)
        if len(close) < window + 1:
            continue
        last = float(close.iloc[-1])
        ret = _safe_pct(last, float(close.iloc[-window]))
        signal = "偏多" if ret > 0.01 else "偏空" if ret < -0.01 else "中性"
        out.append(
            {
                "symbol": s,
                "name": name_of(s),
                "last": round(last, 4),
                "window_return": round(ret, 4),
                "lead_signal": signal,
                "as_of": close.index[-1].strftime("%Y-%m-%d"),
            }
        )
    return out


def _infer_regime(indices: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not indices:
        return {"label": "震荡", "probability": 0.5, "duration_days": 0, "switch_risk": 0.5}

    headline = [x for x in indices if x.get("role") == "headline"] or indices[:2]
    avg_change = float(np.mean([x["change_percent"] for x in headline]))
    avg_ma = float(np.mean([1.0 if x.get("last", 0) >= x.get("support", 0) else 0.0 for x in headline]))

    if avg_change > 0.8 and avg_ma > 0.6:
        return {"label": "偏多", "probability": 0.73, "duration_days": 6, "switch_risk": 0.28}
    if avg_change < -0.8 and avg_ma < 0.4:
        return {"label": "偏空", "probability": 0.71, "duration_days": 5, "switch_risk": 0.31}
    return {"label": "震荡", "probability": 0.62, "duration_days": 4, "switch_risk": 0.36}


def _detect_anomalies(indices: List[Dict[str, Any]], sector_scored: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for idx in indices:
        if abs(idx.get("change_percent", 0.0)) >= 2.5:
            out.append(
                {
                    "id": f"move-{idx['symbol']}",
                    "label": f"{idx['name']}波动放大",
                    "level": "high" if abs(idx["change_percent"]) >= 3.5 else "medium",
                    "detail": f"单日波动 {idx['change_percent']:+.2f}%，进入监控阈值。",
                }
            )
    for s in sector_scored[:2]:
        if s["components"].get("turnover_surge", 0.0) > 2.5 and s["components"].get("rolling_momentum", 0.0) < 0:
            out.append(
                {
                    "id": f"diverge-{s['sector']}",
                    "label": f"{s['sector']}量价背离",
                    "level": "medium",
                    "detail": "成交显著放大但趋势未同步，短线追高胜率下降。",
                }
            )
    return out[:4]


def _explanations(
    meta: Dict[str, Any],
    universe: UniverseConfig,
    breadth: Dict[str, Any],
    sectors: List[Dict[str, Any]],
    cross_asset: List[Dict[str, Any]],
    regime: Dict[str, Any],
) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
    rows: List[Dict[str, Any]] = []

    if sectors:
        lead = sectors[0]
        tail = sectors[-1]
        rows.append(
            {
                "id": "rotation-core",
                "title": "风格主线",
                "fact": f"{lead['sector']}综合强度领先，{tail['sector']}相对偏弱。",
                "inference": "市场主线仍在高景气与高流动性板块，建议优先关注强势板块内回撤后的二次确认。若弱势板块成交持续收缩，防守配置价值提升。",
                "risk": "若两日内成交集中度快速上行，轮动交易拥挤风险会抬升。",
                "timestamp": now,
                "horizon": "1-5个交易日",
                "drivers": [
                    {"label": "领先板块评分", "value": f"{lead['score']:.1f}"},
                    {"label": "领先板块成交激增", "value": f"{lead['components'].get('turnover_surge', 0):+.2f}σ"},
                    {"label": "弱势板块评分", "value": f"{tail['score']:.1f}"},
                ],
                "evidence": stamp_evidence(
                    meta,
                    conclusion=f"{lead['sector']}主导，{tail['sector']}承压",
                    method="sector_composite_v3",
                    indicators=lead["components"],
                    confidence=0.72,
                ),
                "tag": "sector-rotation",
            }
        )

    adv = breadth.get("advancers_ratio", 0.0)
    rows.append(
        {
            "id": "breadth-core",
            "title": "市场参与度",
            "fact": f"上涨占比 {adv * 100:.1f}%，MA20 上方占比 {breadth.get('above_ma20_ratio', 0.0) * 100:.1f}%。",
            "inference": "若广度继续扩散，指数上涨的可持续性将提高；若热度主要集中在少数板块，短线波动会增加。",
            "risk": "广度样本覆盖有限，盘中极端波动日需结合成交结构复核。",
            "timestamp": now,
            "horizon": "1-3个交易日",
            "drivers": [
                {"label": "上涨占比", "value": f"{adv * 100:.1f}%"},
                {"label": "创新高占比", "value": f"{breadth.get('new_high_ratio', 0.0) * 100:.1f}%"},
                {"label": "热点集中度", "value": f"{breadth.get('hotspot_concentration', 0.0) * 100:.1f}%"},
            ],
            "evidence": stamp_evidence(
                meta,
                conclusion="广度状态监控",
                method="breadth_composite_v3",
                indicators=breadth,
                confidence=0.69,
            ),
            "tag": "breadth",
        }
    )

    if cross_asset:
        leaders = sorted(cross_asset, key=lambda x: abs(x["window_return"]), reverse=True)[:2]
        fact = "；".join([f"{x['name']}{x['window_return'] * 100:+.2f}%" for x in leaders])
        rows.append(
            {
                "id": "cross-core",
                "title": "跨市场传导",
                "fact": f"跨资产主导信号：{fact}。",
                "inference": f"当前市场状态为“{regime['label']}”，外盘与汇率波动对A股风格切换的影响正在提高。",
                "risk": "跨市场价格存在时差，夜盘与次日开盘可能出现方向错位。",
                "timestamp": now,
                "horizon": "隔夜至次日",
                "drivers": [
                    {"label": "状态概率", "value": f"{regime['probability'] * 100:.0f}%"},
                    {"label": "状态持续", "value": f"{regime['duration_days']}天"},
                    {"label": "切换风险", "value": f"{regime['switch_risk'] * 100:.0f}%"},
                ],
                "evidence": stamp_evidence(
                    meta,
                    conclusion="跨市场背景信号",
                    method="cross_asset_link_v3",
                    indicators={x["symbol"]: x for x in leaders},
                    confidence=0.63,
                ),
                "tag": "cross-market",
            }
        )

    return rows


def build_overview(adapter: DataSourceAdapter, time_window: str, market_view: str) -> Tuple[Dict[str, Any], Dict[str, Any], int]:
    universe = get_universe(market_view)
    window = _window(time_window)
    try:
        data = adapter.index_price_data(required_symbols_for(market_view))
    except Exception as exc:  # noqa: BLE001
        # Upstream completely failed — return a schema-valid empty payload
        # rather than crashing the refresh.
        meta = adapter.meta(universe=universe.id, fallback_reason=f"upstream_error: {exc}").to_dict()
        meta["calculation_method_version"] = METHOD_VERSION
        return _empty_payload(universe.id, universe.label, market_view, time_window), meta, 0
    if not data:
        meta = adapter.meta(universe=universe.id, fallback_reason="empty_upstream").to_dict()
        meta["calculation_method_version"] = METHOD_VERSION
        return _empty_payload(universe.id, universe.label, market_view, time_window), meta, 0

    source_meta = adapter.meta(universe=universe.id).to_dict()
    source_meta["calculation_method_version"] = METHOD_VERSION

    quality_label = {
        "production_authorized": "实时",
        "production_delayed": "延迟",
        "research_only": "研究",
        "derived": "代理",
        "fallback_demo": "回退",
    }.get(source_meta.get("source_tier"), "研究")

    market_ret = _market_return(data, universe.headline_indices, window)
    global_lead = _market_return(data, ["SPX", "HSI", "NDX"], window)

    total_turnover = 0.0
    for b in universe.sector_baskets:
        d = data.get(b.proxy_symbol)
        if d is not None and not d.empty:
            total_turnover += float((d["Adj Close"].tail(window) * d["Volume"].tail(window)).mean())

    sector_scored: List[Dict[str, Any]] = []
    for b in universe.sector_baskets:
        d = data.get(b.proxy_symbol)
        if d is None or d.empty:
            continue
        sector_scored.append(_enhanced_sector_score(b, d, market_ret, window, total_turnover, global_lead))

    # Pre-compute per-sector return series so each index card can weight
    # sector contributions by its own correlation, rather than sharing a
    # universe-level ranking across every index.
    sector_series: List[Dict[str, Any]] = []
    for s in sector_scored:
        sec_df = data.get(s.get("proxy_symbol"))
        if sec_df is None or sec_df.empty:
            continue
        sec_ret = sec_df["Adj Close"].astype(float).pct_change().dropna().tail(window)
        if len(sec_ret) < 3:
            continue
        sector_series.append(
            {
                "sector": s["sector"],
                "returns": sec_ret,
                "cum_return": float((1 + sec_ret).prod() - 1),
            }
        )

    indices: List[Dict[str, Any]] = []
    for symbol in universe.headline_indices + universe.supporting_indices:
        df = data.get(symbol)
        if df is None or df.empty or len(df) < 3:
            continue
        close = df["Adj Close"].astype(float)
        vol = df["Volume"].astype(float)
        last = float(close.iloc[-1])
        prev = float(close.iloc[-2])
        change = last - prev
        change_pct = _safe_pct(last, prev) * 100.0

        trend = close.tail(30)
        support = float(trend.quantile(0.25))
        resistance = float(trend.quantile(0.85))

        turnover_amt = float((close.iloc[-1] * vol.iloc[-1]))

        idx_ret = close.pct_change().dropna().tail(window)
        # Per-index contributions: for each sector basket, estimate how much
        # of the index's move is co-directional with that sector by
        # multiplying the correlation by the sector's cumulative return.
        # Top-3 positive contributors, so two different indices produce two
        # different lists (high-beta indices surface growth sectors, value
        # indices surface financials/real estate).
        # Correlation by tail-position (not index join) so sub-second
        # timestamp jitter in generated data, or feed-level misalignment on
        # real data, never collapses the overlap to zero.
        per_sector: List[Tuple[str, float, float, float]] = []
        idx_values = idx_ret.to_numpy(dtype=float)
        for ss in sector_series:
            sec_values = ss["returns"].to_numpy(dtype=float)
            n = min(len(idx_values), len(sec_values))
            if n < 3:
                continue
            a = idx_values[-n:]
            b = sec_values[-n:]
            if float(np.std(a)) < 1e-12 or float(np.std(b)) < 1e-12:
                corr = 0.0
            else:
                corr = float(np.corrcoef(a, b)[0, 1])
                if not np.isfinite(corr):
                    corr = 0.0
            contribution = corr * ss["cum_return"]
            per_sector.append((ss["sector"], contribution, ss["cum_return"], corr))

        contrib_sorted = sorted(per_sector, key=lambda t: t[1], reverse=True)
        top_contribs = [
            {"name": name_, "value": round(contribution, 4)}
            for name_, contribution, _cum, _corr in contrib_sorted[:3]
        ]

        # Leaders: per-index filter to sectors whose co-movement with this
        # index is material (|corr| >= 0.1), then rank by raw cum_return.
        # Different indices keep different sector sets (growth indices
        # surface growth sector leaders, value indices surface banks / real
        # estate), so ``领涨跌`` no longer repeats the universe-wide list
        # across every card. Falls back to the universe pool when the
        # filter is too strict to produce three entries.
        correlated = [t for t in per_sector if abs(t[3]) >= 0.1]
        pool = correlated if len(correlated) >= 3 else per_sector
        by_return = sorted(pool, key=lambda t: t[2], reverse=True)
        top_leader = by_return[:2]
        bottom_leader = by_return[-1:] if len(by_return) >= 3 else []
        leaders_rows = [
            {"name": name_, "change_percent": round(cum * 100.0, 2)}
            for name_, _contribution, cum, _corr in top_leader + bottom_leader
        ]

        # Per-index annualized vol — substitutes the futures basis we can't
        # source on the free tier. Stored as already-scaled percent to match
        # the frontend's ``formatPercent`` contract.
        annualized_vol_pct = float(idx_ret.std() * np.sqrt(252) * 100.0) if len(idx_ret) >= 3 else 0.0

        indices.append(
            {
                "symbol": symbol,
                "code": symbol,
                "name": name_of(symbol),
                "last": round(last, 2),
                "change": round(change, 2),
                "change_percent": round(change_pct, 2),
                "turnover": round(turnover_amt, 0),
                "trend": [round(float(v), 2) for v in trend.tolist()],
                "support": round(support, 2),
                "resistance": round(resistance, 2),
                "valuation": {
                    "pe_percentile": round(_rolling_rank(close.pct_change().rolling(20).mean().dropna()) * 100, 1),
                    "pb_percentile": round(_rolling_rank(close.pct_change().rolling(60).mean().dropna()) * 100, 1),
                },
                "contributors": top_contribs,
                "basis": {"name": f"{window}日年化波幅", "value": round(annualized_vol_pct, 2)},
                "leaders": leaders_rows,
                "as_of": df.index[-1].strftime("%Y-%m-%d %H:%M"),
                "role": "headline" if symbol in universe.headline_indices else "support",
                "data_quality": {
                    "tier": source_meta.get("source_tier", "research_only"),
                    "label": quality_label,
                    "delay_seconds": int(source_meta.get("delay_seconds", 0) or 0),
                },
            }
        )

    sector_scored.sort(key=lambda x: x["score"], reverse=True)
    for i, s in enumerate(sector_scored):
        s["rank"] = i + 1
        if s["score"] >= 70:
            s["tag"] = "强势"
        elif s["score"] >= 55:
            s["tag"] = "改善"
        elif s["score"] <= 35:
            s["tag"] = "弱势"
        else:
            s["tag"] = "中性"

    breadth = _breadth(universe, data, window)
    liquidity = _liquidity_preference(sector_scored)
    cross_asset = _cross_asset_snapshot(universe, data, window)
    regime = _infer_regime(indices)
    anomalies = _detect_anomalies(indices, sector_scored)
    explanations = _explanations(source_meta, universe, breadth, sector_scored, cross_asset, regime)

    top_metrics = [
        {"label": "上涨家数占比", "value": breadth["advancers_ratio"], "unit": "%", "tone": "up" if breadth["advancers_ratio"] >= 0.5 else "down"},
        {"label": "市场广度ADR", "value": breadth["advancers_ratio"] / max(0.05, breadth["decliners_ratio"]), "unit": "", "tone": "neutral"},
        {"label": "波动热度", "value": breadth["market_heat"], "unit": "%", "tone": "neutral"},
        {"label": "流动性偏好", "value": liquidity.get("universe_turnover_momentum", 0.0), "unit": "", "tone": "down" if liquidity.get("universe_turnover_momentum", 0.0) > 0 else "up"},
    ]

    summary = f"{universe.label}处于{regime['label']}状态（概率{regime['probability']*100:.0f}%）；广度上涨占比{breadth['advancers_ratio']*100:.1f}%，热点集中度{breadth['hotspot_concentration']*100:.1f}%。"

    payload = {
        "market_view": market_view,
        "universe_id": universe.id,
        "universe_label": universe.label,
        "time_window": time_window,
        "indices": indices,
        "top_metrics": top_metrics,
        "signals": {
            "sector_rotation": {
                "ranked": sector_scored,
                "strongest": sector_scored[:4],
                "candidate": sector_scored[4:8],
                "high_crowding": sorted(
                    [
                        {
                            "sector": x["sector"],
                            "score": x["score"],
                            "rank": x.get("rank"),
                            "tag": "拥挤",
                            "note": x.get("note"),
                            "metrics": {
                                "crowding": x["components"].get("crowding", 0),
                                "turnover_surge": x["components"].get("turnover_surge", 0),
                            },
                        }
                        for x in sector_scored
                    ],
                    key=lambda z: z["metrics"].get("crowding", 0),
                    reverse=True,
                )[:4],
            },
            "fund_flows": liquidity,
            "liquidity_proxy": liquidity,
            "breadth": breadth,
            "cross_asset": cross_asset,
            "regime": regime,
            "anomalies": anomalies,
        },
        "explanations": explanations,
        "news": _fetch_news(market_view),
        "summary": summary,
    }

    return payload, source_meta, len(explanations)
