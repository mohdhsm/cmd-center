"""Pydantic models for Skill and Skill Rating API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Skill Models
# ============================================================================

class SkillBase(BaseModel):
    """Base skill fields."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    category: Optional[str] = Field(default=None, max_length=100)


class SkillCreate(SkillBase):
    """Schema for creating a skill."""
    pass


class SkillUpdate(BaseModel):
    """Schema for updating a skill."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    category: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None


class SkillResponse(BaseModel):
    """Response model for a skill."""
    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SkillListResponse(BaseModel):
    """List of skills (no pagination, typically small list)."""
    items: list[SkillResponse]
    total: int


# ============================================================================
# Skill Rating Models
# ============================================================================

class SkillRatingCreate(BaseModel):
    """Schema for rating an employee's skill."""
    employee_id: int
    skill_id: int
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    notes: Optional[str] = Field(default=None, max_length=1000)


class SkillRatingResponse(BaseModel):
    """Response model for a skill rating."""
    id: int
    employee_id: int
    skill_id: int
    rating: int
    notes: Optional[str]
    rated_by: Optional[str]
    rated_at: datetime

    model_config = {"from_attributes": True}


class SkillRatingWithDetails(SkillRatingResponse):
    """Skill rating with skill and employee names."""
    skill_name: Optional[str] = None
    employee_name: Optional[str] = None


class EmployeeSkillCard(BaseModel):
    """All skills with latest ratings for an employee."""
    employee_id: int
    employee_name: str
    skills: list["SkillWithRating"]


class SkillWithRating(BaseModel):
    """Skill with its latest rating for an employee."""
    skill_id: int
    skill_name: str
    category: Optional[str]
    rating: Optional[int] = None  # None if not rated
    rated_at: Optional[datetime] = None
    notes: Optional[str] = None


# ============================================================================
# Filter Models
# ============================================================================

class SkillFilters(BaseModel):
    """Query filters for listing skills."""
    category: Optional[str] = None
    is_active: Optional[bool] = Field(default=True)
    search: Optional[str] = None


class SkillRatingFilters(BaseModel):
    """Query filters for listing skill ratings."""
    employee_id: Optional[int] = None
    skill_id: Optional[int] = None
    min_rating: Optional[int] = Field(default=None, ge=1, le=5)
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


__all__ = [
    "SkillBase",
    "SkillCreate",
    "SkillUpdate",
    "SkillResponse",
    "SkillListResponse",
    "SkillRatingCreate",
    "SkillRatingResponse",
    "SkillRatingWithDetails",
    "EmployeeSkillCard",
    "SkillWithRating",
    "SkillFilters",
    "SkillRatingFilters",
]
