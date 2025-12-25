"""Aramco pipeline API endpoints."""

from fastapi import APIRouter, Query
from typing import List

from ..models import (
    OverdueDeal,
    StuckDeal,
    OrderReceivedAnalysis,
    ComplianceStatus,
    CashflowBucket,
    CashflowPredictionInput,
    DealPrediction,
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
from ..services.cashflow_prediction_service import get_cashflow_prediction_service

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
    period_type: str = Query("week", pattern="^(week|month)$"),
    horizon_days: int = Query(90, ge=7, le=365),
):
    """Get LLM-powered cashflow projection for Aramco pipeline."""
    service = get_cashflow_prediction_service()
    result = await service.predict_cashflow(CashflowPredictionInput(
        pipeline_name="Aramco Projects",
        horizon_days=horizon_days,
        granularity=period_type,
    ))
    return result.aggregated_forecast


@router.get("/cashflow_critical_deals", response_model=List[DealPrediction])
async def get_aramco_cashflow_critical_deals(
    weeks_ahead: int = Query(2, ge=1, le=8),
):
    """Get deals predicted to invoice within the next N weeks.

    Returns deals with 50%+ confidence, sorted by predicted invoice date.
    """
    service = get_cashflow_prediction_service()
    result = await service.predict_cashflow(CashflowPredictionInput(
        pipeline_name="Aramco Projects",
        horizon_days=weeks_ahead * 7,
        granularity="week",
    ))

    # Filter to predictions with 50%+ confidence
    critical_deals = [
        pred for pred in result.per_deal_predictions
        if pred.predicted_invoice_date and pred.confidence >= 0.5
    ]

    # Sort by predicted invoice date (earliest first)
    critical_deals.sort(key=lambda x: x.predicted_invoice_date)

    return critical_deals


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