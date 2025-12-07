"""Dashboard API endpoints."""

from fastapi import APIRouter
from typing import List

from ..models import DashboardItem
from ..services import get_dashboard_service

router = APIRouter()


@router.get("/today", response_model=List[DashboardItem])
async def get_dashboard_today():
    """Get today's focus dashboard items."""
    service = get_dashboard_service()
    items = await service.get_dashboard_items()
    return items