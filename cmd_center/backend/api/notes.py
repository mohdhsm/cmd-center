"""API endpoints for Internal Note management."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..models.note_models import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    NoteListResponse,
    NoteFilters,
)
from ..services.note_service import NoteService

router = APIRouter()


@router.get("", response_model=NoteListResponse)
def list_notes(
    target_type: Optional[str] = Query(None, description="Filter by target type"),
    target_id: Optional[int] = Query(None, description="Filter by target ID"),
    pinned: Optional[bool] = Query(None, description="Filter pinned notes"),
    tags: Optional[str] = Query(None, description="Filter by tag"),
    is_archived: Optional[bool] = Query(False, description="Include archived notes"),
    search: Optional[str] = Query(None, description="Search in content"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> NoteListResponse:
    """List notes with optional filters. Pinned notes appear first."""
    filters = NoteFilters(
        target_type=target_type,
        target_id=target_id,
        pinned=pinned,
        tags=tags,
        is_archived=is_archived,
        search=search,
        page=page,
        page_size=page_size,
    )
    service = NoteService()
    return service.get_notes(filters)


@router.get("/pinned", response_model=list[NoteResponse])
def list_pinned_notes(
    target_type: Optional[str] = Query(None, description="Filter by target type"),
    target_id: Optional[int] = Query(None, description="Filter by target ID"),
) -> list[NoteResponse]:
    """List all pinned notes, optionally filtered by target."""
    service = NoteService()
    return service.get_pinned_notes(target_type, target_id)


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(note_id: int) -> NoteResponse:
    """Get a single note by ID."""
    service = NoteService()
    note = service.get_note_by_id(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.post("", response_model=NoteResponse, status_code=201)
def create_note(
    data: NoteCreate,
    actor: Optional[str] = Query("system", description="Who is creating the note"),
) -> NoteResponse:
    """Create a new note, optionally with a review reminder."""
    service = NoteService()
    return service.create_note(data, actor=actor)


@router.put("/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: int,
    data: NoteUpdate,
    actor: Optional[str] = Query("system", description="Who is updating"),
) -> NoteResponse:
    """Update a note."""
    service = NoteService()
    note = service.update_note(note_id, data, actor=actor)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.delete("/{note_id}", status_code=204)
def archive_note(
    note_id: int,
    actor: Optional[str] = Query("system", description="Who is archiving"),
) -> None:
    """Archive a note and cancel pending review reminders."""
    service = NoteService()
    if not service.archive_note(note_id, actor=actor):
        raise HTTPException(status_code=404, detail="Note not found")


@router.get("/target/{target_type}/{target_id}", response_model=list[NoteResponse])
def get_notes_for_target(
    target_type: str,
    target_id: int,
    include_archived: bool = Query(False, description="Include archived notes"),
) -> list[NoteResponse]:
    """Get all notes for a specific target entity. Pinned notes appear first."""
    service = NoteService()
    return service.get_notes_for_target(target_type, target_id, include_archived)
