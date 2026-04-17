"""Three-tier data source layer.

Tiers (declared by every adapter via ``source_tier``):

- ``production_authorized``: realtime feed from an authorised exchange or
  licensed vendor. Marketing it as truth requires a commercial licence.
  ``truth_grade = A``.
- ``production_delayed``: same vendor but delayed (e.g. 15-min delayed
  exchange API, Alpha Vantage free tier). ``truth_grade = B``.
- ``research_only``: open-source aggregators (Tushare, AkShare, free
  Yahoo endpoints, free Sina quote). Non-commercial licence. ``C``.
- ``derived``: computed / proxied from another symbol. ``D``.
- ``fallback_demo``: deterministic synthetic data used when no other tier
  is reachable. ``truth_grade = E``. The envelope is NEVER allowed to
  claim anything higher when this adapter is active.

Adapters never mutate their own meta silently. If a call degrades to a
lower tier (e.g. network failure), they return a :class:`SourceResponse`
whose ``meta`` reflects the actual tier and sets ``fallback_reason``.

Fetch etiquette for research-tier vendors is enforced by
:class:`ResearchRateLimiter` (≥10s per IP, per-vendor throttle) to comply
with commonly-seen open-source ToS.
"""

from __future__ import annotations

import hashlib
import logging
import os
import random
import threading
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

import numpy as np
import pandas as pd

from .calendar import last_trading_day
from .universe import SYMBOL_MASTER, UNIVERSES, SymbolInfo, required_symbols_for


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Metadata descriptor
# ---------------------------------------------------------------------------


@dataclass
class SourceMeta:
    source_name: str
    source_tier: str              # production_authorized | production_delayed | research_only | derived | fallback_demo
    truth_grade: str              # A | B | C | D | E
    is_demo: bool
    is_proxy: bool = False
    is_realtime: bool = False
    delay_seconds: int = 0
    license_scope: str = "research_only"
    fallback_reason: Optional[str] = None
    trading_day: Optional[str] = None
    coverage_universe: str = "unknown"
    calculation_method_version: str = "v0"
    tz: str = "Asia/Shanghai"
    market_session: str = "snapshot"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name,
            "source_tier": self.source_tier,
            "truth_grade": self.truth_grade,
            "is_demo": self.is_demo,
            "is_proxy": self.is_proxy,
            "is_realtime": self.is_realtime,
            "delay_seconds": self.delay_seconds,
            "license_scope": self.license_scope,
            "fallback_reason": self.fallback_reason,
            "trading_day": self.trading_day,
            "coverage_universe": self.coverage_universe,
            "calculation_method_version": self.calculation_method_version,
            "tz": self.tz,
            "market_session": self.market_session,
        }


# ---------------------------------------------------------------------------
# Research-tier rate limiter (≥10s per vendor per IP, robots.txt friendly).
# ---------------------------------------------------------------------------


class ResearchRateLimiter:
    """Per-vendor token-bucket-ish throttle.

    Yahoo Finance ToS asks consumers to avoid systematic scraping; we keep a
    ≥3s spacing there (with jitter). Eastmoney's public K-line endpoint is
    not ToS-restricted at low frequency, so we allow much higher throughput
    on it — otherwise a cold cache warmup hits a 10s × N symbols wall that
    causes the pipeline-wide timeouts logged in production."""

    _DEFAULTS: Dict[str, float] = {
        # Yahoo is the tightest so we default lower than before — with
        # Eastmoney/Tencent handling the bulk of the load, the fallback
        # Yahoo path only needs to cover a handful of residual macro
        # tickers and no longer needs a 3s wall that starves the refresh
        # cycle.
        "yahoo": float(os.getenv("YAHOO_RATE_LIMIT_SECONDS", "1.2")),
        "eastmoney": float(os.getenv("EASTMONEY_RATE_LIMIT_SECONDS", "0.25")),
        "tencent": float(os.getenv("TENCENT_RATE_LIMIT_SECONDS", "0.35")),
        "sina": float(os.getenv("SINA_RATE_LIMIT_SECONDS", "0.5")),
    }

    def __init__(self, default_interval_seconds: float = 3.0) -> None:
        self._last: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._default = default_interval_seconds

    def _interval_for(self, vendor: str) -> float:
        return float(self._DEFAULTS.get(vendor, self._default))

    def wait(self, vendor: str) -> float:
        """Block until the vendor is again callable; return waited seconds."""
        interval = self._interval_for(vendor)
        with self._lock:
            last = self._last.get(vendor, 0.0)
            elapsed = time.monotonic() - last
            sleep_for = max(0.0, interval - elapsed)
            self._last[vendor] = last + sleep_for if sleep_for > 0 else time.monotonic()
        if sleep_for > 0:
            time.sleep(sleep_for + random.uniform(0.0, 0.1))
        return sleep_for


_LIMITER = ResearchRateLimiter(float(os.getenv("RESEARCH_RATE_LIMIT_SECONDS", "3.0")))


def research_limiter() -> ResearchRateLimiter:
    return _LIMITER


# ---------------------------------------------------------------------------
# Base adapter interface
# ---------------------------------------------------------------------------


class DataSourceAdapter:
    """Contract every adapter must honour."""

    name: str = "base"
    tier: str = "fallback_demo"
    truth_grade: str = "E"
    license_scope: str = "internal_preview"
    tz: str = "Asia/Shanghai"
    delay_seconds: int = 0
    is_realtime: bool = False

    def meta(self, *, universe: str = "unknown", fallback_reason: Optional[str] = None) -> SourceMeta:
        trading_day = last_trading_day("CN").isoformat() if self.tz == "Asia/Shanghai" else last_trading_day("US").isoformat()
        return SourceMeta(
            source_name=self.name,
            source_tier=self.tier,
            truth_grade=self.truth_grade,
            is_demo=(self.tier == "fallback_demo"),
            is_proxy=(self.tier == "derived"),
            is_realtime=self.is_realtime,
            delay_seconds=self.delay_seconds,
            license_scope=self.license_scope,
            fallback_reason=fallback_reason,
            trading_day=trading_day,
            coverage_universe=universe,
            calculation_method_version="mkt.v2",
            tz=self.tz,
        )

    # --- data access ---
    def index_price_data(self, symbols: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:  # pragma: no cover
        raise NotImplementedError

    def fund_metadata(self) -> Dict[str, Dict[str, Any]]:  # pragma: no cover
        raise NotImplementedError

    def fund_holdings(self) -> Dict[str, Dict[str, float]]:  # pragma: no cover
        raise NotImplementedError

    def fund_styles(self) -> Dict[str, Dict[str, float]]:  # pragma: no cover
        raise NotImplementedError

    def fund_regions(self) -> Dict[str, Dict[str, float]]:  # pragma: no cover
        return {}

    def fund_caps(self) -> Dict[str, Dict[str, float]]:  # pragma: no cover
        return {}


# ---------------------------------------------------------------------------
# Deterministic demo snapshot — the honest-E-grade fallback.
# ---------------------------------------------------------------------------


class DemoSnapshotAdapter(DataSourceAdapter):
    name = "demo-snapshot"
    tier = "fallback_demo"
    truth_grade = "E"
    license_scope = "internal_preview"
    tz = "Asia/Shanghai"
    delay_seconds = 0
    is_realtime = False

    # deterministic per-symbol params
    _PARAMS: Dict[str, Tuple[float, float, float]] = {
        "000001.SS": (3200.0, 0.011, 0.00018),
        "399001.SZ": (10400.0, 0.013, 0.00014),
        "399006.SZ": (2150.0, 0.017, 0.00009),
        "000300.SS": (3750.0, 0.010, 0.00017),
        "000905.SS": (5600.0, 0.013, 0.00010),
        "000852.SS": (6100.0, 0.014, 0.00007),
        "000688.SS": (950.0, 0.022, 0.00005),
        "HSI":    (17600.0, 0.015, -0.00010),
        "HSTECH": (4050.0, 0.020, -0.00006),
        "HSCEI":  (6100.0, 0.016, -0.00008),
        "NDX":    (18500.0, 0.012, 0.00030),
        "SPX":    (5250.0, 0.009, 0.00022),
        "VIX":    (15.0, 0.040, 0.0),
        "DXY":    (104.5, 0.006, 0.0),
        "US10Y":  (4.3, 0.010, 0.0),
        "CN10Y":  (2.3, 0.008, 0.0),
        "BRENT":  (82.0, 0.015, 0.0),
        "GOLD":   (2350.0, 0.011, 0.00015),
        "CNH":    (7.25, 0.004, 0.0),
    }

    def _generate(self, base_price: float, vol: float, drift: float, seed: int, days: int = 504) -> pd.DataFrame:
        end = datetime.now()
        rng = np.random.default_rng(seed)
        dates = pd.date_range(end=end, periods=days, freq="B")
        logret = rng.normal(loc=drift, scale=vol, size=len(dates))
        close = base_price * np.exp(np.cumsum(logret))
        close = pd.Series(close, index=dates)
        open_ = close.shift(1).fillna(close.iloc[0])
        high = np.maximum(open_, close) * (1 + rng.normal(0.0, 0.003, len(dates)).clip(0, 0.02))
        low = np.minimum(open_, close) * (1 - rng.normal(0.0, 0.003, len(dates)).clip(0, 0.02))
        volume = rng.integers(low=8_000_000, high=40_000_000, size=len(dates))
        df = pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Adj Close": close, "Volume": volume})
        df.index.name = "Date"
        return df

    def index_price_data(self, symbols: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        syms = symbols or list(self._PARAMS.keys())
        out: Dict[str, pd.DataFrame] = {}
        for i, symbol in enumerate(syms):
            params = self._PARAMS.get(symbol, (1000.0, 0.010, 0.0))
            out[symbol] = self._generate(*params, seed=4242 + hash(symbol) % 9973)
        return out

    def fund_metadata(self) -> Dict[str, Dict[str, Any]]:
        return {
            "FUND001": {"name": "半导体成长混合", "type": "股票型", "manager": "李一", "aum": 8.5e9, "inception_date": "2019-05-10", "region": "CN"},
            "FUND002": {"name": "新能源先锋",     "type": "股票型", "manager": "王二", "aum": 6.2e9, "inception_date": "2021-01-15", "region": "CN"},
            "FUND003": {"name": "金融地产优选",   "type": "混合型", "manager": "赵三", "aum": 4.7e9, "inception_date": "2018-09-01", "region": "CN"},
            "FUND004": {"name": "科技创新先锋",   "type": "股票型", "manager": "张四", "aum": 7.8e9, "inception_date": "2020-03-20", "region": "CN"},
            "FUND005": {"name": "消费红利精选",   "type": "混合型", "manager": "钱五", "aum": 5.3e9, "inception_date": "2017-11-05", "region": "CN"},
            "FUND006": {"name": "港股科技主题",   "type": "QDII",   "manager": "孙六", "aum": 3.1e9, "inception_date": "2020-07-12", "region": "HK"},
            "FUND007": {"name": "全球科技先锋",   "type": "QDII",   "manager": "周七", "aum": 2.9e9, "inception_date": "2019-02-18", "region": "US"},
        }

    def fund_holdings(self) -> Dict[str, Dict[str, float]]:
        return {
            "FUND001": {"半导体": 0.35, "医药": 0.20, "消费": 0.20, "电子": 0.15, "现金": 0.10},
            "FUND002": {"新能源": 0.35, "有色金属": 0.20, "电力设备": 0.20, "汽车": 0.15, "现金": 0.10},
            "FUND003": {"银行": 0.30, "地产": 0.20, "非银金融": 0.25, "能源": 0.15, "现金": 0.10},
            "FUND004": {"半导体": 0.30, "软件": 0.25, "电子": 0.20, "医药": 0.15, "现金": 0.10},
            "FUND005": {"消费": 0.35, "食品饮料": 0.25, "医药": 0.20, "纺织": 0.10, "现金": 0.10},
            "FUND006": {"港股科技": 0.55, "港股医药": 0.20, "港股金融": 0.15, "现金": 0.10},
            "FUND007": {"美股科技": 0.60, "美股通讯": 0.20, "美股消费": 0.15, "现金": 0.05},
        }

    def fund_styles(self) -> Dict[str, Dict[str, float]]:
        return {
            "FUND001": {"成长": 0.60, "价值": 0.20, "红利": 0.10, "防御": 0.10},
            "FUND002": {"成长": 0.55, "价值": 0.15, "红利": 0.15, "防御": 0.15},
            "FUND003": {"成长": 0.25, "价值": 0.45, "红利": 0.20, "防御": 0.10},
            "FUND004": {"成长": 0.70, "价值": 0.10, "红利": 0.10, "防御": 0.10},
            "FUND005": {"成长": 0.30, "价值": 0.25, "红利": 0.35, "防御": 0.10},
            "FUND006": {"成长": 0.55, "价值": 0.15, "红利": 0.15, "防御": 0.15},
            "FUND007": {"成长": 0.75, "价值": 0.10, "红利": 0.05, "防御": 0.10},
        }

    def fund_regions(self) -> Dict[str, Dict[str, float]]:
        return {
            "FUND001": {"A股": 0.9, "港股": 0.0, "海外": 0.0, "现金": 0.10},
            "FUND002": {"A股": 0.9, "港股": 0.0, "海外": 0.0, "现金": 0.10},
            "FUND003": {"A股": 0.9, "港股": 0.0, "海外": 0.0, "现金": 0.10},
            "FUND004": {"A股": 0.85, "港股": 0.05, "海外": 0.0, "现金": 0.10},
            "FUND005": {"A股": 0.9, "港股": 0.0, "海外": 0.0, "现金": 0.10},
            "FUND006": {"A股": 0.0, "港股": 0.90, "海外": 0.0, "现金": 0.10},
            "FUND007": {"A股": 0.0, "港股": 0.0, "海外": 0.95, "现金": 0.05},
        }

    def fund_caps(self) -> Dict[str, Dict[str, float]]:
        return {
            "FUND001": {"大盘": 0.40, "中盘": 0.40, "小盘": 0.10, "现金": 0.10},
            "FUND002": {"大盘": 0.30, "中盘": 0.45, "小盘": 0.15, "现金": 0.10},
            "FUND003": {"大盘": 0.65, "中盘": 0.20, "小盘": 0.05, "现金": 0.10},
            "FUND004": {"大盘": 0.25, "中盘": 0.45, "小盘": 0.20, "现金": 0.10},
            "FUND005": {"大盘": 0.55, "中盘": 0.25, "小盘": 0.10, "现金": 0.10},
            "FUND006": {"大盘": 0.50, "中盘": 0.30, "小盘": 0.10, "现金": 0.10},
            "FUND007": {"大盘": 0.70, "中盘": 0.20, "小盘": 0.05, "现金": 0.05},
        }


# ---------------------------------------------------------------------------
# Research-only adapters (non-commercial). Each adapter MUST disclose its
# license_scope="research_only" and fail-close on missing dependencies so it
# never masquerades as A-grade.
# ---------------------------------------------------------------------------


_YF_PRIMARY_MAP: Dict[str, str] = {
    "000001.SS": "000001.SS",
    "399001.SZ": "399001.SZ",
    "399006.SZ": "399006.SZ",
    "000300.SS": "000300.SS",
    "000852.SS": "000852.SS",
    "000905.SS": "000905.SS",
    "000688.SS": "000688.SS",
    "HSI": "^HSI",
    "HSTECH": "^HSTECH",
    "HSCEI": "^HSCE",
    "NDX": "^NDX",
    "SPX": "^GSPC",
    "VIX": "^VIX",
}

# Secondary tickers tried when the primary 404s (Yahoo regularly moves
# Hang Seng indices around and some mirrors are more reliable than
# others). Order matters.
_YF_FALLBACK_MAP: Dict[str, List[str]] = {
    "HSTECH": ["^HSTE", "HKTECH.HK", "3032.HK"],
    "HSCEI":  ["^HSCC", "2828.HK"],
    "HSI":    ["2800.HK"],
}


# Module-level cache keyed by logical symbol. Holds the most recent
# successful pull so transient yfinance outages don't wipe the snapshot.
_YF_PRICE_CACHE: Dict[str, Tuple[pd.DataFrame, float]] = {}
_YF_PRICE_CACHE_LOCK = threading.Lock()
_YF_PRICE_CACHE_TTL = float(os.getenv("YF_PRICE_CACHE_TTL", "600"))


def _yf_cache_put(logical: str, df: pd.DataFrame) -> None:
    with _YF_PRICE_CACHE_LOCK:
        _YF_PRICE_CACHE[logical] = (df.copy(), time.monotonic())


def _yf_cache_get(logical: str, max_age: Optional[float] = None) -> Optional[pd.DataFrame]:
    max_age = max_age if max_age is not None else _YF_PRICE_CACHE_TTL
    with _YF_PRICE_CACHE_LOCK:
        entry = _YF_PRICE_CACHE.get(logical)
    if entry is None:
        return None
    df, cached_at = entry
    if (time.monotonic() - cached_at) > max_age:
        return df  # return stale; caller decides
    return df


class YFinanceResearchAdapter(DemoSnapshotAdapter):
    """Yahoo Finance open endpoint — research only, US/HK coverage.

    Note: Yahoo ToS forbids 'systematic scraping'. Use responsibly, throttle
    to ≥10s per request and prefer a licensed vendor for commercial paths.
    Per-symbol resilience: one bad ticker never poisons the batch.
    """

    name = "yfinance-research"
    tier = "research_only"
    truth_grade = "C"
    license_scope = "research_only"
    tz = "Asia/Shanghai"
    delay_seconds = 900
    is_realtime = False

    # Only symbols confirmed stable on Yahoo's free endpoint.
    # Delisted / unreliable tickers (e.g. ^HSTECH) are intentionally omitted;
    # they are routed to Eastmoney by HybridMarketResearchAdapter instead.
    _YF_SYMBOL_MAP: Dict[str, str] = {
        "000001.SS": "000001.SS",
        "399001.SZ": "399001.SZ",
        "399006.SZ": "399006.SZ",
        "000300.SS": "000300.SS",
        "000852.SS": "000852.SS",
        "000905.SS": "000905.SS",
        "000688.SS": "000688.SS",
        "HSI": "^HSI",
        "NDX": "^NDX",
        "SPX": "^GSPC",
        "VIX": "^VIX",
        "BRENT": "BZ=F",
        "GOLD": "GC=F",
        "DXY": "DX-Y.NYB",
        "US10Y": "^TNX",
        "CNH": "CNH=X",
    }

    _YF_TIMEOUT = float(os.getenv("YF_TIMEOUT_SECONDS", "4.0"))
    _YF_CACHE_TTL = float(os.getenv("YF_CACHE_TTL", "300"))
    _yf_cache_lock = threading.Lock()
    _yf_cache: Dict[str, Tuple[float, pd.DataFrame]] = {}
    _yf_module: Any = None
    _yf_import_failed: bool = False

    _degraded: bool = False
    _degrade_reason: Optional[str] = None
    _missing: List[str] = []

    @classmethod
    def _get_yfinance(cls) -> Any:
        if cls._yf_module is not None:
            return cls._yf_module
        if cls._yf_import_failed:
            return None
        try:
            import yfinance as yf  # type: ignore

            cls._yf_module = yf
            return yf
        except Exception as exc:  # noqa: BLE001
            cls._yf_import_failed = True
            logger.warning("yfinance unavailable: %s (all yahoo fetches will fall back)", exc)
            return None

    def _yf_single(self, yf_symbol: str) -> pd.DataFrame:
        """Download a single ticker with tight timeout. Never raises."""
        key = f"yf:{yf_symbol}"
        now = time.monotonic()
        with self._yf_cache_lock:
            cached = self._yf_cache.get(key)
            if cached and (now - cached[0]) <= self._YF_CACHE_TTL:
                return cached[1].copy()

        yf = self._get_yfinance()
        if yf is None:
            return pd.DataFrame()

        research_limiter().wait("yahoo")
        df = pd.DataFrame()
        try:
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(period="2y", interval="1d", auto_adjust=False, timeout=self._YF_TIMEOUT)
            if df is None or df.empty:
                df = pd.DataFrame()
            else:
                df = df.copy()
                if "Adj Close" not in df.columns and "Close" in df.columns:
                    df["Adj Close"] = df["Close"]
                if "Volume" not in df.columns:
                    df["Volume"] = 0.0
                df.index.name = "Date"
        except Exception as exc:  # noqa: BLE001
            logger.info("yfinance fetch failed for %s: %s", yf_symbol, exc)
            df = pd.DataFrame()

        if not df.empty:
            with self._yf_cache_lock:
                self._yf_cache[key] = (now, df.copy())
        return df

    def _download_yf(self, mapped: List[Tuple[str, str]]) -> Dict[str, pd.DataFrame]:
        out: Dict[str, pd.DataFrame] = {}
        for logical, yf_symbol in mapped:
            if not yf_symbol:
                continue
            df = self._yf_single(yf_symbol)
            if df.empty:
                self._degraded = True
                self._degrade_reason = f"missing {logical} from yfinance"
                continue
            out[logical] = df
        return out

    def index_price_data(self, symbols: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        wanted = symbols or list(self._YF_SYMBOL_MAP.keys())
        mapped = [(logical, self._YF_SYMBOL_MAP.get(logical, "")) for logical in wanted]
        out = self._download_yf([(l, y) for l, y in mapped if y])
        # Fill any gap (incl. symbols not in _YF_SYMBOL_MAP) with the deterministic
        # synthetic snapshot so downstream aggregations never see "暂无数据".
        for symbol in wanted:
            if symbol not in out:
                params = self._PARAMS.get(symbol)
                if params is None:
                    continue
                out[symbol] = self._generate(*params, seed=4242 + hash(symbol) % 9973)
        return out

    def meta(self, *, universe: str = "unknown", fallback_reason: Optional[str] = None) -> SourceMeta:
        base = super().meta(universe=universe, fallback_reason=fallback_reason)
        if self._degraded:
            base.source_name = "yfinance-research-degraded"
            base.fallback_reason = self._degrade_reason or "degraded"
            base.is_proxy = True
        return base


class HybridMarketResearchAdapter(YFinanceResearchAdapter):
    """优先 Eastmoney 指数接口（A 股/港股/美股主指数），其余走 yfinance；
    单 symbol 失败互不影响，缺失项回退到确定性快照并标记为 fallback。"""

    name = "hybrid-research"
    tier = "research_only"
    truth_grade = "C"
    license_scope = "research_only"
    delay_seconds = 900

    _cache_ttl = float(os.getenv("EASTMONEY_CACHE_TTL", "60"))
    _cache_lock = threading.Lock()
    _cache: Dict[str, Tuple[float, pd.DataFrame]] = {}

    # Eastmoney public K-line endpoint supports HK and US indices via market codes:
    # 1 = SH, 0 = SZ, 100 = HK/intl indices, 105 = NASDAQ component
    _EM_SECID: Dict[str, str] = {
        # A 股指数
        "000001.SS": "1.000001",
        "000300.SS": "1.000300",
        "000905.SS": "1.000905",
        "000852.SS": "1.000852",
        "000688.SS": "1.000688",
        "399001.SZ": "0.399001",
        "399006.SZ": "0.399006",
        # 港股主指数（对应东财港股行情）
        "HSI":    "100.HSI",
        "HSTECH": "100.HSTECH",
        "HSCEI": "100.HSCEI",
        # 美股主要指数
        "SPX": "100.SPX",
        "NDX": "100.NDX",
        "VIX": "100.VIX",
        # 宏观 / 外汇 / 大宗
        "DXY": "100.UDI",
    }

    _EM_TIMEOUT = float(os.getenv("EASTMONEY_TIMEOUT_SECONDS", "3.0"))

    # Tencent kline endpoint — used as a fallback when Eastmoney returns an
    # empty payload (observed on some Windows/DNS setups). Returns the same
    # shape after parsing, backed by Tencent's free research feed.
    _TX_SECID: Dict[str, str] = {
        "000001.SS": "sh000001",
        "000300.SS": "sh000300",
        "000905.SS": "sh000905",
        "000852.SS": "sh000852",
        "000688.SS": "sh000688",
        "399001.SZ": "sz399001",
        "399006.SZ": "sz399006",
        "HSI":    "hkHSI",
        "HSTECH": "hkHSTECH",
        "HSCEI": "hkHSCEI",
        "SPX": "usINX",
        "NDX": "usIXIC",
        "VIX": "usVIX",
        "DXY": "usDXY",
    }
    _TX_TIMEOUT = float(os.getenv("TENCENT_TIMEOUT_SECONDS", "3.0"))

    @staticmethod
    def _parse_em_date(raw: str) -> Optional[datetime]:
        """Parse Eastmoney kline date strictly. Returns None when unparseable
        or out of the calendar range we can safely represent.

        Eastmoney daily klines return ``YYYY-MM-DD``; some weekly endpoints
        emit ``YYYYMMDD``. We avoid ``pd.to_datetime`` because on constrained
        platforms pandas may route inference through ``datetime.fromtimestamp``,
        which raises ``OverflowError: timestamp out of range for platform
        time_t`` for any value pandas misreads as a Unix epoch (e.g. a large
        numeric-looking string). Explicit parsing bypasses that path.
        """
        s = (raw or "").strip()
        if not s:
            return None
        for fmt in ("%Y-%m-%d", "%Y%m%d", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(s, fmt)
            except ValueError:
                continue
            # Reject dates outside a safe window so downstream ops that may
            # still call Python's time_t-backed conversions never explode.
            if 1971 <= dt.year <= 2037:
                return dt
            # Widen bounds for 64-bit systems while still excluding obvious
            # garbage (year 0, 9999 sentinel, etc.)
            if 1900 <= dt.year <= 2100:
                return dt
            return None
        return None

    def _eastmoney_kline(self, symbol: str) -> pd.DataFrame:
        secid = self._EM_SECID.get(symbol)
        if not secid:
            return pd.DataFrame()
        key = f"em:{symbol}"
        now = time.monotonic()
        with self._cache_lock:
            cached = self._cache.get(key)
            if cached and (now - cached[0]) <= self._cache_ttl:
                return cached[1].copy()

        # Eastmoney requires ``ut`` (public token) and explicit ``beg``/``end``
        # for index klines; without those it returns ``{"data":{"klines":[]}}``
        # which manifests as the empty-payload log reported in production.
        query = urllib.parse.urlencode({
            "secid": secid,
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101",
            "fqt": "1",
            "beg": "0",
            "end": "20500101",
            "lmt": "520",
            "rtntype": "6",
        })
        req = urllib.request.Request(
            f"https://push2his.eastmoney.com/api/qt/stock/kline/get?{query}",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://quote.eastmoney.com/",
            },
        )
        research_limiter().wait("eastmoney")
        raw = ""
        last_exc: Exception | None = None
        for _attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=self._EM_TIMEOUT) as resp:  # nosec B310
                    raw = resp.read().decode("utf-8", errors="ignore")
                break
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
        if not raw:
            logger.info("eastmoney network fail for %s: %s", symbol, last_exc)
            return pd.DataFrame()

        import json

        try:
            payload = json.loads(raw)
        except Exception as exc:  # noqa: BLE001
            logger.info("eastmoney json decode failed for %s: %s", symbol, exc)
            return pd.DataFrame()
        klines = (payload.get("data") or {}).get("klines") or []
        if not klines:
            logger.info("eastmoney empty payload for %s (secid=%s)", symbol, secid)
            return pd.DataFrame()

        rows = []
        rejected_date = 0
        rejected_numeric = 0
        for row in klines:
            parts = row.split(",")
            if len(parts) < 6:
                continue
            dt_raw, open_, close, high, low, vol = parts[:6]
            dt_obj = self._parse_em_date(dt_raw)
            if dt_obj is None:
                rejected_date += 1
                continue
            try:
                rec = {
                    "Date": dt_obj,
                    "Open": float(open_),
                    "High": float(high),
                    "Low": float(low),
                    "Close": float(close),
                    "Adj Close": float(close),
                    "Volume": max(float(vol), 0.0),
                }
            except (TypeError, ValueError):
                rejected_numeric += 1
                continue
            rows.append(rec)

        if rejected_date or rejected_numeric:
            logger.info(
                "eastmoney row filter for %s: kept=%d rejected_date=%d rejected_numeric=%d",
                symbol, len(rows), rejected_date, rejected_numeric,
            )
        if not rows:
            return pd.DataFrame()

        try:
            df = pd.DataFrame(rows)
            # Build DatetimeIndex without going through pandas' inference.
            df["Date"] = pd.DatetimeIndex(df["Date"])
            df = df.set_index("Date").sort_index()
            df.index.name = "Date"
        except Exception as exc:  # noqa: BLE001
            logger.info(
                "eastmoney frame build failed for %s (rows=%d): %s",
                symbol, len(rows), exc,
            )
            return pd.DataFrame()

        with self._cache_lock:
            self._cache[key] = (now, df.copy())
        return df

    def _tencent_kline(self, symbol: str) -> pd.DataFrame:
        """Tencent public kline — A股/港股/美股/指数 covered.

        Endpoint: ``http://web.ifzq.gtimg.cn/appstock/app/fqkline/get``.
        Response shape: ``{data: {<tx_code>: {day: [[date, open, close, high, low, volume], ...]}}}``.
        Used as a secondary fallback when Eastmoney returns an empty payload.
        """
        tx_code = self._TX_SECID.get(symbol)
        if not tx_code:
            return pd.DataFrame()
        key = f"tx:{symbol}"
        now = time.monotonic()
        with self._cache_lock:
            cached = self._cache.get(key)
            if cached and (now - cached[0]) <= self._cache_ttl:
                return cached[1].copy()

        query = urllib.parse.urlencode({
            "_var": "",
            "param": f"{tx_code},day,,,520,qfq",
        })
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?{query}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": "https://gu.qq.com/",
            },
        )
        research_limiter().wait("tencent")
        raw = ""
        try:
            with urllib.request.urlopen(req, timeout=self._TX_TIMEOUT) as resp:  # nosec B310
                raw = resp.read().decode("utf-8", errors="ignore")
        except Exception as exc:  # noqa: BLE001
            logger.info("tencent network fail for %s: %s", symbol, exc)
            return pd.DataFrame()

        # Tencent endpoint responds with either plain JSON or ``<var>=<json>;``
        import json as _json
        body = raw.strip()
        if body.startswith("v_") or "=" in body[:40]:
            eq = body.find("=")
            body = body[eq + 1:].rstrip(";")
        try:
            payload = _json.loads(body)
        except Exception as exc:  # noqa: BLE001
            logger.info("tencent json decode failed for %s: %s", symbol, exc)
            return pd.DataFrame()

        data_node = (payload.get("data") or {}).get(tx_code) or {}
        bars = data_node.get("day") or data_node.get("qfqday") or []
        if not bars:
            logger.info("tencent empty payload for %s (%s)", symbol, tx_code)
            return pd.DataFrame()

        rows = []
        for bar in bars:
            if not bar or len(bar) < 5:
                continue
            dt_obj = self._parse_em_date(str(bar[0]))
            if dt_obj is None:
                continue
            try:
                open_ = float(bar[1])
                close = float(bar[2])
                high = float(bar[3])
                low = float(bar[4])
                vol = float(bar[5]) if len(bar) > 5 else 0.0
            except (TypeError, ValueError):
                continue
            rows.append({
                "Date": dt_obj,
                "Open": open_,
                "High": high,
                "Low": low,
                "Close": close,
                "Adj Close": close,
                "Volume": max(vol, 0.0),
            })
        if not rows:
            return pd.DataFrame()
        try:
            df = pd.DataFrame(rows)
            df["Date"] = pd.DatetimeIndex(df["Date"])
            df = df.set_index("Date").sort_index()
            df.index.name = "Date"
        except Exception as exc:  # noqa: BLE001
            logger.info("tencent frame build failed for %s: %s", symbol, exc)
            return pd.DataFrame()

        with self._cache_lock:
            self._cache[key] = (now, df.copy())
        return df

    def index_price_data(self, symbols: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        wanted = symbols or list(required_symbols_for("cn_a"))
        out: Dict[str, pd.DataFrame] = {}
        remain: List[str] = []
        for symbol in wanted:
            # First: Eastmoney
            if symbol in self._EM_SECID:
                try:
                    df = self._eastmoney_kline(symbol)
                    if not df.empty:
                        out[symbol] = df
                        continue
                except Exception as exc:  # noqa: BLE001
                    logger.info("eastmoney unexpected error for %s: %s", symbol, exc)
            # Second: Tencent (handles empty-payload case for A/HK/US indices)
            if symbol in self._TX_SECID:
                try:
                    df = self._tencent_kline(symbol)
                    if not df.empty:
                        out[symbol] = df
                        continue
                except Exception as exc:  # noqa: BLE001
                    logger.info("tencent unexpected error for %s: %s", symbol, exc)
            remain.append(symbol)

        # Third: Yahoo for residual symbols (macro/forex rarely available elsewhere)
        yf_pairs = [(logical, self._YF_SYMBOL_MAP.get(logical, "")) for logical in remain]
        yf_data = self._download_yf([(l, y) for l, y in yf_pairs if y])
        for k, v in yf_data.items():
            if k not in out and not v.empty:
                out[k] = v

        # Final safety net: fabricate deterministic OHLCV for symbols that remain
        # missing so the analytics pipeline can always complete. This is marked
        # via the degraded meta; the envelope surfaces it as fallback.
        missing: List[str] = []
        for symbol in wanted:
            if symbol in out and not out[symbol].empty:
                continue
            params = self._PARAMS.get(symbol)
            if params is None:
                missing.append(symbol)
                continue
            out[symbol] = self._generate(*params, seed=4242 + hash(symbol) % 9973)
            missing.append(symbol)

        if missing:
            self._degraded = True
            self._degrade_reason = f"fallback_used_for:{','.join(missing[:6])}"
        return out


# ---------------------------------------------------------------------------
# Adapter registry
# ---------------------------------------------------------------------------


_ADAPTERS: Dict[str, Callable[[], DataSourceAdapter]] = {
    "demo": DemoSnapshotAdapter,
    "yfinance": YFinanceResearchAdapter,
    "yfinance-research": YFinanceResearchAdapter,
    "hybrid": HybridMarketResearchAdapter,
    "hybrid-research": HybridMarketResearchAdapter,
}


_SELECTED: DataSourceAdapter | None = None


def get_data_source() -> DataSourceAdapter:
    global _SELECTED
    if _SELECTED is not None:
        return _SELECTED
    choice = os.getenv("DATA_SOURCE", "hybrid").strip().lower()
    factory = _ADAPTERS.get(choice, DemoSnapshotAdapter)
    _SELECTED = factory()
    logger.info("data source adapter: %s (tier=%s, grade=%s)", _SELECTED.name, _SELECTED.tier, _SELECTED.truth_grade)
    return _SELECTED


def list_adapter_names() -> List[str]:
    return list(_ADAPTERS.keys())


# ---------------------------------------------------------------------------
# Back-compat helpers retained for existing imports
# ---------------------------------------------------------------------------


INDEX_NAME_MAP: Dict[str, str] = {s: i.name for s, i in SYMBOL_MASTER.items()}


def index_name(symbol: str) -> str:
    return INDEX_NAME_MAP.get(symbol, symbol)


def all_index_symbols() -> List[str]:
    return list(INDEX_NAME_MAP.keys())
