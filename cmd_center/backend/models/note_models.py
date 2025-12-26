"""Pydantic models for Internal Note API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================================
# Note Models
# ============================================================================

class NoteBase(BaseModel):
    """Base note fields."""
    content: str = Field(..., min_length=1, max_length=10000)
    pinned: bool = Field(default=False)
    tags: Optional[str] = Field(default=None, max_length=500, description="Comma-separated tags")


class NoteCreate(NoteBase):
    """Schema for creating a note."""
    target_type: Optional[str] = None
    target_id: Optional[int] = None

    # Optional: create review reminder when creating note
    review_at: Optional[datetime] = Field(
        default=None,
        description="If set, creates a review reminder at this time"
    )
    reminder_channel: str = Field(
        default="in_app",
        description="Channel for the review reminder if review_at is set"
    )


class NoteUpdate(BaseModel):
    """Schema for updating a note."""
    content: Optional[str] = Field(default=None, min_length=1, max_length=10000)
    pinned: Optional[bool] = None
    tags: Optional[str] = Field(default=None, max_length=500)
    review_at: Optional[datetime] = None


class NoteResponse(BaseModel):
    """Response model for a note."""
    id: int
    content: str
    created_by: Optional[str]
    target_type: Optional[str]
    target_id: Optional[int]
    review_at: Optional[datetime]
    pinned: bool
    tags: Optional[str]
    is_archived: bool
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    """Paginated list of notes."""
    items: list[NoteResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Filter Models
# ============================================================================

class NoteFilters(BaseModel):
    """Query filters for listing notes."""
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    pinned: Optional[bool] = None
    tags: Optional[str] = Field(default=None, description="Filter by tag (single tag)")
    is_archived: Optional[bool] = Field(default=False)
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


__all__ = [
    "NoteBase",
    "NoteCreate",
    "NoteUpdate",
    "NoteResponse",
    "NoteListResponse",
    "NoteFilters",
]
