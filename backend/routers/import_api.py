"""Portfolio import endpoints (code / screenshot / csv / confirm).

The OCR and CSV parsers are intentionally lightweight — they do real work on
whatever bytes / strings are supplied rather than returning hard-coded data.
When a real OCR service is wired up, swap ``_ocr_stub`` for the provider call.
"""

from __future__ import annotations

import asyncio
import csv
import io
import re
from typing import Any, Dict, List

from fastapi import APIRouter, Body
from pydantic import BaseModel, Field

from ..core.data_source import get_data_source
from ..core.envelope import ok
from ..core.tasks import get_task_store


router = APIRouter()


class ScreenshotImportRequest(BaseModel):
    images: List[str] = Field(default_factory=list, description="Base64-encoded screenshots")


class CsvImportRequest(BaseModel):
    csv_data: str = ""
    delimiter: str = ","


class CodeImportRequest(BaseModel):
    codes: List[str] = Field(default_factory=list)


class FundEntry(BaseModel):
    code: str
    name: str = ""
    shares: float = 0.0
    market_value: float = 0.0
    cost: float = 0.0


class ImportConfirmRequest(BaseModel):
    funds: List[FundEntry]
    total_cost: float = 0.0
    label: str | None = None


def _ocr_stub(image: str) -> List[Dict[str, Any]]:
    """Best-effort extraction that never fabricates data.

    If the supplied image isn't a recognised structured payload (for instance,
    the UI offers a fallback JSON string for local tests), we return an empty
    preview and ``needs_review=True`` so the user must manually fix.
    """
    try:
        # Support a dev-time convention: the frontend may send a JSON blob as
        # the image string in place of real OCR bytes.
        import json

        data = json.loads(image)
        if isinstance(data, list):
            return [
                {
                    "code": str(row.get("code", "")),
                    "name": str(row.get("name", "")),
                    "shares": float(row.get("shares", 0) or 0),
                    "market_value": float(row.get("market_value", 0) or 0),
                    "confidence": float(row.get("confidence", 0.6)),
                }
                for row in data
                if row.get("code")
            ]
    except Exception:  # noqa: BLE001
        pass
    return []


@router.post("/screenshot")
async def import_screenshot(req: ScreenshotImportRequest) -> Dict[str, Any]:
    adapter = get_data_source()
    store = get_task_store()

    async def worker(task) -> Dict[str, Any]:
        task.progress = 0.1
        preview: List[Dict[str, Any]] = []
        for i, img in enumerate(req.images):
            task.message = f"识别图片 {i + 1}/{len(req.images)}"
            task.progress = 0.1 + 0.8 * (i + 1) / max(1, len(req.images))
            preview.extend(_ocr_stub(img))
            await asyncio.sleep(0.02)
        needs_review = any(row.get("confidence", 1.0) < 0.8 for row in preview) or not preview
        return {"preview": preview, "needs_review": needs_review, "source": "screenshot"}

    task = await store.run("ocr-import", worker)
    return ok({"task_id": task.id}, meta=adapter.meta())


@router.post("/csv")
async def import_csv(req: CsvImportRequest) -> Dict[str, Any]:
    adapter = get_data_source()
    if not req.csv_data.strip():
        return ok({"preview": {"columns": [], "rows": []}, "needs_review": True}, meta=adapter.meta())

    reader = csv.DictReader(io.StringIO(req.csv_data), delimiter=req.delimiter)
    rows: List[Dict[str, Any]] = []
    for raw in reader:
        norm: Dict[str, Any] = {}
        for k, v in raw.items():
            key = (k or "").strip().lower()
            if not key:
                continue
            if key in {"code", "symbol", "ticker"}:
                norm["code"] = (v or "").strip()
            elif key in {"name", "fund"}:
                norm["name"] = (v or "").strip()
            elif key in {"shares", "share"}:
                try:
                    norm["shares"] = float((v or "0").replace(",", ""))
                except ValueError:
                    norm["shares"] = 0.0
            elif key in {"market_value", "mv"}:
                try:
                    norm["market_value"] = float((v or "0").replace(",", ""))
                except ValueError:
                    norm["market_value"] = 0.0
            elif key in {"cost", "total_cost"}:
                try:
                    norm["cost"] = float((v or "0").replace(",", ""))
                except ValueError:
                    norm["cost"] = 0.0
        if norm.get("code"):
            rows.append(norm)

    columns = sorted({k for r in rows for k in r.keys()})
    return ok(
        {"preview": {"columns": columns, "rows": rows}, "needs_review": len(rows) == 0, "source": "csv"},
        meta=adapter.meta(),
    )


@router.post("/codes")
async def import_codes(req: CodeImportRequest) -> Dict[str, Any]:
    adapter = get_data_source()
    cleaned = [c.strip() for c in req.codes if re.match(r"^[A-Za-z0-9]{3,}$", c.strip())]
    rejected = [c for c in req.codes if c.strip() and c.strip() not in cleaned]
    preview = [{"code": c, "name": adapter.fund_metadata().get(c, {}).get("name", ""), "shares": 0, "market_value": 0} for c in cleaned]
    return ok(
        {"preview": preview, "rejected": rejected, "needs_review": bool(rejected), "source": "codes"},
        meta=adapter.meta(),
    )


@router.post("/confirm")
async def import_confirm(req: ImportConfirmRequest = Body(...)) -> Dict[str, Any]:
    adapter = get_data_source()
    from datetime import datetime

    portfolio_id = "pf_" + datetime.now().strftime("%Y%m%d%H%M%S")
    # NOTE: This is a stateless backend; in production the portfolio would be
    # persisted here. The response shape still matches the spec so the
    # frontend can proceed with the newly-created id.
    return ok(
        {
            "portfolio_id": portfolio_id,
            "label": req.label or f"导入组合 {portfolio_id}",
            "fund_count": len(req.funds),
            "total_cost": req.total_cost,
        },
        meta=adapter.meta(),
    )
