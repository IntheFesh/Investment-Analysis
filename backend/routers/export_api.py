"""Export endpoints — async task-id pattern."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..analytics.portfolio import build_export_preview
from ..core.data_source import get_data_source
from ..core.envelope import ok
from ..core.tasks import get_task_store


router = APIRouter()


class ExportRequest(BaseModel):
    page: str
    portfolio_id: str | None = "pf_default"
    formats: List[str] = Field(default_factory=lambda: ["JSON", "Markdown", "CSV", "PNG"])


@router.post("/page")
async def export_page(req: ExportRequest) -> Dict[str, Any]:
    """Queue an export job. Returns ``task_id`` for polling."""
    adapter = get_data_source()
    store = get_task_store()

    async def worker(task) -> Dict[str, Any]:
        task.message = "准备导出数据"
        task.progress = 0.15
        await asyncio.sleep(0.05)
        preview = None
        if req.page == "portfolio" and req.portfolio_id:
            preview = build_export_preview(adapter, req.portfolio_id)
        task.message = "打包格式"
        task.progress = 0.7
        await asyncio.sleep(0.05)
        filename = f"{req.page}-{req.portfolio_id or 'global'}.zip"
        return {
            "page": req.page,
            "portfolio_id": req.portfolio_id,
            "formats": req.formats,
            "preview": preview,
            "download_link": f"/api/v1/tasks/downloads/{filename}",
        }

    task = await store.run("export-page", worker)
    return ok({"task_id": task.id}, meta=adapter.meta())


@router.get("/history")
async def export_history() -> Dict[str, Any]:
    adapter = get_data_source()
    store = get_task_store()
    tasks = [t.public() for t in store.list(kind="export-page")]
    return ok(tasks, meta=adapter.meta())
