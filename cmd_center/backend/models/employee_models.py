"""Employee and Intervention Pydantic models for API contracts."""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# ============================================================================
# Employee Models
# ============================================================================

class EmployeeBase(BaseModel):
    """Base employee model with shared fields."""

    full_name: str = Field(..., min_length=1, max_length=200)
    role_title: str = Field(..., min_length=1, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)


class EmployeeCreate(EmployeeBase):
    """Request model for creating an employee."""

    reports_to_employee_id: Optional[int] = None
    pipedrive_owner_id: Optional[int] = None


class EmployeeUpdate(BaseModel):
    """Request model for updating an employee (all fields optional)."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    role_title: Optional[str] = Field(None, min_length=1, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    reports_to_employee_id: Optional[int] = None
    pipedrive_owner_id: Optional[int] = None
    is_active: Optional[bool] = None


class EmployeeResponse(EmployeeBase):
    """Response model for employee data."""

    id: int
    reports_to_employee_id: Optional[int] = None
    is_active: bool = True
    pipedrive_owner_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EmployeeWithAggregates(EmployeeResponse):
    """Employee response with computed aggregates."""

    # Manager info
    reports_to_name: Optional[str] = None

    # Deal counts (via pipedrive_owner_id)
    open_deals_count: int = 0
    open_deals_value: float = 0.0

    # Task/note counts (via target_type=employee)
    open_tasks_count: int = 0
    notes_count: int = 0
    pending_reminders_count: int = 0

    # Last intervention
    last_intervention_at: Optional[datetime] = None


class EmployeeListResponse(BaseModel):
    """Paginated list of employees."""

    items: list[EmployeeResponse]
    total: int
    page: int = 1
    page_size: int = 50


# ============================================================================
# Intervention Models
# ============================================================================

class InterventionBase(BaseModel):
    """Base intervention model."""

    actor: str = Field(..., min_length=1, max_length=200)
    object_type: str = Field(..., min_length=1, max_length=50)
    object_id: int
    action_type: str = Field(..., min_length=1, max_length=50)
    summary: str = Field(..., min_length=1)
    status: str = Field(default="done", pattern="^(done|failed|planned)$")
    details: Optional[dict[str, Any]] = None


class InterventionCreate(InterventionBase):
    """Request model for creating an intervention (internal use)."""
    pass


class InterventionResponse(InterventionBase):
    """Response model for intervention data."""

    id: int
    created_at: datetime
    details_json: Optional[str] = None

    class Config:
        from_attributes = True


class InterventionListResponse(BaseModel):
    """Paginated list of interventions."""

    items: list[InterventionResponse]
    total: int
    page: int = 1
    page_size: int = 50


# ============================================================================
# Filter Models
# ============================================================================

class EmployeeFilters(BaseModel):
    """Query filters for employee list."""

    department: Optional[str] = None
    is_active: Optional[bool] = None
    reports_to_employee_id: Optional[int] = None
    search: Optional[str] = None  # Search by name
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)


class InterventionFilters(BaseModel):
    """Query filters for intervention list."""

    actor: Optional[str] = None
    object_type: Optional[str] = None
    object_id: Optional[int] = None
    action_type: Optional[str] = None
    status: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
