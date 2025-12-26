"""Task service for task management with reminder integration.

This service manages tasks that can be linked to any entity (deals, employees, etc.)
and integrates with the unified reminder system.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select, func

from .. import db
from ..db import Task, Employee
from ..models.task_models import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskWithAssignee,
    TaskListResponse,
    TaskFilters,
)
from ..models.reminder_models import ReminderCreate
from ..constants import ActionType, TaskStatus
from .intervention_service import log_action
from .reminder_service import ReminderService

logger = logging.getLogger(__name__)


class TaskService:
    """Service for task CRUD operations with reminder integration."""

    def __init__(self, actor: str = "system"):
        """Initialize task service.

        Args:
            actor: Default actor for audit logging
        """
        self.actor = actor
        self.reminder_service = ReminderService(actor=actor)

    def create_task(
        self,
        data: TaskCreate,
        actor: Optional[str] = None,
    ) -> TaskResponse:
        """Create a new task, optionally with a reminder.

        Args:
            data: Task creation data
            actor: Who is creating the task

        Returns:
            The created task
        """
        actor = actor or self.actor

        with Session(db.engine) as session:
            task = Task(
                title=data.title,
                description=data.description,
                assignee_employee_id=data.assignee_employee_id,
                created_by=actor,
                priority=data.priority,
                is_critical=data.is_critical,
                due_at=data.due_at,
                target_type=data.target_type,
                target_id=data.target_id,
                status=TaskStatus.OPEN.value,
            )
            session.add(task)
            session.commit()
            session.refresh(task)

            task_id = task.id

            # Log the action
            log_action(
                actor=actor,
                object_type="task",
                object_id=task_id,
                action_type=ActionType.TASK_CREATED.value,
                summary=f"Created task: {task.title}",
                details={
                    "title": task.title,
                    "priority": task.priority,
                    "assignee_employee_id": task.assignee_employee_id,
                    "target_type": task.target_type,
                    "target_id": task.target_id,
                },
            )

            logger.info(f"Created task: {task.title} (ID: {task_id})")

            result = TaskResponse.model_validate(task)

        # Create reminder if requested (outside the session)
        if data.reminder_at:
            self.reminder_service.create_reminder(
                ReminderCreate(
                    target_type="task",
                    target_id=task_id,
                    remind_at=data.reminder_at,
                    channel=data.reminder_channel,
                    message=f"Task reminder: {data.title}",
                ),
                actor=actor,
            )

        return result

    def get_task_by_id(
        self,
        task_id: int,
    ) -> Optional[TaskResponse]:
        """Get a task by ID.

        Args:
            task_id: The task ID

        Returns:
            The task if found, None otherwise
        """
        with Session(db.engine) as session:
            task = session.get(Task, task_id)
            if task:
                return TaskResponse.model_validate(task)
            return None

    def get_task_with_assignee(
        self,
        task_id: int,
    ) -> Optional[TaskWithAssignee]:
        """Get a task with assignee name.

        Args:
            task_id: The task ID

        Returns:
            The task with assignee name if found, None otherwise
        """
        with Session(db.engine) as session:
            task = session.get(Task, task_id)
            if not task:
                return None

            assignee_name = None
            if task.assignee_employee_id:
                employee = session.get(Employee, task.assignee_employee_id)
                if employee:
                    assignee_name = employee.full_name

            return TaskWithAssignee(
                id=task.id,
                title=task.title,
                description=task.description,
                assignee_employee_id=task.assignee_employee_id,
                created_by=task.created_by,
                status=task.status,
                priority=task.priority,
                is_critical=task.is_critical,
                due_at=task.due_at,
                completed_at=task.completed_at,
                target_type=task.target_type,
                target_id=task.target_id,
                is_archived=task.is_archived,
                created_at=task.created_at,
                updated_at=task.updated_at,
                assignee_name=assignee_name,
            )

    def get_tasks(
        self,
        filters: Optional[TaskFilters] = None,
    ) -> TaskListResponse:
        """Get paginated list of tasks with optional filters.

        Args:
            filters: Query filters

        Returns:
            Paginated list of tasks
        """
        if filters is None:
            filters = TaskFilters()

        with Session(db.engine) as session:
            query = select(Task)

            # Apply filters
            if filters.status:
                query = query.where(Task.status == filters.status)
            if filters.priority:
                query = query.where(Task.priority == filters.priority)
            if filters.assignee_employee_id is not None:
                query = query.where(Task.assignee_employee_id == filters.assignee_employee_id)
            if filters.is_critical is not None:
                query = query.where(Task.is_critical == filters.is_critical)
            if filters.target_type:
                query = query.where(Task.target_type == filters.target_type)
            if filters.target_id is not None:
                query = query.where(Task.target_id == filters.target_id)
            if filters.is_archived is not None:
                query = query.where(Task.is_archived == filters.is_archived)
            if filters.due_before:
                query = query.where(Task.due_at <= filters.due_before)
            if filters.due_after:
                query = query.where(Task.due_at >= filters.due_after)
            if filters.search:
                search_pattern = f"%{filters.search}%"
                query = query.where(Task.title.ilike(search_pattern))

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = session.exec(count_query).one()

            # Apply pagination and ordering (critical first, then by due date, then by created)
            query = query.order_by(
                Task.is_critical.desc(),
                Task.due_at.asc().nullslast(),
                Task.created_at.desc(),
            )
            query = query.offset((filters.page - 1) * filters.page_size)
            query = query.limit(filters.page_size)

            # Execute query
            tasks = session.exec(query).all()

            items = [TaskResponse.model_validate(t) for t in tasks]

            return TaskListResponse(
                items=items,
                total=total,
                page=filters.page,
                page_size=filters.page_size,
            )

    def update_task(
        self,
        task_id: int,
        data: TaskUpdate,
        actor: Optional[str] = None,
    ) -> Optional[TaskResponse]:
        """Update a task.

        Args:
            task_id: ID of task to update
            data: Fields to update
            actor: Who is updating

        Returns:
            Updated task if found, None otherwise
        """
        actor = actor or self.actor

        with Session(db.engine) as session:
            task = session.get(Task, task_id)
            if not task:
                return None

            changes = {}

            if data.title is not None:
                changes["title"] = {"from": task.title, "to": data.title}
                task.title = data.title
            if data.description is not None:
                changes["description"] = {"from": task.description, "to": data.description}
                task.description = data.description
            if data.assignee_employee_id is not None:
                changes["assignee_employee_id"] = {
                    "from": task.assignee_employee_id,
                    "to": data.assignee_employee_id
                }
                task.assignee_employee_id = data.assignee_employee_id
            if data.status is not None:
                changes["status"] = {"from": task.status, "to": data.status}
                task.status = data.status
            if data.priority is not None:
                changes["priority"] = {"from": task.priority, "to": data.priority}
                task.priority = data.priority
            if data.is_critical is not None:
                changes["is_critical"] = {"from": task.is_critical, "to": data.is_critical}
                task.is_critical = data.is_critical
            if data.due_at is not None:
                changes["due_at"] = {
                    "from": task.due_at.isoformat() if task.due_at else None,
                    "to": data.due_at.isoformat()
                }
                task.due_at = data.due_at

            task.updated_at = datetime.now(timezone.utc)

            session.add(task)
            session.commit()
            session.refresh(task)

            if changes:
                log_action(
                    actor=actor,
                    object_type="task",
                    object_id=task.id,
                    action_type=ActionType.TASK_UPDATED.value,
                    summary=f"Updated task: {task.title}",
                    details={"changes": changes},
                )

            logger.info(f"Updated task: {task.title} (ID: {task_id})")

            return TaskResponse.model_validate(task)

    def complete_task(
        self,
        task_id: int,
        actor: Optional[str] = None,
    ) -> Optional[TaskResponse]:
        """Mark a task as complete and cancel pending reminders.

        Args:
            task_id: ID of task to complete
            actor: Who is completing

        Returns:
            Completed task if found, None otherwise
        """
        actor = actor or self.actor

        with Session(db.engine) as session:
            task = session.get(Task, task_id)
            if not task:
                return None

            task.status = TaskStatus.DONE.value
            task.completed_at = datetime.now(timezone.utc)
            task.updated_at = datetime.now(timezone.utc)

            session.add(task)
            session.commit()
            session.refresh(task)

            # Log the action
            log_action(
                actor=actor,
                object_type="task",
                object_id=task.id,
                action_type=ActionType.TASK_COMPLETED.value,
                summary=f"Completed task: {task.title}",
            )

            logger.info(f"Completed task: {task.title} (ID: {task_id})")

            result = TaskResponse.model_validate(task)

        # Cancel pending reminders for this task (outside session)
        self.reminder_service.cancel_reminders_for_target("task", task_id, actor=actor)

        return result

    def cancel_task(
        self,
        task_id: int,
        actor: Optional[str] = None,
    ) -> bool:
        """Cancel a task and its pending reminders.

        Args:
            task_id: ID of task to cancel
            actor: Who is cancelling

        Returns:
            True if cancelled, False if not found
        """
        actor = actor or self.actor

        with Session(db.engine) as session:
            task = session.get(Task, task_id)
            if not task:
                return False

            task.status = TaskStatus.CANCELLED.value
            task.is_archived = True
            task.updated_at = datetime.now(timezone.utc)

            session.add(task)
            session.commit()

            # Log the action
            log_action(
                actor=actor,
                object_type="task",
                object_id=task.id,
                action_type=ActionType.TASK_CANCELLED.value,
                summary=f"Cancelled task: {task.title}",
            )

            logger.info(f"Cancelled task: {task.title} (ID: {task_id})")

        # Cancel pending reminders for this task (outside session)
        self.reminder_service.cancel_reminders_for_target("task", task_id, actor=actor)

        return True

    def get_overdue_tasks(
        self,
        limit: int = 50,
    ) -> list[TaskResponse]:
        """Get tasks that are past their due date and not completed.

        Args:
            limit: Maximum number of tasks to return

        Returns:
            List of overdue tasks
        """
        now = datetime.now(timezone.utc)

        with Session(db.engine) as session:
            query = (
                select(Task)
                .where(Task.due_at < now)
                .where(Task.status.in_([TaskStatus.OPEN.value, TaskStatus.IN_PROGRESS.value]))
                .where(Task.is_archived == False)
                .order_by(Task.due_at.asc())
                .limit(limit)
            )
            tasks = session.exec(query).all()

            return [TaskResponse.model_validate(t) for t in tasks]

    def get_tasks_for_target(
        self,
        target_type: str,
        target_id: int,
        include_archived: bool = False,
    ) -> list[TaskResponse]:
        """Get all tasks linked to a specific target.

        Args:
            target_type: Type of target entity
            target_id: ID of target entity
            include_archived: Whether to include archived tasks

        Returns:
            List of tasks for the target
        """
        with Session(db.engine) as session:
            query = (
                select(Task)
                .where(Task.target_type == target_type)
                .where(Task.target_id == target_id)
            )

            if not include_archived:
                query = query.where(Task.is_archived == False)

            query = query.order_by(Task.created_at.desc())
            tasks = session.exec(query).all()

            return [TaskResponse.model_validate(t) for t in tasks]


# Singleton pattern
_task_service: Optional[TaskService] = None


def get_task_service() -> TaskService:
    """Get or create task service singleton."""
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service


__all__ = [
    "TaskService",
    "get_task_service",
]
