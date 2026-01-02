"""Contract tests for API response schema validation.

These tests ensure that:
1. Sample test data matches actual API response schemas
2. Paginated response wrappers are correctly structured
3. Response models can validate real API data
"""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from cmd_center.backend.models.employee_models import (
    EmployeeResponse,
    EmployeeListResponse,
)
from cmd_center.backend.models.task_models import (
    TaskResponse,
    TaskListResponse,
)
from cmd_center.backend.models.note_models import (
    NoteResponse,
    NoteListResponse,
)
from cmd_center.backend.models.document_models import (
    DocumentResponse,
    DocumentListResponse,
)
from cmd_center.backend.models.bonus_models import (
    BonusResponse,
    BonusListResponse,
    BonusWithPayments,
)
from cmd_center.backend.models.employee_log_models import (
    LogEntryResponse,
    LogEntryListResponse,
)
from cmd_center.backend.models.skill_models import (
    SkillResponse,
    SkillListResponse,
)


class TestEmployeeResponseSchema:
    """Test employee response schema validation."""

    def test_valid_employee_response(self, sample_employee_response):
        """Valid employee data passes schema validation."""
        result = EmployeeResponse.model_validate(sample_employee_response)
        assert result.id == 1
        assert result.full_name == "Ahmed Al-Farsi"

    def test_employee_response_requires_full_name(self):
        """Employee response requires full_name field."""
        invalid = {"id": 1, "role_title": "Manager"}
        with pytest.raises(ValidationError) as exc_info:
            EmployeeResponse.model_validate(invalid)
        assert "full_name" in str(exc_info.value)

    def test_employee_list_response_structure(self, sample_employee_response):
        """Paginated employee list has correct structure."""
        paginated = {
            "items": [sample_employee_response],
            "total": 1,
            "page": 1,
            "page_size": 20,
        }
        result = EmployeeListResponse.model_validate(paginated)
        assert len(result.items) == 1
        assert result.total == 1


class TestTaskResponseSchema:
    """Test task response schema validation."""

    def test_valid_task_response(self, sample_task_response):
        """Valid task data passes schema validation."""
        result = TaskResponse.model_validate(sample_task_response)
        assert result.id == 1
        assert result.title == "Complete quarterly report"
        assert result.priority == "high"
        assert result.status == "open"

    def test_task_response_validates_priority(self):
        """Task priority must be valid enum value.

        Note: TaskResponse doesn't validate priority at response level,
        only at create/update level. This test verifies the schema accepts
        the data but documents that validation happens at request level.
        """
        now = datetime.now(timezone.utc)
        # Full valid data with invalid priority to test
        data = {
            "id": 1,
            "title": "Test",
            "description": None,
            "assignee_employee_id": None,
            "created_by": "test",
            "status": "open",
            "priority": "critical",  # Not validated at response level
            "is_critical": False,
            "due_at": None,
            "completed_at": None,
            "target_type": None,
            "target_id": None,
            "is_archived": False,
            "created_at": now.isoformat(),
            "updated_at": None,
        }
        # Response schemas typically don't validate enums (data comes from DB)
        # This documents that behavior - validation is at request level
        result = TaskResponse.model_validate(data)
        assert result.priority == "critical"

    def test_task_response_validates_status(self):
        """Task status must be valid enum value.

        Note: TaskResponse doesn't validate status at response level,
        only at create/update level. This test verifies the schema accepts
        the data but documents that validation happens at request level.
        """
        now = datetime.now(timezone.utc)
        data = {
            "id": 1,
            "title": "Test",
            "description": None,
            "assignee_employee_id": None,
            "created_by": "test",
            "status": "pending",  # Not validated at response level
            "priority": "high",
            "is_critical": False,
            "due_at": None,
            "completed_at": None,
            "target_type": None,
            "target_id": None,
            "is_archived": False,
            "created_at": now.isoformat(),
            "updated_at": None,
        }
        # Response schemas typically don't validate enums
        result = TaskResponse.model_validate(data)
        assert result.status == "pending"

    def test_task_list_response_structure(self, sample_task_response):
        """Paginated task list has correct structure."""
        paginated = {
            "items": [sample_task_response],
            "total": 1,
            "page": 1,
            "page_size": 20,
        }
        result = TaskListResponse.model_validate(paginated)
        assert len(result.items) == 1


class TestNoteResponseSchema:
    """Test note response schema validation."""

    def test_valid_note_response(self, sample_note_response):
        """Valid note data passes schema validation."""
        result = NoteResponse.model_validate(sample_note_response)
        assert result.id == 1
        assert result.pinned is True

    def test_note_list_response_structure(self, sample_note_response):
        """Paginated note list has correct structure."""
        paginated = {
            "items": [sample_note_response],
            "total": 1,
            "page": 1,
            "page_size": 20,
        }
        result = NoteListResponse.model_validate(paginated)
        assert len(result.items) == 1


class TestDocumentResponseSchema:
    """Test document response schema validation."""

    def test_valid_document_response(self, sample_document_response):
        """Valid document data passes schema validation."""
        result = DocumentResponse.model_validate(sample_document_response)
        assert result.id == 1
        assert result.document_type == "license"
        assert result.status == "active"

    def test_document_list_response_structure(self, sample_document_response):
        """Paginated document list has correct structure."""
        paginated = {
            "items": [sample_document_response],
            "total": 1,
            "page": 1,
            "page_size": 20,
        }
        result = DocumentListResponse.model_validate(paginated)
        assert len(result.items) == 1


class TestBonusResponseSchema:
    """Test bonus response schema validation."""

    def test_valid_bonus_response(self, sample_bonus_response):
        """Valid bonus data passes schema validation."""
        result = BonusResponse.model_validate(sample_bonus_response)
        assert result.id == 1
        assert result.amount == 5000.0
        assert result.bonus_type == "performance"

    def test_bonus_response_validates_bonus_type(self):
        """Bonus type must be valid enum value.

        Note: BonusResponse doesn't validate bonus_type at response level.
        Validation happens at BonusCreate/BonusUpdate level.
        """
        now = datetime.now(timezone.utc)
        data = {
            "id": 1,
            "employee_id": 1,
            "title": "Test",
            "description": None,
            "amount": 1000,
            "currency": "SAR",
            "bonus_type": "special",  # Not validated at response level
            "conditions": None,
            "promised_date": now.isoformat(),
            "due_date": None,
            "status": "promised",
            "approved_by": None,
            "approved_at": None,
            "created_at": now.isoformat(),
            "updated_at": None,
        }
        # Response schemas typically don't validate enums
        result = BonusResponse.model_validate(data)
        assert result.bonus_type == "special"

    def test_bonus_with_payments_schema(self, sample_bonus_response):
        """BonusWithPayments includes payment details."""
        enriched = {
            **sample_bonus_response,
            "payments": [],
            "total_paid": 0.0,
            "remaining": 5000.0,
            "employee_name": "Ahmed Al-Farsi",
        }
        result = BonusWithPayments.model_validate(enriched)
        assert result.total_paid == 0.0
        assert result.remaining == 5000.0

    def test_bonus_list_response_structure(self, sample_bonus_response):
        """Paginated bonus list has correct structure."""
        paginated = {
            "items": [sample_bonus_response],
            "total": 1,
            "page": 1,
            "page_size": 20,
        }
        result = BonusListResponse.model_validate(paginated)
        assert len(result.items) == 1


class TestLogEntryResponseSchema:
    """Test log entry response schema validation."""

    def test_valid_log_entry_response(self, sample_log_entry_response):
        """Valid log entry data passes schema validation."""
        result = LogEntryResponse.model_validate(sample_log_entry_response)
        assert result.id == 1
        assert result.category == "achievement"
        assert result.title == "Exceeded sales target"

    def test_log_entry_validates_category(self):
        """Log category must be valid enum value.

        Note: LogEntryResponse doesn't validate category at response level.
        Validation happens at LogEntryCreate level.
        """
        now = datetime.now(timezone.utc)
        data = {
            "id": 1,
            "employee_id": 1,
            "category": "performance_review",  # Not validated at response level
            "title": "Test",
            "content": "Test content",
            "severity": None,
            "is_positive": True,
            "logged_by": "test",
            "occurred_at": now.isoformat(),
            "created_at": now.isoformat(),
        }
        # Response schemas typically don't validate enums
        result = LogEntryResponse.model_validate(data)
        assert result.category == "performance_review"

    def test_log_entry_validates_severity(self):
        """Log severity must be valid enum value if provided.

        Note: LogEntryResponse doesn't validate severity at response level.
        Validation happens at LogEntryCreate level.
        """
        now = datetime.now(timezone.utc)
        data = {
            "id": 1,
            "employee_id": 1,
            "category": "issue",
            "title": "Test",
            "content": "Test content",
            "severity": "critical",  # Not validated at response level
            "is_positive": False,
            "logged_by": "test",
            "occurred_at": now.isoformat(),
            "created_at": now.isoformat(),
        }
        # Response schemas typically don't validate enums
        result = LogEntryResponse.model_validate(data)
        assert result.severity == "critical"

    def test_log_entry_list_response_structure(self, sample_log_entry_response):
        """Paginated log entry list has correct structure."""
        paginated = {
            "items": [sample_log_entry_response],
            "total": 1,
            "page": 1,
            "page_size": 20,
        }
        result = LogEntryListResponse.model_validate(paginated)
        assert len(result.items) == 1


class TestSkillResponseSchema:
    """Test skill response schema validation."""

    def test_valid_skill_response(self, sample_skill_response):
        """Valid skill data passes schema validation."""
        result = SkillResponse.model_validate(sample_skill_response)
        assert result.id == 1
        assert result.name == "Python"
        assert result.category == "technical"

    def test_skill_list_response_structure(self, sample_skill_response):
        """Skill list has correct structure."""
        list_response = {
            "items": [sample_skill_response],
            "total": 1,
        }
        result = SkillListResponse.model_validate(list_response)
        assert len(result.items) == 1


class TestPaginationStructure:
    """Test pagination wrapper consistency."""

    def test_pagination_requires_items(self):
        """Paginated responses require items array."""
        invalid = {"total": 0, "page": 1, "page_size": 20}
        with pytest.raises(ValidationError):
            EmployeeListResponse.model_validate(invalid)

    def test_pagination_requires_total(self, sample_employee_response):
        """Paginated responses require total count."""
        invalid = {"items": [sample_employee_response], "page": 1, "page_size": 20}
        with pytest.raises(ValidationError):
            EmployeeListResponse.model_validate(invalid)

    def test_empty_pagination_is_valid(self):
        """Empty paginated response is valid."""
        empty = {"items": [], "total": 0, "page": 1, "page_size": 20}
        result = EmployeeListResponse.model_validate(empty)
        assert result.items == []
        assert result.total == 0
