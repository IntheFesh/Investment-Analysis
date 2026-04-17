"""Simulation endpoints — three engines, sentiment-aware, watermark-tagged."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Literal, Optional, Union

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..analytics.portfolio import portfolio_watermark, resolve_weights
from ..analytics.sentiment import build_overview as build_sentiment
from ..analytics.simulation import (
    HISTORICAL_EVENTS,
    SCENARIO_PRESETS,
    historical_run,
    scenario_run,
    statistical_run,
)
from ..core.data_source import get_data_source
from ..core.envelope import ok
from ..core.snapshot_cache import hot_cache
from ..core.tasks import get_task_store


router = APIRouter()


class StatisticalRequest(BaseModel):
    mode: Literal["statistical"] = "statistical"
    portfolio_id: str = "pf_default"
    horizon_days: int = Field(60, ge=1, le=365)
    num_paths: int = Field(500, ge=50, le=5000)
    confidence_interval: float = Field(0.95, ge=0.5, le=0.995)
    bootstrap: bool = True
    market_view: str = "cn_a"
    use_sentiment_stress: bool = True


class ScenarioRequest(BaseModel):
    mode: Literal["scenario"] = "scenario"
    portfolio_id: str = "pf_default"
    scenario_ids: List[str] = Field(default_factory=list)
    market_view: str = "cn_a"
    use_sentiment_stress: bool = True


class HistoricalRequest(BaseModel):
    mode: Literal["historical"] = "historical"
    portfolio_id: str = "pf_default"
    event_id: str = Field(..., description=" | ".join(HISTORICAL_EVENTS.keys()))
    market_view: str = "cn_a"
    use_sentiment_stress: bool = False


_SIM_SENTIMENT_DEADLINE = 2.5


def _sentiment_stress(market_view: str) -> Optional[Dict[str, Any]]:
    """Best-effort stress parameters. Deadline-bounded so submission stays fast."""
    adapter = get_data_source()
    key = f"sentiment:{market_view}:20D:{adapter.name}"

    def rebuild():
        payload, src_meta, ev_count = build_sentiment(adapter, "20D", market_view)
        src_meta["evidence_count"] = ev_count
        return payload, src_meta

    try:
        payload, _, _ = hot_cache().get_with_deadline(
            key, ttl=60.0, deadline_seconds=_SIM_SENTIMENT_DEADLINE, rebuild=rebuild,
        )
        return payload.get("stress_parameters") if payload else None
    except Exception:  # noqa: BLE001
        return None


@router.post("/run")
async def run_simulation(
    request: Union[StatisticalRequest, ScenarioRequest, HistoricalRequest],
) -> Dict[str, Any]:
    adapter = get_data_source()
    store = get_task_store()

    _, weights = resolve_weights(adapter, request.portfolio_id)
    watermark = portfolio_watermark(request.portfolio_id, weights)

    async def worker(task) -> Dict[str, Any]:
        task.message = "读取组合数据"
        task.progress = 0.12
        # Sentiment lookup happens inside the worker so endpoint submission
        # never blocks on sentiment rebuild.
        stress = await asyncio.to_thread(
            _sentiment_stress, request.market_view,
        ) if getattr(request, "use_sentiment_stress", False) else None
        await asyncio.sleep(0.02)
        if isinstance(request, StatisticalRequest):
            task.message = "分块自助抽样"
            task.progress = 0.45
            result = statistical_run(
                adapter,
                request.portfolio_id,
                request.horizon_days,
                request.num_paths,
                request.confidence_interval,
                request.bootstrap,
                stress_parameters=stress,
            )
        elif isinstance(request, HistoricalRequest):
            task.message = "定位历史重演窗口"
            task.progress = 0.45
            result = historical_run(
                adapter, request.portfolio_id, request.event_id, stress_parameters=stress
            )
        else:
            task.message = "加载叙事情景冲击"
            task.progress = 0.45
            result = scenario_run(
                adapter, request.portfolio_id, request.scenario_ids, stress_parameters=stress
            )
        task.message = "汇总结果"
        task.progress = 0.85
        await asyncio.sleep(0.02)
        result["portfolio_watermark"] = watermark
        return result

    task = await store.run(
        "simulation", worker,
        watermark=watermark,
        watermark_context={"portfolio_id": request.portfolio_id, "holdings_hash": watermark, "mode": request.mode},
    )
    return ok({"task_id": task.id, "watermark": watermark}, meta=adapter.meta(universe="simulation").to_dict())


@router.get("/presets")
async def list_presets() -> Dict[str, Any]:
    adapter = get_data_source()
    return ok(
        [{"id": sid, "label": preset["label"], "factors": preset["factors"]} for sid, preset in SCENARIO_PRESETS.items()],
        meta=adapter.meta(universe="simulation").to_dict(),
    )


@router.get("/historical-events")
async def list_historical_events() -> Dict[str, Any]:
    adapter = get_data_source()
    return ok(
        [{"id": eid, "label": ev["label"], "description": ev["description"]} for eid, ev in HISTORICAL_EVENTS.items()],
        meta=adapter.meta(universe="simulation").to_dict(),
    )
