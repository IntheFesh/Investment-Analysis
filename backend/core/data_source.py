"""Data source abstraction.

The platform reads market / fund data through a :class:`DataSourceAdapter`.
The concrete adapter is selected at process start-up based on ``DATA_SOURCE``.

Available adapters:
- ``demo`` (default, always works): deterministic synthetic snapshot.
  Meta advertises ``is_demo=True`` so the UI shows a clear "演示数据" banner.
- ``yfinance``: stub that attempts yfinance; falls back to demo and logs.
- ``akshare`` / ``tushare``: stubs — can be implemented when the environment
  has network access and valid tokens.

This separation is critical: the API contract never changes across adapters,
only ``meta.data_source`` / ``meta.is_demo`` / ``meta.as_of_trading_day`` do.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Mapping, Tuple

import numpy as np
import pandas as pd


logger = logging.getLogger(__name__)


INDEX_NAME_MAP: Dict[str, str] = {
    "000001.SS": "上证指数",
    "399001.SZ": "深证成指",
    "399006.SZ": "创业板指",
    "000300.SS": "沪深300",
    "000852.SS": "中证1000",
    "HSI": "恒生指数",
    "HSTECH": "恒生科技",
    "NDX": "纳斯达克100",
    "SPX": "标普500",
}


class DataSourceAdapter:
    """Abstract adapter. Subclasses override the data methods."""

    name: str = "base"
    is_demo: bool = True
    tz: str = "UTC"

    def meta(self, as_of: datetime | None = None) -> Dict[str, Any]:
        as_of = as_of or datetime.now(tz=timezone.utc)
        return {
            "data_source": self.name,
            "is_demo": self.is_demo,
            "as_of_trading_day": as_of.date().isoformat(),
            "as_of": as_of.isoformat(),
            "market_session": "snapshot",
            "tz": self.tz,
        }

    def index_price_data(self) -> Dict[str, pd.DataFrame]:  # pragma: no cover
        raise NotImplementedError

    def fund_metadata(self) -> Dict[str, Dict[str, Any]]:  # pragma: no cover
        raise NotImplementedError

    def fund_holdings(self) -> Dict[str, Dict[str, float]]:  # pragma: no cover
        raise NotImplementedError

    def fund_styles(self) -> Dict[str, Dict[str, float]]:  # pragma: no cover
        raise NotImplementedError


class DemoSnapshotAdapter(DataSourceAdapter):
    """Deterministic synthetic snapshot used when no live source is reachable."""

    name = "demo"
    is_demo = True
    tz = "Asia/Shanghai"

    # deterministic per-symbol params keep responses reproducible between restarts
    _INDEX_PARAMS: Dict[str, Tuple[float, float, float]] = {
        "000001.SS": (3200.0, 0.011, 0.00018),
        "399001.SZ": (10400.0, 0.013, 0.00014),
        "399006.SZ": (2150.0, 0.017, 0.00009),
        "000300.SS": (3750.0, 0.010, 0.00017),
        "000852.SS": (6100.0, 0.014, 0.00007),
        "HSI": (17600.0, 0.015, -0.00010),
        "HSTECH": (4050.0, 0.020, -0.00006),
        "NDX": (18500.0, 0.012, 0.00030),
        "SPX": (5250.0, 0.009, 0.00022),
    }

    def _generate(self, base_price: float, vol: float, drift: float, seed: int, days: int = 252) -> pd.DataFrame:
        end = datetime.now()
        start = end - timedelta(days=int(days * 1.5))
        rng = np.random.default_rng(seed)
        dates = pd.date_range(start=start, end=end, freq="B")[-days:]
        logret = rng.normal(loc=drift, scale=vol, size=len(dates))
        close = base_price * np.exp(np.cumsum(logret))
        close = pd.Series(close, index=dates)
        open_ = close.shift(1).fillna(close.iloc[0])
        high = np.maximum(open_, close) * (1 + rng.normal(0.0, 0.003, len(dates)).clip(0, 0.02))
        low = np.minimum(open_, close) * (1 - rng.normal(0.0, 0.003, len(dates)).clip(0, 0.02))
        volume = rng.integers(low=8_000_000, high=40_000_000, size=len(dates))
        df = pd.DataFrame(
            {
                "Open": open_,
                "High": high,
                "Low": low,
                "Close": close,
                "Adj Close": close,
                "Volume": volume,
            }
        )
        df.index.name = "Date"
        return df

    def index_price_data(self) -> Dict[str, pd.DataFrame]:
        seed_base = 4242
        return {
            symbol: self._generate(base, vol, drift, seed=seed_base + i)
            for i, (symbol, (base, vol, drift)) in enumerate(self._INDEX_PARAMS.items())
        }

    def fund_metadata(self) -> Dict[str, Dict[str, Any]]:
        return {
            "FUND001": {"name": "半导体成长混合", "type": "股票型", "manager": "李一", "aum": 8.5e9, "inception_date": "2019-05-10"},
            "FUND002": {"name": "新能源先锋", "type": "股票型", "manager": "王二", "aum": 6.2e9, "inception_date": "2021-01-15"},
            "FUND003": {"name": "金融地产优选", "type": "混合型", "manager": "赵三", "aum": 4.7e9, "inception_date": "2018-09-01"},
            "FUND004": {"name": "科技创新先锋", "type": "股票型", "manager": "张四", "aum": 7.8e9, "inception_date": "2020-03-20"},
            "FUND005": {"name": "消费红利精选", "type": "混合型", "manager": "钱五", "aum": 5.3e9, "inception_date": "2017-11-05"},
        }

    def fund_holdings(self) -> Dict[str, Dict[str, float]]:
        return {
            "FUND001": {"半导体": 0.35, "医药": 0.20, "消费": 0.20, "电子": 0.15, "现金": 0.10},
            "FUND002": {"新能源": 0.35, "有色金属": 0.20, "电力设备": 0.20, "汽车": 0.15, "现金": 0.10},
            "FUND003": {"银行": 0.30, "地产": 0.20, "非银金融": 0.25, "能源": 0.15, "现金": 0.10},
            "FUND004": {"半导体": 0.30, "软件": 0.25, "电子": 0.20, "医药": 0.15, "现金": 0.10},
            "FUND005": {"消费": 0.35, "食品饮料": 0.25, "医药": 0.20, "纺织": 0.10, "现金": 0.10},
        }

    def fund_styles(self) -> Dict[str, Dict[str, float]]:
        return {
            "FUND001": {"成长": 0.60, "价值": 0.20, "红利": 0.10, "防御": 0.10},
            "FUND002": {"成长": 0.55, "价值": 0.15, "红利": 0.15, "防御": 0.15},
            "FUND003": {"成长": 0.25, "价值": 0.45, "红利": 0.20, "防御": 0.10},
            "FUND004": {"成长": 0.70, "价值": 0.10, "红利": 0.10, "防御": 0.10},
            "FUND005": {"成长": 0.30, "价值": 0.25, "红利": 0.35, "防御": 0.10},
        }


class YFinanceAdapter(DemoSnapshotAdapter):
    """Live yfinance adapter with demo fallback.

    On any network / rate-limit error this silently degrades to the demo
    snapshot so the UI keeps rendering, while still advertising
    ``data_source=yfinance-fallback-demo`` so the banner stays honest.
    """

    name = "yfinance"
    is_demo = False
    tz = "Asia/Shanghai"

    _YF_SYMBOL_MAP: Dict[str, str] = {
        "000001.SS": "000001.SS",
        "399001.SZ": "399001.SZ",
        "399006.SZ": "399006.SZ",
        "000300.SS": "000300.SS",
        "000852.SS": "000852.SS",
        "HSI": "^HSI",
        "HSTECH": "^HSTECH",
        "NDX": "^NDX",
        "SPX": "^GSPC",
    }

    def index_price_data(self) -> Dict[str, pd.DataFrame]:
        try:
            import yfinance as yf  # type: ignore

            tickers = list(self._YF_SYMBOL_MAP.values())
            data = yf.download(
                tickers=tickers,
                period="1y",
                interval="1d",
                group_by="ticker",
                auto_adjust=False,
                progress=False,
                threads=False,
            )
            out: Dict[str, pd.DataFrame] = {}
            for logical, yf_symbol in self._YF_SYMBOL_MAP.items():
                try:
                    df = data[yf_symbol].dropna(how="all").copy()
                    if df.empty:
                        raise ValueError("empty")
                    df.index.name = "Date"
                    out[logical] = df
                except Exception:  # noqa: BLE001
                    out[logical] = super().index_price_data()[logical]
            return out
        except Exception as exc:  # noqa: BLE001
            logger.warning("yfinance adapter fell back to demo snapshot: %s", exc)
            self.name = "yfinance-fallback-demo"
            self.is_demo = True
            return super().index_price_data()


_SELECTED: DataSourceAdapter | None = None


def get_data_source() -> DataSourceAdapter:
    """Return the singleton adapter selected by ``DATA_SOURCE`` env."""

    global _SELECTED
    if _SELECTED is not None:
        return _SELECTED

    choice = os.getenv("DATA_SOURCE", "demo").strip().lower()
    if choice == "yfinance":
        _SELECTED = YFinanceAdapter()
    else:
        _SELECTED = DemoSnapshotAdapter()
    return _SELECTED


def index_name(symbol: str) -> str:
    return INDEX_NAME_MAP.get(symbol, symbol)


def all_index_symbols() -> List[str]:
    return list(INDEX_NAME_MAP.keys())
