"""A-share Greed Index (initial v1).

Two-component composite:

- ``volume``        : recent-5d mean volume / 60d mean volume on 沪深 300
                      (proxy for speculative participation).
- ``breadth``       : advancers / (advancers + decliners) from the full
                      A-share spot snapshot.

Both components are normalised into a 0-100 sub-score, averaged with
equal weights, and returned alongside the raw evidence. Consumers read
``score`` (0-100) and ``state`` (greed/fear label).

We intentionally keep the algorithm transparent — the goal is to let the
UI render a dashboard with honest inputs rather than a hand-tuned score.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from ..core.data_source import DataSourceAdapter, HybridMarketResearchAdapter


logger = logging.getLogger(__name__)


METHOD_VERSION = "greed.v1"

PRIMARY_INDEX = "000300.SS"


def _clip01(x: float) -> float:
    if not np.isfinite(x):
        return 0.5
    return float(max(0.0, min(1.0, x)))


def _state_label(score: float) -> str:
    if score >= 80.0:
        return "extreme_greed"
    if score >= 60.0:
        return "greed"
    if score >= 40.0:
        return "neutral"
    if score >= 20.0:
        return "fear"
    return "extreme_fear"


def _state_zh(state: str) -> str:
    return {
        "extreme_greed": "极度贪婪",
        "greed": "贪婪",
        "neutral": "中性",
        "fear": "恐慌",
        "extreme_fear": "极度恐慌",
    }.get(state, state)


def _volume_score(df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
    """Map volume ratio → 0-100. 1.0 maps to 50, clipped at [0.5, 2.0]."""
    if df is None or df.empty or "Volume" not in df.columns:
        return 50.0, {"ratio": None, "reason": "no_volume"}
    vol = df["Volume"].astype(float).dropna()
    if len(vol) < 20:
        return 50.0, {"ratio": None, "reason": "insufficient_window"}
    recent = float(vol.tail(5).mean())
    base = float(vol.tail(60).mean()) if len(vol) >= 60 else float(vol.mean())
    if base <= 0:
        return 50.0, {"ratio": None, "reason": "zero_base"}
    ratio = recent / base
    clipped = max(0.5, min(2.0, ratio))
    normalised = (clipped - 0.5) / 1.5  # 0..1
    return round(_clip01(normalised) * 100.0, 2), {
        "ratio": round(ratio, 3),
        "recent_5d_mean": round(recent, 2),
        "trailing_60d_mean": round(base, 2),
    }


def _breadth_score(adapter: DataSourceAdapter) -> Tuple[float, Dict[str, Any]]:
    """Advancers / (advancers + decliners) from the A-share spot snapshot.

    Requires AkShare. When it's unavailable we fall back to a neutral 50
    with an explicit reason so the UI can render a "数据不足" tag.
    """
    if not isinstance(adapter, HybridMarketResearchAdapter):
        return 50.0, {"reason": "adapter_without_ak_spot"}

    ak = adapter._get_akshare()
    if ak is None:
        return 50.0, {"reason": "akshare_unavailable"}

    try:
        df = ak.stock_zh_a_spot_em()
    except Exception as exc:  # noqa: BLE001
        logger.info("akshare spot snapshot failed: %s", exc)
        return 50.0, {"reason": f"spot_fetch_failed: {exc}"}

    if df is None or df.empty:
        return 50.0, {"reason": "empty_spot_snapshot"}

    chg_col = None
    for cand in ("涨跌幅", "涨跌幅(%)", "pct_chg"):
        if cand in df.columns:
            chg_col = cand
            break
    if chg_col is None:
        return 50.0, {"reason": "missing_pct_col"}

    chg = pd.to_numeric(df[chg_col], errors="coerce").dropna()
    if chg.empty:
        return 50.0, {"reason": "no_numeric_pct"}

    advancers = int((chg > 0).sum())
    decliners = int((chg < 0).sum())
    flat = int((chg == 0).sum())
    denom = advancers + decliners
    ratio = (advancers / denom) if denom else 0.5
    score = round(_clip01(ratio) * 100.0, 2)
    return score, {
        "advancers": advancers,
        "decliners": decliners,
        "unchanged": flat,
        "ratio": round(ratio, 3),
    }


def build_greed_index(adapter: DataSourceAdapter, market_view: str = "cn_a") -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Build the A-share greed index payload.

    Returns ``(payload, meta)``. ``meta`` is the adapter's stamped envelope
    metadata, extended with ``calculation_method_version`` and
    ``evidence_count``.
    """
    data = adapter.index_price_data([PRIMARY_INDEX])
    csi300 = data.get(PRIMARY_INDEX, pd.DataFrame())

    volume_score, volume_evidence = _volume_score(csi300)
    breadth_score, breadth_evidence = _breadth_score(adapter)

    composite = round((volume_score + breadth_score) / 2.0, 2)
    state = _state_label(composite)

    as_of = None
    if not csi300.empty:
        try:
            as_of = csi300.index[-1].strftime("%Y-%m-%d")
        except Exception:  # noqa: BLE001
            as_of = None

    payload: Dict[str, Any] = {
        "market_view": market_view,
        "score": composite,
        "state": state,
        "state_label": _state_zh(state),
        "as_of": as_of,
        "components": {
            "volume": {
                "score": volume_score,
                "weight": 0.5,
                "evidence": volume_evidence,
            },
            "breadth": {
                "score": breadth_score,
                "weight": 0.5,
                "evidence": breadth_evidence,
            },
        },
        "method_version": METHOD_VERSION,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }

    meta = adapter.meta(universe=market_view).to_dict()
    meta["calculation_method_version"] = METHOD_VERSION
    meta["evidence_count"] = 2
    return payload, meta
