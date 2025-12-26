"""API endpoints for legal document tracking."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ..models.document_models import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentWithFiles,
    DocumentListResponse,
    DocumentFilters,
    DocumentFileCreate,
    DocumentFileResponse,
)
from ..services.document_service import get_document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
def create_document(data: DocumentCreate) -> DocumentResponse:
    """Create a new legal document."""
    service = get_document_service()
    return service.create_document(data)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    document_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    responsible_employee_id: Optional[int] = Query(None),
    expiring_within_days: Optional[int] = Query(None, ge=1),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> DocumentListResponse:
    """List documents with filters."""
    service = get_document_service()
    filters = DocumentFilters(
        document_type=document_type,
        status=status,
        responsible_employee_id=responsible_employee_id,
        expiring_within_days=expiring_within_days,
        search=search,
        page=page,
        page_size=page_size,
    )
    return service.get_documents(filters)


@router.get("/expiring", response_model=list[DocumentResponse])
def get_expiring_documents(
    within_days: int = Query(30, ge=1),
    limit: int = Query(50, ge=1, le=100),
) -> list[DocumentResponse]:
    """Get documents expiring within specified days."""
    service = get_document_service()
    return service.get_expiring_documents(within_days=within_days, limit=limit)


@router.get("/{document_id}", response_model=DocumentWithFiles)
def get_document(document_id: int) -> DocumentWithFiles:
    """Get a document by ID with its files."""
    service = get_document_service()
    document = service.get_document_with_files(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(document_id: int, data: DocumentUpdate) -> DocumentResponse:
    """Update a document."""
    service = get_document_service()
    document = service.update_document(document_id, data)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.post("/{document_id}/files", response_model=DocumentFileResponse, status_code=201)
def attach_file(document_id: int, data: DocumentFileCreate) -> DocumentFileResponse:
    """Attach a file to a document."""
    service = get_document_service()
    file = service.attach_file(document_id, data)
    if not file:
        raise HTTPException(status_code=404, detail="Document not found")
    return file


@router.get("/{document_id}/files", response_model=list[DocumentFileResponse])
def get_document_files(document_id: int) -> list[DocumentFileResponse]:
    """Get all files for a document."""
    service = get_document_service()
    return service.get_document_files(document_id)
