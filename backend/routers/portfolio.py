"""Portfolio endpoints (overview, diagnosis, export-pack)."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Path

from ..analytics.portfolio import build_diagnosis, build_export_preview, build_overview
from ..core.data_source import get_data_source
from ..core.envelope import ok
from ..core.tasks import get_task_store


router = APIRouter()


@router.get("/{portfolio_id}/overview")
async def portfolio_overview(portfolio_id: str = Path(...)) -> Dict[str, Any]:
    adapter = get_data_source()
    return ok(build_overview(adapter, portfolio_id), meta=adapter.meta())


@router.get("/{portfolio_id}/diagnosis")
async def portfolio_diagnosis(portfolio_id: str = Path(...)) -> Dict[str, Any]:
    adapter = get_data_source()
    return ok(build_diagnosis(adapter, portfolio_id), meta=adapter.meta())


@router.get("/{portfolio_id}/export-pack")
async def portfolio_export_pack(
    portfolio_id: str = Path(...),
    formats: Optional[List[str]] = None,  # noqa: ARG001 — reserved for future filtering
) -> Dict[str, Any]:
    adapter = get_data_source()
    return ok(build_export_preview(adapter, portfolio_id), meta=adapter.meta())


@router.post("/{portfolio_id}/export-pack/run")
async def portfolio_export_pack_run(
    portfolio_id: str = Path(...),
    body: Dict[str, Any] = Body(default_factory=dict),
) -> Dict[str, Any]:
    """Submit an async export-pack task and return ``task_id``.

    The frontend polls ``/api/v1/tasks/{task_id}`` to watch progress. On
    success, ``result`` contains the same ``build_export_preview`` payload
    plus a deterministic synthetic download link that the UI can offer.
    """
    adapter = get_data_source()
    store = get_task_store()
    formats = body.get("formats") or ["JSON", "Markdown", "CSV"]

    async def worker(task) -> Dict[str, Any]:
        task.message = "正在聚合组合数据"
        task.progress = 0.15
        await asyncio.sleep(0.05)
        preview = build_export_preview(adapter, portfolio_id)
        task.message = "渲染导出文件"
        task.progress = 0.7
        await asyncio.sleep(0.05)
        filename = f"{portfolio_id}-export.zip"
        return {
            "preview": preview,
            "formats": formats,
            "download_link": f"/api/v1/tasks/downloads/{filename}",
            "portfolio_id": portfolio_id,
        }

    task = await store.run("portfolio-export", worker)
    return ok({"task_id": task.id}, meta=adapter.meta())
