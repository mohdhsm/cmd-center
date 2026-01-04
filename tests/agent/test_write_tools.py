"""Tests for write tools that return PendingAction for confirmation."""

import pytest

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


class TestRequestCreateTask:
    """Tests for RequestCreateTask write tool."""

    def test_tool_has_correct_name(self):
        """Tool has correct name."""
        tool = RequestCreateTask()
        assert tool.name == "request_create_task"

    def test_tool_has_description(self):
        """Tool has meaningful description."""
        tool = RequestCreateTask()
        assert "task" in tool.description.lower()
        assert len(tool.description) > 10

    def test_parameters_model_is_set(self):
        """Tool has correct parameters model."""
        tool = RequestCreateTask()
        assert tool.parameters_model == CreateTaskParams

    def test_schema_has_required_fields(self):
        """Schema includes required parameters."""
        tool = RequestCreateTask()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "title" in props
        assert "description" in props
        assert "priority" in props
        assert "due_at" in props

    def test_execute_returns_pending_action(self):
        """Execute returns ToolResult with pending_action."""
        tool = RequestCreateTask()
        result = tool.parse_and_execute({
            "title": "Follow up with client",
            "description": "Call them about the proposal",
            "priority": "high",
            "due_at": "2024-03-15T10:00:00Z",
        })

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert "pending_action" in result.data
        assert result.data["pending_action"]["tool_name"] == "request_create_task"

    def test_execute_generates_preview(self):
        """Execute generates human-readable preview."""
        tool = RequestCreateTask()
        result = tool.parse_and_execute({
            "title": "Follow up with client",
            "priority": "high",
        })

        preview = result.data["pending_action"]["preview"]
        assert "Follow up with client" in preview
        assert "high" in preview.lower()

    def test_execute_includes_payload(self):
        """Execute includes all params in payload."""
        tool = RequestCreateTask()
        result = tool.parse_and_execute({
            "title": "Test Task",
            "description": "Test description",
            "priority": "medium",
            "assignee_employee_id": 42,
        })

        payload = result.data["pending_action"]["payload"]
        assert payload["title"] == "Test Task"
        assert payload["description"] == "Test description"
        assert payload["priority"] == "medium"
        assert payload["assignee_employee_id"] == 42


class TestRequestCreateNote:
    """Tests for RequestCreateNote write tool."""

    def test_tool_has_correct_name(self):
        """Tool has correct name."""
        tool = RequestCreateNote()
        assert tool.name == "request_create_note"

    def test_tool_has_description(self):
        """Tool has meaningful description."""
        tool = RequestCreateNote()
        assert "note" in tool.description.lower()

    def test_parameters_model_is_set(self):
        """Tool has correct parameters model."""
        tool = RequestCreateNote()
        assert tool.parameters_model == CreateNoteParams

    def test_schema_has_required_fields(self):
        """Schema includes required parameters."""
        tool = RequestCreateNote()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "content" in props
        assert "target_type" in props
        assert "target_id" in props

    def test_execute_returns_pending_action(self):
        """Execute returns ToolResult with pending_action."""
        tool = RequestCreateNote()
        result = tool.parse_and_execute({
            "content": "Client seemed interested in premium package",
            "target_type": "deal",
            "target_id": 123,
        })

        assert result.success is True
        assert "pending_action" in result.data
        assert result.data["pending_action"]["tool_name"] == "request_create_note"

    def test_execute_generates_preview(self):
        """Execute generates human-readable preview."""
        tool = RequestCreateNote()
        result = tool.parse_and_execute({
            "content": "Important meeting notes from today",
            "target_type": "deal",
            "target_id": 123,
        })

        preview = result.data["pending_action"]["preview"]
        assert "Important meeting notes" in preview
        assert "deal" in preview.lower()


class TestRequestCreateReminder:
    """Tests for RequestCreateReminder write tool."""

    def test_tool_has_correct_name(self):
        """Tool has correct name."""
        tool = RequestCreateReminder()
        assert tool.name == "request_create_reminder"

    def test_tool_has_description(self):
        """Tool has meaningful description."""
        tool = RequestCreateReminder()
        assert "reminder" in tool.description.lower()

    def test_parameters_model_is_set(self):
        """Tool has correct parameters model."""
        tool = RequestCreateReminder()
        assert tool.parameters_model == CreateReminderParams

    def test_schema_has_required_fields(self):
        """Schema includes required parameters."""
        tool = RequestCreateReminder()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "target_type" in props
        assert "target_id" in props
        assert "remind_at" in props
        assert "message" in props

    def test_execute_returns_pending_action(self):
        """Execute returns ToolResult with pending_action."""
        tool = RequestCreateReminder()
        result = tool.parse_and_execute({
            "target_type": "deal",
            "target_id": 456,
            "remind_at": "2024-03-20T09:00:00Z",
            "message": "Follow up on proposal",
        })

        assert result.success is True
        assert "pending_action" in result.data
        assert result.data["pending_action"]["tool_name"] == "request_create_reminder"

    def test_execute_generates_preview(self):
        """Execute generates human-readable preview."""
        tool = RequestCreateReminder()
        result = tool.parse_and_execute({
            "target_type": "deal",
            "target_id": 456,
            "remind_at": "2024-03-20T09:00:00Z",
            "message": "Call the client",
            "channel": "email",
        })

        preview = result.data["pending_action"]["preview"]
        assert "Call the client" in preview
        assert "2024-03-20" in preview


class TestRequestSendEmail:
    """Tests for RequestSendEmail write tool."""

    def test_tool_has_correct_name(self):
        """Tool has correct name."""
        tool = RequestSendEmail()
        assert tool.name == "request_send_email"

    def test_tool_has_description(self):
        """Tool has meaningful description."""
        tool = RequestSendEmail()
        assert "email" in tool.description.lower()

    def test_parameters_model_is_set(self):
        """Tool has correct parameters model."""
        tool = RequestSendEmail()
        assert tool.parameters_model == SendEmailParams

    def test_schema_has_required_fields(self):
        """Schema includes required parameters."""
        tool = RequestSendEmail()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "to" in props
        assert "subject" in props
        assert "body" in props

    def test_execute_returns_pending_action(self):
        """Execute returns ToolResult with pending_action."""
        tool = RequestSendEmail()
        result = tool.parse_and_execute({
            "to": "client@example.com",
            "subject": "Following up on our meeting",
            "body": "Dear Client,\n\nThank you for your time...",
        })

        assert result.success is True
        assert "pending_action" in result.data
        assert result.data["pending_action"]["tool_name"] == "request_send_email"

    def test_execute_generates_preview(self):
        """Execute generates human-readable preview."""
        tool = RequestSendEmail()
        result = tool.parse_and_execute({
            "to": "client@example.com",
            "subject": "Project Proposal",
            "body": "Hello,\n\nPlease find attached...",
            "cc": "manager@company.com",
        })

        preview = result.data["pending_action"]["preview"]
        assert "client@example.com" in preview
        assert "Project Proposal" in preview

    def test_execute_includes_optional_cc(self):
        """Execute includes optional cc in payload."""
        tool = RequestSendEmail()
        result = tool.parse_and_execute({
            "to": "client@example.com",
            "subject": "Test",
            "body": "Test body",
            "cc": "manager@company.com",
        })

        payload = result.data["pending_action"]["payload"]
        assert payload["cc"] == "manager@company.com"


class TestRequestUpdateDeal:
    """Tests for RequestUpdateDeal write tool."""

    def test_tool_has_correct_name(self):
        """Tool has correct name."""
        tool = RequestUpdateDeal()
        assert tool.name == "request_update_deal"

    def test_tool_has_description(self):
        """Tool has meaningful description."""
        tool = RequestUpdateDeal()
        assert "deal" in tool.description.lower()
        assert "update" in tool.description.lower()

    def test_parameters_model_is_set(self):
        """Tool has correct parameters model."""
        tool = RequestUpdateDeal()
        assert tool.parameters_model == UpdateDealParams

    def test_schema_has_required_fields(self):
        """Schema includes required parameters."""
        tool = RequestUpdateDeal()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        required = schema["function"]["parameters"].get("required", [])
        assert "deal_id" in props
        assert "deal_id" in required
        assert "title" in props
        assert "status" in props
        assert "stage_id" in props
        assert "value" in props

    def test_execute_returns_pending_action(self):
        """Execute returns ToolResult with pending_action."""
        tool = RequestUpdateDeal()
        result = tool.parse_and_execute({
            "deal_id": 789,
            "title": "Updated Deal Name",
            "value": 50000,
        })

        assert result.success is True
        assert "pending_action" in result.data
        assert result.data["pending_action"]["tool_name"] == "request_update_deal"

    def test_execute_generates_preview(self):
        """Execute generates human-readable preview."""
        tool = RequestUpdateDeal()
        result = tool.parse_and_execute({
            "deal_id": 789,
            "status": "won",
            "value": 100000,
        })

        preview = result.data["pending_action"]["preview"]
        assert "789" in preview
        assert "won" in preview.lower() or "100000" in preview


class TestRequestAddDealNote:
    """Tests for RequestAddDealNote write tool."""

    def test_tool_has_correct_name(self):
        """Tool has correct name."""
        tool = RequestAddDealNote()
        assert tool.name == "request_add_deal_note"

    def test_tool_has_description(self):
        """Tool has meaningful description."""
        tool = RequestAddDealNote()
        assert "note" in tool.description.lower()
        assert "deal" in tool.description.lower()

    def test_parameters_model_is_set(self):
        """Tool has correct parameters model."""
        tool = RequestAddDealNote()
        assert tool.parameters_model == AddDealNoteParams

    def test_schema_has_required_fields(self):
        """Schema includes required parameters."""
        tool = RequestAddDealNote()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        required = schema["function"]["parameters"].get("required", [])
        assert "deal_id" in props
        assert "deal_id" in required
        assert "content" in props
        assert "content" in required

    def test_execute_returns_pending_action(self):
        """Execute returns ToolResult with pending_action."""
        tool = RequestAddDealNote()
        result = tool.parse_and_execute({
            "deal_id": 999,
            "content": "Client agreed to terms",
        })

        assert result.success is True
        assert "pending_action" in result.data
        assert result.data["pending_action"]["tool_name"] == "request_add_deal_note"

    def test_execute_generates_preview(self):
        """Execute generates human-readable preview."""
        tool = RequestAddDealNote()
        result = tool.parse_and_execute({
            "deal_id": 999,
            "content": "Important update from meeting",
            "pinned": True,
        })

        preview = result.data["pending_action"]["preview"]
        assert "Important update" in preview
        assert "999" in preview or "deal" in preview.lower()

    def test_execute_includes_pinned_option(self):
        """Execute includes pinned option in payload."""
        tool = RequestAddDealNote()
        result = tool.parse_and_execute({
            "deal_id": 999,
            "content": "Test note",
            "pinned": True,
        })

        payload = result.data["pending_action"]["payload"]
        assert payload["pinned"] is True
