"""Task query endpoints. Support watermark-staleness reporting."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Path, Query

from ..analytics.portfolio import portfolio_watermark, resolve_weights
from ..core.data_source import get_data_source
from ..core.envelope import ok
from ..core.tasks import get_task_store


router = APIRouter()


def _current_watermark_for(kind: str, portfolio_id: Optional[str]) -> Optional[str]:
    if kind in ("simulation", "portfolio-export") and portfolio_id:
        adapter = get_data_source()
        _, weights = resolve_weights(adapter, portfolio_id)
        return portfolio_watermark(portfolio_id, weights)
    return None


@router.get("/")
async def list_tasks(kind: Optional[str] = Query(None)) -> Dict[str, Any]:
    adapter = get_data_source()
    store = get_task_store()
    items = []
    for t in store.list(kind=kind):
        cur = _current_watermark_for(t.kind, t.watermark_context.get("portfolio_id") if t.watermark_context else None)
        items.append(t.public(current_watermark=cur))
    return ok(items, meta=adapter.meta(universe="tasks").to_dict())


@router.get("/{task_id}")
async def get_task(task_id: str = Path(...)) -> Dict[str, Any]:
    adapter = get_data_source()
    store = get_task_store()
    task = store.get(task_id)
    if task is None:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error_code": "TASK_NOT_FOUND",
                "message": f"任务 {task_id} 不存在或已过期",
                "data": None,
            },
        )
    cur = _current_watermark_for(task.kind, task.watermark_context.get("portfolio_id") if task.watermark_context else None)
    return ok(task.public(current_watermark=cur), meta=adapter.meta(universe="tasks").to_dict())


@router.get("/downloads/{filename}")
async def task_download_placeholder(filename: str = Path(...)) -> Dict[str, Any]:
    adapter = get_data_source()
    return ok(
        {
            "filename": filename,
            "note": "演示环境：未实际生成压缩包，真实部署应由导出服务写入对象存储。",
        },
        meta=adapter.meta(universe="tasks").to_dict(),
    )
