"""Unit tests for DocumentService."""

from datetime import datetime, timedelta, timezone

import pytest

from cmd_center.backend.services.document_service import DocumentService
from cmd_center.backend.models.document_models import (
    DocumentCreate,
    DocumentUpdate,
    DocumentFilters,
    DocumentFileCreate,
)
from cmd_center.backend.constants import DocumentStatus


class TestDocumentService:
    """Test cases for DocumentService."""

    def test_create_document(self, override_db):
        """Creating document returns valid Document with ID."""
        service = DocumentService(actor="test_user")
        data = DocumentCreate(
            title="Commercial Registration",
            document_type="registration",
            description="Company commercial registration document",
            reference_number="CR-12345",
            issuing_authority="Ministry of Commerce",
            issue_date=datetime.now(timezone.utc),
            expiry_date=datetime.now(timezone.utc) + timedelta(days=365),
        )
        result = service.create_document(data)

        assert result.id is not None
        assert result.title == "Commercial Registration"
        assert result.document_type == "registration"
        assert result.status == DocumentStatus.ACTIVE.value

    def test_get_document_by_id(self, override_db):
        """Can retrieve document by ID."""
        service = DocumentService()
        data = DocumentCreate(
            title="Test Document",
            document_type="license",
        )
        created = service.create_document(data)

        result = service.get_document_by_id(created.id)
        assert result is not None
        assert result.id == created.id
        assert result.title == "Test Document"

    def test_get_document_by_id_not_found(self, override_db):
        """Returns None for non-existent document."""
        service = DocumentService()
        result = service.get_document_by_id(99999)
        assert result is None

    def test_get_document_with_files(self, override_db):
        """Get document with files and responsible employee name."""
        service = DocumentService()
        data = DocumentCreate(
            title="Document with Files",
            document_type="contract",
        )
        created = service.create_document(data)

        # Attach a file
        file_data = DocumentFileCreate(
            filename="contract.pdf",
            file_path="/uploads/contract.pdf",
            file_type="application/pdf",
            file_size=1024,
        )
        service.attach_file(created.id, file_data)

        result = service.get_document_with_files(created.id)
        assert result is not None
        assert len(result.files) == 1
        assert result.files[0].filename == "contract.pdf"

    def test_get_documents_filters_by_type(self, override_db):
        """Document type filter returns only matching documents."""
        service = DocumentService()
        service.create_document(DocumentCreate(title="Doc 1", document_type="license"))
        service.create_document(DocumentCreate(title="Doc 2", document_type="certificate"))
        service.create_document(DocumentCreate(title="Doc 3", document_type="license"))

        result = service.get_documents(DocumentFilters(document_type="license"))
        assert result.total == 2
        assert all(d.document_type == "license" for d in result.items)

    def test_get_documents_filters_by_status(self, override_db):
        """Status filter returns only matching documents."""
        service = DocumentService()
        doc = service.create_document(DocumentCreate(title="Active Doc", document_type="license"))
        service.update_document(doc.id, DocumentUpdate(status=DocumentStatus.EXPIRED.value))
        service.create_document(DocumentCreate(title="Another Active", document_type="license"))

        result = service.get_documents(DocumentFilters(status=DocumentStatus.ACTIVE.value))
        assert result.total == 1
        assert result.items[0].title == "Another Active"

    def test_get_documents_search(self, override_db):
        """Search filter returns documents matching title."""
        service = DocumentService()
        service.create_document(DocumentCreate(title="Commercial Registration", document_type="registration"))
        service.create_document(DocumentCreate(title="Trade License", document_type="license"))

        result = service.get_documents(DocumentFilters(search="commercial"))
        assert result.total == 1
        assert result.items[0].title == "Commercial Registration"

    def test_get_expiring_documents(self, override_db):
        """Returns documents expiring within N days."""
        service = DocumentService()
        now = datetime.now(timezone.utc)

        # Document expiring in 15 days (should be included)
        service.create_document(DocumentCreate(
            title="Expiring Soon",
            document_type="license",
            expiry_date=now + timedelta(days=15),
        ))

        # Document expiring in 45 days (should be excluded for 30-day check)
        service.create_document(DocumentCreate(
            title="Not Expiring Soon",
            document_type="license",
            expiry_date=now + timedelta(days=45),
        ))

        # Already expired document (should be excluded)
        doc = service.create_document(DocumentCreate(
            title="Already Expired",
            document_type="license",
            expiry_date=now - timedelta(days=5),
        ))
        service.update_document(doc.id, DocumentUpdate(status=DocumentStatus.EXPIRED.value))

        result = service.get_expiring_documents(within_days=30)
        assert len(result) == 1
        assert result[0].title == "Expiring Soon"

    def test_update_document(self, override_db):
        """Update changes fields and sets updated_at."""
        service = DocumentService()
        created = service.create_document(DocumentCreate(
            title="Original Title",
            document_type="license",
        ))

        result = service.update_document(
            created.id,
            DocumentUpdate(title="Updated Title", status=DocumentStatus.RENEWAL_IN_PROGRESS.value),
        )

        assert result is not None
        assert result.title == "Updated Title"
        assert result.status == DocumentStatus.RENEWAL_IN_PROGRESS.value
        assert result.updated_at is not None

    def test_update_document_not_found(self, override_db):
        """Update returns None for non-existent document."""
        service = DocumentService()
        result = service.update_document(99999, DocumentUpdate(title="New Title"))
        assert result is None

    def test_attach_file_to_document(self, override_db):
        """Can attach file to document."""
        service = DocumentService()
        doc = service.create_document(DocumentCreate(
            title="Test Document",
            document_type="contract",
        ))

        file_data = DocumentFileCreate(
            filename="agreement.pdf",
            file_path="/uploads/agreement.pdf",
            file_type="application/pdf",
            file_size=2048,
        )
        result = service.attach_file(doc.id, file_data)

        assert result is not None
        assert result.filename == "agreement.pdf"
        assert result.version == 1
        assert result.is_current is True

    def test_attach_multiple_files_versioning(self, override_db):
        """Attaching new file increments version and marks previous as not current."""
        service = DocumentService()
        doc = service.create_document(DocumentCreate(
            title="Test Document",
            document_type="contract",
        ))

        # First file
        file1 = service.attach_file(doc.id, DocumentFileCreate(
            filename="v1.pdf",
            file_path="/uploads/v1.pdf",
        ))
        assert file1.version == 1

        # Second file
        file2 = service.attach_file(doc.id, DocumentFileCreate(
            filename="v2.pdf",
            file_path="/uploads/v2.pdf",
        ))
        assert file2.version == 2
        assert file2.is_current is True

        # Check all files
        files = service.get_document_files(doc.id)
        assert len(files) == 2
        # First should be the current (v2) due to desc ordering
        assert files[0].version == 2
        assert files[0].is_current is True

    def test_attach_file_to_nonexistent_document(self, override_db):
        """Attach file returns None for non-existent document."""
        service = DocumentService()
        result = service.attach_file(99999, DocumentFileCreate(
            filename="test.pdf",
            file_path="/uploads/test.pdf",
        ))
        assert result is None

    def test_get_document_files(self, override_db):
        """Get all files for a document."""
        service = DocumentService()
        doc = service.create_document(DocumentCreate(
            title="Test Document",
            document_type="contract",
        ))

        service.attach_file(doc.id, DocumentFileCreate(filename="file1.pdf", file_path="/uploads/file1.pdf"))
        service.attach_file(doc.id, DocumentFileCreate(filename="file2.pdf", file_path="/uploads/file2.pdf"))

        files = service.get_document_files(doc.id)
        assert len(files) == 2

    def test_get_documents_pagination(self, override_db):
        """Pagination works correctly."""
        service = DocumentService()
        for i in range(25):
            service.create_document(DocumentCreate(
                title=f"Document {i}",
                document_type="license",
            ))

        result = service.get_documents(DocumentFilters(page=1, page_size=10))
        assert result.total == 25
        assert len(result.items) == 10
        assert result.page == 1
        assert result.page_size == 10

        result2 = service.get_documents(DocumentFilters(page=2, page_size=10))
        assert len(result2.items) == 10

        result3 = service.get_documents(DocumentFilters(page=3, page_size=10))
        assert len(result3.items) == 5
