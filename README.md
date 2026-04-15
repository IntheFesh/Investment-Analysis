# Investment‑Analysis

This repository provides a simple framework for downloading, analysing and visualising financial market data.  It is designed as a teaching example for students learning about portfolio management, risk measurement and optimisation.

## Features

The project is split into a few modules:

* **`data_collection.py`** – Fetches historical price data and company financials using the `yfinance` API.
* **`data_analysis.py`** – Calculates daily returns, volatility, correlation, Sharpe ratios and maximum drawdowns.
* **`portfolio_optimization.py`** – Implements a basic mean–variance optimiser to find portfolio weights that maximise the Sharpe ratio subject to weights summing to 1.
* **`visualizations.py`** – Provides helper functions for plotting price histories and risk–return scatter plots using `matplotlib`.
* **`main.py`** – An example script tying together the above modules to download data for a list of tickers, compute metrics, optimise a portfolio and display results.

## Installation

The code depends on a handful of widely used Python libraries.  To install them into a virtual environment run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The key dependencies are:

* `pandas` and `numpy` for data handling and numerical operations.
* `yfinance` to fetch market data and company financials from Yahoo! Finance.
* `scipy` for optimisation algorithms.
* `matplotlib` for plotting.

## Usage

The easiest way to get started is to run the example script:

```bash
python main.py --tickers AAPL MSFT GOOGL --start 2020-01-01 --end 2024-12-31
```

This will download price data for Apple, Microsoft and Alphabet, compute a variety of risk metrics, optimise the portfolio weights and print the results.  It will also display plots of the individual price series and the risk–return profile of each asset.

You can customise the risk‑free rate used in the optimisation via the `--risk_free_rate` option, and adjust the output plots by modifying the functions in `visualizations.py`.

## Notes

This repository is intended as a learning resource rather than a production‑ready trading tool.  The optimisation routine is deliberately simple and assumes a normal distribution of returns and unconstrained long‑only weights.  In practice, portfolio construction often requires more sophisticated models, constraints and robust estimation techniques.  Feel free to extend the code to meet more specific requirements.