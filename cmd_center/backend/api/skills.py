"""API endpoints for skill management and ratings."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ..models.skill_models import (
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    SkillListResponse,
    SkillFilters,
    SkillRatingCreate,
    SkillRatingResponse,
    SkillRatingWithDetails,
    EmployeeSkillCard,
    SkillWithRating,
    SkillRatingFilters,
)
from ..services.skill_service import get_skill_service

router = APIRouter(prefix="/skills", tags=["skills"])


# ============================================================================
# Skill CRUD
# ============================================================================

@router.post("", response_model=SkillResponse, status_code=201)
def create_skill(data: SkillCreate) -> SkillResponse:
    """Create a new skill definition."""
    service = get_skill_service()
    return service.create_skill(data)


@router.get("", response_model=SkillListResponse)
def list_skills(
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    search: Optional[str] = Query(None),
) -> SkillListResponse:
    """List all skills."""
    service = get_skill_service()
    filters = SkillFilters(
        category=category,
        is_active=is_active,
        search=search,
    )
    return service.get_skills(filters)


@router.get("/{skill_id}", response_model=SkillResponse)
def get_skill(skill_id: int) -> SkillResponse:
    """Get a skill by ID."""
    service = get_skill_service()
    skill = service.get_skill_by_id(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
def update_skill(skill_id: int, data: SkillUpdate) -> SkillResponse:
    """Update a skill."""
    service = get_skill_service()
    skill = service.update_skill(skill_id, data)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.delete("/{skill_id}", response_model=SkillResponse)
def deactivate_skill(skill_id: int) -> SkillResponse:
    """Deactivate a skill (soft delete)."""
    service = get_skill_service()
    skill = service.deactivate_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.get("/{skill_id}/top-rated", response_model=list[SkillRatingWithDetails])
def get_top_rated_for_skill(
    skill_id: int,
    limit: int = Query(10, ge=1, le=50),
) -> list[SkillRatingWithDetails]:
    """Get top-rated employees for a skill."""
    service = get_skill_service()
    return service.get_top_rated_employees(skill_id, limit=limit)


# ============================================================================
# Skill Ratings
# ============================================================================

@router.post("/ratings", response_model=SkillRatingResponse, status_code=201)
def rate_employee_skill(data: SkillRatingCreate) -> SkillRatingResponse:
    """Rate an employee's skill."""
    service = get_skill_service()
    return service.rate_employee_skill(data)


@router.get("/ratings", response_model=list[SkillRatingWithDetails])
def list_skill_ratings(
    employee_id: Optional[int] = Query(None),
    skill_id: Optional[int] = Query(None),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> list[SkillRatingWithDetails]:
    """List skill ratings with filters."""
    service = get_skill_service()
    filters = SkillRatingFilters(
        employee_id=employee_id,
        skill_id=skill_id,
        min_rating=min_rating,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
    return service.get_skill_ratings(filters)


@router.get("/ratings/{rating_id}", response_model=SkillRatingWithDetails)
def get_skill_rating(rating_id: int) -> SkillRatingWithDetails:
    """Get a skill rating by ID."""
    service = get_skill_service()
    rating = service.get_skill_rating_by_id(rating_id)
    if not rating:
        raise HTTPException(status_code=404, detail="Skill rating not found")
    return rating


# ============================================================================
# Employee Skill Cards
# ============================================================================

@router.get("/employee/{employee_id}/card", response_model=EmployeeSkillCard)
def get_employee_skill_card(employee_id: int) -> EmployeeSkillCard:
    """Get all skills with latest ratings for an employee."""
    service = get_skill_service()
    card = service.get_employee_skill_card(employee_id)
    if not card:
        raise HTTPException(status_code=404, detail="Employee not found")
    return card


@router.get("/employee/{employee_id}/ratings", response_model=list[SkillWithRating])
def get_employee_skill_ratings(employee_id: int) -> list[SkillWithRating]:
    """Get latest skill ratings for an employee."""
    service = get_skill_service()
    return service.get_latest_skill_ratings(employee_id)


@router.get("/employee/{employee_id}/skill/{skill_id}/history", response_model=list[SkillRatingResponse])
def get_skill_rating_history(
    employee_id: int,
    skill_id: int,
    limit: int = Query(10, ge=1, le=50),
) -> list[SkillRatingResponse]:
    """Get rating history for an employee's skill."""
    service = get_skill_service()
    return service.get_skill_rating_history(employee_id, skill_id, limit=limit)
