"""Task overdue monitoring loop.

Checks for overdue tasks and escalates as needed.
"""

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from ...db import Task, Employee
from ...constants import FindingSeverity, TaskStatus, TargetType
from ..loop_engine import BaseLoop
from ..reminder_service import get_reminder_service
from ...models.reminder_models import ReminderCreate


class TaskOverdueLoop(BaseLoop):
    """Monitor tasks for overdue status."""

    name = "task_overdue"
    description = "Check for overdue and soon-due tasks"
    interval_minutes = 60  # Run every hour

    # Configurable thresholds (in hours)
    CRITICAL_HOURS = 0  # Already overdue
    WARNING_HOURS = 24  # Due within 24 hours

    def execute(self, session: Session) -> None:
        """Check for overdue and soon-due tasks."""
        now = datetime.now(timezone.utc)
        # Use naive datetime for database comparison (SQLite stores naive)
        now_naive = now.replace(tzinfo=None)
        warning_cutoff = now_naive + timedelta(hours=self.WARNING_HOURS)

        # Find open tasks that are overdue or due soon
        query = (
            select(Task)
            .where(Task.due_at <= warning_cutoff)
            .where(Task.status.in_([
                TaskStatus.OPEN.value,
                TaskStatus.IN_PROGRESS.value,
            ]))
            .where(Task.is_archived == False)
            .order_by(Task.due_at.asc())
        )
        tasks = session.exec(query).all()

        for task in tasks:
            # Ensure we compare naive datetimes
            due = task.due_at.replace(tzinfo=None) if task.due_at.tzinfo else task.due_at
            is_overdue = due < now_naive

            # Get assignee name
            assignee_name = "Unassigned"
            if task.assignee_employee_id:
                employee = session.get(Employee, task.assignee_employee_id)
                if employee:
                    assignee_name = employee.full_name

            # Determine severity and message
            if is_overdue:
                hours_overdue = int((now_naive - due).total_seconds() / 3600)
                days_overdue = hours_overdue // 24

                if task.is_critical:
                    severity = FindingSeverity.CRITICAL.value
                    if days_overdue >= 1:
                        message = f"CRITICAL task '{task.title}' is {days_overdue} days overdue!"
                    else:
                        message = f"CRITICAL task '{task.title}' is {hours_overdue} hours overdue!"
                    recommended = "Escalate immediately to management"
                else:
                    severity = FindingSeverity.WARNING.value
                    if days_overdue >= 1:
                        message = f"Task '{task.title}' is {days_overdue} days overdue"
                    else:
                        message = f"Task '{task.title}' is {hours_overdue} hours overdue"
                    recommended = f"Follow up with {assignee_name}"
            else:
                # Due soon but not overdue
                hours_until = int((due - now_naive).total_seconds() / 3600)
                severity = FindingSeverity.INFO.value
                message = f"Task '{task.title}' is due in {hours_until} hours"
                recommended = "Ensure task is on track for completion"

                # Only create findings for critical tasks that are due soon
                if not task.is_critical:
                    continue

                severity = FindingSeverity.WARNING.value
                message = f"CRITICAL task '{task.title}' is due in {hours_until} hours"

            # Add context
            message += f" (Assigned to: {assignee_name})"

            # Add finding (with deduplication)
            finding = self.add_finding(
                session=session,
                severity=severity,
                target_type=TargetType.TASK.value,
                target_id=task.id,
                message=message,
                recommended_action=recommended,
            )

            # If overdue and critical, create escalation reminder
            if finding and is_overdue and task.is_critical:
                self._create_escalation_reminder(task, assignee_name)

    def _create_escalation_reminder(self, task: Task, assignee_name: str) -> None:
        """Create an escalation reminder for overdue critical tasks."""
        reminder_service = get_reminder_service()

        # Use naive datetime for consistency with database
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        remind_at = now_naive + timedelta(hours=2)  # Follow up in 2 hours

        try:
            reminder_service.create_reminder(
                ReminderCreate(
                    target_type=TargetType.TASK.value,
                    target_id=task.id,
                    remind_at=remind_at,
                    channel="email",
                    message=f"ESCALATION: Critical task '{task.title}' (assigned to {assignee_name}) is still overdue",
                ),
                actor="task_overdue_loop",
            )
        except Exception:
            # Reminder may already exist, that's okay
            pass
