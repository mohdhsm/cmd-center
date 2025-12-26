"""Intervention (audit log) API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..services.intervention_service import get_intervention_service
from ..models.employee_models import (
    InterventionResponse,
    InterventionListResponse,
    InterventionFilters,
)

router = APIRouter()


@router.get("", response_model=InterventionListResponse)
async def list_interventions(
    actor: Optional[str] = Query(None, description="Filter by actor"),
    object_type: Optional[str] = Query(None, description="Filter by object type"),
    object_id: Optional[int] = Query(None, description="Filter by object ID"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    from_date: Optional[datetime] = Query(None, description="Filter from date"),
    to_date: Optional[datetime] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
):
    """List interventions with optional filters.

    Returns a paginated list of audit log entries.
    Interventions are read-only - they are created automatically
    by service operations.
    """
    service = get_intervention_service()
    filters = InterventionFilters(
        actor=actor,
        object_type=object_type,
        object_id=object_id,
        action_type=action_type,
        status=status,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
    return service.get_interventions(filters)


@router.get("/{intervention_id}", response_model=InterventionResponse)
async def get_intervention(intervention_id: int):
    """Get a single intervention by ID."""
    service = get_intervention_service()
    intervention = service.get_intervention_by_id(intervention_id)
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")
    return intervention


@router.get("/object/{object_type}/{object_id}", response_model=list[InterventionResponse])
async def get_interventions_for_object(
    object_type: str,
    object_id: int,
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
):
    """Get all interventions for a specific object.

    Useful for viewing the complete history of actions on an entity.
    For example: /interventions/object/employee/123
    """
    service = get_intervention_service()
    return service.get_interventions_for_object(object_type, object_id, limit)


@router.get("/actor/{actor}", response_model=list[InterventionResponse])
async def get_interventions_by_actor(
    actor: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
):
    """Get recent interventions by a specific actor.

    Shows what actions a specific user or system process has taken.
    """
    service = get_intervention_service()
    return service.get_recent_interventions_by_actor(actor, limit)
