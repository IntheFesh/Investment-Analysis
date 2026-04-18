"""Symbol master, universe config, industry/region/cap taxonomy.

One source of truth shared by every analytics module so different pages
cannot drift to private dictionaries.

A "universe" is a named bag of tickers + metadata used to scope a view.
Market-view dropdowns (``cn_a``, ``hk``, ``global``) each resolve to a
different bag with different indices, sector baskets and breadth pool.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional


@dataclass(frozen=True)
class SymbolInfo:
    symbol: str
    name: str
    region: str           # "CN" | "HK" | "US" | "GLOBAL"
    asset_class: str      # "equity_index" | "sector_basket" | "currency" | "rate" | "commodity" | "vol"
    cap_tier: Optional[str] = None  # "large" | "mid" | "small" (for index only)
    industry: Optional[str] = None
    license_note: str = "research_only"


SYMBOL_MASTER: Dict[str, SymbolInfo] = {
    # A-share headline indices
    "000001.SS": SymbolInfo("000001.SS", "上证指数", "CN", "equity_index", "large"),
    "399001.SZ": SymbolInfo("399001.SZ", "深证成指", "CN", "equity_index", "large"),
    "399006.SZ": SymbolInfo("399006.SZ", "创业板指", "CN", "equity_index", "mid"),
    "000300.SS": SymbolInfo("000300.SS", "沪深300", "CN", "equity_index", "large"),
    "000852.SS": SymbolInfo("000852.SS", "中证1000", "CN", "equity_index", "small"),
    "000905.SS": SymbolInfo("000905.SS", "中证500", "CN", "equity_index", "mid"),
    "000688.SS": SymbolInfo("000688.SS", "科创50", "CN", "equity_index", "mid"),
    # A-share sector ETFs (used as sector rotation proxies)
    "512480.SS": SymbolInfo("512480.SS", "半导体ETF",   "CN", "sector_basket", industry="半导体"),
    "515030.SS": SymbolInfo("515030.SS", "新能源车ETF", "CN", "sector_basket", industry="新能源"),
    "512170.SS": SymbolInfo("512170.SS", "医疗ETF",     "CN", "sector_basket", industry="医药"),
    "515170.SS": SymbolInfo("515170.SS", "食品饮料ETF", "CN", "sector_basket", industry="消费"),
    "512880.SS": SymbolInfo("512880.SS", "证券ETF",     "CN", "sector_basket", industry="金融"),
    "512660.SS": SymbolInfo("512660.SS", "军工ETF",     "CN", "sector_basket", industry="军工"),
    "512200.SS": SymbolInfo("512200.SS", "地产ETF",     "CN", "sector_basket", industry="地产"),
    # HK
    "HSI":    SymbolInfo("HSI",    "恒生指数",   "HK", "equity_index", "large"),
    "HSTECH": SymbolInfo("HSTECH", "恒生科技",   "HK", "equity_index", "mid", industry="科技"),
    "HSCEI":  SymbolInfo("HSCEI",  "恒生中国企业", "HK", "equity_index", "large"),
    # US indices
    "NDX": SymbolInfo("NDX", "纳斯达克100", "US", "equity_index", "large", industry="科技"),
    "SPX": SymbolInfo("SPX", "标普500",     "US", "equity_index", "large"),
    "DJI": SymbolInfo("DJI", "道琼斯工业",   "US", "equity_index", "large"),
    "RUT": SymbolInfo("RUT", "罗素2000",    "US", "equity_index", "small"),
    # US sector ETFs (SPDR sector family)
    "XLK": SymbolInfo("XLK", "美股科技ETF",   "US", "sector_basket", industry="科技"),
    "XLF": SymbolInfo("XLF", "美股金融ETF",   "US", "sector_basket", industry="金融"),
    "XLE": SymbolInfo("XLE", "美股能源ETF",   "US", "sector_basket", industry="能源"),
    "XLV": SymbolInfo("XLV", "美股医疗ETF",   "US", "sector_basket", industry="医药"),
    "XLY": SymbolInfo("XLY", "美股可选消费ETF", "US", "sector_basket", industry="消费"),
    "XLI": SymbolInfo("XLI", "美股工业ETF",   "US", "sector_basket", industry="工业"),
    # Macro
    "VIX": SymbolInfo("VIX", "标普波动率",   "US", "vol"),
    "DXY": SymbolInfo("DXY", "美元指数",     "GLOBAL", "currency"),
    "US10Y": SymbolInfo("US10Y", "美国10年期国债收益率", "US", "rate"),
    "CN10Y": SymbolInfo("CN10Y", "中国10年期国债收益率", "CN", "rate"),
    "BRENT": SymbolInfo("BRENT", "布伦特原油", "GLOBAL", "commodity"),
    "GOLD":  SymbolInfo("GOLD",  "伦敦金",     "GLOBAL", "commodity"),
    "CNH":   SymbolInfo("CNH",   "离岸人民币",  "CN", "currency"),
}


# ---------------------------------------------------------------------------
# Sector basket proxies. Each entry is: (representative instrument, caveat)
# Caveats are surfaced in evidence panels so the UI shows the proxy truth.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SectorBasket:
    sector: str
    proxy_symbol: str
    is_proxy: bool = True
    caveat: str = ""
    region: str = "CN"


SECTOR_BASKETS_CN: List[SectorBasket] = [
    SectorBasket("半导体",   "512480.SS", True, "以国联安半导体ETF跟踪的半导体产业指数为代理"),
    SectorBasket("新能源",   "515030.SS", True, "以新能源车ETF作为新能源产业代理"),
    SectorBasket("医药",     "512170.SS", True, "以医疗ETF作为医药/医疗服务代理"),
    SectorBasket("消费",     "515170.SS", True, "以食品饮料ETF作为核心消费代理"),
    SectorBasket("金融",     "512880.SS", True, "以证券ETF作为金融行业代理"),
    SectorBasket("军工",     "512660.SS", True, "以军工ETF作为国防军工代理"),
    SectorBasket("地产",     "512200.SS", True, "以地产ETF作为房地产板块代理"),
    SectorBasket("科创",     "000688.SS", True, "以科创50代理硬科技赛道"),
]

SECTOR_BASKETS_HK: List[SectorBasket] = [
    SectorBasket("港股科技", "HSTECH", True, "恒生科技指数代表港股科技龙头", region="HK"),
    SectorBasket("港股蓝筹", "HSI",    True, "恒生指数代表港股蓝筹", region="HK"),
    SectorBasket("中概H股",  "HSCEI",  True, "H股指数代表在港上市中资", region="HK"),
]

SECTOR_BASKETS_US: List[SectorBasket] = [
    SectorBasket("美股科技",     "XLK", True, "SPDR 科技精选 ETF，代表美股科技板块", region="US"),
    SectorBasket("美股金融",     "XLF", True, "SPDR 金融精选 ETF，代表美股金融板块", region="US"),
    SectorBasket("美股能源",     "XLE", True, "SPDR 能源精选 ETF，代表美股能源板块", region="US"),
    SectorBasket("美股医疗",     "XLV", True, "SPDR 医疗精选 ETF，代表美股医疗板块", region="US"),
    SectorBasket("美股可选消费", "XLY", True, "SPDR 可选消费精选 ETF，代表美股可选消费板块", region="US"),
    SectorBasket("美股工业",     "XLI", True, "SPDR 工业精选 ETF，代表美股工业板块", region="US"),
]

# Kept as a backwards-compat alias for imports that still reference the
# old name; points to the new US-focused basket list.
SECTOR_BASKETS_GLOBAL = SECTOR_BASKETS_US


# ---------------------------------------------------------------------------
# Universe configs per market view.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class UniverseConfig:
    id: str
    label: str
    headline_indices: List[str]
    supporting_indices: List[str]
    sector_baskets: List[SectorBasket]
    breadth_pool: List[str]        # indices whose daily returns feed breadth
    cross_asset: List[str] = field(default_factory=list)
    liquidity_proxy_symbols: List[str] = field(default_factory=list)
    region_focus: str = "CN"
    narrative_hint: str = ""


UNIVERSES: Dict[str, UniverseConfig] = {
    "cn_a": UniverseConfig(
        id="cn_a",
        label="A股主视角",
        headline_indices=["000300.SS", "000001.SS", "399006.SZ", "000852.SS"],
        supporting_indices=["000905.SS", "000688.SS", "399001.SZ"],
        sector_baskets=SECTOR_BASKETS_CN,
        breadth_pool=["000300.SS", "000905.SS", "000852.SS", "000688.SS", "399006.SZ", "399001.SZ", "000001.SS"],
        cross_asset=["CN10Y", "CNH"],
        liquidity_proxy_symbols=["000300.SS", "000905.SS"],
        region_focus="CN",
        narrative_hint="以 A 股指数体系为核心，关注行业轮动、广度与流动性代理。",
    ),
    "hk": UniverseConfig(
        id="hk",
        label="港股补充视角",
        headline_indices=["HSI", "HSTECH", "HSCEI"],
        supporting_indices=["NDX", "SPX"],
        sector_baskets=SECTOR_BASKETS_HK,
        breadth_pool=["HSI", "HSTECH", "HSCEI"],
        cross_asset=["CNH", "US10Y"],
        liquidity_proxy_symbols=["HSI", "HSTECH"],
        region_focus="HK",
        narrative_hint="港股视角，广度样本有限，跨市场联动权重更高。",
    ),
    "global": UniverseConfig(
        id="global",
        label="美股视角",
        headline_indices=["SPX", "NDX", "DJI", "RUT"],
        supporting_indices=["XLK", "XLF"],
        sector_baskets=SECTOR_BASKETS_US,
        breadth_pool=["SPX", "NDX", "DJI", "RUT", "XLK", "XLF", "XLE", "XLV"],
        cross_asset=["VIX", "DXY", "US10Y", "BRENT", "GOLD"],
        liquidity_proxy_symbols=["SPX", "NDX"],
        region_focus="US",
        narrative_hint="以标普、纳指、道琼斯、罗素为主轴，结合 SPDR 行业 ETF 观察美股板块轮动与资金偏好。",
    ),
}


def get_universe(market_view: str) -> UniverseConfig:
    return UNIVERSES.get(market_view) or UNIVERSES["cn_a"]


def all_symbols() -> List[str]:
    return list(SYMBOL_MASTER.keys())


def info(symbol: str) -> Optional[SymbolInfo]:
    return SYMBOL_MASTER.get(symbol)


def industry_for(symbol: str) -> Optional[str]:
    i = SYMBOL_MASTER.get(symbol)
    return i.industry if i else None


def region_for(symbol: str) -> str:
    i = SYMBOL_MASTER.get(symbol)
    return i.region if i else "UNKNOWN"


def name_of(symbol: str) -> str:
    i = SYMBOL_MASTER.get(symbol)
    return i.name if i else symbol


def required_symbols_for(view: str) -> List[str]:
    u = get_universe(view)
    seen: List[str] = []
    for s in list(u.headline_indices) + list(u.supporting_indices) + [b.proxy_symbol for b in u.sector_baskets] + list(u.breadth_pool) + list(u.cross_asset):
        if s not in seen:
            seen.append(s)
    return seen


# Backwards-compat alias used by old market.py imports.
INDEX_NAME_MAP: Mapping[str, str] = {k: v.name for k, v in SYMBOL_MASTER.items()}
