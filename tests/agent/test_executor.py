"""Tests for ActionExecutor service."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from cmd_center.agent.tools.base import PendingAction


class TestActionExecutorHasExecuteMethod:
    """Tests that ActionExecutor has execute method."""

    def test_executor_has_execute_method(self):
        """ActionExecutor has execute method."""
        from cmd_center.agent.core.executor import ActionExecutor

        executor = ActionExecutor()
        assert hasattr(executor, 'execute')
        assert callable(executor.execute)

    def test_executor_default_actor(self):
        """ActionExecutor uses default actor 'omnious'."""
        from cmd_center.agent.core.executor import ActionExecutor

        executor = ActionExecutor()
        assert executor.actor == "omnious"

    def test_executor_custom_actor(self):
        """ActionExecutor can be initialized with custom actor."""
        from cmd_center.agent.core.executor import ActionExecutor

        executor = ActionExecutor(actor="test_user")
        assert executor.actor == "test_user"


class TestExecuteCreateTask:
    """Tests for executing create task action."""

    @pytest.fixture
    def executor(self):
        """Create ActionExecutor instance."""
        from cmd_center.agent.core.executor import ActionExecutor
        return ActionExecutor()

    @pytest.fixture
    def task_action(self):
        """Create a pending action for task creation."""
        return PendingAction(
            tool_name="request_create_task",
            preview="CREATE TASK\n  Title: Follow up with client",
            payload={
                "title": "Follow up with client",
                "description": "Call about the proposal",
                "priority": "high",
            },
        )

    @patch('cmd_center.agent.core.executor.TaskService')
    @patch('cmd_center.agent.core.executor.log_action')
    def test_execute_create_task(self, mock_log, mock_task_service_class, executor, task_action):
        """Execute dispatches to TaskService for create_task."""
        # Setup mock
        mock_service = MagicMock()
        mock_task = MagicMock()
        mock_task.id = 123
        mock_service.create_task.return_value = mock_task
        mock_task_service_class.return_value = mock_service

        result = executor.execute(task_action)

        assert result["success"] is True
        mock_service.create_task.assert_called_once()

    @patch('cmd_center.agent.core.executor.TaskService')
    @patch('cmd_center.agent.core.executor.log_action')
    def test_execute_create_task_passes_params(self, mock_log, mock_task_service_class, executor, task_action):
        """Execute passes correct params to TaskService."""
        mock_service = MagicMock()
        mock_task = MagicMock()
        mock_task.id = 123
        mock_service.create_task.return_value = mock_task
        mock_task_service_class.return_value = mock_service

        executor.execute(task_action)

        call_args = mock_service.create_task.call_args
        task_data = call_args[0][0]  # First positional arg
        assert task_data.title == "Follow up with client"
        assert task_data.description == "Call about the proposal"
        assert task_data.priority == "high"


class TestExecuteLogsIntervention:
    """Tests that execute logs intervention after successful execution."""

    @pytest.fixture
    def executor(self):
        """Create ActionExecutor instance."""
        from cmd_center.agent.core.executor import ActionExecutor
        return ActionExecutor()

    @pytest.fixture
    def task_action(self):
        """Create a pending action for task creation."""
        return PendingAction(
            tool_name="request_create_task",
            preview="CREATE TASK\n  Title: Test task",
            payload={"title": "Test task"},
        )

    @patch('cmd_center.agent.core.executor.TaskService')
    @patch('cmd_center.agent.core.executor.log_action')
    def test_execute_logs_intervention(self, mock_log, mock_task_service_class, executor, task_action):
        """Execute logs intervention after successful task creation."""
        mock_service = MagicMock()
        mock_task = MagicMock()
        mock_task.id = 456
        mock_service.create_task.return_value = mock_task
        mock_task_service_class.return_value = mock_service

        executor.execute(task_action)

        # Verify log_action was called
        mock_log.assert_called_once()
        call_kwargs = mock_log.call_args[1]
        assert call_kwargs["actor"] == "omnious"
        assert "task" in call_kwargs["object_type"].lower()

    @patch('cmd_center.agent.core.executor.TaskService')
    @patch('cmd_center.agent.core.executor.log_action')
    def test_execute_uses_custom_actor(self, mock_log, mock_task_service_class, task_action):
        """Execute uses custom actor for logging."""
        from cmd_center.agent.core.executor import ActionExecutor

        executor = ActionExecutor(actor="custom_actor")

        mock_service = MagicMock()
        mock_task = MagicMock()
        mock_task.id = 789
        mock_service.create_task.return_value = mock_task
        mock_task_service_class.return_value = mock_service

        executor.execute(task_action)

        call_kwargs = mock_log.call_args[1]
        assert call_kwargs["actor"] == "custom_actor"


class TestExecuteUnknownToolFails:
    """Tests that execute fails for unknown tools."""

    @pytest.fixture
    def executor(self):
        """Create ActionExecutor instance."""
        from cmd_center.agent.core.executor import ActionExecutor
        return ActionExecutor()

    def test_execute_unknown_tool_fails(self, executor):
        """Execute returns error for unknown tool."""
        action = PendingAction(
            tool_name="unknown_tool",
            preview="Unknown action",
            payload={},
        )

        result = executor.execute(action)

        assert result["success"] is False
        assert "error" in result
        assert "unknown" in result["error"].lower() or "unsupported" in result["error"].lower()


class TestExecuteNoteCreation:
    """Tests for executing create note action."""

    @pytest.fixture
    def executor(self):
        """Create ActionExecutor instance."""
        from cmd_center.agent.core.executor import ActionExecutor
        return ActionExecutor()

    @pytest.fixture
    def note_action(self):
        """Create a pending action for note creation."""
        return PendingAction(
            tool_name="request_create_note",
            preview="CREATE NOTE",
            payload={
                "content": "Important meeting notes",
                "target_type": "deal",
                "target_id": 123,
            },
        )

    @patch('cmd_center.agent.core.executor.NoteService')
    @patch('cmd_center.agent.core.executor.log_action')
    def test_execute_create_note(self, mock_log, mock_note_service_class, executor, note_action):
        """Execute dispatches to NoteService for create_note."""
        mock_service = MagicMock()
        mock_note = MagicMock()
        mock_note.id = 456
        mock_service.create_note.return_value = mock_note
        mock_note_service_class.return_value = mock_service

        result = executor.execute(note_action)

        assert result["success"] is True
        mock_service.create_note.assert_called_once()


class TestExecuteReminderCreation:
    """Tests for executing create reminder action."""

    @pytest.fixture
    def executor(self):
        """Create ActionExecutor instance."""
        from cmd_center.agent.core.executor import ActionExecutor
        return ActionExecutor()

    @pytest.fixture
    def reminder_action(self):
        """Create a pending action for reminder creation."""
        return PendingAction(
            tool_name="request_create_reminder",
            preview="CREATE REMINDER",
            payload={
                "target_type": "deal",
                "target_id": 123,
                "remind_at": "2024-03-20T09:00:00Z",
                "message": "Follow up",
            },
        )

    @patch('cmd_center.agent.core.executor.ReminderService')
    @patch('cmd_center.agent.core.executor.log_action')
    def test_execute_create_reminder(self, mock_log, mock_reminder_service_class, executor, reminder_action):
        """Execute dispatches to ReminderService for create_reminder."""
        mock_service = MagicMock()
        mock_reminder = MagicMock()
        mock_reminder.id = 789
        mock_service.create_reminder.return_value = mock_reminder
        mock_reminder_service_class.return_value = mock_service

        result = executor.execute(reminder_action)

        assert result["success"] is True
        mock_service.create_reminder.assert_called_once()


class TestExecuteSendEmail:
    """Tests for executing send email action."""

    @pytest.fixture
    def executor(self):
        """Create ActionExecutor instance."""
        from cmd_center.agent.core.executor import ActionExecutor
        return ActionExecutor()

    @pytest.fixture
    def email_action(self):
        """Create a pending action for sending email."""
        return PendingAction(
            tool_name="request_send_email",
            preview="SEND EMAIL",
            payload={
                "to": "client@example.com",
                "subject": "Follow up",
                "body": "Hello, following up on our meeting...",
            },
        )

    @patch('cmd_center.agent.core.executor.get_msgraph_email_service')
    @patch('cmd_center.agent.core.executor.log_action')
    def test_execute_send_email(self, mock_log, mock_get_email_service, executor, email_action):
        """Execute dispatches to email service for send_email."""
        mock_service = MagicMock()
        mock_service.send_email = AsyncMock(return_value=True)
        mock_get_email_service.return_value = mock_service

        result = executor.execute(email_action)

        assert result["success"] is True
        mock_service.send_email.assert_called_once()


class TestExecuteUpdateDeal:
    """Tests for executing update deal action."""

    @pytest.fixture
    def executor(self):
        """Create ActionExecutor instance."""
        from cmd_center.agent.core.executor import ActionExecutor
        return ActionExecutor()

    @pytest.fixture
    def update_deal_action(self):
        """Create a pending action for updating deal."""
        return PendingAction(
            tool_name="request_update_deal",
            preview="UPDATE DEAL",
            payload={
                "deal_id": 123,
                "status": "won",
                "value": 50000,
            },
        )

    @patch('cmd_center.agent.core.executor.get_pipedrive_client')
    @patch('cmd_center.agent.core.executor.log_action')
    def test_execute_update_deal(self, mock_log, mock_get_pipedrive_client, executor, update_deal_action):
        """Execute dispatches to Pipedrive client for update_deal."""
        mock_client = MagicMock()
        mock_client.update_deal = AsyncMock(return_value={"id": 123})
        mock_get_pipedrive_client.return_value = mock_client

        result = executor.execute(update_deal_action)

        assert result["success"] is True
        mock_client.update_deal.assert_called_once()


class TestExecuteAddDealNote:
    """Tests for executing add deal note action."""

    @pytest.fixture
    def executor(self):
        """Create ActionExecutor instance."""
        from cmd_center.agent.core.executor import ActionExecutor
        return ActionExecutor()

    @pytest.fixture
    def add_deal_note_action(self):
        """Create a pending action for adding deal note."""
        return PendingAction(
            tool_name="request_add_deal_note",
            preview="ADD DEAL NOTE",
            payload={
                "deal_id": 123,
                "content": "Client agreed to terms",
            },
        )

    @patch('cmd_center.agent.core.executor.get_pipedrive_client')
    @patch('cmd_center.agent.core.executor.log_action')
    def test_execute_add_deal_note(self, mock_log, mock_get_pipedrive_client, executor, add_deal_note_action):
        """Execute dispatches to Pipedrive client for add_deal_note."""
        mock_client = MagicMock()
        mock_client.add_deal_note = AsyncMock(return_value={"id": 456})
        mock_get_pipedrive_client.return_value = mock_client

        result = executor.execute(add_deal_note_action)

        assert result["success"] is True
        mock_client.add_deal_note.assert_called_once()
