"""API endpoints for employee log tracking."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ..models.employee_log_models import (
    LogEntryCreate,
    LogEntryResponse,
    LogEntryWithEmployee,
    LogEntryListResponse,
    LogEntryFilters,
)
from ..services.employee_log_service import get_employee_log_service

router = APIRouter(prefix="/employee-logs", tags=["employee-logs"])


@router.post("", response_model=LogEntryResponse, status_code=201)
def create_log_entry(data: LogEntryCreate) -> LogEntryResponse:
    """Create a new log entry for an employee."""
    service = get_employee_log_service()
    return service.create_log_entry(data)


@router.get("", response_model=LogEntryListResponse)
def list_log_entries(
    employee_id: Optional[int] = Query(None),
    category: Optional[str] = Query(None),
    is_positive: Optional[bool] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> LogEntryListResponse:
    """List log entries with filters."""
    service = get_employee_log_service()
    filters = LogEntryFilters(
        employee_id=employee_id,
        category=category,
        is_positive=is_positive,
        from_date=from_date,
        to_date=to_date,
        search=search,
        page=page,
        page_size=page_size,
    )
    return service.get_log_entries(filters)


@router.get("/issues", response_model=list[LogEntryWithEmployee])
def get_recent_issues(
    severity: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> list[LogEntryWithEmployee]:
    """Get recent issue logs with employee names."""
    service = get_employee_log_service()
    return service.get_recent_issues(severity=severity, limit=limit)


@router.get("/employee/{employee_id}", response_model=list[LogEntryResponse])
def get_logs_by_employee(
    employee_id: int,
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
) -> list[LogEntryResponse]:
    """Get log entries for a specific employee."""
    service = get_employee_log_service()
    return service.get_logs_by_employee(employee_id, category=category, limit=limit)


@router.get("/employee/{employee_id}/summary")
def get_employee_summary(employee_id: int) -> dict:
    """Get summary statistics for an employee's logs."""
    service = get_employee_log_service()
    return service.get_employee_summary(employee_id)


@router.get("/{log_id}", response_model=LogEntryWithEmployee)
def get_log_entry(log_id: int) -> LogEntryWithEmployee:
    """Get a log entry by ID with employee name."""
    service = get_employee_log_service()
    log_entry = service.get_log_entry_with_employee(log_id)
    if not log_entry:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return log_entry
