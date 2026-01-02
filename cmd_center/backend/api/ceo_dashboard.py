"""CEO Dashboard API endpoints."""

from fastapi import APIRouter

from ..models import CEODashboardMetrics
from ..services import get_ceo_dashboard_service

router = APIRouter(prefix="/ceo-dashboard", tags=["ceo-dashboard"])


@router.get("/metrics", response_model=CEODashboardMetrics)
async def get_ceo_dashboard_metrics():
    """Get all CEO Dashboard metrics.

    Returns a comprehensive view of:
    - Cash health (runway, collections, velocity)
    - Urgent deals requiring attention
    - Pipeline velocity by stage
    - Strategic priority progress
    - Department scorecard (Sales MVP)
    """
    service = get_ceo_dashboard_service()
    return await service.get_dashboard_metrics()
