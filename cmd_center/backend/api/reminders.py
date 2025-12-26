"""API endpoints for Reminder management."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..models.reminder_models import (
    ReminderCreate,
    ReminderUpdate,
    ReminderResponse,
    ReminderListResponse,
    ReminderFilters,
)
from ..services.reminder_service import ReminderService

router = APIRouter()


@router.get("", response_model=ReminderListResponse)
def list_reminders(
    target_type: Optional[str] = Query(None, description="Filter by target type"),
    target_id: Optional[int] = Query(None, description="Filter by target ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    channel: Optional[str] = Query(None, description="Filter by channel"),
    from_date: Optional[datetime] = Query(None, description="Filter from date"),
    to_date: Optional[datetime] = Query(None, description="Filter to date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> ReminderListResponse:
    """List reminders with optional filters."""
    filters = ReminderFilters(
        target_type=target_type,
        target_id=target_id,
        status=status,
        channel=channel,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
    service = ReminderService()
    return service.get_reminders(filters)


@router.get("/pending", response_model=list[ReminderResponse])
def list_pending_reminders(
    before: Optional[datetime] = Query(None, description="Get reminders due before this time"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of reminders"),
) -> list[ReminderResponse]:
    """List pending reminders due for processing."""
    service = ReminderService()
    return service.get_pending_reminders(before=before, limit=limit)


@router.get("/{reminder_id}", response_model=ReminderResponse)
def get_reminder(reminder_id: int) -> ReminderResponse:
    """Get a single reminder by ID."""
    service = ReminderService()
    reminder = service.get_reminder_by_id(reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder


@router.post("", response_model=ReminderResponse, status_code=201)
def create_reminder(
    data: ReminderCreate,
    actor: Optional[str] = Query("system", description="Who is creating the reminder"),
) -> ReminderResponse:
    """Create a new reminder."""
    service = ReminderService()
    return service.create_reminder(data, actor=actor)


@router.put("/{reminder_id}", response_model=ReminderResponse)
def update_reminder(
    reminder_id: int,
    data: ReminderUpdate,
    actor: Optional[str] = Query("system", description="Who is updating"),
) -> ReminderResponse:
    """Update a pending reminder."""
    service = ReminderService()
    reminder = service.update_reminder(reminder_id, data, actor=actor)
    if not reminder:
        raise HTTPException(
            status_code=404,
            detail="Reminder not found or cannot be updated (only pending reminders can be updated)"
        )
    return reminder


@router.post("/{reminder_id}/dismiss", response_model=ReminderResponse)
def dismiss_reminder(
    reminder_id: int,
    actor: Optional[str] = Query("system", description="Who is dismissing"),
) -> ReminderResponse:
    """Dismiss a pending reminder."""
    service = ReminderService()
    reminder = service.dismiss_reminder(reminder_id, actor=actor)
    if not reminder:
        raise HTTPException(
            status_code=404,
            detail="Reminder not found or cannot be dismissed (only pending reminders can be dismissed)"
        )
    return reminder


@router.delete("/{reminder_id}", status_code=204)
def cancel_reminder(
    reminder_id: int,
    actor: Optional[str] = Query("system", description="Who is cancelling"),
) -> None:
    """Cancel a pending reminder."""
    service = ReminderService()
    if not service.cancel_reminder(reminder_id, actor=actor):
        raise HTTPException(
            status_code=404,
            detail="Reminder not found or cannot be cancelled (only pending reminders can be cancelled)"
        )


@router.get("/target/{target_type}/{target_id}", response_model=list[ReminderResponse])
def get_reminders_for_target(
    target_type: str,
    target_id: int,
    status: Optional[str] = Query(None, description="Filter by status"),
) -> list[ReminderResponse]:
    """Get all reminders for a specific target entity."""
    service = ReminderService()
    return service.get_reminders_for_target(target_type, target_id, status=status)


@router.delete("/target/{target_type}/{target_id}", status_code=200)
def cancel_reminders_for_target(
    target_type: str,
    target_id: int,
    actor: Optional[str] = Query("system", description="Who is cancelling"),
) -> dict:
    """Cancel all pending reminders for a target entity."""
    service = ReminderService()
    count = service.cancel_reminders_for_target(target_type, target_id, actor=actor)
    return {"cancelled": count}
