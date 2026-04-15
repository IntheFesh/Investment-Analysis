"""
Export router: endpoints to generate export packages for pages or portfolios.

The export endpoint triggers a background job to assemble files such as JSON,
Markdown, CSV and PNG images.  Here we return a placeholder download link.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ExportRequest(BaseModel):
    page: str
    portfolio_id: str | None = None
    formats: List[str] = ["JSON", "Markdown", "CSV", "PNG"]


@router.post("/page")
async def export_page(req: ExportRequest) -> Dict[str, Any]:
    """Generate an export package for a given page and return a download link.

    In this placeholder implementation we synchronously return a fake link.
    """
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    download_link = f"https://example.com/downloads/{req.page}-{req.portfolio_id or 'global'}.zip"
    return {
        "success": True,
        "message": "ok",
        "data": {"task_id": "task123", "download_link": download_link},
        "meta": {"timestamp": timestamp, "version": "v1"},
    }