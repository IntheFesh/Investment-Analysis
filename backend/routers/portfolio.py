"""Portfolio endpoints — sentiment-aware, watermark-tagged, settings-aware."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Path, Query

from ..analytics.portfolio import (
    build_diagnosis,
    build_export_preview,
    build_overview,
    portfolio_watermark,
    resolve_weights,
)
from ..analytics.sentiment import build_overview as build_sentiment
from ..core.data_source import get_data_source
from ..core.envelope import ok
from ..core.snapshot_cache import hot_cache
from ..core.tasks import get_task_store
from ..core.user_store import get_user_store


router = APIRouter()


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


@router.get("/{portfolio_id}/overview")
async def portfolio_overview(portfolio_id: str = Path(...)) -> Dict[str, Any]:
    adapter = get_data_source()
    payload, meta, _ = build_overview(adapter, portfolio_id)
    return ok(payload, meta=meta)


@router.get("/{portfolio_id}/diagnosis")
async def portfolio_diagnosis(
    portfolio_id: str = Path(...),
    market_view: str = Query("cn_a"),
) -> Dict[str, Any]:
    adapter = get_data_source()
    sent = _sentiment_snapshot(market_view)
    payload, meta, _ = build_diagnosis(adapter, portfolio_id, sentiment_snapshot=sent)
    return ok(payload, meta=meta)


@router.get("/{portfolio_id}/export-pack")
async def portfolio_export_pack(
    portfolio_id: str = Path(...),
    market_view: str = Query("cn_a"),
    formats: Optional[List[str]] = None,  # noqa: ARG001 — reserved for future filtering
) -> Dict[str, Any]:
    adapter = get_data_source()
    sent = _sentiment_snapshot(market_view)
    preview = build_export_preview(adapter, portfolio_id, sentiment_snapshot=sent)
    meta = adapter.meta(universe="portfolio").to_dict()
    meta["calculation_method_version"] = "pf.v2"
    return ok(preview, meta=meta)


@router.post("/{portfolio_id}/export-pack/run")
async def portfolio_export_pack_run(
    portfolio_id: str = Path(...),
    body: Dict[str, Any] = Body(default_factory=dict),
) -> Dict[str, Any]:
    adapter = get_data_source()
    store = get_task_store()

    user = get_user_store().get()
    formats = body.get("formats") or user.preferences.get("default_export_format") or ["JSON", "Markdown", "CSV"]
    market_view = body.get("market_view") or user.preferences.get("market_view") or "cn_a"

    _, weights = resolve_weights(adapter, portfolio_id)
    watermark = portfolio_watermark(portfolio_id, weights)

    async def worker(task) -> Dict[str, Any]:
        task.message = "聚合组合数据"
        task.progress = 0.15
        await asyncio.sleep(0.02)
        sent = _sentiment_snapshot(market_view)
        task.message = "生成导出文件"
        task.progress = 0.65
        preview = build_export_preview(adapter, portfolio_id, sentiment_snapshot=sent)
        await asyncio.sleep(0.02)
        filename = f"{portfolio_id}-{watermark}.zip"
        return {
            "preview": preview,
            "formats": formats,
            "download_link": f"/api/v1/tasks/downloads/{filename}",
            "portfolio_id": portfolio_id,
            "watermark": watermark,
            "note": "演示环境：下载链接为占位符，生产部署需接入对象存储。",
        }

    task = await store.run(
        "portfolio-export", worker,
        watermark=watermark,
        watermark_context={"portfolio_id": portfolio_id, "holdings_hash": watermark},
    )
    meta = adapter.meta(universe="portfolio").to_dict()
    return ok({"task_id": task.id, "watermark": watermark}, meta=meta)
