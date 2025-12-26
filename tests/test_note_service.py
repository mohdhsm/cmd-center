"""Unit tests for NoteService."""

import pytest
from datetime import datetime, timedelta, timezone

from cmd_center.backend.services.note_service import NoteService, get_note_service
from cmd_center.backend.services.reminder_service import ReminderService
from cmd_center.backend.models.note_models import NoteCreate, NoteUpdate, NoteFilters


class TestNoteService:
    """Tests for NoteService CRUD operations."""

    def test_create_note(self, override_db):
        """Creates note with all fields."""
        service = NoteService(actor="test")
        data = NoteCreate(
            content="Important note about this deal",
            pinned=True,
            tags="important,followup",
        )

        result = service.create_note(data)

        assert result.id is not None
        assert result.content == "Important note about this deal"
        assert result.pinned is True
        assert result.tags == "important,followup"

    def test_create_note_with_target(self, override_db):
        """Creates note linked to a target entity."""
        service = NoteService(actor="test")
        data = NoteCreate(
            content="Note for deal",
            target_type="deal",
            target_id=123,
        )

        result = service.create_note(data)

        assert result.target_type == "deal"
        assert result.target_id == 123

    def test_create_note_with_review_reminder(self, override_db):
        """Creates note and review reminder when review_at set."""
        service = NoteService(actor="test")
        review_at = datetime.now(timezone.utc) + timedelta(days=7)
        data = NoteCreate(
            content="Review this later",
            review_at=review_at,
            reminder_channel="email",
        )

        result = service.create_note(data)

        # Verify reminder was created
        reminder_service = ReminderService()
        reminders = reminder_service.get_reminders_for_target("note", result.id)
        assert len(reminders) == 1
        assert reminders[0].channel == "email"

    def test_get_note_by_id(self, override_db):
        """Can retrieve note by ID."""
        service = NoteService(actor="test")
        created = service.create_note(NoteCreate(content="Test note"))

        result = service.get_note_by_id(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.content == "Test note"

    def test_get_note_by_id_not_found(self, override_db):
        """Returns None for non-existent note."""
        service = NoteService(actor="test")

        result = service.get_note_by_id(99999)

        assert result is None

    def test_get_notes_filters_by_target(self, override_db):
        """target_type/target_id filter works."""
        service = NoteService(actor="test")

        service.create_note(NoteCreate(content="N1", target_type="deal", target_id=100))
        service.create_note(NoteCreate(content="N2", target_type="deal", target_id=100))
        service.create_note(NoteCreate(content="N3", target_type="deal", target_id=200))

        result = service.get_notes(NoteFilters(target_type="deal", target_id=100))

        assert result.total == 2
        assert all(n.target_id == 100 for n in result.items)

    def test_get_notes_filters_pinned(self, override_db):
        """Pinned filter returns pinned notes."""
        service = NoteService(actor="test")

        service.create_note(NoteCreate(content="Normal", pinned=False))
        service.create_note(NoteCreate(content="Pinned", pinned=True))

        result = service.get_notes(NoteFilters(pinned=True))

        assert result.total == 1
        assert result.items[0].pinned is True

    def test_get_notes_pinned_first(self, override_db):
        """Pinned notes sorted to top."""
        service = NoteService(actor="test")

        service.create_note(NoteCreate(content="Normal"))
        service.create_note(NoteCreate(content="Pinned", pinned=True))
        service.create_note(NoteCreate(content="Normal 2"))

        result = service.get_notes()

        assert result.items[0].pinned is True

    def test_get_notes_filters_by_tags(self, override_db):
        """Tag filter works."""
        service = NoteService(actor="test")

        service.create_note(NoteCreate(content="N1", tags="important,urgent"))
        service.create_note(NoteCreate(content="N2", tags="followup"))
        service.create_note(NoteCreate(content="N3", tags="important"))

        result = service.get_notes(NoteFilters(tags="important"))

        assert result.total == 2

    def test_get_notes_search(self, override_db):
        """Search in content works."""
        service = NoteService(actor="test")

        service.create_note(NoteCreate(content="Meeting notes from client call"))
        service.create_note(NoteCreate(content="Follow up needed"))
        service.create_note(NoteCreate(content="Client requested proposal"))

        result = service.get_notes(NoteFilters(search="client"))

        assert result.total == 2

    def test_update_note(self, override_db):
        """Update changes fields."""
        service = NoteService(actor="test")
        note = service.create_note(NoteCreate(
            content="Original",
            pinned=False,
        ))

        result = service.update_note(
            note.id,
            NoteUpdate(content="Updated", pinned=True)
        )

        assert result is not None
        assert result.content == "Updated"
        assert result.pinned is True

    def test_update_note_not_found(self, override_db):
        """Update returns None for non-existent note."""
        service = NoteService(actor="test")

        result = service.update_note(99999, NoteUpdate(content="Test"))

        assert result is None

    def test_archive_note(self, override_db):
        """Archive sets is_archived=True."""
        service = NoteService(actor="test")
        note = service.create_note(NoteCreate(content="To archive"))

        result = service.archive_note(note.id)

        assert result is True

        updated = service.get_note_by_id(note.id)
        assert updated.is_archived is True

    def test_archive_note_cancels_reminders(self, override_db):
        """Archiving cancels pending reminders."""
        service = NoteService(actor="test")
        review_at = datetime.now(timezone.utc) + timedelta(days=7)
        note = service.create_note(NoteCreate(
            content="Note with review",
            review_at=review_at,
        ))

        service.archive_note(note.id)

        # Verify reminder was cancelled
        reminder_service = ReminderService()
        reminders = reminder_service.get_reminders_for_target("note", note.id, status="pending")
        assert len(reminders) == 0

    def test_get_notes_for_target(self, override_db):
        """Get all notes for specific target."""
        service = NoteService(actor="test")

        service.create_note(NoteCreate(content="N1", target_type="deal", target_id=100))
        service.create_note(NoteCreate(content="N2", target_type="deal", target_id=100))
        service.create_note(NoteCreate(content="N3", target_type="deal", target_id=200))

        result = service.get_notes_for_target("deal", 100)

        assert len(result) == 2
        assert all(n.target_id == 100 for n in result)

    def test_get_pinned_notes(self, override_db):
        """Get all pinned notes."""
        service = NoteService(actor="test")

        service.create_note(NoteCreate(content="Pinned 1", pinned=True))
        service.create_note(NoteCreate(content="Normal"))
        service.create_note(NoteCreate(content="Pinned 2", pinned=True))

        result = service.get_pinned_notes()

        assert len(result) == 2
        assert all(n.pinned for n in result)

    def test_get_notes_excludes_archived(self, override_db):
        """By default, archived notes are excluded."""
        service = NoteService(actor="test")

        service.create_note(NoteCreate(content="Active"))
        archived = service.create_note(NoteCreate(content="Archived"))
        service.archive_note(archived.id)

        result = service.get_notes()

        assert result.total == 1
        assert result.items[0].content == "Active"

    def test_get_notes_pagination(self, override_db):
        """Pagination works correctly."""
        service = NoteService(actor="test")

        for i in range(10):
            service.create_note(NoteCreate(content=f"Note {i}"))

        page1 = service.get_notes(NoteFilters(page=1, page_size=3))
        assert page1.total == 10
        assert len(page1.items) == 3

        page2 = service.get_notes(NoteFilters(page=2, page_size=3))
        assert len(page2.items) == 3

        # Different notes on each page
        page1_ids = {n.id for n in page1.items}
        page2_ids = {n.id for n in page2.items}
        assert page1_ids.isdisjoint(page2_ids)


class TestNoteServiceSingleton:
    """Test singleton pattern."""

    def test_get_note_service_returns_same_instance(self, override_db):
        """get_note_service returns the same instance."""
        import cmd_center.backend.services.note_service as module
        module._note_service = None

        service1 = get_note_service()
        service2 = get_note_service()

        assert service1 is service2
