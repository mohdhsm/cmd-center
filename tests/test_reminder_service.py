"""Unit tests for ReminderService."""

import pytest
from datetime import datetime, timedelta, timezone

from cmd_center.backend.services.reminder_service import (
    ReminderService,
    get_reminder_service,
)
from cmd_center.backend.models.reminder_models import (
    ReminderCreate,
    ReminderUpdate,
    ReminderFilters,
)
from cmd_center.backend.constants import ReminderStatus


class TestReminderService:
    """Tests for ReminderService CRUD operations."""

    def test_create_reminder(self, override_db):
        """Creates reminder with all fields."""
        service = ReminderService(actor="test")
        data = ReminderCreate(
            target_type="task",
            target_id=123,
            remind_at=datetime.now(timezone.utc) + timedelta(hours=24),
            channel="email",
            message="Don't forget!",
        )

        result = service.create_reminder(data)

        assert result.id is not None
        assert result.target_type == "task"
        assert result.target_id == 123
        assert result.channel == "email"
        assert result.message == "Don't forget!"
        assert result.status == "pending"

    def test_create_reminder_defaults(self, override_db):
        """Creates reminder with default values."""
        service = ReminderService(actor="test")
        data = ReminderCreate(
            target_type="note",
            target_id=456,
            remind_at=datetime.now(timezone.utc) + timedelta(days=1),
        )

        result = service.create_reminder(data)

        assert result.channel == "in_app"
        assert result.message is None
        assert result.is_recurring is False
        assert result.status == "pending"

    def test_get_reminder_by_id(self, override_db):
        """Can retrieve reminder by ID."""
        service = ReminderService(actor="test")
        data = ReminderCreate(
            target_type="task",
            target_id=1,
            remind_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        created = service.create_reminder(data)

        result = service.get_reminder_by_id(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.target_type == "task"

    def test_get_reminder_by_id_not_found(self, override_db):
        """Returns None for non-existent reminder."""
        service = ReminderService(actor="test")

        result = service.get_reminder_by_id(99999)

        assert result is None

    def test_get_pending_reminders_before_time(self, override_db):
        """Returns only pending reminders before cutoff."""
        service = ReminderService(actor="test")
        now = datetime.now(timezone.utc)

        # Create reminders at different times
        past = service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=1,
            remind_at=now - timedelta(hours=1),
        ))
        future = service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=2,
            remind_at=now + timedelta(hours=24),
        ))

        result = service.get_pending_reminders(before=now)

        assert len(result) == 1
        assert result[0].id == past.id

    def test_get_pending_reminders_excludes_sent(self, override_db):
        """Excludes already sent reminders."""
        service = ReminderService(actor="test")
        now = datetime.now(timezone.utc)

        # Create a reminder and mark it sent
        reminder = service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=1,
            remind_at=now - timedelta(hours=1),
        ))
        service.mark_reminder_sent(reminder.id)

        # Create another pending reminder
        pending = service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=2,
            remind_at=now - timedelta(minutes=30),
        ))

        result = service.get_pending_reminders(before=now)

        assert len(result) == 1
        assert result[0].id == pending.id

    def test_get_reminders_for_target(self, override_db):
        """Returns reminders for specific target_type/target_id."""
        service = ReminderService(actor="test")
        now = datetime.now(timezone.utc)

        # Create reminders for different targets
        service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=100,
            remind_at=now + timedelta(hours=1),
        ))
        service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=100,
            remind_at=now + timedelta(hours=2),
        ))
        service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=200,
            remind_at=now + timedelta(hours=1),
        ))

        result = service.get_reminders_for_target("task", 100)

        assert len(result) == 2
        assert all(r.target_id == 100 for r in result)

    def test_dismiss_reminder(self, override_db):
        """Sets status to dismissed."""
        service = ReminderService(actor="test")
        reminder = service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=1,
            remind_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))

        result = service.dismiss_reminder(reminder.id)

        assert result is not None
        assert result.status == "dismissed"

    def test_dismiss_non_pending_fails(self, override_db):
        """Cannot dismiss already sent reminder."""
        service = ReminderService(actor="test")
        reminder = service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=1,
            remind_at=datetime.now(timezone.utc) - timedelta(hours=1),
        ))
        service.mark_reminder_sent(reminder.id)

        result = service.dismiss_reminder(reminder.id)

        assert result is None

    def test_cancel_reminder(self, override_db):
        """Cancels pending reminder."""
        service = ReminderService(actor="test")
        reminder = service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=1,
            remind_at=datetime.now(timezone.utc) + timedelta(hours=1),
        ))

        result = service.cancel_reminder(reminder.id)

        assert result is True

        # Verify status
        updated = service.get_reminder_by_id(reminder.id)
        assert updated.status == "cancelled"

    def test_cancel_reminders_for_target(self, override_db):
        """Cancels all pending reminders for target."""
        service = ReminderService(actor="test")
        now = datetime.now(timezone.utc)

        # Create multiple reminders for same target
        service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=100,
            remind_at=now + timedelta(hours=1),
        ))
        service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=100,
            remind_at=now + timedelta(hours=2),
        ))
        # One for different target
        service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=200,
            remind_at=now + timedelta(hours=1),
        ))

        count = service.cancel_reminders_for_target("task", 100)

        assert count == 2

        # Verify remaining reminder is not cancelled
        remaining = service.get_reminders_for_target("task", 200)
        assert len(remaining) == 1
        assert remaining[0].status == "pending"

    def test_mark_reminder_sent(self, override_db):
        """Sending updates status and sent_at."""
        service = ReminderService(actor="test")
        reminder = service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=1,
            remind_at=datetime.now(timezone.utc) - timedelta(hours=1),
        ))

        result = service.mark_reminder_sent(reminder.id)

        assert result is not None
        assert result.status == "sent"
        assert result.sent_at is not None

    def test_mark_reminder_failed(self, override_db):
        """Failed send sets status=failed and error_message."""
        service = ReminderService(actor="test")
        reminder = service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=1,
            remind_at=datetime.now(timezone.utc) - timedelta(hours=1),
        ))

        result = service.mark_reminder_failed(reminder.id, "SMTP connection failed")

        assert result is not None
        assert result.status == "failed"
        assert result.error_message == "SMTP connection failed"

    def test_update_reminder(self, override_db):
        """Can update pending reminder."""
        service = ReminderService(actor="test")
        original_time = datetime.now(timezone.utc) + timedelta(hours=1)
        reminder = service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=1,
            remind_at=original_time,
            channel="in_app",
        ))

        new_time = datetime.now(timezone.utc) + timedelta(hours=5)
        result = service.update_reminder(
            reminder.id,
            ReminderUpdate(remind_at=new_time, channel="email")
        )

        assert result is not None
        # Compare without timezone info (SQLite doesn't store timezone)
        assert result.remind_at.replace(tzinfo=None) == new_time.replace(tzinfo=None)
        assert result.channel == "email"

    def test_update_sent_reminder_fails(self, override_db):
        """Cannot update already sent reminder."""
        service = ReminderService(actor="test")
        reminder = service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=1,
            remind_at=datetime.now(timezone.utc) - timedelta(hours=1),
        ))
        service.mark_reminder_sent(reminder.id)

        result = service.update_reminder(
            reminder.id,
            ReminderUpdate(message="New message")
        )

        assert result is None

    def test_get_reminders_filters_by_status(self, override_db):
        """Can filter reminders by status."""
        service = ReminderService(actor="test")
        now = datetime.now(timezone.utc)

        # Create reminders with different statuses
        pending = service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=1,
            remind_at=now + timedelta(hours=1),
        ))
        sent = service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=2,
            remind_at=now - timedelta(hours=1),
        ))
        service.mark_reminder_sent(sent.id)

        result = service.get_reminders(ReminderFilters(status="pending"))

        assert result.total == 1
        assert result.items[0].id == pending.id

    def test_get_reminders_filters_by_channel(self, override_db):
        """Can filter reminders by channel."""
        service = ReminderService(actor="test")
        now = datetime.now(timezone.utc)

        service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=1,
            remind_at=now + timedelta(hours=1),
            channel="email",
        ))
        service.create_reminder(ReminderCreate(
            target_type="task",
            target_id=2,
            remind_at=now + timedelta(hours=1),
            channel="in_app",
        ))

        result = service.get_reminders(ReminderFilters(channel="email"))

        assert result.total == 1
        assert result.items[0].channel == "email"

    def test_get_reminders_pagination(self, override_db):
        """Pagination works correctly."""
        service = ReminderService(actor="test")
        now = datetime.now(timezone.utc)

        # Create 10 reminders
        for i in range(10):
            service.create_reminder(ReminderCreate(
                target_type="task",
                target_id=i,
                remind_at=now + timedelta(hours=i+1),
            ))

        # Get page 1
        page1 = service.get_reminders(ReminderFilters(page=1, page_size=3))
        assert page1.total == 10
        assert len(page1.items) == 3

        # Get page 2
        page2 = service.get_reminders(ReminderFilters(page=2, page_size=3))
        assert len(page2.items) == 3

        # Different reminders on each page
        page1_ids = {r.id for r in page1.items}
        page2_ids = {r.id for r in page2.items}
        assert page1_ids.isdisjoint(page2_ids)


class TestReminderServiceSingleton:
    """Test singleton pattern."""

    def test_get_reminder_service_returns_same_instance(self, override_db):
        """get_reminder_service returns the same instance."""
        # Reset singleton for this test
        import cmd_center.backend.services.reminder_service as module
        module._reminder_service = None

        service1 = get_reminder_service()
        service2 = get_reminder_service()

        assert service1 is service2
