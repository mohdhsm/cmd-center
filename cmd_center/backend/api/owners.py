"""Owner KPI API endpoints."""

from fastapi import APIRouter, Query
from typing import List

from ..models import OwnerKPI
from ..services import get_owner_kpi_service

router = APIRouter()


@router.get("/kpis", response_model=List[OwnerKPI])
async def get_owner_kpis(
    days_back: int = Query(30, ge=1),
    pipelines: List[str] = Query(None),
):
    """Get KPIs for all owners/salespeople."""
    service = get_owner_kpi_service()
    
    if not pipelines:
        pipelines = ["Aramco Projects", "pipeline"]
    
    kpis = await service.get_owner_kpis(
        pipeline_names=pipelines,
        days_back=days_back,
    )
    return kpis