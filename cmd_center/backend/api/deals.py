"""Deals API endpoints."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from ..models import DealBase, DealNote
from ..services import get_deal_health_service, get_llm_analysis_service

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