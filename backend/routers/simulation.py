"""Simulation endpoints — returns a ``task_id`` per the product spec."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Literal, Union

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..analytics.simulation import SCENARIO_PRESETS, scenario_run, statistical_run
from ..core.data_source import get_data_source
from ..core.envelope import ok
from ..core.tasks import get_task_store


router = APIRouter()


class StatisticalRequest(BaseModel):
    mode: Literal["statistical"] = "statistical"
    portfolio_id: str = "pf_default"
    horizon_days: int = Field(60, ge=1, le=365)
    num_paths: int = Field(500, ge=50, le=5000)
    confidence_interval: float = Field(0.95, ge=0.5, le=0.995)
    bootstrap: bool = False


class ScenarioRequest(BaseModel):
    mode: Literal["scenario"] = "scenario"
    portfolio_id: str = "pf_default"
    scenario_ids: List[str] = Field(default_factory=list)


@router.post("/run")
async def run_simulation(
    request: Union[StatisticalRequest, ScenarioRequest],
) -> Dict[str, Any]:
    """Submit a simulation and return ``task_id``."""
    adapter = get_data_source()
    store = get_task_store()

    async def worker(task) -> Dict[str, Any]:
        task.message = "读取组合数据"
        task.progress = 0.1
        await asyncio.sleep(0.05)
        if isinstance(request, StatisticalRequest):
            task.message = "运行蒙特卡洛抽样"
            task.progress = 0.4
            result = statistical_run(
                adapter,
                request.portfolio_id,
                request.horizon_days,
                request.num_paths,
                request.confidence_interval,
                request.bootstrap,
            )
        else:
            task.message = "加载情景冲击配置"
            task.progress = 0.4
            result = scenario_run(adapter, request.portfolio_id, request.scenario_ids)
        task.message = "汇总结果"
        task.progress = 0.85
        await asyncio.sleep(0.05)
        return result

    task = await store.run("simulation", worker)
    return ok({"task_id": task.id}, meta=adapter.meta())


@router.get("/presets")
async def list_presets() -> Dict[str, Any]:
    adapter = get_data_source()
    return ok(
        [{"id": sid, "label": preset["label"]} for sid, preset in SCENARIO_PRESETS.items()],
        meta=adapter.meta(),
    )
