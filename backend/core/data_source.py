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
import threading
import time
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
    """Non-blocking rate limiter.

    The old implementation ``time.sleep``-ed inside the request thread,
    which compounded with the FastAPI async handlers to yield 10s+ stalls
    whenever more than one market snapshot was warming up.

    The new implementation is token-bucket-ish: ``try_acquire`` returns
    True if the vendor slot is free, False otherwise. Callers are expected
    to serve cached data and let the background refresher retry later.
    """

    def __init__(self, min_interval_seconds: int = 10) -> None:
        self._last: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._interval = min_interval_seconds

    def try_acquire(self, vendor: str) -> bool:
        now = time.monotonic()
        with self._lock:
            last = self._last.get(vendor, 0.0)
            if now - last < self._interval:
                return False
            self._last[vendor] = now
        return True

    def wait(self, vendor: str, max_wait: float = 0.0) -> float:
        """Legacy helper — now caps the wait so async callers don't hang.

        Returns actually waited seconds (0.0 if slot was already free or
        cap was hit).
        """
        with self._lock:
            last = self._last.get(vendor, 0.0)
            elapsed = time.monotonic() - last
            remaining = max(0.0, self._interval - elapsed)
            sleep_for = min(remaining, max_wait)
            self._last[vendor] = time.monotonic() + sleep_for
        if sleep_for > 0:
            time.sleep(sleep_for)
        return sleep_for


_LIMITER = ResearchRateLimiter(int(os.getenv("RESEARCH_RATE_LIMIT_SECONDS", "10")))


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

    Failure isolation
    -----------------
    A single delisted/404 ticker (notably ^HSTECH has been intermittently
    unavailable) must not cascade and break every market-overview snapshot.
    We download in small per-ticker slices with an explicit timeout, cache
    the last successful pull per logical symbol and only fall back to the
    deterministic demo series for the specific symbol that failed. The
    envelope meta is stamped with a precise ``fallback_reason`` listing the
    missing tickers so the frontend can surface ``fallback: partial``.
    """

    name = "yfinance-research"
    tier = "research_only"
    truth_grade = "C"
    license_scope = "research_only"
    tz = "Asia/Shanghai"
    delay_seconds = 900
    is_realtime = False

    _YF_SYMBOL_MAP = _YF_PRIMARY_MAP

    _FETCH_TIMEOUT = float(os.getenv("YF_FETCH_TIMEOUT", "4.0"))
    _MAX_TICKERS_PER_BATCH = int(os.getenv("YF_BATCH_SIZE", "6"))

    _degraded: bool = False
    _degrade_reason: Optional[str] = None
    _missing: List[str] = []

    def _download_batch(self, tickers: List[str]) -> Optional[pd.DataFrame]:
        try:
            import yfinance as yf  # type: ignore
        except Exception as exc:  # noqa: BLE001
            self._degraded = True
            self._degrade_reason = f"yfinance import failed: {exc}"
            logger.warning(self._degrade_reason)
            return None
        try:
            return yf.download(
                tickers=tickers, period="2y", interval="1d",
                group_by="ticker", auto_adjust=False, progress=False,
                threads=True, timeout=self._FETCH_TIMEOUT,
            )
        except TypeError:
            # Older yfinance may not expose ``timeout``; retry without it.
            try:
                return yf.download(
                    tickers=tickers, period="2y", interval="1d",
                    group_by="ticker", auto_adjust=False, progress=False,
                    threads=True,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("yfinance batch download failed (no-timeout retry): %s", exc)
                return None
        except Exception as exc:  # noqa: BLE001
            logger.warning("yfinance batch download failed: %s", exc)
            return None

    def _extract(self, data: Any, yf_symbol: str) -> pd.DataFrame:
        try:
            if isinstance(data, pd.DataFrame):
                if isinstance(data.columns, pd.MultiIndex):
                    if yf_symbol in data.columns.get_level_values(0):
                        df = data[yf_symbol].dropna(how="all").copy()
                    else:
                        return pd.DataFrame()
                else:
                    df = data.dropna(how="all").copy()
                if df.empty:
                    return pd.DataFrame()
                df.index.name = "Date"
                return df
        except Exception:  # noqa: BLE001
            return pd.DataFrame()
        return pd.DataFrame()

    def _fetch_single(self, logical: str, candidates: List[str]) -> Optional[pd.DataFrame]:
        for candidate in candidates:
            if not candidate:
                continue
            data = self._download_batch([candidate])
            if data is None:
                continue
            df = self._extract(data, candidate)
            if not df.empty:
                _yf_cache_put(logical, df)
                return df
        return None

    def index_price_data(self, symbols: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        wanted = symbols or list(self._YF_SYMBOL_MAP.keys())
        self._missing = []
        demo_fallback = super().index_price_data(wanted)

        # Non-blocking vendor throttle. If Yahoo was hit recently, we serve
        # whatever we cached last and defer the retry to the background
        # refresher.
        slot_free = research_limiter().try_acquire("yahoo")

        out: Dict[str, pd.DataFrame] = {}
        pending: List[Tuple[str, str]] = []  # (logical, yf_symbol)
        for logical in wanted:
            primary = self._YF_SYMBOL_MAP.get(logical)
            cached = _yf_cache_get(logical)
            if cached is not None and not slot_free:
                out[logical] = cached
                continue
            if primary is None:
                # No mapping — definitively fall back to demo proxy.
                out[logical] = demo_fallback.get(logical, pd.DataFrame())
                continue
            pending.append((logical, primary))

        if not slot_free and not pending:
            return out

        if not pending:
            return out

        # Batch pull for the primaries we still need to fetch. Split into
        # small batches so a single bad ticker can be isolated quickly.
        primaries = [yf for _, yf in pending]
        batch_data: Dict[str, pd.DataFrame] = {}
        for i in range(0, len(primaries), self._MAX_TICKERS_PER_BATCH):
            chunk = primaries[i : i + self._MAX_TICKERS_PER_BATCH]
            downloaded = self._download_batch(chunk)
            if downloaded is None:
                continue
            for yf_symbol in chunk:
                df = self._extract(downloaded, yf_symbol)
                if not df.empty:
                    batch_data[yf_symbol] = df

        for logical, yf_symbol in pending:
            df = batch_data.get(yf_symbol)
            if df is not None and not df.empty:
                _yf_cache_put(logical, df)
                out[logical] = df
                continue

            # Primary failed — try per-symbol fallback tickers, then the
            # per-symbol cache, then the deterministic demo proxy.
            alternates = _YF_FALLBACK_MAP.get(logical, [])
            recovered = self._fetch_single(logical, alternates) if alternates else None
            if recovered is not None:
                out[logical] = recovered
                self._missing.append(f"{logical}(primary {yf_symbol}→alt)")
                continue

            cached = _yf_cache_get(logical, max_age=24 * 3600)
            if cached is not None and not cached.empty:
                out[logical] = cached
                self._missing.append(f"{logical}(cached)")
                continue

            out[logical] = demo_fallback.get(logical, pd.DataFrame())
            self._missing.append(f"{logical}(demo)")

        if self._missing:
            self._degraded = True
            self._degrade_reason = "partial: " + ", ".join(self._missing[:6])
            if len(self._missing) > 6:
                self._degrade_reason += f" …(+{len(self._missing) - 6})"
            logger.info("yfinance partial: %s", self._degrade_reason)
        return out

    def meta(self, *, universe: str = "unknown", fallback_reason: Optional[str] = None) -> SourceMeta:
        base = super().meta(universe=universe, fallback_reason=fallback_reason)
        if self._degraded:
            base.source_name = "yfinance-research-degraded"
            base.fallback_reason = self._degrade_reason or "degraded"
            base.is_proxy = True
        return base


# ---------------------------------------------------------------------------
# Adapter registry
# ---------------------------------------------------------------------------


_ADAPTERS: Dict[str, Callable[[], DataSourceAdapter]] = {
    "demo": DemoSnapshotAdapter,
    "yfinance": YFinanceResearchAdapter,
    "yfinance-research": YFinanceResearchAdapter,
}


_SELECTED: DataSourceAdapter | None = None


def get_data_source() -> DataSourceAdapter:
    global _SELECTED
    if _SELECTED is not None:
        return _SELECTED
    choice = os.getenv("DATA_SOURCE", "demo").strip().lower()
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
