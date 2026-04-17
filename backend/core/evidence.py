"""Unified evidence object builder.

Every algorithmic conclusion shown to a user should be wrapped in one of
these. The frontend's EvidencePanel component can then open any conclusion
and see:
  - What primitive indicators it was computed from.
  - Which data sources + truth_grade they came from.
  - Which method version was used.
  - Confidence, failure conditions, risks.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class Evidence:
    conclusion: str
    method: str
    method_version: str
    source_name: str
    source_tier: str
    truth_grade: str
    universe: str
    indicators: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.6        # 0-1
    is_proxy: bool = False
    failure_conditions: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    computed_at: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def stamp_evidence(
    meta: Dict[str, Any],
    *,
    conclusion: str,
    method: str,
    method_version: Optional[str] = None,
    indicators: Optional[Dict[str, Any]] = None,
    confidence: float = 0.6,
    is_proxy: Optional[bool] = None,
    failure_conditions: Optional[List[str]] = None,
    risks: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Convenience helper that reads provenance from ``meta``."""
    ev = Evidence(
        conclusion=conclusion,
        method=method,
        method_version=method_version or str(meta.get("calculation_method_version", "v0")),
        source_name=str(meta.get("source_name", "unknown")),
        source_tier=str(meta.get("source_tier", "fallback_demo")),
        truth_grade=str(meta.get("truth_grade", "E")),
        universe=str(meta.get("coverage_universe", "unknown")),
        indicators=indicators or {},
        confidence=float(confidence),
        is_proxy=bool(meta.get("is_proxy", False)) if is_proxy is None else is_proxy,
        failure_conditions=failure_conditions or [],
        risks=risks or [],
    )
    return ev.to_dict()
