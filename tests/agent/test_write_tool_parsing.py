"""Unit tests for write tool parameter parsing.

Tests parameter validation, preview generation, payload construction,
and schema generation for all 6 write tools:
- RequestCreateTask
- RequestCreateNote
- RequestCreateReminder
- RequestSendEmail
- RequestUpdateDeal
- RequestAddDealNote
"""

import pytest
from pydantic import ValidationError

from cmd_center.agent.tools.write_tools import (
    RequestCreateTask,
    RequestCreateNote,
    RequestCreateReminder,
    RequestSendEmail,
    RequestUpdateDeal,
    RequestAddDealNote,
    CreateTaskParams,
    CreateNoteParams,
    CreateReminderParams,
    SendEmailParams,
    UpdateDealParams,
    AddDealNoteParams,
)
from cmd_center.agent.tools.base import ToolResult


# ============================================================================
# CreateTaskParams Tests
# ============================================================================


class TestCreateTaskParamsValidation:
    """Parameter validation tests for CreateTaskParams."""

    def test_required_field_title_missing_raises_error(self):
        """Title is required and raises error when missing."""
        with pytest.raises(ValidationError) as exc_info:
            CreateTaskParams()
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("title",) for e in errors)

    def test_optional_fields_have_correct_defaults(self):
        """Optional fields have correct default values."""
        params = CreateTaskParams(title="Test task")
        assert params.description is None
        assert params.priority == "medium"
        assert params.assignee_employee_id is None
        assert params.due_at is None
        assert params.target_type is None
        assert params.target_id is None

    def test_field_types_validated_title_must_be_str(self):
        """Title must be a string type."""
        # Pydantic coerces integers to strings, so test with dict which fails
        with pytest.raises(ValidationError):
            CreateTaskParams(title={"invalid": "type"})

    def test_field_types_validated_assignee_employee_id_must_be_int(self):
        """assignee_employee_id must be an integer if provided."""
        # String that cannot be coerced to int
        with pytest.raises(ValidationError):
            CreateTaskParams(title="Test", assignee_employee_id="not-an-int")

    def test_field_types_validated_target_id_must_be_int(self):
        """target_id must be an integer if provided."""
        with pytest.raises(ValidationError):
            CreateTaskParams(title="Test", target_id="not-an-int")


class TestRequestCreateTaskPreview:
    """Preview generation tests for RequestCreateTask."""

    def test_preview_includes_title(self):
        """Preview includes task title."""
        tool = RequestCreateTask()
        result = tool.parse_and_execute({"title": "Follow up with client"})
        preview = result.data["pending_action"]["preview"]
        assert "Follow up with client" in preview

    def test_preview_includes_priority(self):
        """Preview includes priority level."""
        tool = RequestCreateTask()
        result = tool.parse_and_execute({"title": "Task", "priority": "high"})
        preview = result.data["pending_action"]["preview"]
        assert "high" in preview.lower()

    def test_preview_includes_description(self):
        """Preview includes description when provided."""
        tool = RequestCreateTask()
        result = tool.parse_and_execute({
            "title": "Task",
            "description": "Detailed task description"
        })
        preview = result.data["pending_action"]["preview"]
        assert "Detailed task description" in preview

    def test_preview_includes_assignee(self):
        """Preview includes assignee ID when provided."""
        tool = RequestCreateTask()
        result = tool.parse_and_execute({
            "title": "Task",
            "assignee_employee_id": 42
        })
        preview = result.data["pending_action"]["preview"]
        assert "42" in preview

    def test_preview_includes_due_date(self):
        """Preview includes due date when provided."""
        tool = RequestCreateTask()
        result = tool.parse_and_execute({
            "title": "Task",
            "due_at": "2024-03-15T10:00:00Z"
        })
        preview = result.data["pending_action"]["preview"]
        assert "2024-03-15" in preview

    def test_preview_includes_target_info(self):
        """Preview includes target type and ID when provided."""
        tool = RequestCreateTask()
        result = tool.parse_and_execute({
            "title": "Task",
            "target_type": "deal",
            "target_id": 123
        })
        preview = result.data["pending_action"]["preview"]
        assert "deal" in preview.lower()
        assert "123" in preview

    def test_preview_format_is_human_readable(self):
        """Preview format is human-readable with clear structure."""
        tool = RequestCreateTask()
        result = tool.parse_and_execute({
            "title": "Important Task",
            "priority": "high"
        })
        preview = result.data["pending_action"]["preview"]
        assert "CREATE TASK" in preview
        assert "Title:" in preview

    def test_preview_contains_all_required_info_for_decision(self):
        """Preview contains all info needed for user to make decision."""
        tool = RequestCreateTask()
        result = tool.parse_and_execute({
            "title": "Review proposal",
            "description": "Check pricing",
            "priority": "high",
            "assignee_employee_id": 5,
            "due_at": "2024-03-20T09:00:00Z",
            "target_type": "deal",
            "target_id": 999
        })
        preview = result.data["pending_action"]["preview"]
        # All key information should be in preview
        assert "Review proposal" in preview
        assert "Check pricing" in preview
        assert "high" in preview.lower()
        assert "5" in preview
        assert "2024-03-20" in preview
        assert "deal" in preview.lower()
        assert "999" in preview


class TestRequestCreateTaskPayload:
    """Payload construction tests for RequestCreateTask."""

    def test_payload_includes_all_input_parameters(self):
        """Payload includes all provided input parameters."""
        tool = RequestCreateTask()
        result = tool.parse_and_execute({
            "title": "Test Task",
            "description": "Description",
            "priority": "high",
            "assignee_employee_id": 10,
            "due_at": "2024-03-15T10:00:00Z",
            "target_type": "deal",
            "target_id": 100
        })
        payload = result.data["pending_action"]["payload"]
        assert payload["title"] == "Test Task"
        assert payload["description"] == "Description"
        assert payload["priority"] == "high"
        assert payload["assignee_employee_id"] == 10
        assert payload["due_at"] == "2024-03-15T10:00:00Z"
        assert payload["target_type"] == "deal"
        assert payload["target_id"] == 100

    def test_payload_handles_optional_none_values(self):
        """Payload correctly handles None values for optional fields."""
        tool = RequestCreateTask()
        result = tool.parse_and_execute({"title": "Minimal Task"})
        payload = result.data["pending_action"]["payload"]
        assert payload["title"] == "Minimal Task"
        assert payload["description"] is None
        assert payload["assignee_employee_id"] is None
        assert payload["due_at"] is None
        assert payload["target_type"] is None
        assert payload["target_id"] is None

    def test_payload_preserves_datetime_format(self):
        """Payload preserves ISO datetime format."""
        tool = RequestCreateTask()
        due_date = "2024-12-31T23:59:59Z"
        result = tool.parse_and_execute({
            "title": "Task",
            "due_at": due_date
        })
        payload = result.data["pending_action"]["payload"]
        assert payload["due_at"] == due_date


class TestRequestCreateTaskSchema:
    """Schema generation tests for RequestCreateTask."""

    def test_schema_is_valid_openai_format(self):
        """Schema is in valid OpenAI function format."""
        tool = RequestCreateTask()
        schema = tool.get_openai_schema()
        assert schema["type"] == "function"
        assert "function" in schema
        assert "name" in schema["function"]
        assert "description" in schema["function"]
        assert "parameters" in schema["function"]

    def test_schema_required_fields_marked_correctly(self):
        """Required fields are correctly marked in schema."""
        tool = RequestCreateTask()
        schema = tool.get_openai_schema()
        required = schema["function"]["parameters"].get("required", [])
        assert "title" in required

    def test_schema_has_descriptions_for_all_parameters(self):
        """All parameters have descriptions."""
        tool = RequestCreateTask()
        schema = tool.get_openai_schema()
        properties = schema["function"]["parameters"]["properties"]
        for prop_name, prop_def in properties.items():
            assert "description" in prop_def, f"Missing description for {prop_name}"


# ============================================================================
# CreateNoteParams Tests
# ============================================================================


class TestCreateNoteParamsValidation:
    """Parameter validation tests for CreateNoteParams."""

    def test_required_field_content_missing_raises_error(self):
        """Content is required and raises error when missing."""
        with pytest.raises(ValidationError) as exc_info:
            CreateNoteParams(target_type="deal", target_id=1)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("content",) for e in errors)

    def test_required_field_target_type_missing_raises_error(self):
        """target_type is required and raises error when missing."""
        with pytest.raises(ValidationError) as exc_info:
            CreateNoteParams(content="Note", target_id=1)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("target_type",) for e in errors)

    def test_required_field_target_id_missing_raises_error(self):
        """target_id is required and raises error when missing."""
        with pytest.raises(ValidationError) as exc_info:
            CreateNoteParams(content="Note", target_type="deal")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("target_id",) for e in errors)

    def test_optional_fields_have_correct_defaults(self):
        """Optional fields have correct default values."""
        params = CreateNoteParams(content="Note", target_type="deal", target_id=1)
        assert params.pinned is False

    def test_field_types_validated_target_id_must_be_int(self):
        """target_id must be an integer."""
        with pytest.raises(ValidationError):
            CreateNoteParams(content="Note", target_type="deal", target_id="invalid")


class TestRequestCreateNotePreview:
    """Preview generation tests for RequestCreateNote."""

    def test_preview_includes_content(self):
        """Preview includes note content."""
        tool = RequestCreateNote()
        result = tool.parse_and_execute({
            "content": "Important meeting notes",
            "target_type": "deal",
            "target_id": 123
        })
        preview = result.data["pending_action"]["preview"]
        assert "Important meeting notes" in preview

    def test_preview_truncates_long_content(self):
        """Long content is truncated in preview."""
        tool = RequestCreateNote()
        long_content = "A" * 200  # Exceeds 100 char truncation limit
        result = tool.parse_and_execute({
            "content": long_content,
            "target_type": "deal",
            "target_id": 123
        })
        preview = result.data["pending_action"]["preview"]
        assert "..." in preview
        assert len(preview) < len(long_content) + 100  # Allow for other preview text

    def test_preview_includes_target_info(self):
        """Preview includes target type and ID."""
        tool = RequestCreateNote()
        result = tool.parse_and_execute({
            "content": "Note",
            "target_type": "person",
            "target_id": 456
        })
        preview = result.data["pending_action"]["preview"]
        assert "person" in preview.lower()
        assert "456" in preview

    def test_preview_includes_pinned_status(self):
        """Preview indicates pinned status when true."""
        tool = RequestCreateNote()
        result = tool.parse_and_execute({
            "content": "Pinned note",
            "target_type": "deal",
            "target_id": 123,
            "pinned": True
        })
        preview = result.data["pending_action"]["preview"]
        assert "Pin" in preview or "pin" in preview.lower()

    def test_preview_format_is_human_readable(self):
        """Preview format is human-readable."""
        tool = RequestCreateNote()
        result = tool.parse_and_execute({
            "content": "Test note",
            "target_type": "deal",
            "target_id": 123
        })
        preview = result.data["pending_action"]["preview"]
        assert "CREATE NOTE" in preview


class TestRequestCreateNotePayload:
    """Payload construction tests for RequestCreateNote."""

    def test_payload_includes_all_input_parameters(self):
        """Payload includes all provided input parameters."""
        tool = RequestCreateNote()
        result = tool.parse_and_execute({
            "content": "Test note content",
            "target_type": "organization",
            "target_id": 789,
            "pinned": True
        })
        payload = result.data["pending_action"]["payload"]
        assert payload["content"] == "Test note content"
        assert payload["target_type"] == "organization"
        assert payload["target_id"] == 789
        assert payload["pinned"] is True

    def test_payload_handles_optional_none_values(self):
        """Payload correctly handles default values."""
        tool = RequestCreateNote()
        result = tool.parse_and_execute({
            "content": "Note",
            "target_type": "deal",
            "target_id": 1
        })
        payload = result.data["pending_action"]["payload"]
        assert payload["pinned"] is False


class TestRequestCreateNoteSchema:
    """Schema generation tests for RequestCreateNote."""

    def test_schema_is_valid_openai_format(self):
        """Schema is in valid OpenAI function format."""
        tool = RequestCreateNote()
        schema = tool.get_openai_schema()
        assert schema["type"] == "function"
        assert "function" in schema

    def test_schema_required_fields_marked_correctly(self):
        """Required fields are correctly marked in schema."""
        tool = RequestCreateNote()
        schema = tool.get_openai_schema()
        required = schema["function"]["parameters"].get("required", [])
        assert "content" in required
        assert "target_type" in required
        assert "target_id" in required

    def test_schema_has_descriptions_for_all_parameters(self):
        """All parameters have descriptions."""
        tool = RequestCreateNote()
        schema = tool.get_openai_schema()
        properties = schema["function"]["parameters"]["properties"]
        for prop_name, prop_def in properties.items():
            assert "description" in prop_def, f"Missing description for {prop_name}"


# ============================================================================
# CreateReminderParams Tests
# ============================================================================


class TestCreateReminderParamsValidation:
    """Parameter validation tests for CreateReminderParams."""

    def test_required_field_target_type_missing_raises_error(self):
        """target_type is required and raises error when missing."""
        with pytest.raises(ValidationError) as exc_info:
            CreateReminderParams(
                target_id=1,
                remind_at="2024-03-20T09:00:00Z",
                message="Test"
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("target_type",) for e in errors)

    def test_required_field_target_id_missing_raises_error(self):
        """target_id is required and raises error when missing."""
        with pytest.raises(ValidationError) as exc_info:
            CreateReminderParams(
                target_type="deal",
                remind_at="2024-03-20T09:00:00Z",
                message="Test"
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("target_id",) for e in errors)

    def test_required_field_remind_at_missing_raises_error(self):
        """remind_at is required and raises error when missing."""
        with pytest.raises(ValidationError) as exc_info:
            CreateReminderParams(
                target_type="deal",
                target_id=1,
                message="Test"
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("remind_at",) for e in errors)

    def test_required_field_message_missing_raises_error(self):
        """message is required and raises error when missing."""
        with pytest.raises(ValidationError) as exc_info:
            CreateReminderParams(
                target_type="deal",
                target_id=1,
                remind_at="2024-03-20T09:00:00Z"
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("message",) for e in errors)

    def test_optional_fields_have_correct_defaults(self):
        """Optional fields have correct default values."""
        params = CreateReminderParams(
            target_type="deal",
            target_id=1,
            remind_at="2024-03-20T09:00:00Z",
            message="Test"
        )
        assert params.channel == "app"


class TestRequestCreateReminderPreview:
    """Preview generation tests for RequestCreateReminder."""

    def test_preview_includes_message(self):
        """Preview includes reminder message."""
        tool = RequestCreateReminder()
        result = tool.parse_and_execute({
            "target_type": "deal",
            "target_id": 123,
            "remind_at": "2024-03-20T09:00:00Z",
            "message": "Follow up on proposal"
        })
        preview = result.data["pending_action"]["preview"]
        assert "Follow up on proposal" in preview

    def test_preview_includes_remind_at_datetime(self):
        """Preview includes remind_at datetime."""
        tool = RequestCreateReminder()
        result = tool.parse_and_execute({
            "target_type": "deal",
            "target_id": 123,
            "remind_at": "2024-03-20T09:00:00Z",
            "message": "Test"
        })
        preview = result.data["pending_action"]["preview"]
        assert "2024-03-20" in preview

    def test_preview_includes_target_info(self):
        """Preview includes target type and ID."""
        tool = RequestCreateReminder()
        result = tool.parse_and_execute({
            "target_type": "person",
            "target_id": 456,
            "remind_at": "2024-03-20T09:00:00Z",
            "message": "Test"
        })
        preview = result.data["pending_action"]["preview"]
        assert "person" in preview.lower()
        assert "456" in preview

    def test_preview_includes_channel(self):
        """Preview includes notification channel."""
        tool = RequestCreateReminder()
        result = tool.parse_and_execute({
            "target_type": "deal",
            "target_id": 123,
            "remind_at": "2024-03-20T09:00:00Z",
            "message": "Test",
            "channel": "email"
        })
        preview = result.data["pending_action"]["preview"]
        assert "email" in preview.lower()

    def test_preview_format_is_human_readable(self):
        """Preview format is human-readable."""
        tool = RequestCreateReminder()
        result = tool.parse_and_execute({
            "target_type": "deal",
            "target_id": 123,
            "remind_at": "2024-03-20T09:00:00Z",
            "message": "Test"
        })
        preview = result.data["pending_action"]["preview"]
        assert "CREATE REMINDER" in preview


class TestRequestCreateReminderPayload:
    """Payload construction tests for RequestCreateReminder."""

    def test_payload_includes_all_input_parameters(self):
        """Payload includes all provided input parameters."""
        tool = RequestCreateReminder()
        result = tool.parse_and_execute({
            "target_type": "deal",
            "target_id": 123,
            "remind_at": "2024-03-20T09:00:00Z",
            "message": "Follow up",
            "channel": "sms"
        })
        payload = result.data["pending_action"]["payload"]
        assert payload["target_type"] == "deal"
        assert payload["target_id"] == 123
        assert payload["remind_at"] == "2024-03-20T09:00:00Z"
        assert payload["message"] == "Follow up"
        assert payload["channel"] == "sms"

    def test_payload_preserves_datetime_format(self):
        """Payload preserves ISO datetime format for remind_at."""
        tool = RequestCreateReminder()
        remind_time = "2024-12-31T23:59:59Z"
        result = tool.parse_and_execute({
            "target_type": "deal",
            "target_id": 123,
            "remind_at": remind_time,
            "message": "Test"
        })
        payload = result.data["pending_action"]["payload"]
        assert payload["remind_at"] == remind_time


class TestRequestCreateReminderSchema:
    """Schema generation tests for RequestCreateReminder."""

    def test_schema_is_valid_openai_format(self):
        """Schema is in valid OpenAI function format."""
        tool = RequestCreateReminder()
        schema = tool.get_openai_schema()
        assert schema["type"] == "function"
        assert "function" in schema

    def test_schema_required_fields_marked_correctly(self):
        """Required fields are correctly marked in schema."""
        tool = RequestCreateReminder()
        schema = tool.get_openai_schema()
        required = schema["function"]["parameters"].get("required", [])
        assert "target_type" in required
        assert "target_id" in required
        assert "remind_at" in required
        assert "message" in required

    def test_schema_has_descriptions_for_all_parameters(self):
        """All parameters have descriptions."""
        tool = RequestCreateReminder()
        schema = tool.get_openai_schema()
        properties = schema["function"]["parameters"]["properties"]
        for prop_name, prop_def in properties.items():
            assert "description" in prop_def, f"Missing description for {prop_name}"


# ============================================================================
# SendEmailParams Tests
# ============================================================================


class TestSendEmailParamsValidation:
    """Parameter validation tests for SendEmailParams."""

    def test_required_field_to_missing_raises_error(self):
        """to is required and raises error when missing."""
        with pytest.raises(ValidationError) as exc_info:
            SendEmailParams(subject="Test", body="Test body")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("to",) for e in errors)

    def test_required_field_subject_missing_raises_error(self):
        """subject is required and raises error when missing."""
        with pytest.raises(ValidationError) as exc_info:
            SendEmailParams(to="test@example.com", body="Test body")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("subject",) for e in errors)

    def test_required_field_body_missing_raises_error(self):
        """body is required and raises error when missing."""
        with pytest.raises(ValidationError) as exc_info:
            SendEmailParams(to="test@example.com", subject="Test")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("body",) for e in errors)

    def test_optional_fields_have_correct_defaults(self):
        """Optional fields have correct default values."""
        params = SendEmailParams(
            to="test@example.com",
            subject="Test",
            body="Body"
        )
        assert params.cc is None
        assert params.from_mailbox is None


class TestRequestSendEmailPreview:
    """Preview generation tests for RequestSendEmail."""

    def test_preview_includes_to_address(self):
        """Preview includes recipient email address."""
        tool = RequestSendEmail()
        result = tool.parse_and_execute({
            "to": "client@example.com",
            "subject": "Test Subject",
            "body": "Test body"
        })
        preview = result.data["pending_action"]["preview"]
        assert "client@example.com" in preview

    def test_preview_includes_subject(self):
        """Preview includes email subject."""
        tool = RequestSendEmail()
        result = tool.parse_and_execute({
            "to": "client@example.com",
            "subject": "Project Proposal Discussion",
            "body": "Test body"
        })
        preview = result.data["pending_action"]["preview"]
        assert "Project Proposal Discussion" in preview

    def test_preview_includes_body(self):
        """Preview includes email body."""
        tool = RequestSendEmail()
        result = tool.parse_and_execute({
            "to": "client@example.com",
            "subject": "Test",
            "body": "Dear Client, thank you for your time"
        })
        preview = result.data["pending_action"]["preview"]
        assert "Dear Client" in preview

    def test_preview_truncates_long_body(self):
        """Long email body is truncated in preview."""
        tool = RequestSendEmail()
        long_body = "A" * 300  # Exceeds 150 char truncation limit
        result = tool.parse_and_execute({
            "to": "client@example.com",
            "subject": "Test",
            "body": long_body
        })
        preview = result.data["pending_action"]["preview"]
        assert "..." in preview

    def test_preview_includes_cc_when_provided(self):
        """Preview includes CC address when provided."""
        tool = RequestSendEmail()
        result = tool.parse_and_execute({
            "to": "client@example.com",
            "subject": "Test",
            "body": "Body",
            "cc": "manager@company.com"
        })
        preview = result.data["pending_action"]["preview"]
        assert "manager@company.com" in preview

    def test_preview_includes_from_mailbox_when_provided(self):
        """Preview includes from mailbox when provided."""
        tool = RequestSendEmail()
        result = tool.parse_and_execute({
            "to": "client@example.com",
            "subject": "Test",
            "body": "Body",
            "from_mailbox": "sales@company.com"
        })
        preview = result.data["pending_action"]["preview"]
        assert "sales@company.com" in preview

    def test_preview_format_is_human_readable(self):
        """Preview format is human-readable."""
        tool = RequestSendEmail()
        result = tool.parse_and_execute({
            "to": "client@example.com",
            "subject": "Test",
            "body": "Body"
        })
        preview = result.data["pending_action"]["preview"]
        assert "SEND EMAIL" in preview


class TestRequestSendEmailPayload:
    """Payload construction tests for RequestSendEmail."""

    def test_payload_includes_all_input_parameters(self):
        """Payload includes all provided input parameters."""
        tool = RequestSendEmail()
        result = tool.parse_and_execute({
            "to": "recipient@example.com",
            "subject": "Test Subject",
            "body": "Test body content",
            "cc": "copy@example.com",
            "from_mailbox": "sender@company.com"
        })
        payload = result.data["pending_action"]["payload"]
        assert payload["to"] == "recipient@example.com"
        assert payload["subject"] == "Test Subject"
        assert payload["body"] == "Test body content"
        assert payload["cc"] == "copy@example.com"
        assert payload["from_mailbox"] == "sender@company.com"

    def test_payload_handles_optional_none_values(self):
        """Payload correctly handles None values for optional fields."""
        tool = RequestSendEmail()
        result = tool.parse_and_execute({
            "to": "recipient@example.com",
            "subject": "Test",
            "body": "Body"
        })
        payload = result.data["pending_action"]["payload"]
        assert payload["cc"] is None
        assert payload["from_mailbox"] is None

    def test_payload_preserves_multiline_body(self):
        """Payload preserves multiline email body."""
        tool = RequestSendEmail()
        multiline_body = "Dear Client,\n\nThank you for your time.\n\nBest regards"
        result = tool.parse_and_execute({
            "to": "client@example.com",
            "subject": "Test",
            "body": multiline_body
        })
        payload = result.data["pending_action"]["payload"]
        assert payload["body"] == multiline_body


class TestRequestSendEmailSchema:
    """Schema generation tests for RequestSendEmail."""

    def test_schema_is_valid_openai_format(self):
        """Schema is in valid OpenAI function format."""
        tool = RequestSendEmail()
        schema = tool.get_openai_schema()
        assert schema["type"] == "function"
        assert "function" in schema

    def test_schema_required_fields_marked_correctly(self):
        """Required fields are correctly marked in schema."""
        tool = RequestSendEmail()
        schema = tool.get_openai_schema()
        required = schema["function"]["parameters"].get("required", [])
        assert "to" in required
        assert "subject" in required
        assert "body" in required

    def test_schema_has_descriptions_for_all_parameters(self):
        """All parameters have descriptions."""
        tool = RequestSendEmail()
        schema = tool.get_openai_schema()
        properties = schema["function"]["parameters"]["properties"]
        for prop_name, prop_def in properties.items():
            assert "description" in prop_def, f"Missing description for {prop_name}"


# ============================================================================
# UpdateDealParams Tests
# ============================================================================


class TestUpdateDealParamsValidation:
    """Parameter validation tests for UpdateDealParams."""

    def test_required_field_deal_id_missing_raises_error(self):
        """deal_id is required and raises error when missing."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateDealParams(title="New Title")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("deal_id",) for e in errors)

    def test_optional_fields_have_correct_defaults(self):
        """Optional fields have correct default values."""
        params = UpdateDealParams(deal_id=123)
        assert params.title is None
        assert params.status is None
        assert params.stage_id is None
        assert params.value is None

    def test_field_types_validated_deal_id_must_be_int(self):
        """deal_id must be an integer."""
        with pytest.raises(ValidationError):
            UpdateDealParams(deal_id="not-an-int")

    def test_field_types_validated_stage_id_must_be_int(self):
        """stage_id must be an integer if provided."""
        with pytest.raises(ValidationError):
            UpdateDealParams(deal_id=123, stage_id="not-an-int")

    def test_field_types_validated_value_must_be_numeric(self):
        """value must be numeric if provided."""
        with pytest.raises(ValidationError):
            UpdateDealParams(deal_id=123, value="not-a-number")


class TestRequestUpdateDealPreview:
    """Preview generation tests for RequestUpdateDeal."""

    def test_preview_includes_deal_id(self):
        """Preview includes deal ID."""
        tool = RequestUpdateDeal()
        result = tool.parse_and_execute({
            "deal_id": 789,
            "title": "New Title"
        })
        preview = result.data["pending_action"]["preview"]
        assert "789" in preview

    def test_preview_includes_new_title(self):
        """Preview includes new title when provided."""
        tool = RequestUpdateDeal()
        result = tool.parse_and_execute({
            "deal_id": 789,
            "title": "Updated Deal Name"
        })
        preview = result.data["pending_action"]["preview"]
        assert "Updated Deal Name" in preview

    def test_preview_includes_new_status(self):
        """Preview includes new status when provided."""
        tool = RequestUpdateDeal()
        result = tool.parse_and_execute({
            "deal_id": 789,
            "status": "won"
        })
        preview = result.data["pending_action"]["preview"]
        assert "won" in preview.lower()

    def test_preview_includes_new_stage_id(self):
        """Preview includes new stage ID when provided."""
        tool = RequestUpdateDeal()
        result = tool.parse_and_execute({
            "deal_id": 789,
            "stage_id": 5
        })
        preview = result.data["pending_action"]["preview"]
        assert "5" in preview

    def test_preview_includes_new_value(self):
        """Preview includes new value when provided."""
        tool = RequestUpdateDeal()
        result = tool.parse_and_execute({
            "deal_id": 789,
            "value": 50000.0
        })
        preview = result.data["pending_action"]["preview"]
        assert "50000" in preview

    def test_preview_format_is_human_readable(self):
        """Preview format is human-readable."""
        tool = RequestUpdateDeal()
        result = tool.parse_and_execute({
            "deal_id": 789,
            "status": "won"
        })
        preview = result.data["pending_action"]["preview"]
        assert "UPDATE DEAL" in preview


class TestRequestUpdateDealPayload:
    """Payload construction tests for RequestUpdateDeal."""

    def test_payload_includes_all_input_parameters(self):
        """Payload includes all provided input parameters."""
        tool = RequestUpdateDeal()
        result = tool.parse_and_execute({
            "deal_id": 789,
            "title": "New Title",
            "status": "won",
            "stage_id": 10,
            "value": 75000.50
        })
        payload = result.data["pending_action"]["payload"]
        assert payload["deal_id"] == 789
        assert payload["title"] == "New Title"
        assert payload["status"] == "won"
        assert payload["stage_id"] == 10
        assert payload["value"] == 75000.50

    def test_payload_handles_optional_none_values(self):
        """Payload correctly handles None values for optional fields."""
        tool = RequestUpdateDeal()
        result = tool.parse_and_execute({"deal_id": 123})
        payload = result.data["pending_action"]["payload"]
        assert payload["deal_id"] == 123
        assert payload["title"] is None
        assert payload["status"] is None
        assert payload["stage_id"] is None
        assert payload["value"] is None

    def test_payload_preserves_float_value(self):
        """Payload preserves float value correctly."""
        tool = RequestUpdateDeal()
        result = tool.parse_and_execute({
            "deal_id": 123,
            "value": 99999.99
        })
        payload = result.data["pending_action"]["payload"]
        assert payload["value"] == 99999.99


class TestRequestUpdateDealSchema:
    """Schema generation tests for RequestUpdateDeal."""

    def test_schema_is_valid_openai_format(self):
        """Schema is in valid OpenAI function format."""
        tool = RequestUpdateDeal()
        schema = tool.get_openai_schema()
        assert schema["type"] == "function"
        assert "function" in schema

    def test_schema_required_fields_marked_correctly(self):
        """Required fields are correctly marked in schema."""
        tool = RequestUpdateDeal()
        schema = tool.get_openai_schema()
        required = schema["function"]["parameters"].get("required", [])
        assert "deal_id" in required
        # Optional fields should not be required
        assert "title" not in required
        assert "status" not in required

    def test_schema_has_descriptions_for_all_parameters(self):
        """All parameters have descriptions."""
        tool = RequestUpdateDeal()
        schema = tool.get_openai_schema()
        properties = schema["function"]["parameters"]["properties"]
        for prop_name, prop_def in properties.items():
            assert "description" in prop_def, f"Missing description for {prop_name}"


# ============================================================================
# AddDealNoteParams Tests
# ============================================================================


class TestAddDealNoteParamsValidation:
    """Parameter validation tests for AddDealNoteParams."""

    def test_required_field_deal_id_missing_raises_error(self):
        """deal_id is required and raises error when missing."""
        with pytest.raises(ValidationError) as exc_info:
            AddDealNoteParams(content="Note content")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("deal_id",) for e in errors)

    def test_required_field_content_missing_raises_error(self):
        """content is required and raises error when missing."""
        with pytest.raises(ValidationError) as exc_info:
            AddDealNoteParams(deal_id=123)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("content",) for e in errors)

    def test_optional_fields_have_correct_defaults(self):
        """Optional fields have correct default values."""
        params = AddDealNoteParams(deal_id=123, content="Note")
        assert params.pinned is False

    def test_field_types_validated_deal_id_must_be_int(self):
        """deal_id must be an integer."""
        with pytest.raises(ValidationError):
            AddDealNoteParams(deal_id="not-an-int", content="Note")


class TestRequestAddDealNotePreview:
    """Preview generation tests for RequestAddDealNote."""

    def test_preview_includes_deal_id(self):
        """Preview includes deal ID."""
        tool = RequestAddDealNote()
        result = tool.parse_and_execute({
            "deal_id": 999,
            "content": "Note content"
        })
        preview = result.data["pending_action"]["preview"]
        assert "999" in preview

    def test_preview_includes_content(self):
        """Preview includes note content."""
        tool = RequestAddDealNote()
        result = tool.parse_and_execute({
            "deal_id": 999,
            "content": "Important update from meeting"
        })
        preview = result.data["pending_action"]["preview"]
        assert "Important update from meeting" in preview

    def test_preview_truncates_long_content(self):
        """Long content is truncated in preview."""
        tool = RequestAddDealNote()
        long_content = "A" * 200  # Exceeds 100 char truncation limit
        result = tool.parse_and_execute({
            "deal_id": 999,
            "content": long_content
        })
        preview = result.data["pending_action"]["preview"]
        assert "..." in preview

    def test_preview_includes_pinned_status(self):
        """Preview indicates pinned status when true."""
        tool = RequestAddDealNote()
        result = tool.parse_and_execute({
            "deal_id": 999,
            "content": "Note",
            "pinned": True
        })
        preview = result.data["pending_action"]["preview"]
        assert "Pin" in preview or "pin" in preview.lower()

    def test_preview_format_is_human_readable(self):
        """Preview format is human-readable."""
        tool = RequestAddDealNote()
        result = tool.parse_and_execute({
            "deal_id": 999,
            "content": "Note"
        })
        preview = result.data["pending_action"]["preview"]
        assert "ADD DEAL NOTE" in preview


class TestRequestAddDealNotePayload:
    """Payload construction tests for RequestAddDealNote."""

    def test_payload_includes_all_input_parameters(self):
        """Payload includes all provided input parameters."""
        tool = RequestAddDealNote()
        result = tool.parse_and_execute({
            "deal_id": 999,
            "content": "Detailed note content",
            "pinned": True
        })
        payload = result.data["pending_action"]["payload"]
        assert payload["deal_id"] == 999
        assert payload["content"] == "Detailed note content"
        assert payload["pinned"] is True

    def test_payload_handles_optional_none_values(self):
        """Payload correctly handles default values for optional fields."""
        tool = RequestAddDealNote()
        result = tool.parse_and_execute({
            "deal_id": 123,
            "content": "Note"
        })
        payload = result.data["pending_action"]["payload"]
        assert payload["pinned"] is False


class TestRequestAddDealNoteSchema:
    """Schema generation tests for RequestAddDealNote."""

    def test_schema_is_valid_openai_format(self):
        """Schema is in valid OpenAI function format."""
        tool = RequestAddDealNote()
        schema = tool.get_openai_schema()
        assert schema["type"] == "function"
        assert "function" in schema

    def test_schema_required_fields_marked_correctly(self):
        """Required fields are correctly marked in schema."""
        tool = RequestAddDealNote()
        schema = tool.get_openai_schema()
        required = schema["function"]["parameters"].get("required", [])
        assert "deal_id" in required
        assert "content" in required
        # pinned is optional
        assert "pinned" not in required

    def test_schema_has_descriptions_for_all_parameters(self):
        """All parameters have descriptions."""
        tool = RequestAddDealNote()
        schema = tool.get_openai_schema()
        properties = schema["function"]["parameters"]["properties"]
        for prop_name, prop_def in properties.items():
            assert "description" in prop_def, f"Missing description for {prop_name}"


# ============================================================================
# Cross-Tool Tests
# ============================================================================


class TestAllWriteToolsCommonBehavior:
    """Tests for behavior common to all write tools."""

    @pytest.mark.parametrize("tool_class,min_params", [
        (RequestCreateTask, {"title": "Test"}),
        (RequestCreateNote, {"content": "Test", "target_type": "deal", "target_id": 1}),
        (RequestCreateReminder, {"target_type": "deal", "target_id": 1, "remind_at": "2024-03-20T09:00:00Z", "message": "Test"}),
        (RequestSendEmail, {"to": "test@example.com", "subject": "Test", "body": "Body"}),
        (RequestUpdateDeal, {"deal_id": 123}),
        (RequestAddDealNote, {"deal_id": 123, "content": "Note"}),
    ])
    def test_all_tools_return_success_with_pending_action(self, tool_class, min_params):
        """All write tools return success with pending_action in data."""
        tool = tool_class()
        result = tool.parse_and_execute(min_params)
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert "pending_action" in result.data

    @pytest.mark.parametrize("tool_class,min_params", [
        (RequestCreateTask, {"title": "Test"}),
        (RequestCreateNote, {"content": "Test", "target_type": "deal", "target_id": 1}),
        (RequestCreateReminder, {"target_type": "deal", "target_id": 1, "remind_at": "2024-03-20T09:00:00Z", "message": "Test"}),
        (RequestSendEmail, {"to": "test@example.com", "subject": "Test", "body": "Body"}),
        (RequestUpdateDeal, {"deal_id": 123}),
        (RequestAddDealNote, {"deal_id": 123, "content": "Note"}),
    ])
    def test_all_tools_include_tool_name_in_pending_action(self, tool_class, min_params):
        """All write tools include correct tool_name in pending_action."""
        tool = tool_class()
        result = tool.parse_and_execute(min_params)
        assert result.data["pending_action"]["tool_name"] == tool.name

    @pytest.mark.parametrize("tool_class", [
        RequestCreateTask,
        RequestCreateNote,
        RequestCreateReminder,
        RequestSendEmail,
        RequestUpdateDeal,
        RequestAddDealNote,
    ])
    def test_all_tools_generate_valid_openai_schema(self, tool_class):
        """All write tools generate valid OpenAI-compatible schema."""
        tool = tool_class()
        schema = tool.get_openai_schema()

        # Check schema structure
        assert schema["type"] == "function"
        assert "function" in schema
        assert "name" in schema["function"]
        assert "description" in schema["function"]
        assert "parameters" in schema["function"]

        # Check parameters structure
        params = schema["function"]["parameters"]
        assert params["type"] == "object"
        assert "properties" in params

    @pytest.mark.parametrize("tool_class", [
        RequestCreateTask,
        RequestCreateNote,
        RequestCreateReminder,
        RequestSendEmail,
        RequestUpdateDeal,
        RequestAddDealNote,
    ])
    def test_all_tools_have_non_empty_description(self, tool_class):
        """All write tools have non-empty description."""
        tool = tool_class()
        assert tool.description
        assert len(tool.description) > 10

    @pytest.mark.parametrize("tool_class,invalid_params", [
        (RequestCreateTask, {}),  # Missing title
        (RequestCreateNote, {"content": "Test"}),  # Missing target_type and target_id
        (RequestCreateReminder, {"target_type": "deal"}),  # Missing required fields
        (RequestSendEmail, {"to": "test@example.com"}),  # Missing subject and body
        (RequestUpdateDeal, {}),  # Missing deal_id
        (RequestAddDealNote, {"deal_id": 123}),  # Missing content
    ])
    def test_all_tools_handle_invalid_params_gracefully(self, tool_class, invalid_params):
        """All write tools return error result for invalid params."""
        tool = tool_class()
        result = tool.parse_and_execute(invalid_params)
        assert result.success is False
        assert result.error is not None
