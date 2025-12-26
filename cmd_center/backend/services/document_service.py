"""Document service for legal document tracking.

This service manages legal documents, their files, and expiry tracking.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlmodel import Session, select, func

from .. import db
from ..db import LegalDocument, LegalDocumentFile, Employee
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
from ..constants import ActionType, DocumentStatus
from .intervention_service import log_action

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for legal document CRUD operations."""

    def __init__(self, actor: str = "system"):
        self.actor = actor

    def create_document(
        self,
        data: DocumentCreate,
        actor: Optional[str] = None,
    ) -> DocumentResponse:
        """Create a new legal document."""
        actor = actor or self.actor

        with Session(db.engine) as session:
            document = LegalDocument(
                title=data.title,
                document_type=data.document_type,
                description=data.description,
                issue_date=data.issue_date,
                expiry_date=data.expiry_date,
                reference_number=data.reference_number,
                issuing_authority=data.issuing_authority,
                responsible_employee_id=data.responsible_employee_id,
                status=DocumentStatus.ACTIVE.value,
            )
            session.add(document)
            session.commit()
            session.refresh(document)

            log_action(
                actor=actor,
                object_type="document",
                object_id=document.id,
                action_type=ActionType.DOCUMENT_CREATED.value,
                summary=f"Created document: {document.title}",
                details={
                    "document_type": document.document_type,
                    "expiry_date": document.expiry_date.isoformat() if document.expiry_date else None,
                },
            )

            logger.info(f"Created document: {document.title} (ID: {document.id})")

            return DocumentResponse.model_validate(document)

    def get_document_by_id(self, document_id: int) -> Optional[DocumentResponse]:
        """Get a document by ID."""
        with Session(db.engine) as session:
            document = session.get(LegalDocument, document_id)
            if document:
                return DocumentResponse.model_validate(document)
            return None

    def get_document_with_files(self, document_id: int) -> Optional[DocumentWithFiles]:
        """Get a document with its files and responsible employee name."""
        with Session(db.engine) as session:
            document = session.get(LegalDocument, document_id)
            if not document:
                return None

            # Get files
            files_query = (
                select(LegalDocumentFile)
                .where(LegalDocumentFile.document_id == document_id)
                .order_by(LegalDocumentFile.version.desc())
            )
            files = session.exec(files_query).all()

            # Get responsible employee name
            responsible_name = None
            if document.responsible_employee_id:
                employee = session.get(Employee, document.responsible_employee_id)
                if employee:
                    responsible_name = employee.full_name

            return DocumentWithFiles(
                id=document.id,
                title=document.title,
                document_type=document.document_type,
                description=document.description,
                issue_date=document.issue_date,
                expiry_date=document.expiry_date,
                status=document.status,
                reference_number=document.reference_number,
                issuing_authority=document.issuing_authority,
                responsible_employee_id=document.responsible_employee_id,
                created_at=document.created_at,
                updated_at=document.updated_at,
                files=[DocumentFileResponse.model_validate(f) for f in files],
                responsible_employee_name=responsible_name,
            )

    def get_documents(
        self,
        filters: Optional[DocumentFilters] = None,
    ) -> DocumentListResponse:
        """Get paginated list of documents."""
        if filters is None:
            filters = DocumentFilters()

        with Session(db.engine) as session:
            query = select(LegalDocument)

            if filters.document_type:
                query = query.where(LegalDocument.document_type == filters.document_type)
            if filters.status:
                query = query.where(LegalDocument.status == filters.status)
            if filters.responsible_employee_id is not None:
                query = query.where(
                    LegalDocument.responsible_employee_id == filters.responsible_employee_id
                )
            if filters.expiring_within_days:
                cutoff = datetime.now(timezone.utc) + timedelta(days=filters.expiring_within_days)
                query = query.where(LegalDocument.expiry_date <= cutoff)
                query = query.where(LegalDocument.expiry_date >= datetime.now(timezone.utc))
            if filters.search:
                search_pattern = f"%{filters.search}%"
                query = query.where(LegalDocument.title.ilike(search_pattern))

            count_query = select(func.count()).select_from(query.subquery())
            total = session.exec(count_query).one()

            query = query.order_by(LegalDocument.expiry_date.asc().nullslast())
            query = query.offset((filters.page - 1) * filters.page_size)
            query = query.limit(filters.page_size)

            documents = session.exec(query).all()

            return DocumentListResponse(
                items=[DocumentResponse.model_validate(d) for d in documents],
                total=total,
                page=filters.page,
                page_size=filters.page_size,
            )

    def get_expiring_documents(
        self,
        within_days: int = 30,
        limit: int = 50,
    ) -> list[DocumentResponse]:
        """Get documents expiring within specified days."""
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=within_days)

        with Session(db.engine) as session:
            query = (
                select(LegalDocument)
                .where(LegalDocument.expiry_date >= now)
                .where(LegalDocument.expiry_date <= cutoff)
                .where(LegalDocument.status == DocumentStatus.ACTIVE.value)
                .order_by(LegalDocument.expiry_date.asc())
                .limit(limit)
            )
            documents = session.exec(query).all()

            return [DocumentResponse.model_validate(d) for d in documents]

    def update_document(
        self,
        document_id: int,
        data: DocumentUpdate,
        actor: Optional[str] = None,
    ) -> Optional[DocumentResponse]:
        """Update a document."""
        actor = actor or self.actor

        with Session(db.engine) as session:
            document = session.get(LegalDocument, document_id)
            if not document:
                return None

            changes = {}

            if data.title is not None:
                changes["title"] = {"from": document.title, "to": data.title}
                document.title = data.title
            if data.document_type is not None:
                changes["document_type"] = {"from": document.document_type, "to": data.document_type}
                document.document_type = data.document_type
            if data.description is not None:
                document.description = data.description
            if data.reference_number is not None:
                document.reference_number = data.reference_number
            if data.issuing_authority is not None:
                document.issuing_authority = data.issuing_authority
            if data.issue_date is not None:
                document.issue_date = data.issue_date
            if data.expiry_date is not None:
                changes["expiry_date"] = {
                    "from": document.expiry_date.isoformat() if document.expiry_date else None,
                    "to": data.expiry_date.isoformat()
                }
                document.expiry_date = data.expiry_date
            if data.status is not None:
                changes["status"] = {"from": document.status, "to": data.status}
                document.status = data.status
            if data.responsible_employee_id is not None:
                document.responsible_employee_id = data.responsible_employee_id

            document.updated_at = datetime.now(timezone.utc)

            session.add(document)
            session.commit()
            session.refresh(document)

            if changes:
                log_action(
                    actor=actor,
                    object_type="document",
                    object_id=document.id,
                    action_type=ActionType.DOCUMENT_UPDATED.value,
                    summary=f"Updated document: {document.title}",
                    details={"changes": changes},
                )

            return DocumentResponse.model_validate(document)

    def attach_file(
        self,
        document_id: int,
        data: DocumentFileCreate,
        actor: Optional[str] = None,
    ) -> Optional[DocumentFileResponse]:
        """Attach a file to a document."""
        actor = actor or self.actor

        with Session(db.engine) as session:
            document = session.get(LegalDocument, document_id)
            if not document:
                return None

            # Get current max version
            version_query = (
                select(func.max(LegalDocumentFile.version))
                .where(LegalDocumentFile.document_id == document_id)
            )
            max_version = session.exec(version_query).one() or 0

            # Mark previous files as not current
            update_query = (
                select(LegalDocumentFile)
                .where(LegalDocumentFile.document_id == document_id)
                .where(LegalDocumentFile.is_current == True)
            )
            for old_file in session.exec(update_query).all():
                old_file.is_current = False
                session.add(old_file)

            # Create new file
            file = LegalDocumentFile(
                document_id=document_id,
                filename=data.filename,
                file_path=data.file_path,
                file_type=data.file_type,
                file_size=data.file_size,
                version=max_version + 1,
                is_current=True,
                uploaded_by=actor,
            )
            session.add(file)
            session.commit()
            session.refresh(file)

            logger.info(f"Attached file to document {document_id}: {data.filename}")

            return DocumentFileResponse.model_validate(file)

    def get_document_files(self, document_id: int) -> list[DocumentFileResponse]:
        """Get all files for a document."""
        with Session(db.engine) as session:
            query = (
                select(LegalDocumentFile)
                .where(LegalDocumentFile.document_id == document_id)
                .order_by(LegalDocumentFile.version.desc())
            )
            files = session.exec(query).all()

            return [DocumentFileResponse.model_validate(f) for f in files]


# Singleton pattern
_document_service: Optional[DocumentService] = None


def get_document_service() -> DocumentService:
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service


__all__ = [
    "DocumentService",
    "get_document_service",
]
