"""Contract tests for API request schema validation.

These tests ensure that:
1. Frontend-constructed payloads match API create/update schemas
2. Required fields are properly enforced
3. Enum values are validated correctly
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from cmd_center.backend.models.employee_models import (
    EmployeeCreate,
    EmployeeUpdate,
)
from cmd_center.backend.models.task_models import (
    TaskCreate,
    TaskUpdate,
)
from cmd_center.backend.models.note_models import (
    NoteCreate,
    NoteUpdate,
)
from cmd_center.backend.models.document_models import (
    DocumentCreate,
    DocumentUpdate,
)
from cmd_center.backend.models.bonus_models import (
    BonusCreate,
    BonusUpdate,
)
from cmd_center.backend.models.employee_log_models import (
    LogEntryCreate,
)
from cmd_center.backend.models.skill_models import (
    SkillCreate,
    SkillUpdate,
)


class TestEmployeeCreateSchema:
    """Test employee creation payload validation."""

    def test_valid_employee_create(self):
        """Valid employee creation payload."""
        payload = {
            "full_name": "John Doe",
            "role_title": "Developer",
            "department": "engineering",
            "email": "john@company.com",
        }
        result = EmployeeCreate.model_validate(payload)
        assert result.full_name == "John Doe"

    def test_employee_create_requires_full_name(self):
        """Employee creation requires full_name."""
        payload = {"role_title": "Developer"}
        with pytest.raises(ValidationError) as exc_info:
            EmployeeCreate.model_validate(payload)
        assert "full_name" in str(exc_info.value)

    def test_employee_create_requires_role_title(self):
        """Employee creation requires role_title."""
        payload = {"full_name": "John Doe"}
        with pytest.raises(ValidationError) as exc_info:
            EmployeeCreate.model_validate(payload)
        assert "role_title" in str(exc_info.value)


class TestTaskCreateSchema:
    """Test task creation payload validation."""

    def test_valid_task_create(self):
        """Valid task creation payload."""
        payload = {
            "title": "Complete report",
            "assignee_employee_id": 1,
            "priority": "high",
        }
        result = TaskCreate.model_validate(payload)
        assert result.title == "Complete report"
        assert result.priority == "high"

    def test_task_create_requires_title(self):
        """Task creation requires title."""
        payload = {"priority": "high"}
        with pytest.raises(ValidationError) as exc_info:
            TaskCreate.model_validate(payload)
        assert "title" in str(exc_info.value)

    def test_task_create_validates_priority(self):
        """Task priority must be valid enum."""
        valid_priorities = ["low", "medium", "high"]
        for priority in valid_priorities:
            payload = {"title": "Test", "priority": priority}
            result = TaskCreate.model_validate(payload)
            assert result.priority == priority

    def test_task_create_rejects_invalid_priority(self):
        """Task creation rejects invalid priority."""
        invalid_priorities = ["critical", "urgent", "normal", "HIGH"]
        for priority in invalid_priorities:
            payload = {"title": "Test", "priority": priority}
            with pytest.raises(ValidationError):
                TaskCreate.model_validate(payload)


class TestNoteCreateSchema:
    """Test note creation payload validation."""

    def test_valid_note_create(self):
        """Valid note creation payload."""
        payload = {
            "content": "Meeting notes from today",
            "target_type": "deal",
            "target_id": 100,
            "tags": "meeting,important",
        }
        result = NoteCreate.model_validate(payload)
        assert result.content == "Meeting notes from today"

    def test_note_create_requires_content(self):
        """Note creation requires content."""
        payload = {"target_type": "deal", "target_id": 100}
        with pytest.raises(ValidationError) as exc_info:
            NoteCreate.model_validate(payload)
        assert "content" in str(exc_info.value)


class TestDocumentCreateSchema:
    """Test document creation payload validation."""

    def test_valid_document_create(self):
        """Valid document creation payload."""
        now = datetime.now(timezone.utc)
        payload = {
            "title": "Business License",
            "document_type": "license",
            "expiry_date": now.isoformat(),
            "status": "active",
        }
        result = DocumentCreate.model_validate(payload)
        assert result.title == "Business License"

    def test_document_create_requires_title(self):
        """Document creation requires title."""
        payload = {"document_type": "license"}
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate.model_validate(payload)
        assert "title" in str(exc_info.value)


class TestBonusCreateSchema:
    """Test bonus creation payload validation."""

    def test_valid_bonus_create(self):
        """Valid bonus creation payload."""
        now = datetime.now(timezone.utc)
        payload = {
            "title": "Q4 Bonus",
            "employee_id": 1,
            "amount": 5000.0,
            "currency": "SAR",
            "bonus_type": "performance",
            "promised_date": now.isoformat(),
        }
        result = BonusCreate.model_validate(payload)
        assert result.title == "Q4 Bonus"
        assert result.amount == 5000.0

    def test_bonus_create_requires_promised_date(self):
        """Bonus creation requires promised_date - this caught Bug #12."""
        payload = {
            "title": "Bonus",
            "employee_id": 1,
            "amount": 5000,
            "currency": "SAR",
            # Missing promised_date
        }
        with pytest.raises(ValidationError) as exc_info:
            BonusCreate.model_validate(payload)
        assert "promised_date" in str(exc_info.value)

    def test_bonus_create_requires_employee_id(self):
        """Bonus creation requires employee_id."""
        now = datetime.now(timezone.utc)
        payload = {
            "title": "Bonus",
            "amount": 5000,
            "promised_date": now.isoformat(),
        }
        with pytest.raises(ValidationError) as exc_info:
            BonusCreate.model_validate(payload)
        assert "employee_id" in str(exc_info.value)

    def test_bonus_create_validates_bonus_type(self):
        """Bonus type must be valid enum."""
        now = datetime.now(timezone.utc)
        valid_types = ["performance", "project", "annual", "other"]

        for bonus_type in valid_types:
            payload = {
                "title": "Test",
                "employee_id": 1,
                "amount": 1000,
                "bonus_type": bonus_type,
                "promised_date": now.isoformat(),
            }
            result = BonusCreate.model_validate(payload)
            assert result.bonus_type == bonus_type

    def test_bonus_create_rejects_invalid_bonus_type(self):
        """Bonus creation rejects invalid bonus_type."""
        now = datetime.now(timezone.utc)
        invalid_types = ["special", "bonus", "reward", "Performance"]

        for bonus_type in invalid_types:
            payload = {
                "title": "Test",
                "employee_id": 1,
                "amount": 1000,
                "bonus_type": bonus_type,
                "promised_date": now.isoformat(),
            }
            with pytest.raises(ValidationError):
                BonusCreate.model_validate(payload)

    def test_bonus_create_requires_positive_amount(self):
        """Bonus amount must be positive."""
        now = datetime.now(timezone.utc)
        payload = {
            "title": "Test",
            "employee_id": 1,
            "amount": -100,  # Negative
            "promised_date": now.isoformat(),
        }
        with pytest.raises(ValidationError):
            BonusCreate.model_validate(payload)


class TestLogEntryCreateSchema:
    """Test log entry creation payload validation."""

    def test_valid_log_entry_create(self):
        """Valid log entry creation payload."""
        payload = {
            "employee_id": 1,
            "category": "achievement",
            "title": "Exceeded target",
            "content": "Exceeded sales target by 20%",
            "severity": "low",
        }
        result = LogEntryCreate.model_validate(payload)
        assert result.category == "achievement"

    def test_log_entry_validates_category(self):
        """Log category must be valid enum - this caught Bug #7."""
        valid_categories = ["achievement", "issue", "feedback", "milestone", "other"]

        for category in valid_categories:
            payload = {
                "employee_id": 1,
                "category": category,
                "title": "Test",
                "content": "Test content",
            }
            result = LogEntryCreate.model_validate(payload)
            assert result.category == category

    def test_log_entry_rejects_invalid_category(self):
        """Log creation rejects invalid category - would have caught Bug #7."""
        invalid_categories = ["performance_review", "review", "assessment", "Achievement"]

        for category in invalid_categories:
            payload = {
                "employee_id": 1,
                "category": category,
                "title": "Test",
                "content": "Test content",
            }
            with pytest.raises(ValidationError):
                LogEntryCreate.model_validate(payload)

    def test_log_entry_validates_severity(self):
        """Log severity must be valid enum - this caught Bug #7."""
        valid_severities = ["low", "medium", "high"]

        for severity in valid_severities:
            payload = {
                "employee_id": 1,
                "category": "issue",
                "title": "Test",
                "content": "Test content",
                "severity": severity,
            }
            result = LogEntryCreate.model_validate(payload)
            assert result.severity == severity

    def test_log_entry_rejects_invalid_severity(self):
        """Log creation rejects invalid severity - would have caught Bug #7."""
        invalid_severities = ["critical", "urgent", "warning", "High"]

        for severity in invalid_severities:
            payload = {
                "employee_id": 1,
                "category": "issue",
                "title": "Test",
                "content": "Test content",
                "severity": severity,
            }
            with pytest.raises(ValidationError):
                LogEntryCreate.model_validate(payload)

    def test_log_entry_requires_title(self):
        """Log entry requires title field."""
        payload = {
            "employee_id": 1,
            "category": "achievement",
            "content": "Test content",
        }
        with pytest.raises(ValidationError) as exc_info:
            LogEntryCreate.model_validate(payload)
        assert "title" in str(exc_info.value)

    def test_log_entry_requires_content(self):
        """Log entry requires content field."""
        payload = {
            "employee_id": 1,
            "category": "achievement",
            "title": "Test",
        }
        with pytest.raises(ValidationError) as exc_info:
            LogEntryCreate.model_validate(payload)
        assert "content" in str(exc_info.value)


class TestSkillCreateSchema:
    """Test skill creation payload validation."""

    def test_valid_skill_create(self):
        """Valid skill creation payload."""
        payload = {
            "name": "Python",
            "category": "technical",
            "description": "Python programming",
        }
        result = SkillCreate.model_validate(payload)
        assert result.name == "Python"

    def test_skill_create_requires_name(self):
        """Skill creation requires name."""
        payload = {"category": "technical"}
        with pytest.raises(ValidationError) as exc_info:
            SkillCreate.model_validate(payload)
        assert "name" in str(exc_info.value)


class TestUpdateSchemas:
    """Test update schema validation."""

    def test_employee_update_all_fields_optional(self):
        """Employee update has all optional fields."""
        payload = {"department": "sales"}
        result = EmployeeUpdate.model_validate(payload)
        assert result.department == "sales"
        assert result.full_name is None

    def test_task_update_all_fields_optional(self):
        """Task update has all optional fields."""
        payload = {"priority": "low"}
        result = TaskUpdate.model_validate(payload)
        assert result.priority == "low"
        assert result.title is None

    def test_bonus_update_validates_status(self):
        """Bonus update validates status enum."""
        valid_statuses = ["promised", "approved", "partial", "paid", "cancelled"]

        for status in valid_statuses:
            payload = {"status": status}
            result = BonusUpdate.model_validate(payload)
            assert result.status == status

    def test_bonus_update_rejects_invalid_status(self):
        """Bonus update rejects invalid status."""
        invalid_statuses = ["pending", "completed", "active"]

        for status in invalid_statuses:
            payload = {"status": status}
            with pytest.raises(ValidationError):
                BonusUpdate.model_validate(payload)
