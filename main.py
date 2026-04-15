"""
main
====

Example command‑line script demonstrating how to use the functions defined in
the other modules.  It downloads price data for a list of tickers over a
user‑specified period, computes risk metrics, optimises the portfolio and
displays results.

To run:

```
python main.py --tickers AAPL MSFT GOOGL --start 2020-01-01 --end 2024-12-31
```

Additional options allow you to set the risk‑free rate and choose the sampling
interval.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from typing import List

import numpy as np
import pandas as pd

from data_collection import fetch_stock_data
from data_analysis import (
    compute_daily_returns,
    compute_volatility,
    compute_sharpe_ratio,
    compute_max_drawdown,
)
from portfolio_optimization import optimise_portfolio, portfolio_performance
from visualizations import plot_price_series, plot_risk_return_scatter


def parse_arguments(argv: List[str]) -> argparse.Namespace:
    """Parse command‑line arguments."""
    parser = argparse.ArgumentParser(description="Financial analysis and portfolio optimisation")
    parser.add_argument('--tickers', nargs='+', required=True, help='List of ticker symbols')
    parser.add_argument('--start', type=str, required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--interval', type=str, default='1d', help='Data interval (e.g. 1d, 1wk, 1mo)')
    parser.add_argument('--risk_free_rate', type=float, default=0.0, help='Annual risk-free rate (e.g. 0.02 for 2%)')
    return parser.parse_args(argv)


def main(argv: List[str]) -> None:
    args = parse_arguments(argv)
    # Validate dates
    try:
        start = datetime.strptime(args.start, '%Y-%m-%d')
        end = datetime.strptime(args.end, '%Y-%m-%d')
        if end <= start:
            raise ValueError('End date must be after start date.')
    except ValueError as exc:
        print(f"Invalid date format: {exc}")
        return

    # Fetch price data
    price_data = fetch_stock_data(args.tickers, args.start, args.end, args.interval)
    # Construct a combined DataFrame of adjusted closes
    combined = pd.concat(
        {ticker: df['Adj Close'] for ticker, df in price_data.items()},
        axis=1
    ).dropna(how='all')

    # Compute returns and risk metrics
    returns = compute_daily_returns(combined)
    volatilities = compute_volatility(returns)
    sharpe_ratios = compute_sharpe_ratio(returns, risk_free_rate=args.risk_free_rate)
    max_drawdowns = compute_max_drawdown(combined)

    # Optimise portfolio
    weights = optimise_portfolio(returns, risk_free_rate=args.risk_free_rate)
    port_return, port_vol, port_sharpe = portfolio_performance(weights, returns, args.risk_free_rate)

    # Display numerical results
    print('\nIndividual asset metrics:')
    for ticker in args.tickers:
        print(f"{ticker}: Annual Return={returns[ticker].mean()*252:.2%}, "
              f"Volatility={volatilities[ticker]:.2%}, "
              f"Sharpe Ratio={sharpe_ratios[ticker]:.2f}, "
              f"Max Drawdown={max_drawdowns[ticker]:.2%}")
    print('\nOptimised portfolio:')
    for ticker, weight in zip(args.tickers, weights):
        print(f"Weight of {ticker}: {weight:.2%}")
    print(f"Expected portfolio return: {port_return:.2%}")
    print(f"Portfolio volatility: {port_vol:.2%}")
    print(f"Portfolio Sharpe ratio: {port_sharpe:.2f}\n")

    # Generate plots
    plot_price_series(price_data)
    plot_risk_return_scatter(
        returns=returns.mean() * 252,
        volatilities=volatilities,
        sharpe_ratios=sharpe_ratios,
    )
    # Show the figures at the end
    import matplotlib.pyplot as plt
    plt.show()


if __name__ == '__main__':  # pragma: no cover
    main(sys.argv[1:])