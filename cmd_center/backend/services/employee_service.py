"""Employee service for CRUD operations.

This service manages the employee directory, which is the foundation
for all people-related features (tasks, notes, bonuses, skills, etc.).
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select, func

from .. import db
from ..db import Employee, Deal
from ..models.employee_models import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeWithAggregates,
    EmployeeListResponse,
    EmployeeFilters,
)
from ..constants import ActionType
from .intervention_service import log_action

logger = logging.getLogger(__name__)


class EmployeeService:
    """Service for employee CRUD operations."""

    def __init__(self, actor: str = "system"):
        """Initialize employee service.

        Args:
            actor: Default actor for audit logging (can be overridden per method)
        """
        self.actor = actor

    def create_employee(
        self,
        data: EmployeeCreate,
        actor: Optional[str] = None,
    ) -> EmployeeResponse:
        """Create a new employee.

        Args:
            data: Employee creation data
            actor: Who is creating the employee (for audit log)

        Returns:
            The created employee
        """
        actor = actor or self.actor

        with Session(db.engine) as session:
            employee = Employee(
                full_name=data.full_name,
                role_title=data.role_title,
                department=data.department,
                email=data.email,
                phone=data.phone,
                reports_to_employee_id=data.reports_to_employee_id,
                pipedrive_owner_id=data.pipedrive_owner_id,
            )
            session.add(employee)
            session.commit()
            session.refresh(employee)

            # Log the action
            log_action(
                actor=actor,
                object_type="employee",
                object_id=employee.id,
                action_type=ActionType.EMPLOYEE_CREATED.value,
                summary=f"Created employee: {employee.full_name}",
                details={
                    "full_name": employee.full_name,
                    "role_title": employee.role_title,
                    "department": employee.department,
                },
            )

            logger.info(f"Created employee: {employee.full_name} (ID: {employee.id})")

            return EmployeeResponse.model_validate(employee)

    def get_employee_by_id(
        self,
        employee_id: int,
    ) -> Optional[EmployeeResponse]:
        """Get an employee by ID.

        Args:
            employee_id: The employee ID

        Returns:
            The employee if found, None otherwise
        """
        with Session(db.engine) as session:
            employee = session.get(Employee, employee_id)
            if employee:
                return EmployeeResponse.model_validate(employee)
            return None

    def get_employee_with_aggregates(
        self,
        employee_id: int,
    ) -> Optional[EmployeeWithAggregates]:
        """Get an employee with computed aggregates.

        Includes deal counts, task counts, notes counts, etc.

        Args:
            employee_id: The employee ID

        Returns:
            The employee with aggregates if found, None otherwise
        """
        with Session(db.engine) as session:
            employee = session.get(Employee, employee_id)
            if not employee:
                return None

            # Get manager name
            reports_to_name = None
            if employee.reports_to_employee_id:
                manager = session.get(Employee, employee.reports_to_employee_id)
                if manager:
                    reports_to_name = manager.full_name

            # Get deal counts if linked to Pipedrive
            open_deals_count = 0
            open_deals_value = 0.0
            if employee.pipedrive_owner_id:
                deal_query = (
                    select(
                        func.count(Deal.id),
                        func.coalesce(func.sum(Deal.value), 0),
                    )
                    .where(Deal.owner_id == employee.pipedrive_owner_id)
                    .where(Deal.status == "open")
                )
                result = session.exec(deal_query).one()
                open_deals_count = result[0]
                open_deals_value = result[1]

            # TODO: Add task, note, and reminder counts after those tables are created

            return EmployeeWithAggregates(
                id=employee.id,
                full_name=employee.full_name,
                role_title=employee.role_title,
                department=employee.department,
                email=employee.email,
                phone=employee.phone,
                reports_to_employee_id=employee.reports_to_employee_id,
                is_active=employee.is_active,
                pipedrive_owner_id=employee.pipedrive_owner_id,
                created_at=employee.created_at,
                updated_at=employee.updated_at,
                reports_to_name=reports_to_name,
                open_deals_count=open_deals_count,
                open_deals_value=open_deals_value,
            )

    def get_employees(
        self,
        filters: Optional[EmployeeFilters] = None,
    ) -> EmployeeListResponse:
        """Get paginated list of employees with optional filters.

        Args:
            filters: Query filters (department, is_active, search, etc.)

        Returns:
            Paginated list of employees
        """
        if filters is None:
            filters = EmployeeFilters()

        with Session(db.engine) as session:
            # Build base query
            query = select(Employee)

            # Apply filters
            if filters.department:
                query = query.where(Employee.department == filters.department)
            if filters.is_active is not None:
                query = query.where(Employee.is_active == filters.is_active)
            if filters.reports_to_employee_id is not None:
                query = query.where(
                    Employee.reports_to_employee_id == filters.reports_to_employee_id
                )
            if filters.search:
                # Case-insensitive search on full_name
                search_pattern = f"%{filters.search}%"
                query = query.where(Employee.full_name.ilike(search_pattern))

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = session.exec(count_query).one()

            # Apply pagination and ordering
            query = query.order_by(Employee.full_name)
            query = query.offset((filters.page - 1) * filters.page_size)
            query = query.limit(filters.page_size)

            # Execute query
            employees = session.exec(query).all()

            # Convert to response models
            items = [
                EmployeeResponse.model_validate(e)
                for e in employees
            ]

            return EmployeeListResponse(
                items=items,
                total=total,
                page=filters.page,
                page_size=filters.page_size,
            )

    def update_employee(
        self,
        employee_id: int,
        data: EmployeeUpdate,
        actor: Optional[str] = None,
    ) -> Optional[EmployeeResponse]:
        """Update an employee.

        Args:
            employee_id: The employee ID to update
            data: Fields to update (only non-None fields are updated)
            actor: Who is updating the employee (for audit log)

        Returns:
            The updated employee if found, None otherwise
        """
        actor = actor or self.actor

        with Session(db.engine) as session:
            employee = session.get(Employee, employee_id)
            if not employee:
                return None

            # Track what changed for audit log
            changes = {}

            # Update only provided fields
            if data.full_name is not None:
                changes["full_name"] = {"from": employee.full_name, "to": data.full_name}
                employee.full_name = data.full_name
            if data.role_title is not None:
                changes["role_title"] = {"from": employee.role_title, "to": data.role_title}
                employee.role_title = data.role_title
            if data.department is not None:
                changes["department"] = {"from": employee.department, "to": data.department}
                employee.department = data.department
            if data.email is not None:
                changes["email"] = {"from": employee.email, "to": data.email}
                employee.email = data.email
            if data.phone is not None:
                changes["phone"] = {"from": employee.phone, "to": data.phone}
                employee.phone = data.phone
            if data.reports_to_employee_id is not None:
                changes["reports_to_employee_id"] = {
                    "from": employee.reports_to_employee_id,
                    "to": data.reports_to_employee_id,
                }
                employee.reports_to_employee_id = data.reports_to_employee_id
            if data.pipedrive_owner_id is not None:
                changes["pipedrive_owner_id"] = {
                    "from": employee.pipedrive_owner_id,
                    "to": data.pipedrive_owner_id,
                }
                employee.pipedrive_owner_id = data.pipedrive_owner_id
            if data.is_active is not None:
                changes["is_active"] = {"from": employee.is_active, "to": data.is_active}
                employee.is_active = data.is_active

            # Update timestamp
            employee.updated_at = datetime.now(timezone.utc)

            session.add(employee)
            session.commit()
            session.refresh(employee)

            # Log the action
            if changes:
                log_action(
                    actor=actor,
                    object_type="employee",
                    object_id=employee.id,
                    action_type=ActionType.EMPLOYEE_UPDATED.value,
                    summary=f"Updated employee: {employee.full_name}",
                    details={"changes": changes},
                )

            logger.info(f"Updated employee: {employee.full_name} (ID: {employee.id})")

            return EmployeeResponse.model_validate(employee)

    def delete_employee(
        self,
        employee_id: int,
        actor: Optional[str] = None,
    ) -> bool:
        """Soft delete an employee (set is_active=False).

        Args:
            employee_id: The employee ID to delete
            actor: Who is deleting the employee (for audit log)

        Returns:
            True if deleted, False if not found
        """
        actor = actor or self.actor

        with Session(db.engine) as session:
            employee = session.get(Employee, employee_id)
            if not employee:
                return False

            # Soft delete
            employee.is_active = False
            employee.updated_at = datetime.now(timezone.utc)

            session.add(employee)
            session.commit()

            # Log the action
            log_action(
                actor=actor,
                object_type="employee",
                object_id=employee.id,
                action_type=ActionType.EMPLOYEE_DEACTIVATED.value,
                summary=f"Deactivated employee: {employee.full_name}",
            )

            logger.info(f"Deactivated employee: {employee.full_name} (ID: {employee.id})")

            return True

    def get_employee_by_pipedrive_owner_id(
        self,
        pipedrive_owner_id: int,
    ) -> Optional[EmployeeResponse]:
        """Get an employee by their Pipedrive owner ID.

        Useful for linking Pipedrive deals to internal employees.

        Args:
            pipedrive_owner_id: The Pipedrive owner ID

        Returns:
            The employee if found, None otherwise
        """
        with Session(db.engine) as session:
            query = select(Employee).where(
                Employee.pipedrive_owner_id == pipedrive_owner_id
            )
            employee = session.exec(query).first()
            if employee:
                return EmployeeResponse.model_validate(employee)
            return None


# Singleton pattern
_employee_service: Optional[EmployeeService] = None


def get_employee_service() -> EmployeeService:
    """Get or create employee service singleton."""
    global _employee_service
    if _employee_service is None:
        _employee_service = EmployeeService()
    return _employee_service


__all__ = [
    "EmployeeService",
    "get_employee_service",
]
