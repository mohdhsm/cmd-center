"""Tests for task tools."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from cmd_center.agent.tools.task_tools import (
    GetTasks, GetTasksParams,
    GetOverdueTasks, GetOverdueTasksParams,
    GetPendingReminders, GetPendingRemindersParams,
    GetNotes, GetNotesParams,
)
from cmd_center.agent.tools.base import ToolResult


class TestGetTasks:
    """Tests for GetTasks tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = GetTasks()
        assert tool.name == "get_tasks"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = GetTasks()
        assert len(tool.description) > 20

    def test_params_have_defaults(self):
        """Parameters have sensible defaults."""
        params = GetTasksParams()
        assert params.limit == 20
        assert params.status is None
        assert params.assignee_id is None
        assert params.is_critical is None

    def test_schema_has_status_param(self):
        """Schema includes status parameter."""
        tool = GetTasks()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "status" in props

    def test_schema_has_limit_param(self):
        """Schema includes limit parameter."""
        tool = GetTasks()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "limit" in props

    @patch("cmd_center.agent.tools.task_tools.get_task_service")
    def test_execute_returns_tasks(self, mock_get_service):
        """Execute returns tasks from service."""
        mock_service = Mock()
        mock_service.get_tasks.return_value = Mock(
            items=[
                Mock(id=1, title="Task 1", status="open", priority="high", is_critical=False, due_at=None, assignee_employee_id=1),
                Mock(id=2, title="Task 2", status="done", priority="low", is_critical=False, due_at=None, assignee_employee_id=2),
            ],
            total=2,
        )
        mock_get_service.return_value = mock_service

        tool = GetTasks()
        result = tool.parse_and_execute({})

        assert result.success is True
        assert "tasks" in result.data
        assert len(result.data["tasks"]) == 2
        assert result.data["count"] == 2

    @patch("cmd_center.agent.tools.task_tools.get_task_service")
    def test_execute_with_status_filter(self, mock_get_service):
        """Execute filters by status."""
        mock_service = Mock()
        mock_service.get_tasks.return_value = Mock(items=[], total=0)
        mock_get_service.return_value = mock_service

        tool = GetTasks()
        result = tool.parse_and_execute({"status": "open"})

        assert result.success is True
        mock_service.get_tasks.assert_called_once()

    @patch("cmd_center.agent.tools.task_tools.get_task_service")
    def test_execute_handles_service_error(self, mock_get_service):
        """Execute handles service errors gracefully."""
        mock_service = Mock()
        mock_service.get_tasks.side_effect = Exception("Service unavailable")
        mock_get_service.return_value = mock_service

        tool = GetTasks()
        result = tool.parse_and_execute({})

        assert result.success is False
        assert "Service unavailable" in result.error


class TestGetOverdueTasks:
    """Tests for GetOverdueTasks tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = GetOverdueTasks()
        assert tool.name == "get_overdue_tasks"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = GetOverdueTasks()
        assert len(tool.description) > 20

    def test_params_have_defaults(self):
        """Parameters have sensible defaults."""
        params = GetOverdueTasksParams()
        assert params.limit == 20

    def test_schema_has_limit_param(self):
        """Schema includes limit parameter."""
        tool = GetOverdueTasks()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "limit" in props

    @patch("cmd_center.agent.tools.task_tools.get_task_service")
    def test_execute_returns_overdue_tasks(self, mock_get_service):
        """Execute returns overdue tasks."""
        mock_service = Mock()
        mock_service.get_overdue_tasks.return_value = [
            Mock(id=1, title="Overdue Task", status="open", priority="high", is_critical=True, due_at=None, assignee_employee_id=1),
        ]
        mock_get_service.return_value = mock_service

        tool = GetOverdueTasks()
        result = tool.parse_and_execute({})

        assert result.success is True
        assert "tasks" in result.data
        assert len(result.data["tasks"]) == 1

    @patch("cmd_center.agent.tools.task_tools.get_task_service")
    def test_execute_handles_service_error(self, mock_get_service):
        """Execute handles service errors gracefully."""
        mock_service = Mock()
        mock_service.get_overdue_tasks.side_effect = Exception("Database error")
        mock_get_service.return_value = mock_service

        tool = GetOverdueTasks()
        result = tool.parse_and_execute({})

        assert result.success is False
        assert "Database error" in result.error


class TestGetPendingReminders:
    """Tests for GetPendingReminders tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = GetPendingReminders()
        assert tool.name == "get_pending_reminders"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = GetPendingReminders()
        assert len(tool.description) > 20

    def test_params_have_defaults(self):
        """Parameters have sensible defaults."""
        params = GetPendingRemindersParams()
        assert params.limit == 20

    def test_schema_has_limit_param(self):
        """Schema includes limit parameter."""
        tool = GetPendingReminders()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "limit" in props

    @patch("cmd_center.agent.tools.task_tools.get_reminder_service")
    def test_execute_returns_pending_reminders(self, mock_get_service):
        """Execute returns pending reminders from service."""
        # Create mock reminder objects matching ReminderResponse structure
        mock_reminder1 = Mock()
        mock_reminder1.id = 1
        mock_reminder1.target_type = "task"
        mock_reminder1.target_id = 100
        mock_reminder1.remind_at = datetime(2026, 1, 5, 10, 0, tzinfo=timezone.utc)
        mock_reminder1.channel = "email"
        mock_reminder1.message = "Follow up on task"
        mock_reminder1.status = "pending"

        mock_reminder2 = Mock()
        mock_reminder2.id = 2
        mock_reminder2.target_type = "deal"
        mock_reminder2.target_id = 200
        mock_reminder2.remind_at = datetime(2026, 1, 6, 14, 30, tzinfo=timezone.utc)
        mock_reminder2.channel = "in_app"
        mock_reminder2.message = "Check deal status"
        mock_reminder2.status = "pending"

        mock_service = Mock()
        mock_service.get_pending_reminders.return_value = [mock_reminder1, mock_reminder2]
        mock_get_service.return_value = mock_service

        tool = GetPendingReminders()
        result = tool.parse_and_execute({})

        assert result.success is True
        assert "reminders" in result.data
        assert len(result.data["reminders"]) == 2
        assert result.data["count"] == 2
        assert result.data["reminders"][0]["id"] == 1
        assert result.data["reminders"][0]["target_type"] == "task"
        assert result.data["reminders"][0]["target_id"] == 100

    @patch("cmd_center.agent.tools.task_tools.get_reminder_service")
    def test_execute_with_custom_limit(self, mock_get_service):
        """Execute respects limit parameter."""
        mock_service = Mock()
        mock_service.get_pending_reminders.return_value = []
        mock_get_service.return_value = mock_service

        tool = GetPendingReminders()
        result = tool.parse_and_execute({"limit": 50})

        assert result.success is True
        # Verify service was called with limit parameter
        mock_service.get_pending_reminders.assert_called_once()
        call_kwargs = mock_service.get_pending_reminders.call_args.kwargs
        assert call_kwargs.get("limit") == 50

    @patch("cmd_center.agent.tools.task_tools.get_reminder_service")
    def test_execute_handles_service_error(self, mock_get_service):
        """Execute handles service errors gracefully."""
        mock_service = Mock()
        mock_service.get_pending_reminders.side_effect = Exception("Database connection error")
        mock_get_service.return_value = mock_service

        tool = GetPendingReminders()
        result = tool.parse_and_execute({})

        assert result.success is False
        assert "Database connection error" in result.error

    @patch("cmd_center.agent.tools.task_tools.get_reminder_service")
    def test_execute_returns_empty_list_when_no_reminders(self, mock_get_service):
        """Execute returns empty list when no pending reminders."""
        mock_service = Mock()
        mock_service.get_pending_reminders.return_value = []
        mock_get_service.return_value = mock_service

        tool = GetPendingReminders()
        result = tool.parse_and_execute({})

        assert result.success is True
        assert result.data["reminders"] == []
        assert result.data["count"] == 0


class TestGetNotes:
    """Tests for GetNotes tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = GetNotes()
        assert tool.name == "get_notes"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = GetNotes()
        assert len(tool.description) > 20

    def test_params_have_defaults(self):
        """Parameters have sensible defaults."""
        params = GetNotesParams()
        assert params.page_size == 20
        assert params.target_type is None
        assert params.target_id is None
        assert params.pinned is None
        assert params.search is None

    def test_schema_has_target_type_param(self):
        """Schema includes target_type parameter."""
        tool = GetNotes()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "target_type" in props

    def test_schema_has_page_size_param(self):
        """Schema includes page_size parameter."""
        tool = GetNotes()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "page_size" in props

    @patch("cmd_center.agent.tools.task_tools.get_note_service")
    def test_execute_returns_notes(self, mock_get_service):
        """Execute returns notes from service."""
        mock_note1 = Mock()
        mock_note1.id = 1
        mock_note1.content = "This is a test note"
        mock_note1.created_by = "john"
        mock_note1.target_type = "deal"
        mock_note1.target_id = 100
        mock_note1.review_at = None
        mock_note1.pinned = False
        mock_note1.tags = "important"
        mock_note1.is_archived = False
        mock_note1.created_at = datetime(2026, 1, 3, 10, 0, tzinfo=timezone.utc)
        mock_note1.updated_at = None

        mock_note2 = Mock()
        mock_note2.id = 2
        mock_note2.content = "Another note"
        mock_note2.created_by = "jane"
        mock_note2.target_type = "deal"
        mock_note2.target_id = 200
        mock_note2.review_at = None
        mock_note2.pinned = True
        mock_note2.tags = None
        mock_note2.is_archived = False
        mock_note2.created_at = datetime(2026, 1, 2, 14, 30, tzinfo=timezone.utc)
        mock_note2.updated_at = None

        mock_service = Mock()
        mock_service.get_notes.return_value = Mock(
            items=[mock_note1, mock_note2],
            total=2,
            page=1,
            page_size=20,
        )
        mock_get_service.return_value = mock_service

        tool = GetNotes()
        result = tool.parse_and_execute({})

        assert result.success is True
        assert "notes" in result.data
        assert len(result.data["notes"]) == 2
        assert result.data["count"] == 2
        assert result.data["notes"][0]["id"] == 1
        assert result.data["notes"][0]["content"] == "This is a test note"
        assert result.data["notes"][0]["created_by"] == "john"

    @patch("cmd_center.agent.tools.task_tools.get_note_service")
    def test_execute_with_target_filter(self, mock_get_service):
        """Execute filters by target type and ID."""
        mock_service = Mock()
        mock_service.get_notes.return_value = Mock(items=[], total=0, page=1, page_size=20)
        mock_get_service.return_value = mock_service

        tool = GetNotes()
        result = tool.parse_and_execute({"target_type": "deal", "target_id": 100})

        assert result.success is True
        mock_service.get_notes.assert_called_once()

    @patch("cmd_center.agent.tools.task_tools.get_note_service")
    def test_execute_handles_service_error(self, mock_get_service):
        """Execute handles service errors gracefully."""
        mock_service = Mock()
        mock_service.get_notes.side_effect = Exception("Database error")
        mock_get_service.return_value = mock_service

        tool = GetNotes()
        result = tool.parse_and_execute({})

        assert result.success is False
        assert "Database error" in result.error

    @patch("cmd_center.agent.tools.task_tools.get_note_service")
    def test_execute_returns_empty_list_when_no_notes(self, mock_get_service):
        """Execute returns empty list when no notes found."""
        mock_service = Mock()
        mock_service.get_notes.return_value = Mock(items=[], total=0, page=1, page_size=20)
        mock_get_service.return_value = mock_service

        tool = GetNotes()
        result = tool.parse_and_execute({})

        assert result.success is True
        assert result.data["notes"] == []
        assert result.data["count"] == 0

    @patch("cmd_center.agent.tools.task_tools.get_note_service")
    def test_execute_truncates_long_content(self, mock_get_service):
        """Execute truncates content longer than 500 characters."""
        long_content = "A" * 1000
        mock_note = Mock()
        mock_note.id = 1
        mock_note.content = long_content
        mock_note.created_by = "john"
        mock_note.target_type = None
        mock_note.target_id = None
        mock_note.review_at = None
        mock_note.pinned = False
        mock_note.tags = None
        mock_note.is_archived = False
        mock_note.created_at = datetime(2026, 1, 3, 10, 0, tzinfo=timezone.utc)
        mock_note.updated_at = None

        mock_service = Mock()
        mock_service.get_notes.return_value = Mock(items=[mock_note], total=1, page=1, page_size=20)
        mock_get_service.return_value = mock_service

        tool = GetNotes()
        result = tool.parse_and_execute({})

        assert result.success is True
        assert len(result.data["notes"][0]["content"]) == 500
