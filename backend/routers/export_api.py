"""Export endpoints — async task-id pattern."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..analytics.portfolio import build_export_preview, portfolio_watermark, resolve_weights
from ..analytics.sentiment import build_overview as build_sentiment
from ..core.data_source import get_data_source
from ..core.envelope import ok
from ..core.snapshot_cache import hot_cache
from ..core.tasks import get_task_store
from ..core.user_store import get_user_store


router = APIRouter()


class ExportRequest(BaseModel):
    page: str
    portfolio_id: Optional[str] = "pf_default"
    formats: Optional[List[str]] = None
    market_view: Optional[str] = None


def _sentiment_snapshot(market_view: str) -> Optional[Dict[str, Any]]:
    adapter = get_data_source()
    key = f"sentiment:{market_view}:20D:{adapter.name}"

    def rebuild():
        payload, src_meta, ev_count = build_sentiment(adapter, "20D", market_view)
        src_meta["evidence_count"] = ev_count
        return payload, src_meta

    try:
        payload, _, _ = hot_cache().get(key, ttl=60.0, rebuild=rebuild)
        return payload
    except Exception:  # noqa: BLE001
        return None


@router.post("/page")
async def export_page(req: ExportRequest) -> Dict[str, Any]:
    """Queue an export job. Returns ``task_id`` for polling."""
    adapter = get_data_source()
    store = get_task_store()
    user = get_user_store().get()
    formats = req.formats or user.preferences.get("default_export_format") or ["JSON", "Markdown"]
    market_view = req.market_view or user.preferences.get("market_view") or "cn_a"

    watermark: Optional[str] = None
    if req.portfolio_id:
        _, weights = resolve_weights(adapter, req.portfolio_id)
        watermark = portfolio_watermark(req.portfolio_id, weights)

    async def worker(task) -> Dict[str, Any]:
        task.message = "准备导出数据"
        task.progress = 0.15
        await asyncio.sleep(0.02)
        preview = None
        if req.page == "portfolio" and req.portfolio_id:
            sent = _sentiment_snapshot(market_view)
            preview = build_export_preview(adapter, req.portfolio_id, sentiment_snapshot=sent)
        task.message = "打包格式"
        task.progress = 0.7
        await asyncio.sleep(0.02)
        suffix = watermark or "global"
        filename = f"{req.page}-{req.portfolio_id or 'global'}-{suffix}.zip"
        return {
            "page": req.page,
            "portfolio_id": req.portfolio_id,
            "formats": formats,
            "preview": preview,
            "watermark": watermark,
            "download_link": f"/api/v1/tasks/downloads/{filename}",
            "note": "演示环境：下载链接为占位符，生产部署需接入对象存储。",
        }

    task = await store.run(
        "export-page", worker,
        watermark=watermark,
        watermark_context={"portfolio_id": req.portfolio_id, "page": req.page},
    )
    meta = adapter.meta(universe="export").to_dict()
    return ok({"task_id": task.id, "watermark": watermark}, meta=meta)


@router.get("/history")
async def export_history() -> Dict[str, Any]:
    adapter = get_data_source()
    store = get_task_store()
    tasks = [t.public() for t in store.list(kind="export-page")]
    return ok(tasks, meta=adapter.meta(universe="export").to_dict())
