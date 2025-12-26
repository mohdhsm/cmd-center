"""Employee log service for tracking achievements, issues, and feedback.

This service manages employee log entries for performance tracking.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select, func

from .. import db
from ..db import EmployeeLogEntry, Employee
from ..models.employee_log_models import (
    LogEntryCreate,
    LogEntryResponse,
    LogEntryWithEmployee,
    LogEntryListResponse,
    LogEntryFilters,
)
from ..constants import ActionType
from .intervention_service import log_action

logger = logging.getLogger(__name__)


class EmployeeLogService:
    """Service for employee log entry CRUD operations."""

    def __init__(self, actor: str = "system"):
        self.actor = actor

    def create_log_entry(
        self,
        data: LogEntryCreate,
        actor: Optional[str] = None,
    ) -> LogEntryResponse:
        """Create a new log entry for an employee."""
        actor = actor or self.actor

        with Session(db.engine) as session:
            log_entry = EmployeeLogEntry(
                employee_id=data.employee_id,
                category=data.category,
                title=data.title,
                content=data.content,
                severity=data.severity,
                is_positive=data.is_positive,
                logged_by=actor,
                occurred_at=data.occurred_at or datetime.now(timezone.utc),
            )
            session.add(log_entry)
            session.commit()
            session.refresh(log_entry)

            log_action(
                actor=actor,
                object_type="employee_log",
                object_id=log_entry.id,
                action_type=ActionType.LOG_ENTRY_CREATED.value,
                summary=f"Created {data.category} log for employee {data.employee_id}: {data.title}",
                details={
                    "category": data.category,
                    "is_positive": data.is_positive,
                    "severity": data.severity,
                },
            )

            logger.info(f"Created log entry: {log_entry.title} (ID: {log_entry.id})")

            return LogEntryResponse.model_validate(log_entry)

    def get_log_entry_by_id(self, log_id: int) -> Optional[LogEntryResponse]:
        """Get a log entry by ID."""
        with Session(db.engine) as session:
            log_entry = session.get(EmployeeLogEntry, log_id)
            if log_entry:
                return LogEntryResponse.model_validate(log_entry)
            return None

    def get_log_entry_with_employee(self, log_id: int) -> Optional[LogEntryWithEmployee]:
        """Get a log entry with employee name."""
        with Session(db.engine) as session:
            log_entry = session.get(EmployeeLogEntry, log_id)
            if not log_entry:
                return None

            # Get employee name
            employee_name = None
            if log_entry.employee_id:
                employee = session.get(Employee, log_entry.employee_id)
                if employee:
                    employee_name = employee.full_name

            return LogEntryWithEmployee(
                id=log_entry.id,
                employee_id=log_entry.employee_id,
                category=log_entry.category,
                title=log_entry.title,
                content=log_entry.content,
                severity=log_entry.severity,
                is_positive=log_entry.is_positive,
                logged_by=log_entry.logged_by,
                occurred_at=log_entry.occurred_at,
                created_at=log_entry.created_at,
                employee_name=employee_name,
            )

    def get_log_entries(
        self,
        filters: Optional[LogEntryFilters] = None,
    ) -> LogEntryListResponse:
        """Get paginated list of log entries."""
        if filters is None:
            filters = LogEntryFilters()

        with Session(db.engine) as session:
            query = select(EmployeeLogEntry)

            if filters.employee_id is not None:
                query = query.where(EmployeeLogEntry.employee_id == filters.employee_id)
            if filters.category:
                query = query.where(EmployeeLogEntry.category == filters.category)
            if filters.is_positive is not None:
                query = query.where(EmployeeLogEntry.is_positive == filters.is_positive)
            if filters.from_date:
                query = query.where(EmployeeLogEntry.occurred_at >= filters.from_date)
            if filters.to_date:
                query = query.where(EmployeeLogEntry.occurred_at <= filters.to_date)
            if filters.search:
                search_pattern = f"%{filters.search}%"
                query = query.where(
                    EmployeeLogEntry.title.ilike(search_pattern)
                    | EmployeeLogEntry.content.ilike(search_pattern)
                )

            count_query = select(func.count()).select_from(query.subquery())
            total = session.exec(count_query).one()

            query = query.order_by(EmployeeLogEntry.occurred_at.desc())
            query = query.offset((filters.page - 1) * filters.page_size)
            query = query.limit(filters.page_size)

            entries = session.exec(query).all()

            return LogEntryListResponse(
                items=[LogEntryResponse.model_validate(e) for e in entries],
                total=total,
                page=filters.page,
                page_size=filters.page_size,
            )

    def get_logs_by_employee(
        self,
        employee_id: int,
        category: Optional[str] = None,
        limit: int = 50,
    ) -> list[LogEntryResponse]:
        """Get log entries for a specific employee."""
        with Session(db.engine) as session:
            query = (
                select(EmployeeLogEntry)
                .where(EmployeeLogEntry.employee_id == employee_id)
            )

            if category:
                query = query.where(EmployeeLogEntry.category == category)

            query = query.order_by(EmployeeLogEntry.occurred_at.desc()).limit(limit)
            entries = session.exec(query).all()

            return [LogEntryResponse.model_validate(e) for e in entries]

    def get_logs_by_category(
        self,
        category: str,
        is_positive: Optional[bool] = None,
        limit: int = 50,
    ) -> list[LogEntryResponse]:
        """Get log entries by category."""
        with Session(db.engine) as session:
            query = (
                select(EmployeeLogEntry)
                .where(EmployeeLogEntry.category == category)
            )

            if is_positive is not None:
                query = query.where(EmployeeLogEntry.is_positive == is_positive)

            query = query.order_by(EmployeeLogEntry.occurred_at.desc()).limit(limit)
            entries = session.exec(query).all()

            return [LogEntryResponse.model_validate(e) for e in entries]

    def get_recent_issues(
        self,
        severity: Optional[str] = None,
        limit: int = 20,
    ) -> list[LogEntryWithEmployee]:
        """Get recent issue logs with employee names."""
        with Session(db.engine) as session:
            query = (
                select(EmployeeLogEntry)
                .where(EmployeeLogEntry.category == "issue")
            )

            if severity:
                query = query.where(EmployeeLogEntry.severity == severity)

            query = query.order_by(EmployeeLogEntry.occurred_at.desc()).limit(limit)
            entries = session.exec(query).all()

            results = []
            for entry in entries:
                employee_name = None
                if entry.employee_id:
                    employee = session.get(Employee, entry.employee_id)
                    if employee:
                        employee_name = employee.full_name

                results.append(
                    LogEntryWithEmployee(
                        id=entry.id,
                        employee_id=entry.employee_id,
                        category=entry.category,
                        title=entry.title,
                        content=entry.content,
                        severity=entry.severity,
                        is_positive=entry.is_positive,
                        logged_by=entry.logged_by,
                        occurred_at=entry.occurred_at,
                        created_at=entry.created_at,
                        employee_name=employee_name,
                    )
                )

            return results

    def get_employee_summary(
        self,
        employee_id: int,
    ) -> dict:
        """Get summary statistics for an employee's logs."""
        with Session(db.engine) as session:
            # Count by category
            category_counts = {}
            categories = ["achievement", "issue", "feedback", "milestone", "other"]
            for cat in categories:
                count_query = (
                    select(func.count())
                    .select_from(EmployeeLogEntry)
                    .where(EmployeeLogEntry.employee_id == employee_id)
                    .where(EmployeeLogEntry.category == cat)
                )
                category_counts[cat] = session.exec(count_query).one()

            # Count positive vs negative
            positive_query = (
                select(func.count())
                .select_from(EmployeeLogEntry)
                .where(EmployeeLogEntry.employee_id == employee_id)
                .where(EmployeeLogEntry.is_positive == True)
            )
            positive_count = session.exec(positive_query).one()

            negative_query = (
                select(func.count())
                .select_from(EmployeeLogEntry)
                .where(EmployeeLogEntry.employee_id == employee_id)
                .where(EmployeeLogEntry.is_positive == False)
            )
            negative_count = session.exec(negative_query).one()

            return {
                "employee_id": employee_id,
                "total_logs": sum(category_counts.values()),
                "by_category": category_counts,
                "positive_count": positive_count,
                "negative_count": negative_count,
            }


# Singleton pattern
_employee_log_service: Optional[EmployeeLogService] = None


def get_employee_log_service() -> EmployeeLogService:
    global _employee_log_service
    if _employee_log_service is None:
        _employee_log_service = EmployeeLogService()
    return _employee_log_service


__all__ = [
    "EmployeeLogService",
    "get_employee_log_service",
]
