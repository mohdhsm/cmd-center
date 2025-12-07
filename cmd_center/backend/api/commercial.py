"""Commercial pipeline API endpoints."""

from fastapi import APIRouter, Query
from typing import List

from ..models import StuckDeal, DealSummary
from ..services import get_deal_health_service, get_llm_analysis_service

router = APIRouter()


@router.get("/inactive", response_model=List[StuckDeal])
async def get_commercial_inactive_deals(min_days: int = Query(60, ge=1)):
    """Get inactive deals from commercial pipeline (no movement for 60+ days)."""
    service = get_deal_health_service()
    deals = await service.get_stuck_deals("pipeline", min_days=min_days)
    return deals


@router.get("/recent_summary", response_model=List[DealSummary])
async def get_commercial_recent_summary(days_back: int = Query(14, ge=1)):
    """Get LLM summaries of recently active commercial deals."""
    service = get_llm_analysis_service()
    deals = await service.summarize_recent_deals("pipeline", days=days_back)
    return deals