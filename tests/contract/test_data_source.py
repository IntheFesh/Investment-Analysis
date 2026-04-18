"""Round-0 contract tests for data_source hardening.

- The hybrid adapter must not silently default to the cn_a universe when
  called with ``symbols=None``; instead it serves the union of all known
  universes.
- Passing an explicit empty list is a programming bug and must raise.
"""

from __future__ import annotations

import pytest

from backend.core.data_source import HybridMarketResearchAdapter
from backend.core.universe import required_symbols_for


def test_empty_symbols_list_raises() -> None:
    adapter = HybridMarketResearchAdapter()
    with pytest.raises(ValueError, match="empty list"):
        adapter.index_price_data([])


def test_probe_symbol_returns_structured_report(monkeypatch) -> None:
    adapter = HybridMarketResearchAdapter()

    # Short-circuit the vendor fetchers so the test runs offline.
    import pandas as pd

    def _stub(symbol):
        idx = pd.date_range("2024-01-01", periods=3, freq="D")
        return pd.DataFrame({
            "Open": [1, 2, 3], "High": [1, 2, 3], "Low": [1, 2, 3],
            "Close": [1, 2, 3], "Adj Close": [1, 2, 3], "Volume": [10, 20, 30],
        }, index=idx)

    monkeypatch.setattr(adapter, "_eastmoney_kline", _stub)
    report = adapter.probe_symbol("000300.SS")
    assert report["symbol"] == "000300.SS"
    assert report["final_vendor"] == "eastmoney"
    assert report["final_rows"] == 3
    assert report["attempts"]
    first = report["attempts"][0]
    assert first["vendor"] == "eastmoney"
    assert first["ok"] is True
    assert "last_raw_date" in first
    assert "latency_ms" in first
    # Breaker state is surfaced even on success so debug panel can show trends.
    assert "breaker_open" in first


def test_universe_resolution_stays_view_specific() -> None:
    # Guard rail for Round 1: make sure cn_a / hk / global do NOT return
    # the same symbol set. If this ever fails, the market_view dropdown is
    # silently collapsing to one universe again.
    cn = set(required_symbols_for("cn_a"))
    hk = set(required_symbols_for("hk"))
    gl = set(required_symbols_for("global"))
    assert cn != hk
    assert cn != gl
    assert hk != gl
    # Each view must contribute at least 5 distinct symbols.
    assert len(cn) >= 5
    assert len(hk) >= 5
    assert len(gl) >= 5
