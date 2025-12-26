"""Note service for internal notes management with reminder integration.

This service manages internal notes that can be linked to any entity
and integrates with the unified reminder system for review reminders.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select, func

from .. import db
from ..db import InternalNote
from ..models.note_models import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    NoteListResponse,
    NoteFilters,
)
from ..models.reminder_models import ReminderCreate
from ..constants import ActionType
from .intervention_service import log_action
from .reminder_service import ReminderService

logger = logging.getLogger(__name__)


class NoteService:
    """Service for internal note CRUD operations with reminder integration."""

    def __init__(self, actor: str = "system"):
        """Initialize note service.

        Args:
            actor: Default actor for audit logging
        """
        self.actor = actor
        self.reminder_service = ReminderService(actor=actor)

    def create_note(
        self,
        data: NoteCreate,
        actor: Optional[str] = None,
    ) -> NoteResponse:
        """Create a new note, optionally with a review reminder.

        Args:
            data: Note creation data
            actor: Who is creating the note

        Returns:
            The created note
        """
        actor = actor or self.actor

        with Session(db.engine) as session:
            note = InternalNote(
                content=data.content,
                created_by=actor,
                target_type=data.target_type,
                target_id=data.target_id,
                review_at=data.review_at,
                pinned=data.pinned,
                tags=data.tags,
            )
            session.add(note)
            session.commit()
            session.refresh(note)

            note_id = note.id

            # Log the action
            log_action(
                actor=actor,
                object_type="note",
                object_id=note_id,
                action_type=ActionType.NOTE_ADDED.value,
                summary=f"Added note for {data.target_type or 'general'}:{data.target_id or 'none'}",
                details={
                    "target_type": data.target_type,
                    "target_id": data.target_id,
                    "pinned": data.pinned,
                    "has_review_reminder": data.review_at is not None,
                },
            )

            logger.info(f"Created note (ID: {note_id})")

            result = NoteResponse.model_validate(note)

        # Create review reminder if requested (outside the session)
        if data.review_at:
            self.reminder_service.create_reminder(
                ReminderCreate(
                    target_type="note",
                    target_id=note_id,
                    remind_at=data.review_at,
                    channel=data.reminder_channel,
                    message="Note review reminder",
                ),
                actor=actor,
            )

        return result

    def get_note_by_id(
        self,
        note_id: int,
    ) -> Optional[NoteResponse]:
        """Get a note by ID.

        Args:
            note_id: The note ID

        Returns:
            The note if found, None otherwise
        """
        with Session(db.engine) as session:
            note = session.get(InternalNote, note_id)
            if note:
                return NoteResponse.model_validate(note)
            return None

    def get_notes(
        self,
        filters: Optional[NoteFilters] = None,
    ) -> NoteListResponse:
        """Get paginated list of notes with optional filters.

        Args:
            filters: Query filters

        Returns:
            Paginated list of notes (pinned notes first)
        """
        if filters is None:
            filters = NoteFilters()

        with Session(db.engine) as session:
            query = select(InternalNote)

            # Apply filters
            if filters.target_type:
                query = query.where(InternalNote.target_type == filters.target_type)
            if filters.target_id is not None:
                query = query.where(InternalNote.target_id == filters.target_id)
            if filters.pinned is not None:
                query = query.where(InternalNote.pinned == filters.pinned)
            if filters.is_archived is not None:
                query = query.where(InternalNote.is_archived == filters.is_archived)
            if filters.tags:
                # Simple contains check for tag
                tag_pattern = f"%{filters.tags}%"
                query = query.where(InternalNote.tags.ilike(tag_pattern))
            if filters.search:
                search_pattern = f"%{filters.search}%"
                query = query.where(InternalNote.content.ilike(search_pattern))

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total = session.exec(count_query).one()

            # Apply ordering (pinned first, then by creation date)
            query = query.order_by(
                InternalNote.pinned.desc(),
                InternalNote.created_at.desc(),
            )
            query = query.offset((filters.page - 1) * filters.page_size)
            query = query.limit(filters.page_size)

            # Execute query
            notes = session.exec(query).all()

            items = [NoteResponse.model_validate(n) for n in notes]

            return NoteListResponse(
                items=items,
                total=total,
                page=filters.page,
                page_size=filters.page_size,
            )

    def update_note(
        self,
        note_id: int,
        data: NoteUpdate,
        actor: Optional[str] = None,
    ) -> Optional[NoteResponse]:
        """Update a note.

        Args:
            note_id: ID of note to update
            data: Fields to update
            actor: Who is updating

        Returns:
            Updated note if found, None otherwise
        """
        actor = actor or self.actor

        with Session(db.engine) as session:
            note = session.get(InternalNote, note_id)
            if not note:
                return None

            changes = {}

            if data.content is not None:
                changes["content"] = {"updated": True}  # Don't log full content
                note.content = data.content
            if data.pinned is not None:
                changes["pinned"] = {"from": note.pinned, "to": data.pinned}
                note.pinned = data.pinned
            if data.tags is not None:
                changes["tags"] = {"from": note.tags, "to": data.tags}
                note.tags = data.tags
            if data.review_at is not None:
                changes["review_at"] = {
                    "from": note.review_at.isoformat() if note.review_at else None,
                    "to": data.review_at.isoformat()
                }
                note.review_at = data.review_at

            note.updated_at = datetime.now(timezone.utc)

            session.add(note)
            session.commit()
            session.refresh(note)

            if changes:
                log_action(
                    actor=actor,
                    object_type="note",
                    object_id=note.id,
                    action_type=ActionType.NOTE_UPDATED.value,
                    summary=f"Updated note (ID: {note_id})",
                    details={"changes": changes},
                )

            logger.info(f"Updated note (ID: {note_id})")

            return NoteResponse.model_validate(note)

    def archive_note(
        self,
        note_id: int,
        actor: Optional[str] = None,
    ) -> bool:
        """Archive a note and cancel pending reminders.

        Args:
            note_id: ID of note to archive
            actor: Who is archiving

        Returns:
            True if archived, False if not found
        """
        actor = actor or self.actor

        with Session(db.engine) as session:
            note = session.get(InternalNote, note_id)
            if not note:
                return False

            note.is_archived = True
            note.updated_at = datetime.now(timezone.utc)

            session.add(note)
            session.commit()

            # Log the action
            log_action(
                actor=actor,
                object_type="note",
                object_id=note.id,
                action_type=ActionType.NOTE_ARCHIVED.value,
                summary=f"Archived note (ID: {note_id})",
            )

            logger.info(f"Archived note (ID: {note_id})")

        # Cancel pending reminders for this note (outside session)
        self.reminder_service.cancel_reminders_for_target("note", note_id, actor=actor)

        return True

    def get_notes_for_target(
        self,
        target_type: str,
        target_id: int,
        include_archived: bool = False,
    ) -> list[NoteResponse]:
        """Get all notes linked to a specific target.

        Args:
            target_type: Type of target entity
            target_id: ID of target entity
            include_archived: Whether to include archived notes

        Returns:
            List of notes for the target (pinned first)
        """
        with Session(db.engine) as session:
            query = (
                select(InternalNote)
                .where(InternalNote.target_type == target_type)
                .where(InternalNote.target_id == target_id)
            )

            if not include_archived:
                query = query.where(InternalNote.is_archived == False)

            query = query.order_by(
                InternalNote.pinned.desc(),
                InternalNote.created_at.desc(),
            )
            notes = session.exec(query).all()

            return [NoteResponse.model_validate(n) for n in notes]

    def get_pinned_notes(
        self,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
    ) -> list[NoteResponse]:
        """Get all pinned notes, optionally filtered by target.

        Args:
            target_type: Optional target type filter
            target_id: Optional target ID filter

        Returns:
            List of pinned notes
        """
        with Session(db.engine) as session:
            query = (
                select(InternalNote)
                .where(InternalNote.pinned == True)
                .where(InternalNote.is_archived == False)
            )

            if target_type:
                query = query.where(InternalNote.target_type == target_type)
            if target_id is not None:
                query = query.where(InternalNote.target_id == target_id)

            query = query.order_by(InternalNote.created_at.desc())
            notes = session.exec(query).all()

            return [NoteResponse.model_validate(n) for n in notes]


# Singleton pattern
_note_service: Optional[NoteService] = None


def get_note_service() -> NoteService:
    """Get or create note service singleton."""
    global _note_service
    if _note_service is None:
        _note_service = NoteService()
    return _note_service


__all__ = [
    "NoteService",
    "get_note_service",
]
