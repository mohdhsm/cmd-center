"""Document expiry monitoring loop.

Checks for documents expiring soon and creates reminders/tasks.
"""

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from ...db import LegalDocument
from ...constants import FindingSeverity, DocumentStatus, TargetType
from ..loop_engine import BaseLoop
from ..reminder_service import get_reminder_service
from ..task_service import get_task_service
from ...models.reminder_models import ReminderCreate
from ...models.task_models import TaskCreate


class DocsExpiryLoop(BaseLoop):
    """Monitor documents for upcoming expiry."""

    name = "docs_expiry"
    description = "Check for documents expiring within 30 days"
    interval_minutes = 60 * 6  # Run every 6 hours

    # Configurable thresholds
    CRITICAL_DAYS = 7
    WARNING_DAYS = 30

    def execute(self, session: Session) -> None:
        """Check for expiring documents."""
        now = datetime.now(timezone.utc)
        # Use naive datetime for database comparison (SQLite stores naive)
        now_naive = now.replace(tzinfo=None)
        warning_cutoff = now_naive + timedelta(days=self.WARNING_DAYS)

        # Find active documents expiring within 30 days
        query = (
            select(LegalDocument)
            .where(LegalDocument.expiry_date >= now_naive)
            .where(LegalDocument.expiry_date <= warning_cutoff)
            .where(LegalDocument.status == DocumentStatus.ACTIVE.value)
            .order_by(LegalDocument.expiry_date.asc())
        )
        documents = session.exec(query).all()

        for doc in documents:
            # Ensure we compare naive datetimes
            expiry = doc.expiry_date.replace(tzinfo=None) if doc.expiry_date.tzinfo else doc.expiry_date
            days_until_expiry = (expiry - now_naive).days

            # Determine severity
            if days_until_expiry <= self.CRITICAL_DAYS:
                severity = FindingSeverity.CRITICAL.value
                message = f"Document '{doc.title}' expires in {days_until_expiry} days!"
                recommended = "Initiate immediate renewal process"
            else:
                severity = FindingSeverity.WARNING.value
                message = f"Document '{doc.title}' expires in {days_until_expiry} days"
                recommended = "Schedule renewal with responsible party"

            # Add finding (with deduplication)
            finding = self.add_finding(
                session=session,
                severity=severity,
                target_type=TargetType.DOCUMENT.value,
                target_id=doc.id,
                message=message,
                recommended_action=recommended,
            )

            # If this is a new finding (not deduplicated), create reminder and task
            if finding:
                self._create_reminder(doc, days_until_expiry)
                if severity == FindingSeverity.CRITICAL.value:
                    self._create_renewal_task(doc)

    def _create_reminder(self, doc: LegalDocument, days_until: int) -> None:
        """Create a reminder for document expiry."""
        reminder_service = get_reminder_service()

        # Ensure expiry_date is naive for comparison
        expiry = doc.expiry_date.replace(tzinfo=None) if doc.expiry_date.tzinfo else doc.expiry_date
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)

        # Set reminder for 7 days before expiry or now if less
        remind_at = expiry - timedelta(days=7)
        if remind_at < now_naive:
            remind_at = now_naive + timedelta(hours=1)

        try:
            reminder_service.create_reminder(
                ReminderCreate(
                    target_type=TargetType.DOCUMENT.value,
                    target_id=doc.id,
                    remind_at=remind_at,
                    channel="email",
                    message=f"Document '{doc.title}' expires on {expiry.strftime('%Y-%m-%d')}",
                ),
                actor="docs_expiry_loop",
            )
        except Exception:
            # Reminder may already exist, that's okay
            pass

    def _create_renewal_task(self, doc: LegalDocument) -> None:
        """Create a renewal task for critical documents."""
        task_service = get_task_service()

        # Ensure expiry_date is naive for arithmetic
        expiry = doc.expiry_date.replace(tzinfo=None) if doc.expiry_date.tzinfo else doc.expiry_date

        try:
            task_service.create_task(
                TaskCreate(
                    title=f"Renew: {doc.title}",
                    description=f"Document expires on {expiry.strftime('%Y-%m-%d')}. Initiate renewal process immediately.",
                    priority="high",
                    is_critical=True,
                    due_at=expiry - timedelta(days=1),
                    target_type=TargetType.DOCUMENT.value,
                    target_id=doc.id,
                    assignee_employee_id=doc.responsible_employee_id,
                ),
                actor="docs_expiry_loop",
            )
        except Exception:
            # Task may already exist, that's okay
            pass
