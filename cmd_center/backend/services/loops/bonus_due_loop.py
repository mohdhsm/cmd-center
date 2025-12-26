"""Bonus due date monitoring loop.

Checks for bonuses with upcoming due dates and creates reminders.
"""

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from ...db import EmployeeBonus, Employee
from ...constants import FindingSeverity, BonusStatus, TargetType
from ..loop_engine import BaseLoop
from ..reminder_service import get_reminder_service
from ...models.reminder_models import ReminderCreate


class BonusDueLoop(BaseLoop):
    """Monitor bonuses for upcoming due dates."""

    name = "bonus_due"
    description = "Check for bonuses due within 30 days"
    interval_minutes = 60 * 12  # Run every 12 hours

    # Configurable thresholds
    CRITICAL_DAYS = 7
    WARNING_DAYS = 30

    def execute(self, session: Session) -> None:
        """Check for bonuses with upcoming due dates."""
        now = datetime.now(timezone.utc)
        # Use naive datetime for database comparison (SQLite stores naive)
        now_naive = now.replace(tzinfo=None)
        warning_cutoff = now_naive + timedelta(days=self.WARNING_DAYS)

        # Find unpaid bonuses with due dates within 30 days
        query = (
            select(EmployeeBonus)
            .where(EmployeeBonus.due_date >= now_naive)
            .where(EmployeeBonus.due_date <= warning_cutoff)
            .where(EmployeeBonus.status.notin_([
                BonusStatus.PAID.value,
                BonusStatus.CANCELLED.value,
            ]))
            .order_by(EmployeeBonus.due_date.asc())
        )
        bonuses = session.exec(query).all()

        for bonus in bonuses:
            # Ensure we compare naive datetimes
            due = bonus.due_date.replace(tzinfo=None) if bonus.due_date.tzinfo else bonus.due_date
            days_until_due = (due - now_naive).days

            # Get employee name
            employee = session.get(Employee, bonus.employee_id)
            employee_name = employee.full_name if employee else f"Employee #{bonus.employee_id}"

            # Determine severity
            if days_until_due <= self.CRITICAL_DAYS:
                severity = FindingSeverity.CRITICAL.value
                message = f"Bonus '{bonus.title}' for {employee_name} due in {days_until_due} days!"
                recommended = "Process payment immediately"
            else:
                severity = FindingSeverity.WARNING.value
                message = f"Bonus '{bonus.title}' for {employee_name} due in {days_until_due} days"
                recommended = "Schedule payment processing"

            # Include amount info
            if bonus.status == BonusStatus.PARTIAL.value:
                message += f" (Partial payment pending)"

            # Add finding (with deduplication)
            finding = self.add_finding(
                session=session,
                severity=severity,
                target_type=TargetType.BONUS.value,
                target_id=bonus.id,
                message=message,
                recommended_action=recommended,
            )

            # If this is a new finding (not deduplicated), create reminder
            if finding:
                self._create_reminder(bonus, employee_name, days_until_due)

    def _create_reminder(
        self,
        bonus: EmployeeBonus,
        employee_name: str,
        days_until: int,
    ) -> None:
        """Create a reminder for bonus due date."""
        reminder_service = get_reminder_service()

        # Ensure due_date is naive for comparison
        due = bonus.due_date.replace(tzinfo=None) if bonus.due_date.tzinfo else bonus.due_date
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)

        # Set reminder for 3 days before due or now if less
        remind_at = due - timedelta(days=3)
        if remind_at < now_naive:
            remind_at = now_naive + timedelta(hours=1)

        try:
            reminder_service.create_reminder(
                ReminderCreate(
                    target_type=TargetType.BONUS.value,
                    target_id=bonus.id,
                    remind_at=remind_at,
                    channel="email",
                    message=f"Bonus '{bonus.title}' for {employee_name} due on {due.strftime('%Y-%m-%d')} ({bonus.amount} {bonus.currency})",
                ),
                actor="bonus_due_loop",
            )
        except Exception:
            # Reminder may already exist, that's okay
            pass
