"""Core infrastructure for the investment research API.

Modules:
- envelope: unified response envelope helpers with meta fields
  (data_source, is_demo, as_of_trading_day, market_session, tz).
- data_source: DataSourceAdapter abstraction; selected via DATA_SOURCE env.
- tasks: in-process async task store for export / simulation / ocr endpoints.
"""
