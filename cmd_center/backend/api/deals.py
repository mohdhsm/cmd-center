"""Deals API endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from ..models import DealBase, DealNote, DealStageHistory, StagePerformanceMetrics
from ..models import DealHealthContext, DealHealthResult
from ..services import get_deal_health_service, get_llm_analysis_service
from ..services.pipedrive_sync import sync_stage_history_for_deal
from ..services.writer_service import get_writer_service

# Stage name to code mapping
STAGE_NAME_TO_CODE = {
    "Order Received": "OR",
    "Approved": "APR",
    "Awaiting Payment": "AP",
    "Awaiting Site Readiness": "ASR",
    "Everything Ready": "ER",
    "Under Progress": "UP",
    "Underprogress": "UP",
    "Awaiting MDD": "MDD",
    "Awaiting GCC": "GCC",
    "Awaiting GR": "GR",
    "Invoice Issued": "INV",
}

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


@router.get("/{deal_id}/health-summary", response_model=DealHealthResult)
async def get_deal_health_summary(deal_id: int):
    """Get LLM-powered deal health analysis."""
    health_service = get_deal_health_service()
    writer_service = get_writer_service()

    # 1. Fetch deal details
    deal = health_service.get_deal_detail(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    # 2. Fetch notes
    notes = health_service.get_deal_notes(deal_id, limit=15)

    # 3. Fetch stage history
    stage_history_data = health_service.get_stage_history(deal_id)

    # 4. Calculate days_since_last_note
    days_since_last_note = None
    if notes:
        last_note_date = notes[0].date
        if last_note_date:
            days_since_last_note = (datetime.now(timezone.utc) - last_note_date).days

    # 5. Convert stage name to code
    stage_name = deal.stage or "Unknown"
    stage_code = STAGE_NAME_TO_CODE.get(stage_name, "UNK")

    # 6. Calculate days_in_stage from stage history
    days_in_stage = 0
    if stage_history_data and stage_history_data.transitions:
        # Find current stage in history (last transition)
        for t in reversed(stage_history_data.transitions):
            if t.stage_name == stage_name and t.entered_at:
                days_in_stage = (datetime.now(timezone.utc) - t.entered_at).days
                break

    # 7. Build stage history for context
    stage_history = []
    if stage_history_data and stage_history_data.transitions:
        for t in stage_history_data.transitions:
            stage_history.append({
                "stage_name": t.stage_name,
                "entered_at": t.entered_at.isoformat() if t.entered_at else None,
                "duration_hours": t.duration_hours or 0
            })

    # 8. Build notes for context
    notes_context = []
    for note in notes:
        notes_context.append({
            "date": note.date.isoformat() if note.date else "Unknown",
            "author": note.author or "Unknown",
            "content": note.content or ""
        })

    # 9. Build context
    context = DealHealthContext(
        deal_id=deal_id,
        deal_title=deal.title or f"Deal #{deal_id}",
        stage=stage_name,
        stage_code=stage_code,
        days_in_stage=days_in_stage,
        owner_name=deal.owner or "Unknown",
        value_sar=deal.value_sar,
        notes=notes_context,
        stage_history=stage_history,
        last_activity_date=notes[0].date if notes else None,
        days_since_last_note=days_since_last_note
    )

    # 10. Call writer service
    try:
        result = await writer_service.analyze_deal_health(context)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze deal health: {str(e)}"
        )