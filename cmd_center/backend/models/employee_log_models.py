"""Pydantic models for Employee Log Entry API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Employee Log Models
# ============================================================================

class LogEntryBase(BaseModel):
    """Base log entry fields."""
    category: str = Field(..., description="achievement, issue, feedback, milestone, other")
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=5000)
    severity: Optional[str] = Field(default=None, description="For issues: low, medium, high")
    is_positive: bool = Field(default=True)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        allowed = {"achievement", "issue", "feedback", "milestone", "other"}
        if v not in allowed:
            raise ValueError(f"category must be one of: {allowed}")
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"low", "medium", "high"}
            if v not in allowed:
                raise ValueError(f"severity must be one of: {allowed}")
        return v


class LogEntryCreate(LogEntryBase):
    """Schema for creating a log entry."""
    employee_id: int
    occurred_at: Optional[datetime] = None  # Defaults to now


class LogEntryResponse(BaseModel):
    """Response model for a log entry."""
    id: int
    employee_id: int
    category: str
    title: str
    content: str
    severity: Optional[str]
    is_positive: bool
    logged_by: Optional[str]
    occurred_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class LogEntryWithEmployee(LogEntryResponse):
    """Log entry with employee name."""
    employee_name: Optional[str] = None


class LogEntryListResponse(BaseModel):
    """Paginated list of log entries."""
    items: list[LogEntryResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Filter Models
# ============================================================================

class LogEntryFilters(BaseModel):
    """Query filters for listing log entries."""
    employee_id: Optional[int] = None
    category: Optional[str] = None
    is_positive: Optional[bool] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


__all__ = [
    "LogEntryBase",
    "LogEntryCreate",
    "LogEntryResponse",
    "LogEntryWithEmployee",
    "LogEntryListResponse",
    "LogEntryFilters",
]
