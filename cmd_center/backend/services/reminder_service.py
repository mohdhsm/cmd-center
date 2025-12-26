"""Reminder service for unified reminder management.

This service provides a centralized way to manage reminders for all entity types
(tasks, notes, documents, bonuses, etc.). It handles creation, querying,
dismissal, and sending of reminders.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select, func

from .. import db
from ..db import Reminder
from ..models.reminder_models import (
    ReminderCreate,
    ReminderUpdate,
    ReminderResponse,
    ReminderListResponse,
    ReminderFilters,
)
from ..constants import ActionType, ReminderStatus
from .intervention_service import log_action

logger = logging.getLogger(__name__)


class ReminderService:
    """Service for reminder CRUD and lifecycle operations."""

    def __init__(self, actor: str = "system"):
        """Initialize reminder service.

        Args:
            actor: Default actor for audit logging
        """
        self.actor = actor

    def create_reminder(
        self,
        data: ReminderCreate,
        actor: Optional[str] = None,
    ) -> ReminderResponse:
        """Create a new reminder.

        Args:
            data: Reminder creation data
            actor: Who is creating the reminder

        Returns:
            The created reminder
        """
        actor = actor or self.actor

        with Session(db.engine) as session:
            reminder = Reminder(
                target_type=data.target_type,
                target_id=data.target_id,
                remind_at=data.remind_at,
                channel=data.channel,
                message=data.message,
                is_recurring=data.is_recurring,
                recurrence_rule=data.recurrence_rule,
                status=ReminderStatus.PENDING.value,
            )
            session.add(reminder)
            session.commit()
            session.refresh(reminder)

            # Log the action
            log_action(
                actor=actor,
                object_type="reminder",
                object_id=reminder.id,
                action_type=ActionType.REMINDER_CREATED.value,
                summary=f"Created reminder for {data.target_type}:{data.target_id}",
                details={
                    "target_type": data.target_type,
                    "target_id": data.target_id,
                    "remind_at": data.remind_at.isoformat(),
                    "channel": data.channel,
                },
            )

            logger.info(
                f"Created reminder: {reminder.id} for {data.target_type}:{data.target_id}"
            )

            return ReminderResponse.model_validate(reminder)

    def get_reminder_by_id(
        self,
        reminder_id: int,
    ) -> Optional[ReminderResponse]:
        """Get a reminder by ID.

        Args:
            reminder_id: The reminder ID

        Returns:
            The reminder if found, None otherwise
        """
        with Session(db.engine) as session:
            reminder = session.get(Reminder, reminder_id)
            if reminder:
                return ReminderResponse.model_validate(reminder)
            return None

    def get_reminders(
        self,
        filters: Optional[ReminderFilters] = None,
    ) -> ReminderListResponse:
        """Get paginated list of reminders with optional filters.

        Args:
            filters: Query filters

        Returns:
            Paginated list of reminders
        """
        if filters is None:
            filters = ReminderFilters()

        with Session(db.engine) as session:
            query = select(Reminder)

            # Apply filters
            if filters.target_type:
                query = query.where(Reminder.target_type == filters.target_type)
            if filters.target_id is not None:
                query = query.where(Reminder.target_id == filters.target_id)
            if filters.status:
                query = query.where(Reminder.status == filters.status)
            if filters.channel:
                query = query.where(Reminder.channel == filters.channel)
            if filters.from_date:
                query = query.where(Reminder.remind_at >= filters.from_date)
            if filters.to_date:
                query = query.where(Reminder.remind_at <= filters.to_date)

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = session.exec(count_query).one()

            # Apply pagination and ordering
            query = query.order_by(Reminder.remind_at.asc())
            query = query.offset((filters.page - 1) * filters.page_size)
            query = query.limit(filters.page_size)

            # Execute query
            reminders = session.exec(query).all()

            items = [ReminderResponse.model_validate(r) for r in reminders]

            return ReminderListResponse(
                items=items,
                total=total,
                page=filters.page,
                page_size=filters.page_size,
            )

    def get_pending_reminders(
        self,
        before: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[ReminderResponse]:
        """Get pending reminders due before a given time.

        Args:
            before: Only return reminders due before this time (default: now)
            limit: Maximum number of reminders to return

        Returns:
            List of pending reminders ordered by remind_at
        """
        if before is None:
            before = datetime.now(timezone.utc)

        with Session(db.engine) as session:
            query = (
                select(Reminder)
                .where(Reminder.status == ReminderStatus.PENDING.value)
                .where(Reminder.remind_at <= before)
                .order_by(Reminder.remind_at.asc())
                .limit(limit)
            )
            reminders = session.exec(query).all()

            return [ReminderResponse.model_validate(r) for r in reminders]

    def get_reminders_for_target(
        self,
        target_type: str,
        target_id: int,
        status: Optional[str] = None,
    ) -> list[ReminderResponse]:
        """Get all reminders for a specific target.

        Args:
            target_type: Type of target entity
            target_id: ID of target entity
            status: Optional status filter

        Returns:
            List of reminders for the target
        """
        with Session(db.engine) as session:
            query = (
                select(Reminder)
                .where(Reminder.target_type == target_type)
                .where(Reminder.target_id == target_id)
            )

            if status:
                query = query.where(Reminder.status == status)

            query = query.order_by(Reminder.remind_at.asc())
            reminders = session.exec(query).all()

            return [ReminderResponse.model_validate(r) for r in reminders]

    def update_reminder(
        self,
        reminder_id: int,
        data: ReminderUpdate,
        actor: Optional[str] = None,
    ) -> Optional[ReminderResponse]:
        """Update a reminder.

        Args:
            reminder_id: ID of reminder to update
            data: Fields to update
            actor: Who is updating

        Returns:
            Updated reminder if found, None otherwise
        """
        actor = actor or self.actor

        with Session(db.engine) as session:
            reminder = session.get(Reminder, reminder_id)
            if not reminder:
                return None

            # Can only update pending reminders
            if reminder.status != ReminderStatus.PENDING.value:
                logger.warning(
                    f"Cannot update reminder {reminder_id}: status is {reminder.status}"
                )
                return None

            # Update fields
            if data.remind_at is not None:
                reminder.remind_at = data.remind_at
            if data.channel is not None:
                reminder.channel = data.channel
            if data.message is not None:
                reminder.message = data.message
            if data.is_recurring is not None:
                reminder.is_recurring = data.is_recurring
            if data.recurrence_rule is not None:
                reminder.recurrence_rule = data.recurrence_rule

            reminder.updated_at = datetime.now(timezone.utc)

            session.add(reminder)
            session.commit()
            session.refresh(reminder)

            logger.info(f"Updated reminder: {reminder_id}")

            return ReminderResponse.model_validate(reminder)

    def dismiss_reminder(
        self,
        reminder_id: int,
        actor: Optional[str] = None,
    ) -> Optional[ReminderResponse]:
        """Dismiss a reminder (mark as dismissed).

        Args:
            reminder_id: ID of reminder to dismiss
            actor: Who is dismissing

        Returns:
            Dismissed reminder if found and was pending, None otherwise
        """
        actor = actor or self.actor

        with Session(db.engine) as session:
            reminder = session.get(Reminder, reminder_id)
            if not reminder:
                return None

            # Can only dismiss pending reminders
            if reminder.status != ReminderStatus.PENDING.value:
                logger.warning(
                    f"Cannot dismiss reminder {reminder_id}: status is {reminder.status}"
                )
                return None

            reminder.status = ReminderStatus.DISMISSED.value
            reminder.updated_at = datetime.now(timezone.utc)

            session.add(reminder)
            session.commit()
            session.refresh(reminder)

            # Log the action
            log_action(
                actor=actor,
                object_type="reminder",
                object_id=reminder.id,
                action_type=ActionType.REMINDER_DISMISSED.value,
                summary=f"Dismissed reminder for {reminder.target_type}:{reminder.target_id}",
            )

            logger.info(f"Dismissed reminder: {reminder_id}")

            return ReminderResponse.model_validate(reminder)

    def cancel_reminder(
        self,
        reminder_id: int,
        actor: Optional[str] = None,
    ) -> bool:
        """Cancel a pending reminder.

        Args:
            reminder_id: ID of reminder to cancel
            actor: Who is cancelling

        Returns:
            True if cancelled, False if not found or not pending
        """
        actor = actor or self.actor

        with Session(db.engine) as session:
            reminder = session.get(Reminder, reminder_id)
            if not reminder:
                return False

            # Can only cancel pending reminders
            if reminder.status != ReminderStatus.PENDING.value:
                return False

            reminder.status = ReminderStatus.CANCELLED.value
            reminder.updated_at = datetime.now(timezone.utc)

            session.add(reminder)
            session.commit()

            # Log the action
            log_action(
                actor=actor,
                object_type="reminder",
                object_id=reminder.id,
                action_type=ActionType.REMINDER_CANCELLED.value,
                summary=f"Cancelled reminder for {reminder.target_type}:{reminder.target_id}",
            )

            logger.info(f"Cancelled reminder: {reminder_id}")

            return True

    def cancel_reminders_for_target(
        self,
        target_type: str,
        target_id: int,
        actor: Optional[str] = None,
    ) -> int:
        """Cancel all pending reminders for a target.

        Useful when a task is completed or a note is archived.

        Args:
            target_type: Type of target entity
            target_id: ID of target entity
            actor: Who is cancelling

        Returns:
            Number of reminders cancelled
        """
        actor = actor or self.actor

        with Session(db.engine) as session:
            query = (
                select(Reminder)
                .where(Reminder.target_type == target_type)
                .where(Reminder.target_id == target_id)
                .where(Reminder.status == ReminderStatus.PENDING.value)
            )
            reminders = session.exec(query).all()

            count = 0
            for reminder in reminders:
                reminder.status = ReminderStatus.CANCELLED.value
                reminder.updated_at = datetime.now(timezone.utc)
                session.add(reminder)
                count += 1

            session.commit()

            if count > 0:
                logger.info(
                    f"Cancelled {count} reminders for {target_type}:{target_id}"
                )

            return count

    def mark_reminder_sent(
        self,
        reminder_id: int,
        actor: Optional[str] = None,
    ) -> Optional[ReminderResponse]:
        """Mark a reminder as sent.

        Called by the reminder processing loop after successfully sending.

        Args:
            reminder_id: ID of reminder
            actor: Who/what processed it

        Returns:
            Updated reminder if found, None otherwise
        """
        actor = actor or self.actor

        with Session(db.engine) as session:
            reminder = session.get(Reminder, reminder_id)
            if not reminder:
                return None

            reminder.status = ReminderStatus.SENT.value
            reminder.sent_at = datetime.now(timezone.utc)
            reminder.updated_at = datetime.now(timezone.utc)

            session.add(reminder)
            session.commit()
            session.refresh(reminder)

            # Log the action
            log_action(
                actor=actor,
                object_type="reminder",
                object_id=reminder.id,
                action_type=ActionType.REMINDER_SENT.value,
                summary=f"Sent reminder for {reminder.target_type}:{reminder.target_id} via {reminder.channel}",
            )

            logger.info(f"Marked reminder {reminder_id} as sent")

            return ReminderResponse.model_validate(reminder)

    def mark_reminder_failed(
        self,
        reminder_id: int,
        error_message: str,
        actor: Optional[str] = None,
    ) -> Optional[ReminderResponse]:
        """Mark a reminder as failed.

        Called by the reminder processing loop when sending fails.

        Args:
            reminder_id: ID of reminder
            error_message: Error description
            actor: Who/what processed it

        Returns:
            Updated reminder if found, None otherwise
        """
        actor = actor or self.actor

        with Session(db.engine) as session:
            reminder = session.get(Reminder, reminder_id)
            if not reminder:
                return None

            reminder.status = ReminderStatus.FAILED.value
            reminder.error_message = error_message
            reminder.updated_at = datetime.now(timezone.utc)

            session.add(reminder)
            session.commit()
            session.refresh(reminder)

            # Log the action
            log_action(
                actor=actor,
                object_type="reminder",
                object_id=reminder.id,
                action_type=ActionType.REMINDER_FAILED.value,
                summary=f"Failed to send reminder for {reminder.target_type}:{reminder.target_id}",
                details={"error": error_message},
            )

            logger.error(f"Reminder {reminder_id} failed: {error_message}")

            return ReminderResponse.model_validate(reminder)


# Singleton pattern
_reminder_service: Optional[ReminderService] = None


def get_reminder_service() -> ReminderService:
    """Get or create reminder service singleton."""
    global _reminder_service
    if _reminder_service is None:
        _reminder_service = ReminderService()
    return _reminder_service


__all__ = [
    "ReminderService",
    "get_reminder_service",
]
