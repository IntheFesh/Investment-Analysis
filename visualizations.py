"""
visualizations
==============

Matplotlib helper routines for plotting financial data.  These functions take
`pandas` DataFrames or dictionaries and produce charts illustrating price
histories and risk–return characteristics.  Users may customise colours,
markers and other aesthetic parameters by extending the functions provided here.
"""

from __future__ import annotations

from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd


def plot_price_series(price_data: Dict[str, pd.DataFrame]) -> None:
    """Plot closing prices for multiple assets on a single figure.

    Parameters
    ----------
    price_data: dict[str, pandas.DataFrame]
        Mapping of ticker symbols to their price DataFrames (as returned from
        ``data_collection.fetch_stock_data``).  Only the ``Adj Close`` column
        is plotted.
    """
    plt.figure(figsize=(10, 6))
    for ticker, df in price_data.items():
        if 'Adj Close' not in df.columns:
            continue
        plt.plot(df.index, df['Adj Close'], label=ticker)
    plt.xlabel('Date')
    plt.ylabel('Adjusted Close Price')
    plt.title('Adjusted Closing Prices')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    # Do not call plt.show() here to allow callers to control display behaviour


def plot_risk_return_scatter(
    returns: pd.Series,
    volatilities: pd.Series,
    sharpe_ratios: pd.Series,
) -> None:
    """Create a scatter plot of return vs volatility for multiple assets.

    Each point represents an asset, labelled by its ticker.  The colour intensity
    reflects the Sharpe ratio, with higher ratios appearing darker.

    Parameters
    ----------
    returns: pandas.Series
        Annualised returns for each asset.
    volatilities: pandas.Series
        Annualised volatilities corresponding to the assets.
    sharpe_ratios: pandas.Series
        Annualised Sharpe ratios.
    """
    plt.figure(figsize=(8, 5))
    # Normalise sharpe ratios for colouring; avoid division by zero
    if sharpe_ratios.max() == sharpe_ratios.min():
        colours = 'tab:blue'
    else:
        norm = (sharpe_ratios - sharpe_ratios.min()) / (sharpe_ratios.max() - sharpe_ratios.min())
        colours = plt.cm.viridis(norm)
    for i, ticker in enumerate(returns.index):
        plt.scatter(volatilities[ticker], returns[ticker], color=colours[i] if isinstance(colours, list) else colours, s=80)
        plt.text(volatilities[ticker], returns[ticker], ticker, fontsize=9, ha='left', va='bottom')
    plt.xlabel('Volatility (annualised)')
    plt.ylabel('Return (annualised)')
    plt.title('Risk–Return Profile')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    # Again, no plt.show() here