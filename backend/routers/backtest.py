"""Backtest endpoints — walk-forward base engine."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..analytics.backtest import BacktestConfig, backtest_portfolio
from ..analytics.portfolio import portfolio_watermark, resolve_weights
from ..core.data_source import get_data_source
from ..core.envelope import ok
from ..core.snapshot_cache import warm_cache
from ..core.tasks import get_task_store


router = APIRouter()


class BacktestRequest(BaseModel):
    portfolio_id: str = "pf_default"
    start: Optional[str] = None
    end: Optional[str] = None
    rebalance: str = Field("M", pattern="^(D|W|M|Q)$")
    transaction_cost_bps: float = Field(8.0, ge=0.0, le=200.0)
    slippage_bps: float = Field(3.0, ge=0.0, le=200.0)
    benchmark_symbol: Optional[str] = "000300.SS"
    async_mode: bool = True


@router.post("/run")
async def run_backtest(req: BacktestRequest) -> Dict[str, Any]:
    adapter = get_data_source()
    _, weights = resolve_weights(adapter, req.portfolio_id)
    watermark = portfolio_watermark(req.portfolio_id, weights)

    cfg = BacktestConfig(
        start=req.start, end=req.end, rebalance=req.rebalance,
        transaction_cost_bps=req.transaction_cost_bps, slippage_bps=req.slippage_bps,
        benchmark_symbol=req.benchmark_symbol,
    )
    cache_key = f"backtest:{req.portfolio_id}:{watermark}:{cfg.cache_key()}"

    def rebuild():
        result, src = backtest_portfolio(adapter, req.portfolio_id, cfg=cfg)
        return result, src

    if not req.async_mode:
        result, meta, _ = warm_cache().get(cache_key, ttl=900.0, rebuild=rebuild)
        return ok({"result": result, "watermark": watermark}, meta=meta)

    store = get_task_store()

    async def worker(task) -> Dict[str, Any]:
        task.message = "加载代理净值序列"
        task.progress = 0.2
        await asyncio.sleep(0.02)
        result, _, _ = warm_cache().get(cache_key, ttl=900.0, rebuild=rebuild)
        task.message = "滚动再平衡完成"
        task.progress = 0.9
        await asyncio.sleep(0.02)
        return {"result": result, "watermark": watermark}

    task = await store.run(
        "backtest", worker,
        watermark=watermark,
        watermark_context={"portfolio_id": req.portfolio_id, "cache_key": cache_key},
    )
    return ok({"task_id": task.id, "watermark": watermark}, meta=adapter.meta(universe="backtest").to_dict())


@router.get("/config/defaults")
async def config_defaults() -> Dict[str, Any]:
    adapter = get_data_source()
    return ok(
        {
            "rebalance_options": [
                {"id": "D", "label": "每日"},
                {"id": "W", "label": "每周"},
                {"id": "M", "label": "每月"},
                {"id": "Q", "label": "每季度"},
            ],
            "transaction_cost_bps": 8.0,
            "slippage_bps": 3.0,
            "benchmark_symbol": "000300.SS",
            "caveat": "回测基于基金代理指数，非真实净值；结果仅作相对比较与回归保护。",
        },
        meta=adapter.meta(universe="backtest").to_dict(),
    )
