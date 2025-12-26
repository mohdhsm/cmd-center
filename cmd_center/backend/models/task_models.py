"""Pydantic models for Task API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Task Models
# ============================================================================

class TaskBase(BaseModel):
    """Base task fields."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(default=None, max_length=5000)
    priority: str = Field(default="medium")
    is_critical: bool = Field(default=False)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        allowed = {"low", "medium", "high"}
        if v not in allowed:
            raise ValueError(f"priority must be one of: {allowed}")
        return v


class TaskCreate(TaskBase):
    """Schema for creating a task."""
    assignee_employee_id: Optional[int] = None
    due_at: Optional[datetime] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None

    # Optional: create reminder when creating task
    reminder_at: Optional[datetime] = Field(
        default=None,
        description="If set, creates a reminder at this time"
    )
    reminder_channel: str = Field(
        default="in_app",
        description="Channel for the reminder if reminder_at is set"
    )


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = Field(default=None, max_length=5000)
    assignee_employee_id: Optional[int] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    is_critical: Optional[bool] = None
    due_at: Optional[datetime] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"open", "in_progress", "done", "cancelled"}
            if v not in allowed:
                raise ValueError(f"status must be one of: {allowed}")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"low", "medium", "high"}
            if v not in allowed:
                raise ValueError(f"priority must be one of: {allowed}")
        return v


class TaskResponse(BaseModel):
    """Response model for a task."""
    id: int
    title: str
    description: Optional[str]
    assignee_employee_id: Optional[int]
    created_by: Optional[str]
    status: str
    priority: str
    is_critical: bool
    due_at: Optional[datetime]
    completed_at: Optional[datetime]
    target_type: Optional[str]
    target_id: Optional[int]
    is_archived: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class TaskWithAssignee(TaskResponse):
    """Task response with assignee name."""
    assignee_name: Optional[str] = None


class TaskListResponse(BaseModel):
    """Paginated list of tasks."""
    items: list[TaskResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Filter Models
# ============================================================================

class TaskFilters(BaseModel):
    """Query filters for listing tasks."""
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_employee_id: Optional[int] = None
    is_critical: Optional[bool] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    is_archived: Optional[bool] = Field(default=False)
    due_before: Optional[datetime] = None
    due_after: Optional[datetime] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


__all__ = [
    "TaskBase",
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskWithAssignee",
    "TaskListResponse",
    "TaskFilters",
]
