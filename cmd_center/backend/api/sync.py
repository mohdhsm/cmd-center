"""Sync API endpoints."""

from fastapi import APIRouter, HTTPException
from ..services.sync_scheduler import manual_sync_stages

router = APIRouter()


@router.post("/stages")
async def sync_stages():
    """Manually trigger stages sync."""
    try:
        result = await manual_sync_stages()
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))