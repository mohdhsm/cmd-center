"""Intervention service for audit logging.

This service provides a centralized way to log all significant actions
in the system. Every operation that modifies data should create an
intervention record for audit trail purposes.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional, Any

from sqlmodel import Session, select, func

from .. import db
from ..db import Intervention

# Access db.engine dynamically to support test fixture overrides
def _get_engine():
    return db.engine
from ..models.employee_models import (
    InterventionResponse,
    InterventionListResponse,
    InterventionFilters,
)

logger = logging.getLogger(__name__)


def log_action(
    actor: str,
    object_type: str,
    object_id: int,
    action_type: str,
    summary: str,
    status: str = "done",
    details: Optional[dict[str, Any]] = None,
) -> Intervention:
    """Log an intervention (audit) record.

    This is the primary function for audit logging. Call it whenever
    a significant action occurs in the system.

    Args:
        actor: Who performed the action (username, email, or "system")
        object_type: Type of object affected (e.g., "employee", "task", "deal")
        object_id: ID of the affected object
        action_type: Type of action (use ActionType enum values)
        summary: Human-readable description of the action
        status: Result status ("done", "failed", "planned")
        details: Optional dict with additional context (serialized to JSON)

    Returns:
        The created Intervention record

    Example:
        >>> log_action(
        ...     actor="admin@example.com",
        ...     object_type="employee",
        ...     object_id=123,
        ...     action_type="employee_created",
        ...     summary="Created employee: John Doe",
        ...     details={"full_name": "John Doe", "role": "Engineer"}
        ... )
    """
    intervention = Intervention(
        actor=actor,
        object_type=object_type,
        object_id=object_id,
        action_type=action_type,
        summary=summary,
        status=status,
        details_json=json.dumps(details) if details else None,
    )

    with Session(db.engine) as session:
        session.add(intervention)
        session.commit()
        session.refresh(intervention)

    logger.info(
        f"Intervention logged: {action_type} on {object_type}:{object_id} by {actor}"
    )

    return intervention


class InterventionService:
    """Service for querying intervention records."""

    def get_interventions(
        self,
        filters: Optional[InterventionFilters] = None,
    ) -> InterventionListResponse:
        """Get paginated list of interventions with optional filters.

        Args:
            filters: Query filters (actor, object_type, action_type, etc.)

        Returns:
            Paginated list of interventions
        """
        if filters is None:
            filters = InterventionFilters()

        with Session(db.engine) as session:
            # Build base query
            query = select(Intervention)

            # Apply filters
            if filters.actor:
                query = query.where(Intervention.actor == filters.actor)
            if filters.object_type:
                query = query.where(Intervention.object_type == filters.object_type)
            if filters.object_id is not None:
                query = query.where(Intervention.object_id == filters.object_id)
            if filters.action_type:
                query = query.where(Intervention.action_type == filters.action_type)
            if filters.status:
                query = query.where(Intervention.status == filters.status)
            if filters.from_date:
                query = query.where(Intervention.created_at >= filters.from_date)
            if filters.to_date:
                query = query.where(Intervention.created_at <= filters.to_date)

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = session.exec(count_query).one()

            # Apply pagination and ordering
            query = query.order_by(Intervention.created_at.desc())
            query = query.offset((filters.page - 1) * filters.page_size)
            query = query.limit(filters.page_size)

            # Execute query
            interventions = session.exec(query).all()

            # Convert to response models
            items = [
                InterventionResponse.model_validate(i)
                for i in interventions
            ]

            return InterventionListResponse(
                items=items,
                total=total,
                page=filters.page,
                page_size=filters.page_size,
            )

    def get_intervention_by_id(
        self,
        intervention_id: int,
    ) -> Optional[InterventionResponse]:
        """Get a single intervention by ID.

        Args:
            intervention_id: The intervention ID

        Returns:
            The intervention if found, None otherwise
        """
        with Session(db.engine) as session:
            intervention = session.get(Intervention, intervention_id)
            if intervention:
                return InterventionResponse.model_validate(intervention)
            return None

    def get_interventions_for_object(
        self,
        object_type: str,
        object_id: int,
        limit: int = 50,
    ) -> list[InterventionResponse]:
        """Get all interventions for a specific object.

        Useful for showing the history of actions on a specific entity.

        Args:
            object_type: Type of object (e.g., "employee", "task")
            object_id: ID of the object
            limit: Maximum number of results

        Returns:
            List of interventions ordered by most recent first
        """
        with Session(db.engine) as session:
            query = (
                select(Intervention)
                .where(Intervention.object_type == object_type)
                .where(Intervention.object_id == object_id)
                .order_by(Intervention.created_at.desc())
                .limit(limit)
            )
            interventions = session.exec(query).all()

            return [
                InterventionResponse.model_validate(i)
                for i in interventions
            ]

    def get_recent_interventions_by_actor(
        self,
        actor: str,
        limit: int = 20,
    ) -> list[InterventionResponse]:
        """Get recent interventions by a specific actor.

        Args:
            actor: The actor (username or "system")
            limit: Maximum number of results

        Returns:
            List of interventions ordered by most recent first
        """
        with Session(db.engine) as session:
            query = (
                select(Intervention)
                .where(Intervention.actor == actor)
                .order_by(Intervention.created_at.desc())
                .limit(limit)
            )
            interventions = session.exec(query).all()

            return [
                InterventionResponse.model_validate(i)
                for i in interventions
            ]


# Singleton pattern
_intervention_service: Optional[InterventionService] = None


def get_intervention_service() -> InterventionService:
    """Get or create intervention service singleton."""
    global _intervention_service
    if _intervention_service is None:
        _intervention_service = InterventionService()
    return _intervention_service


__all__ = [
    "log_action",
    "InterventionService",
    "get_intervention_service",
]
