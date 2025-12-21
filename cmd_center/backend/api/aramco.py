"""Aramco pipeline API endpoints."""

from fastapi import APIRouter, Query
from typing import List

from ..models import (
    OverdueDeal,
    StuckDeal,
    OrderReceivedAnalysis,
    ComplianceStatus,
    CashflowBucket,
    OverdueSummaryResponse,
    StuckSummaryResponse,
    OrderReceivedSummaryResponse,
)
from ..services import (
    get_deal_health_service,
    get_llm_analysis_service,
    get_cashflow_service,
    get_aramco_summary_service,
)

router = APIRouter()


@router.get("/overdue", response_model=List[OverdueDeal])
async def get_aramco_overdue_deals(min_days: int = Query(7, ge=1)):
    """Get overdue deals from Aramco pipeline."""
    service = get_deal_health_service()
    deals = service.get_overdue_deals("Aramco Projects", min_days=min_days)
    return deals


@router.get("/stuck", response_model=List[StuckDeal])
async def get_aramco_stuck_deals(min_days: int = Query(30, ge=1)):
    """Get stuck deals from Aramco pipeline."""
    service = get_deal_health_service()
    deals = service.get_stuck_deals("Aramco Projects", min_days=min_days)
    return deals


@router.get("/order_received", response_model=List[OrderReceivedAnalysis])
async def get_aramco_order_received(min_days: int = Query(30, ge=1)):
    """Get and analyze deals in 'Order received' stage."""
    service = get_deal_health_service()
    deals = service.get_order_received_deals("Aramco Projects")
    return deals


@router.get("/compliance", response_model=List[ComplianceStatus])
async def get_aramco_compliance():
    """Get compliance status for Aramco deals."""
   # service = get_llm_analysis_service()
   # deals = await service.analyze_compliance("Aramco Projects")
    deals = []
    return deals


@router.get("/cashflow_projection", response_model=List[CashflowBucket])
async def get_aramco_cashflow_projection(
    period_type: str = Query("week", regex="^(week|month)$"),
    periods_ahead: int = Query(12, ge=1, le=52),
):
    """Get cashflow projection for Aramco pipeline."""
#     service = get_cashflow_service()
    # buckets = await service.get_cashflow_projection(
        # "Aramco Projects",
        # period_type=period_type,
        # weeks_ahead=periods_ahead,
    # )
    buckets = []
    return buckets


# ============================================================================
# CEO RADAR SUMMARY ENDPOINTS
# ============================================================================

@router.get("/overdue_summary", response_model=OverdueSummaryResponse)
async def get_overdue_summary():
    """
    Get executive summary for overdue deals.

    Returns:
        OverdueSummaryResponse with snapshot, PM performance, and intervention list
    """
    service = get_aramco_summary_service()
    return service.generate_overdue_summary("Aramco Projects")


@router.get("/stuck_summary", response_model=StuckSummaryResponse)
async def get_stuck_summary():
    """
    Get executive summary for stuck deals.

    Returns:
        StuckSummaryResponse with snapshot, PM control, worst deals, and bottlenecks
    """
    service = get_aramco_summary_service()
    return service.generate_stuck_summary("Aramco Projects")


@router.get("/order_received_summary", response_model=OrderReceivedSummaryResponse)
async def get_order_received_summary():
    """
    Get executive summary for Order Received deals.

    Returns:
        OrderReceivedSummaryResponse with snapshot, PM acceleration, blockers, and fast wins
    """
    service = get_aramco_summary_service()
    return service.generate_order_received_summary("Aramco Projects")