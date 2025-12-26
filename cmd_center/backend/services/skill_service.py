"""Skill service for managing skills and employee skill ratings.

This service manages skill definitions and employee skill ratings.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select, func

from .. import db
from ..db import Skill, EmployeeSkillRating, Employee
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
from ..constants import ActionType
from .intervention_service import log_action

logger = logging.getLogger(__name__)


class SkillService:
    """Service for skill and skill rating CRUD operations."""

    def __init__(self, actor: str = "system"):
        self.actor = actor

    # =========================================================================
    # Skill CRUD
    # =========================================================================

    def create_skill(
        self,
        data: SkillCreate,
        actor: Optional[str] = None,
    ) -> SkillResponse:
        """Create a new skill definition."""
        actor = actor or self.actor

        with Session(db.engine) as session:
            skill = Skill(
                name=data.name,
                description=data.description,
                category=data.category,
                is_active=True,
            )
            session.add(skill)
            session.commit()
            session.refresh(skill)

            log_action(
                actor=actor,
                object_type="skill",
                object_id=skill.id,
                action_type=ActionType.SKILL_CREATED.value,
                summary=f"Created skill: {skill.name}",
                details={"category": skill.category},
            )

            logger.info(f"Created skill: {skill.name} (ID: {skill.id})")

            return SkillResponse.model_validate(skill)

    def get_skill_by_id(self, skill_id: int) -> Optional[SkillResponse]:
        """Get a skill by ID."""
        with Session(db.engine) as session:
            skill = session.get(Skill, skill_id)
            if skill:
                return SkillResponse.model_validate(skill)
            return None

    def get_skill_by_name(self, name: str) -> Optional[SkillResponse]:
        """Get a skill by name."""
        with Session(db.engine) as session:
            query = select(Skill).where(Skill.name == name)
            skill = session.exec(query).first()
            if skill:
                return SkillResponse.model_validate(skill)
            return None

    def get_skills(
        self,
        filters: Optional[SkillFilters] = None,
    ) -> SkillListResponse:
        """Get list of skills (no pagination, typically small)."""
        if filters is None:
            filters = SkillFilters()

        with Session(db.engine) as session:
            query = select(Skill)

            if filters.category:
                query = query.where(Skill.category == filters.category)
            if filters.is_active is not None:
                query = query.where(Skill.is_active == filters.is_active)
            if filters.search:
                search_pattern = f"%{filters.search}%"
                query = query.where(Skill.name.ilike(search_pattern))

            query = query.order_by(Skill.category.asc().nullslast(), Skill.name.asc())
            skills = session.exec(query).all()

            return SkillListResponse(
                items=[SkillResponse.model_validate(s) for s in skills],
                total=len(skills),
            )

    def update_skill(
        self,
        skill_id: int,
        data: SkillUpdate,
        actor: Optional[str] = None,
    ) -> Optional[SkillResponse]:
        """Update a skill."""
        actor = actor or self.actor

        with Session(db.engine) as session:
            skill = session.get(Skill, skill_id)
            if not skill:
                return None

            changes = {}

            if data.name is not None:
                changes["name"] = {"from": skill.name, "to": data.name}
                skill.name = data.name
            if data.description is not None:
                skill.description = data.description
            if data.category is not None:
                changes["category"] = {"from": skill.category, "to": data.category}
                skill.category = data.category
            if data.is_active is not None:
                changes["is_active"] = {"from": skill.is_active, "to": data.is_active}
                skill.is_active = data.is_active

            session.add(skill)
            session.commit()
            session.refresh(skill)

            if changes:
                log_action(
                    actor=actor,
                    object_type="skill",
                    object_id=skill.id,
                    action_type=ActionType.SKILL_UPDATED.value,
                    summary=f"Updated skill: {skill.name}",
                    details={"changes": changes},
                )

            return SkillResponse.model_validate(skill)

    def deactivate_skill(
        self,
        skill_id: int,
        actor: Optional[str] = None,
    ) -> Optional[SkillResponse]:
        """Deactivate a skill."""
        return self.update_skill(
            skill_id,
            SkillUpdate(is_active=False),
            actor=actor,
        )

    # =========================================================================
    # Skill Rating CRUD
    # =========================================================================

    def rate_employee_skill(
        self,
        data: SkillRatingCreate,
        actor: Optional[str] = None,
    ) -> SkillRatingResponse:
        """Rate an employee's skill (creates new rating entry)."""
        actor = actor or self.actor

        with Session(db.engine) as session:
            rating = EmployeeSkillRating(
                employee_id=data.employee_id,
                skill_id=data.skill_id,
                rating=data.rating,
                notes=data.notes,
                rated_by=actor,
            )
            session.add(rating)
            session.commit()
            session.refresh(rating)

            # Get skill name for logging
            skill = session.get(Skill, data.skill_id)
            skill_name = skill.name if skill else f"ID:{data.skill_id}"

            log_action(
                actor=actor,
                object_type="skill_rating",
                object_id=rating.id,
                action_type=ActionType.SKILL_RATING_CREATED.value,
                summary=f"Rated employee {data.employee_id} on {skill_name}: {data.rating}/5",
                details={
                    "employee_id": data.employee_id,
                    "skill_id": data.skill_id,
                    "rating": data.rating,
                },
            )

            logger.info(
                f"Rated employee {data.employee_id} on skill {data.skill_id}: {data.rating}/5"
            )

            return SkillRatingResponse.model_validate(rating)

    def get_skill_rating_by_id(self, rating_id: int) -> Optional[SkillRatingWithDetails]:
        """Get a skill rating by ID with skill and employee names."""
        with Session(db.engine) as session:
            rating = session.get(EmployeeSkillRating, rating_id)
            if not rating:
                return None

            # Get names
            skill_name = None
            employee_name = None

            skill = session.get(Skill, rating.skill_id)
            if skill:
                skill_name = skill.name

            employee = session.get(Employee, rating.employee_id)
            if employee:
                employee_name = employee.full_name

            return SkillRatingWithDetails(
                id=rating.id,
                employee_id=rating.employee_id,
                skill_id=rating.skill_id,
                rating=rating.rating,
                notes=rating.notes,
                rated_by=rating.rated_by,
                rated_at=rating.rated_at,
                skill_name=skill_name,
                employee_name=employee_name,
            )

    def get_skill_ratings(
        self,
        filters: Optional[SkillRatingFilters] = None,
    ) -> list[SkillRatingWithDetails]:
        """Get skill ratings with filters."""
        if filters is None:
            filters = SkillRatingFilters()

        with Session(db.engine) as session:
            query = select(EmployeeSkillRating)

            if filters.employee_id is not None:
                query = query.where(EmployeeSkillRating.employee_id == filters.employee_id)
            if filters.skill_id is not None:
                query = query.where(EmployeeSkillRating.skill_id == filters.skill_id)
            if filters.min_rating is not None:
                query = query.where(EmployeeSkillRating.rating >= filters.min_rating)
            if filters.from_date:
                query = query.where(EmployeeSkillRating.rated_at >= filters.from_date)
            if filters.to_date:
                query = query.where(EmployeeSkillRating.rated_at <= filters.to_date)

            query = query.order_by(EmployeeSkillRating.rated_at.desc())
            query = query.offset((filters.page - 1) * filters.page_size)
            query = query.limit(filters.page_size)

            ratings = session.exec(query).all()

            results = []
            for r in ratings:
                skill_name = None
                employee_name = None

                skill = session.get(Skill, r.skill_id)
                if skill:
                    skill_name = skill.name

                employee = session.get(Employee, r.employee_id)
                if employee:
                    employee_name = employee.full_name

                results.append(
                    SkillRatingWithDetails(
                        id=r.id,
                        employee_id=r.employee_id,
                        skill_id=r.skill_id,
                        rating=r.rating,
                        notes=r.notes,
                        rated_by=r.rated_by,
                        rated_at=r.rated_at,
                        skill_name=skill_name,
                        employee_name=employee_name,
                    )
                )

            return results

    def get_latest_skill_ratings(
        self,
        employee_id: int,
    ) -> list[SkillWithRating]:
        """Get latest rating for each skill for an employee."""
        with Session(db.engine) as session:
            # Get all active skills
            skills_query = (
                select(Skill)
                .where(Skill.is_active == True)
                .order_by(Skill.category.asc().nullslast(), Skill.name.asc())
            )
            skills = session.exec(skills_query).all()

            results = []
            for skill in skills:
                # Get latest rating for this skill/employee
                rating_query = (
                    select(EmployeeSkillRating)
                    .where(EmployeeSkillRating.employee_id == employee_id)
                    .where(EmployeeSkillRating.skill_id == skill.id)
                    .order_by(EmployeeSkillRating.rated_at.desc())
                    .limit(1)
                )
                latest_rating = session.exec(rating_query).first()

                results.append(
                    SkillWithRating(
                        skill_id=skill.id,
                        skill_name=skill.name,
                        category=skill.category,
                        rating=latest_rating.rating if latest_rating else None,
                        rated_at=latest_rating.rated_at if latest_rating else None,
                        notes=latest_rating.notes if latest_rating else None,
                    )
                )

            return results

    def get_employee_skill_card(
        self,
        employee_id: int,
    ) -> Optional[EmployeeSkillCard]:
        """Get all skills with ratings for an employee."""
        with Session(db.engine) as session:
            employee = session.get(Employee, employee_id)
            if not employee:
                return None

            skills = self.get_latest_skill_ratings(employee_id)

            return EmployeeSkillCard(
                employee_id=employee_id,
                employee_name=employee.full_name,
                skills=skills,
            )

    def get_skill_rating_history(
        self,
        employee_id: int,
        skill_id: int,
        limit: int = 10,
    ) -> list[SkillRatingResponse]:
        """Get rating history for an employee's skill."""
        with Session(db.engine) as session:
            query = (
                select(EmployeeSkillRating)
                .where(EmployeeSkillRating.employee_id == employee_id)
                .where(EmployeeSkillRating.skill_id == skill_id)
                .order_by(EmployeeSkillRating.rated_at.desc())
                .limit(limit)
            )
            ratings = session.exec(query).all()

            return [SkillRatingResponse.model_validate(r) for r in ratings]

    def get_top_rated_employees(
        self,
        skill_id: int,
        limit: int = 10,
    ) -> list[SkillRatingWithDetails]:
        """Get top-rated employees for a skill (latest rating only)."""
        with Session(db.engine) as session:
            # Get all employees with ratings for this skill
            # We need to get the latest rating per employee
            # Using a subquery approach

            # First get all employee IDs who have ratings for this skill
            employees_query = (
                select(EmployeeSkillRating.employee_id)
                .where(EmployeeSkillRating.skill_id == skill_id)
                .distinct()
            )
            employee_ids = session.exec(employees_query).all()

            results = []
            for emp_id in employee_ids:
                # Get latest rating for this employee
                rating_query = (
                    select(EmployeeSkillRating)
                    .where(EmployeeSkillRating.skill_id == skill_id)
                    .where(EmployeeSkillRating.employee_id == emp_id)
                    .order_by(EmployeeSkillRating.rated_at.desc())
                    .limit(1)
                )
                rating = session.exec(rating_query).first()
                if rating:
                    employee = session.get(Employee, emp_id)
                    skill = session.get(Skill, skill_id)
                    results.append(
                        SkillRatingWithDetails(
                            id=rating.id,
                            employee_id=rating.employee_id,
                            skill_id=rating.skill_id,
                            rating=rating.rating,
                            notes=rating.notes,
                            rated_by=rating.rated_by,
                            rated_at=rating.rated_at,
                            skill_name=skill.name if skill else None,
                            employee_name=employee.full_name if employee else None,
                        )
                    )

            # Sort by rating descending and limit
            results.sort(key=lambda x: x.rating, reverse=True)
            return results[:limit]


# Singleton pattern
_skill_service: Optional[SkillService] = None


def get_skill_service() -> SkillService:
    global _skill_service
    if _skill_service is None:
        _skill_service = SkillService()
    return _skill_service


__all__ = [
    "SkillService",
    "get_skill_service",
]
