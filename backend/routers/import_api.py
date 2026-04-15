"""
Import router: endpoints for importing portfolio data via different methods.

This router exposes endpoints for uploading screenshots or CSV files and
confirming the imported data.  The placeholder implementation returns
simplified preview data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ScreenshotImportRequest(BaseModel):
    images: List[str]  # In a real API this would be file uploads


class CsvImportRequest(BaseModel):
    csv_data: str  # In a real API this would be a file upload; here we accept CSV content


class ImportConfirmRequest(BaseModel):
    funds: List[Dict[str, Any]]
    total_cost: float


@router.post("/screenshot")
async def import_screenshot(req: ScreenshotImportRequest) -> Dict[str, Any]:
    """Extract portfolio holdings from uploaded screenshots (placeholder)."""
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    # Placeholder OCR result
    preview = [
        {"code": "000001", "name": "平安银行", "shares": 1000, "market_value": 12000.0},
        {"code": "005939", "name": "易方达中证海外互联ETF", "shares": 500, "market_value": 15000.0},
    ]
    return {
        "success": True,
        "message": "ok",
        "data": {"preview": preview},
        "meta": {"timestamp": timestamp, "version": "v1"},
    }


@router.post("/csv")
async def import_csv(req: CsvImportRequest) -> Dict[str, Any]:
    """Parse uploaded CSV file and return field mapping preview (placeholder)."""
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    # Parse CSV preview; here we return a static mapping
    preview = {
        "columns": ["code", "shares", "cost"],
        "rows": [
            {"code": "000001", "shares": 1000, "cost": 10000.0},
            {"code": "005939", "shares": 500, "cost": 8000.0},
        ],
    }
    return {
        "success": True,
        "message": "ok",
        "data": {"preview": preview},
        "meta": {"timestamp": timestamp, "version": "v1"},
    }


@router.post("/confirm")
async def import_confirm(req: ImportConfirmRequest) -> Dict[str, Any]:
    """Confirm imported data and create a new portfolio (placeholder)."""
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    # In a real implementation, this would persist the data and return a new portfolio ID
    portfolio_id = "pf_" + datetime.now().strftime("%Y%m%d%H%M%S")
    return {
        "success": True,
        "message": "ok",
        "data": {"portfolio_id": portfolio_id},
        "meta": {"timestamp": timestamp, "version": "v1"},
    }