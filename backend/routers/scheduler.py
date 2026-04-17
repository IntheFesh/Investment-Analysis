"""Scheduler inspection endpoints."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from ..core.calendar import is_trading_day, last_trading_day, recent_trading_days
from ..core.data_source import get_data_source
from ..core.envelope import ok
from ..core.scheduler import get_scheduler, register_default_jobs


router = APIRouter()


@router.get("/status")
async def status() -> Dict[str, Any]:
    adapter = get_data_source()
    sched = get_scheduler()
    jobs = [
        {
            "name": j.name,
            "region": j.region,
            "description": j.description,
            "depends_on": j.depends_on,
            "cache_namespaces": j.cache_namespaces,
        }
        for j in sched.jobs()
    ]
    runs = [
        {
            "name": r.name,
            "status": r.status,
            "last_run_at": r.last_run_at,
            "last_error": r.last_error,
            "duration_ms": r.duration_ms,
        }
        for r in sched.status()
    ]
    today = last_trading_day("CN")
    data = {
        "jobs": jobs,
        "runs": runs,
        "calendar": {
            "last_trading_day_cn": today.isoformat(),
            "is_trading_day_today_cn": is_trading_day(today),
            "recent_cn": [d.isoformat() for d in recent_trading_days(5, "CN")],
        },
        "note": "Scheduler 是骨架实现：生产部署需接入真实交易所日历与任务队列。",
    }
    return ok(data, meta=adapter.meta(universe="scheduler").to_dict())


@router.post("/tick")
async def tick(force: bool = False) -> Dict[str, Any]:
    """Manually advance the scheduler (demo / ops only)."""
    adapter = get_data_source()
    register_default_jobs()
    results = get_scheduler().tick(force=force)
    return ok(
        {
            "executed": [
                {"name": name, "status": run.status, "last_error": run.last_error, "duration_ms": run.duration_ms}
                for name, run in results.items()
            ],
            "forced": force,
        },
        meta=adapter.meta(universe="scheduler").to_dict(),
    )
