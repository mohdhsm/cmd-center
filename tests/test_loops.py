"""Unit tests for individual loop implementations."""

from datetime import datetime, timedelta, timezone

import pytest

from cmd_center.backend.services.loops import (
    DocsExpiryLoop,
    BonusDueLoop,
    TaskOverdueLoop,
    ReminderProcessingLoop,
)
from cmd_center.backend.services.document_service import DocumentService
from cmd_center.backend.services.bonus_service import BonusService
from cmd_center.backend.services.task_service import TaskService
from cmd_center.backend.services.reminder_service import ReminderService
from cmd_center.backend.services.employee_service import EmployeeService
from cmd_center.backend.models.document_models import DocumentCreate
from cmd_center.backend.models.bonus_models import BonusCreate
from cmd_center.backend.models.task_models import TaskCreate
from cmd_center.backend.models.reminder_models import ReminderCreate
from cmd_center.backend.models.employee_models import EmployeeCreate
from cmd_center.backend.constants import (
    FindingSeverity,
    DocumentStatus,
    BonusStatus,
    TaskStatus,
    ReminderStatus,
)


class TestDocsExpiryLoop:
    """Test cases for DocsExpiryLoop."""

    def test_finds_expiring_in_30_days(self, override_db):
        """Documents expiring in 30 days generate finding."""
        doc_service = DocumentService()
        now = datetime.now(timezone.utc)

        # Create document expiring in 20 days
        doc_service.create_document(DocumentCreate(
            title="Expiring Document",
            document_type="license",
            expiry_date=now + timedelta(days=20),
        ))

        loop = DocsExpiryLoop()
        result = loop.run()

        assert result.findings_count == 1

    def test_finds_expiring_in_7_days_critical(self, override_db):
        """Documents expiring in 7 days are critical severity."""
        doc_service = DocumentService()
        now = datetime.now(timezone.utc)

        # Create document expiring in 5 days
        doc_service.create_document(DocumentCreate(
            title="Critical Document",
            document_type="license",
            expiry_date=now + timedelta(days=5),
        ))

        loop = DocsExpiryLoop()
        result = loop.run()

        assert result.findings_count == 1

        # Verify it's critical by checking the loop run
        from cmd_center.backend.services.loop_engine import get_loop_service
        service = get_loop_service()
        run = service.get_loop_run_by_id(result.id)
        assert run.findings[0].severity == FindingSeverity.CRITICAL.value

    def test_ignores_expired_documents(self, override_db):
        """Already expired documents are not included."""
        doc_service = DocumentService()
        now = datetime.now(timezone.utc)

        # Create already expired document
        doc = doc_service.create_document(DocumentCreate(
            title="Expired Document",
            document_type="license",
            expiry_date=now - timedelta(days=5),
        ))
        # Mark as expired
        from cmd_center.backend.models.document_models import DocumentUpdate
        doc_service.update_document(doc.id, DocumentUpdate(status=DocumentStatus.EXPIRED.value))

        loop = DocsExpiryLoop()
        result = loop.run()

        assert result.findings_count == 0

    def test_ignores_documents_beyond_30_days(self, override_db):
        """Documents expiring beyond 30 days are not included."""
        doc_service = DocumentService()
        now = datetime.now(timezone.utc)

        # Create document expiring in 45 days
        doc_service.create_document(DocumentCreate(
            title="Future Document",
            document_type="license",
            expiry_date=now + timedelta(days=45),
        ))

        loop = DocsExpiryLoop()
        result = loop.run()

        assert result.findings_count == 0


class TestBonusDueLoop:
    """Test cases for BonusDueLoop."""

    @pytest.fixture
    def employee_id(self, override_db):
        """Create an employee and return its ID."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))
        return employee.id

    def test_finds_bonus_due_in_30_days(self, override_db, employee_id):
        """Bonuses due in 30 days generate finding."""
        bonus_service = BonusService()
        now = datetime.now(timezone.utc)

        # Create bonus due in 20 days
        bonus_service.create_bonus(BonusCreate(
            employee_id=employee_id,
            title="Due Bonus",
            amount=5000.0,
            promised_date=now,
            due_date=now + timedelta(days=20),
        ))

        loop = BonusDueLoop()
        result = loop.run()

        assert result.findings_count == 1

    def test_finds_bonus_due_in_7_days_critical(self, override_db, employee_id):
        """Bonuses due in 7 days are critical severity."""
        bonus_service = BonusService()
        now = datetime.now(timezone.utc)

        # Create bonus due in 5 days
        bonus_service.create_bonus(BonusCreate(
            employee_id=employee_id,
            title="Urgent Bonus",
            amount=5000.0,
            promised_date=now,
            due_date=now + timedelta(days=5),
        ))

        loop = BonusDueLoop()
        result = loop.run()

        # Verify it's critical
        from cmd_center.backend.services.loop_engine import get_loop_service
        service = get_loop_service()
        run = service.get_loop_run_by_id(result.id)
        assert run.findings[0].severity == FindingSeverity.CRITICAL.value

    def test_ignores_paid_bonuses(self, override_db, employee_id):
        """Paid bonuses are not included."""
        bonus_service = BonusService()
        now = datetime.now(timezone.utc)

        # Create and fully pay bonus
        bonus = bonus_service.create_bonus(BonusCreate(
            employee_id=employee_id,
            title="Paid Bonus",
            amount=1000.0,
            promised_date=now,
            due_date=now + timedelta(days=10),
        ))
        from cmd_center.backend.models.bonus_models import BonusPaymentCreate
        bonus_service.record_payment(bonus.id, BonusPaymentCreate(
            amount=1000.0,
            payment_date=now,
        ))

        loop = BonusDueLoop()
        result = loop.run()

        assert result.findings_count == 0


class TestTaskOverdueLoop:
    """Test cases for TaskOverdueLoop."""

    def test_finds_overdue_tasks(self, override_db):
        """Overdue tasks generate finding."""
        task_service = TaskService()
        now = datetime.now(timezone.utc)

        # Create overdue task
        task_service.create_task(TaskCreate(
            title="Overdue Task",
            due_at=now - timedelta(hours=2),
        ))

        loop = TaskOverdueLoop()
        result = loop.run()

        assert result.findings_count == 1

    def test_critical_overdue_is_critical_severity(self, override_db):
        """Overdue critical tasks are critical severity."""
        task_service = TaskService()
        now = datetime.now(timezone.utc)

        # Create overdue critical task
        task_service.create_task(TaskCreate(
            title="Critical Overdue",
            due_at=now - timedelta(hours=1),
            is_critical=True,
        ))

        loop = TaskOverdueLoop()
        result = loop.run()

        from cmd_center.backend.services.loop_engine import get_loop_service
        service = get_loop_service()
        run = service.get_loop_run_by_id(result.id)
        assert run.findings[0].severity == FindingSeverity.CRITICAL.value

    def test_ignores_completed_tasks(self, override_db):
        """Completed tasks are not included."""
        task_service = TaskService()
        now = datetime.now(timezone.utc)

        # Create and complete task
        task = task_service.create_task(TaskCreate(
            title="Completed Task",
            due_at=now - timedelta(hours=1),
        ))
        task_service.complete_task(task.id)

        loop = TaskOverdueLoop()
        result = loop.run()

        assert result.findings_count == 0


class TestReminderProcessingLoop:
    """Test cases for ReminderProcessingLoop."""

    def test_processes_due_reminders(self, override_db):
        """Processes reminders where remind_at <= now."""
        reminder_service = ReminderService()
        now = datetime.now(timezone.utc)

        # Create due reminder
        reminder_service.create_reminder(ReminderCreate(
            target_type="test",
            target_id=1,
            remind_at=now - timedelta(minutes=5),
            channel="in_app",
            message="Test reminder",
        ))

        loop = ReminderProcessingLoop()
        result = loop.run()

        # Check reminder was processed
        reminders = reminder_service.get_pending_reminders()
        assert len(reminders) == 0  # No pending left

    def test_updates_status_after_send(self, override_db):
        """Status updated to sent after successful send."""
        reminder_service = ReminderService()
        now = datetime.now(timezone.utc)

        # Create due reminder
        reminder = reminder_service.create_reminder(ReminderCreate(
            target_type="test",
            target_id=1,
            remind_at=now - timedelta(minutes=5),
            channel="in_app",
            message="Test reminder",
        ))

        loop = ReminderProcessingLoop()
        loop.run()

        # Check status
        updated = reminder_service.get_reminder_by_id(reminder.id)
        assert updated.status == ReminderStatus.SENT.value
        assert updated.sent_at is not None

    def test_ignores_future_reminders(self, override_db):
        """Future reminders are not processed."""
        reminder_service = ReminderService()
        now = datetime.now(timezone.utc)

        # Create future reminder
        reminder = reminder_service.create_reminder(ReminderCreate(
            target_type="test",
            target_id=1,
            remind_at=now + timedelta(hours=1),
            channel="in_app",
            message="Future reminder",
        ))

        loop = ReminderProcessingLoop()
        result = loop.run()

        # Check reminder still pending (use get_reminder_by_id since it's not due yet)
        updated = reminder_service.get_reminder_by_id(reminder.id)
        assert updated.status == ReminderStatus.PENDING.value

    def test_processes_email_reminders(self, override_db):
        """Email reminders are processed."""
        reminder_service = ReminderService()
        now = datetime.now(timezone.utc)

        # Create due email reminder
        reminder = reminder_service.create_reminder(ReminderCreate(
            target_type="test",
            target_id=1,
            remind_at=now - timedelta(minutes=5),
            channel="email",
            message="Email reminder",
        ))

        loop = ReminderProcessingLoop()
        loop.run()

        # Check status
        updated = reminder_service.get_reminder_by_id(reminder.id)
        assert updated.status == ReminderStatus.SENT.value
