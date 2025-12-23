"""Deals API endpoints."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from ..models import DealBase, DealNote, DealStageHistory, StagePerformanceMetrics
from ..services import get_deal_health_service, get_llm_analysis_service
from ..services.pipedrive_sync import sync_stage_history_for_deal

router = APIRouter()


@router.get("/{deal_id}/detail", response_model=DealBase)
async def get_deal_detail(deal_id: int):
    """Get detailed information for a single deal."""
    service = get_deal_health_service()
    deal = service.get_deal_detail(deal_id)

    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    return deal


@router.get("/{deal_id}/notes", response_model=List[DealNote])
async def get_deal_notes(deal_id: int, limit: int = Query(10, ge=1, le=100)):
    """Get notes for a specific deal."""
    service = get_deal_health_service()
    notes = service.get_deal_notes(deal_id, limit)
    return notes


@router.get("/{deal_id}/stage-history", response_model=DealStageHistory)
async def get_deal_stage_history(deal_id: int):
    """Get complete stage transition history for a deal."""
    service = get_deal_health_service()
    history = service.get_stage_history(deal_id)

    if not history:
        raise HTTPException(
            status_code=404,
            detail="Deal not found or no stage history available"
        )

    return history


@router.post("/{deal_id}/sync-stage-history")
async def sync_deal_stage_history(deal_id: int):
    """Manually trigger stage history sync for a specific deal."""
    try:
        result = await sync_stage_history_for_deal(deal_id)
        return {
            "success": True,
            "deal_id": deal_id,
            "events_synced": result.get("events_synced", 0),
            "spans_created": result.get("spans_created", 0),
            "spans_updated": result.get("spans_updated", 0)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync stage history: {str(e)}"
        )


@router.get("/stages/{stage_id}/performance", response_model=StagePerformanceMetrics)
async def get_stage_performance_metrics(
    stage_id: int,
    days: int = Query(90, ge=1, le=365),
    stuck_threshold_hours: int = Query(168, ge=1)
):
    """Get performance metrics for a specific stage."""
    service = get_deal_health_service()
    metrics = service.get_stage_performance(stage_id, days, stuck_threshold_hours)

    if not metrics:
        raise HTTPException(status_code=404, detail="Stage not found")

    return metrics