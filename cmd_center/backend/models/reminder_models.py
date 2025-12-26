"""Pydantic models for Reminder API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Reminder Models
# ============================================================================

class ReminderBase(BaseModel):
    """Base reminder fields."""
    target_type: str = Field(..., description="Entity type: task, note, document, bonus, etc.")
    target_id: int = Field(..., description="ID of the target entity")
    remind_at: datetime = Field(..., description="When to send the reminder")
    channel: str = Field(default="in_app", description="Notification channel: in_app, email")
    message: Optional[str] = Field(default=None, description="Custom reminder message")


class ReminderCreate(ReminderBase):
    """Schema for creating a reminder."""
    is_recurring: bool = Field(default=False, description="Whether reminder repeats")
    recurrence_rule: Optional[str] = Field(default=None, description="iCal RRULE for recurring")

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v: str) -> str:
        allowed = {"in_app", "email"}
        if v not in allowed:
            raise ValueError(f"channel must be one of: {allowed}")
        return v


class ReminderUpdate(BaseModel):
    """Schema for updating a reminder."""
    remind_at: Optional[datetime] = None
    channel: Optional[str] = None
    message: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[str] = None

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"in_app", "email"}
            if v not in allowed:
                raise ValueError(f"channel must be one of: {allowed}")
        return v


class ReminderResponse(BaseModel):
    """Response model for a reminder."""
    id: int
    target_type: str
    target_id: int
    remind_at: datetime
    channel: str
    message: Optional[str]
    status: str
    sent_at: Optional[datetime]
    error_message: Optional[str]
    is_recurring: bool
    recurrence_rule: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ReminderListResponse(BaseModel):
    """Paginated list of reminders."""
    items: list[ReminderResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Filter Models
# ============================================================================

class ReminderFilters(BaseModel):
    """Query filters for listing reminders."""
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    status: Optional[str] = None
    channel: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


__all__ = [
    "ReminderBase",
    "ReminderCreate",
    "ReminderUpdate",
    "ReminderResponse",
    "ReminderListResponse",
    "ReminderFilters",
]
