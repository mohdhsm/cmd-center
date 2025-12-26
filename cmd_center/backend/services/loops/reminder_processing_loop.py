"""Reminder processing loop.

Processes pending reminders and sends notifications.
"""

import logging
from datetime import datetime, timezone

from sqlmodel import Session, select

from ...db import Reminder
from ...constants import ReminderStatus, ReminderChannel, FindingSeverity
from ..loop_engine import BaseLoop

logger = logging.getLogger(__name__)


class ReminderProcessingLoop(BaseLoop):
    """Process and send pending reminders."""

    name = "reminder_processing"
    description = "Process pending reminders and send notifications"
    interval_minutes = 5  # Run every 5 minutes

    def execute(self, session: Session) -> None:
        """Process all pending reminders that are due."""
        now = datetime.now(timezone.utc)
        # Use naive datetime for database comparison (SQLite stores naive)
        now_naive = now.replace(tzinfo=None)

        # Find pending reminders that are due
        query = (
            select(Reminder)
            .where(Reminder.remind_at <= now_naive)
            .where(Reminder.status == ReminderStatus.PENDING.value)
            .order_by(Reminder.remind_at.asc())
            .limit(100)  # Process in batches
        )
        reminders = session.exec(query).all()

        for reminder in reminders:
            try:
                self._process_reminder(session, reminder)
            except Exception as e:
                self._mark_failed(session, reminder, str(e))
                self.add_finding(
                    session=session,
                    severity=FindingSeverity.WARNING.value,
                    target_type=reminder.target_type,
                    target_id=reminder.target_id,
                    message=f"Failed to send reminder: {str(e)}",
                    recommended_action="Check notification configuration",
                )

    def _process_reminder(self, session: Session, reminder: Reminder) -> None:
        """Process a single reminder."""
        channel = reminder.channel

        if channel == ReminderChannel.EMAIL.value:
            self._send_email_reminder(reminder)
        elif channel == ReminderChannel.IN_APP.value:
            self._send_in_app_reminder(reminder)
        else:
            raise ValueError(f"Unknown channel: {channel}")

        # Mark as sent
        reminder.status = ReminderStatus.SENT.value
        reminder.sent_at = datetime.now(timezone.utc)
        session.add(reminder)
        session.commit()

        logger.info(
            f"Sent {channel} reminder for {reminder.target_type}:{reminder.target_id}"
        )

    def _send_email_reminder(self, reminder: Reminder) -> None:
        """Send an email reminder."""
        # In production, this would integrate with the email service
        # For now, we just log it
        logger.info(
            f"[EMAIL] Reminder: {reminder.message or 'No message'} "
            f"(Target: {reminder.target_type}:{reminder.target_id})"
        )

        # TODO: Integrate with actual email service
        # from ..email_service import get_email_service
        # email_service = get_email_service()
        # email_service.send_reminder_email(reminder)

    def _send_in_app_reminder(self, reminder: Reminder) -> None:
        """Send an in-app reminder."""
        # In-app reminders are just marked as sent
        # The frontend will query for sent reminders
        logger.info(
            f"[IN_APP] Reminder: {reminder.message or 'No message'} "
            f"(Target: {reminder.target_type}:{reminder.target_id})"
        )

    def _mark_failed(self, session: Session, reminder: Reminder, error: str) -> None:
        """Mark a reminder as failed."""
        reminder.status = ReminderStatus.FAILED.value
        reminder.error_message = error
        session.add(reminder)
        session.commit()

        logger.error(
            f"Failed to send reminder {reminder.id}: {error}"
        )
