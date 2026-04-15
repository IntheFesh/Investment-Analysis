"""
data_collection
================

Helper functions for downloading financial market data.  At present this module leverages the
`yfinance` package to retrieve daily price histories and company financial statements from
Yahoo! Finance.  Because the API is public and unauthenticated it is suitable for small
educational projects but may be rate‑limited for large batch jobs.

Functions in this module return `pandas.DataFrame` objects or dictionaries keyed by ticker
symbols.  Errors encountered during download will be caught and raised as informative exceptions.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf


logger = logging.getLogger(__name__)


def fetch_stock_data(
    tickers: List[str],
    start_date: str,
    end_date: str,
    interval: str = "1d",
) -> Dict[str, pd.DataFrame]:
    """Download historical price data for one or more tickers.

    Parameters
    ----------
    tickers: list[str]
        A list of ticker symbols (e.g. ``["AAPL", "MSFT"]``).
    start_date: str
        The start date (inclusive) in ``YYYY-MM-DD`` format.
    end_date: str
        The end date (exclusive) in ``YYYY-MM-DD`` format.
    interval: str, default "1d"
        The sampling interval for the data.  See `yfinance.download` for valid
        intervals (e.g. "1d", "1wk", "1mo").

    Returns
    -------
    dict[str, pd.DataFrame]
        A mapping of ticker symbols to price data.  Each DataFrame has a DatetimeIndex
        and columns ``["Open", "High", "Low", "Close", "Adj Close", "Volume"]``.
    """
    if not tickers:
        raise ValueError("At least one ticker must be provided.")

    logger.info("Downloading price data for %s", ", ".join(tickers))
    data = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, start=start_date, end=end_date, interval=interval, progress=False)
            if df.empty:
                raise RuntimeError(f"No data returned for {ticker}; check symbol or date range")
            df.sort_index(inplace=True)
            data[ticker] = df
        except Exception as exc:  # pragma: no cover - external API
            logger.error("Failed to download data for %s: %s", ticker, exc)
            raise
    return data


def fetch_income_statement(ticker: str, period: str = "annual") -> pd.DataFrame:
    """Fetch the income statement for a given ticker.

    Returns a DataFrame where columns represent reporting periods and rows represent
    financial items (e.g. ``Total Revenue``, ``Gross Profit``, etc.).  Financial data is
    typically updated quarterly or annually; this helper defaults to annual results.

    Parameters
    ----------
    ticker: str
        The ticker symbol.
    period: str, default "annual"
        "annual" for yearly results or "quarterly" for quarterly results.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the income statement.  If the API does not return
        financials, an empty DataFrame is returned.
    """
    try:
        stock = yf.Ticker(ticker)
        if period == "annual":
            financials = stock.financials
        elif period == "quarterly":
            financials = stock.quarterly_financials
        else:
            raise ValueError("period must be 'annual' or 'quarterly'")
        return financials
    except Exception as exc:  # pragma: no cover - external API
        logger.error("Failed to fetch financials for %s: %s", ticker, exc)
        raise