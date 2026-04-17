"""Task query endpoints used by the frontend to poll async jobs."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Path, Query

from ..core.data_source import get_data_source
from ..core.envelope import ok
from ..core.tasks import get_task_store


router = APIRouter()


@router.get("/")
async def list_tasks(kind: Optional[str] = Query(None)) -> Dict[str, Any]:
    adapter = get_data_source()
    store = get_task_store()
    return ok([t.public() for t in store.list(kind=kind)], meta=adapter.meta())


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
    return ok(task.public(), meta=adapter.meta())


@router.get("/downloads/{filename}")
async def task_download_placeholder(filename: str = Path(...)) -> Dict[str, Any]:
    """Synthetic download endpoint for the demo adapter.

    A real deployment would stream a file from object storage; here we
    acknowledge the request so the UI can demonstrate the full flow without
    pretending the file is real.
    """
    adapter = get_data_source()
    return ok(
        {
            "filename": filename,
            "note": "演示环境：未实际生成压缩包，真实部署时应由导出服务写入对象存储。",
        },
        meta=adapter.meta(),
    )
