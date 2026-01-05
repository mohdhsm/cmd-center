"""Phase 3 contract tests for write operations.

These contract tests verify the interfaces and data structures for Phase 3
write operations, including:
1. PendingAction contract - structure, auto-generated timestamps, equality, serialization
2. Write Tool Result contract - all 6 write tools return proper ToolResult
3. ActionExecutor contract - execute method interface and return types
4. Confirmation Flow contract - agent confirmation interface

Contract tests ensure interfaces remain stable as implementation evolves.
"""

import pytest
from dataclasses import fields, asdict
from datetime import datetime, timezone
from typing import Optional
from unittest.mock import patch, MagicMock

from cmd_center.agent.tools.base import PendingAction, ToolResult
from cmd_center.agent.tools.write_tools import (
    RequestCreateTask,
    RequestCreateNote,
    RequestCreateReminder,
    RequestSendEmail,
    RequestUpdateDeal,
    RequestAddDealNote,
)
from cmd_center.agent.core.executor import ActionExecutor
from cmd_center.agent.core.agent import OmniousAgent


# =============================================================================
# PendingAction Contract Tests
# =============================================================================


class TestPendingActionContract:
    """Contract tests for PendingAction dataclass."""

    def test_has_tool_name_field(self):
        """PendingAction must have tool_name field."""
        field_names = [f.name for f in fields(PendingAction)]
        assert "tool_name" in field_names

    def test_has_preview_field(self):
        """PendingAction must have preview field."""
        field_names = [f.name for f in fields(PendingAction)]
        assert "preview" in field_names

    def test_has_payload_field(self):
        """PendingAction must have payload field."""
        field_names = [f.name for f in fields(PendingAction)]
        assert "payload" in field_names

    def test_has_created_at_field(self):
        """PendingAction must have created_at field."""
        field_names = [f.name for f in fields(PendingAction)]
        assert "created_at" in field_names

    def test_created_at_is_auto_generated(self):
        """created_at is auto-generated if not provided."""
        before = datetime.now(timezone.utc)
        action = PendingAction(
            tool_name="test_tool",
            preview="Test preview",
            payload={"key": "value"},
        )
        after = datetime.now(timezone.utc)

        assert action.created_at is not None
        assert isinstance(action.created_at, datetime)
        assert before <= action.created_at <= after

    def test_created_at_is_timezone_aware(self):
        """created_at has timezone information."""
        action = PendingAction(
            tool_name="test_tool",
            preview="Test preview",
            payload={},
        )

        assert action.created_at.tzinfo is not None

    def test_created_at_can_be_provided(self):
        """created_at can be explicitly provided."""
        specific_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        action = PendingAction(
            tool_name="test_tool",
            preview="Test preview",
            payload={},
            created_at=specific_time,
        )

        assert action.created_at == specific_time

    def test_equality_with_same_data(self):
        """Two PendingActions with same data are equal."""
        timestamp = datetime.now(timezone.utc)
        action1 = PendingAction(
            tool_name="request_create_task",
            preview="Create task: Test",
            payload={"title": "Test"},
            created_at=timestamp,
        )
        action2 = PendingAction(
            tool_name="request_create_task",
            preview="Create task: Test",
            payload={"title": "Test"},
            created_at=timestamp,
        )

        assert action1 == action2

    def test_inequality_with_different_tool_name(self):
        """PendingActions with different tool_name are not equal."""
        timestamp = datetime.now(timezone.utc)
        action1 = PendingAction(
            tool_name="request_create_task",
            preview="Test",
            payload={},
            created_at=timestamp,
        )
        action2 = PendingAction(
            tool_name="request_create_note",
            preview="Test",
            payload={},
            created_at=timestamp,
        )

        assert action1 != action2

    def test_can_serialize_to_dict(self):
        """PendingAction can be serialized to dict using asdict."""
        action = PendingAction(
            tool_name="request_create_task",
            preview="Create task",
            payload={"title": "Test", "priority": "high"},
        )

        result = asdict(action)

        assert isinstance(result, dict)
        assert result["tool_name"] == "request_create_task"
        assert result["preview"] == "Create task"
        assert result["payload"] == {"title": "Test", "priority": "high"}
        assert "created_at" in result

    def test_payload_is_dict(self):
        """payload field must be a dict."""
        action = PendingAction(
            tool_name="test",
            preview="test",
            payload={"key": "value", "nested": {"a": 1}},
        )

        assert isinstance(action.payload, dict)


# =============================================================================
# Write Tool Result Contract Tests
# =============================================================================


class TestWriteToolResultContract:
    """Contract tests for write tool result format."""

    # All 6 write tools
    WRITE_TOOLS = [
        (RequestCreateTask, {"title": "Test task"}),
        (RequestCreateNote, {"content": "Test note", "target_type": "deal", "target_id": 1}),
        (RequestCreateReminder, {"target_type": "deal", "target_id": 1, "remind_at": "2024-03-20T09:00:00Z", "message": "Follow up"}),
        (RequestSendEmail, {"to": "test@example.com", "subject": "Test", "body": "Test body"}),
        (RequestUpdateDeal, {"deal_id": 123, "status": "won"}),
        (RequestAddDealNote, {"deal_id": 123, "content": "Test note"}),
    ]

    @pytest.mark.parametrize("tool_class,params", WRITE_TOOLS)
    def test_write_tool_returns_tool_result(self, tool_class, params):
        """All write tools return ToolResult."""
        tool = tool_class()
        result = tool.parse_and_execute(params)

        assert isinstance(result, ToolResult)

    @pytest.mark.parametrize("tool_class,params", WRITE_TOOLS)
    def test_write_tool_returns_success_true(self, tool_class, params):
        """All write tools return success=True for valid params."""
        tool = tool_class()
        result = tool.parse_and_execute(params)

        assert result.success is True

    @pytest.mark.parametrize("tool_class,params", WRITE_TOOLS)
    def test_result_data_contains_pending_action_key(self, tool_class, params):
        """Result data contains 'pending_action' key."""
        tool = tool_class()
        result = tool.parse_and_execute(params)

        assert "pending_action" in result.data

    @pytest.mark.parametrize("tool_class,params", WRITE_TOOLS)
    def test_pending_action_has_tool_name_key(self, tool_class, params):
        """pending_action has 'tool_name' key."""
        tool = tool_class()
        result = tool.parse_and_execute(params)
        pending = result.data["pending_action"]

        assert "tool_name" in pending

    @pytest.mark.parametrize("tool_class,params", WRITE_TOOLS)
    def test_pending_action_has_preview_key(self, tool_class, params):
        """pending_action has 'preview' key."""
        tool = tool_class()
        result = tool.parse_and_execute(params)
        pending = result.data["pending_action"]

        assert "preview" in pending

    @pytest.mark.parametrize("tool_class,params", WRITE_TOOLS)
    def test_pending_action_has_payload_key(self, tool_class, params):
        """pending_action has 'payload' key."""
        tool = tool_class()
        result = tool.parse_and_execute(params)
        pending = result.data["pending_action"]

        assert "payload" in pending

    @pytest.mark.parametrize("tool_class,params", WRITE_TOOLS)
    def test_tool_name_matches_tool(self, tool_class, params):
        """tool_name in pending_action matches the tool that was called."""
        tool = tool_class()
        result = tool.parse_and_execute(params)
        pending = result.data["pending_action"]

        assert pending["tool_name"] == tool.name

    @pytest.mark.parametrize("tool_class,params", WRITE_TOOLS)
    def test_preview_is_non_empty_string(self, tool_class, params):
        """preview is a non-empty string."""
        tool = tool_class()
        result = tool.parse_and_execute(params)
        pending = result.data["pending_action"]

        assert isinstance(pending["preview"], str)
        assert len(pending["preview"]) > 0

    @pytest.mark.parametrize("tool_class,params", WRITE_TOOLS)
    def test_payload_is_dict(self, tool_class, params):
        """payload is a dict."""
        tool = tool_class()
        result = tool.parse_and_execute(params)
        pending = result.data["pending_action"]

        assert isinstance(pending["payload"], dict)

    @pytest.mark.parametrize("tool_class,params", WRITE_TOOLS)
    def test_payload_contains_input_parameters(self, tool_class, params):
        """payload contains the input parameters."""
        tool = tool_class()
        result = tool.parse_and_execute(params)
        pending = result.data["pending_action"]
        payload = pending["payload"]

        # Each param passed should appear in payload
        for key, value in params.items():
            assert key in payload
            assert payload[key] == value


# =============================================================================
# ActionExecutor Contract Tests
# =============================================================================


class TestActionExecutorContract:
    """Contract tests for ActionExecutor interface."""

    @pytest.fixture
    def executor(self):
        """Create ActionExecutor instance."""
        return ActionExecutor()

    def test_has_execute_method(self, executor):
        """ActionExecutor has execute method."""
        assert hasattr(executor, 'execute')
        assert callable(executor.execute)

    def test_execute_takes_pending_action(self, executor):
        """execute method accepts PendingAction as argument."""
        # Create a valid action (unknown tool, but should still accept it)
        action = PendingAction(
            tool_name="unknown_tool",
            preview="Unknown",
            payload={},
        )

        # Should not raise TypeError
        result = executor.execute(action)
        assert result is not None

    def test_execute_returns_dict(self, executor):
        """execute returns a dict."""
        action = PendingAction(
            tool_name="unknown_tool",
            preview="Unknown",
            payload={},
        )

        result = executor.execute(action)
        assert isinstance(result, dict)

    def test_execute_result_has_success_key(self, executor):
        """execute result has 'success' key."""
        action = PendingAction(
            tool_name="unknown_tool",
            preview="Unknown",
            payload={},
        )

        result = executor.execute(action)
        assert "success" in result

    def test_success_is_bool(self, executor):
        """success value is a boolean."""
        action = PendingAction(
            tool_name="unknown_tool",
            preview="Unknown",
            payload={},
        )

        result = executor.execute(action)
        assert isinstance(result["success"], bool)

    @patch('cmd_center.agent.core.executor.TaskService')
    @patch('cmd_center.agent.core.executor.log_action')
    def test_success_result_has_result_dict(self, mock_log, mock_task_service_class, executor):
        """On success, execute returns 'result' dict."""
        mock_service = MagicMock()
        mock_task = MagicMock()
        mock_task.id = 123
        mock_service.create_task.return_value = mock_task
        mock_task_service_class.return_value = mock_service

        action = PendingAction(
            tool_name="request_create_task",
            preview="Create task",
            payload={"title": "Test Task"},
        )

        result = executor.execute(action)

        assert result["success"] is True
        assert "result" in result
        assert isinstance(result["result"], dict)

    def test_failure_result_has_error_string(self, executor):
        """On failure, execute returns 'error' string."""
        action = PendingAction(
            tool_name="unknown_tool",
            preview="Unknown",
            payload={},
        )

        result = executor.execute(action)

        assert result["success"] is False
        assert "error" in result
        assert isinstance(result["error"], str)

    def test_unknown_tool_returns_success_false(self, executor):
        """Unknown tool returns success=False."""
        action = PendingAction(
            tool_name="nonexistent_tool",
            preview="Nonexistent",
            payload={},
        )

        result = executor.execute(action)

        assert result["success"] is False

    def test_unknown_tool_returns_error_message(self, executor):
        """Unknown tool returns descriptive error message."""
        action = PendingAction(
            tool_name="completely_unknown_tool",
            preview="Unknown action",
            payload={},
        )

        result = executor.execute(action)

        assert "error" in result
        error_lower = result["error"].lower()
        assert "unknown" in error_lower or "unsupported" in error_lower


# =============================================================================
# Confirmation Flow Contract Tests
# =============================================================================


class TestConfirmationFlowContract:
    """Contract tests for agent confirmation flow interface."""

    @pytest.fixture
    def agent(self):
        """Create agent instance with mocked config."""
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    def test_has_pending_action_attribute(self, agent):
        """Agent has pending_action attribute."""
        assert hasattr(agent, 'pending_action')

    def test_pending_action_initially_none(self, agent):
        """pending_action is initially None."""
        assert agent.pending_action is None

    def test_pending_action_can_be_set(self, agent):
        """pending_action can be set to a PendingAction."""
        action = PendingAction(
            tool_name="request_create_task",
            preview="Create task",
            payload={"title": "Test"},
        )
        agent.pending_action = action

        assert agent.pending_action is not None
        assert isinstance(agent.pending_action, PendingAction)

    def test_pending_action_can_be_cleared(self, agent):
        """pending_action can be cleared by setting to None."""
        action = PendingAction(
            tool_name="test",
            preview="test",
            payload={},
        )
        agent.pending_action = action
        agent.pending_action = None

        assert agent.pending_action is None

    def test_has_has_pending_action_method(self, agent):
        """Agent has has_pending_action method."""
        assert hasattr(agent, 'has_pending_action')
        assert callable(agent.has_pending_action)

    def test_has_pending_action_returns_bool(self, agent):
        """has_pending_action returns bool."""
        result = agent.has_pending_action()
        assert isinstance(result, bool)

    def test_has_pending_action_false_when_none(self, agent):
        """has_pending_action returns False when no pending action."""
        assert agent.has_pending_action() is False

    def test_has_pending_action_true_when_set(self, agent):
        """has_pending_action returns True when pending action exists."""
        action = PendingAction(
            tool_name="test",
            preview="test",
            payload={},
        )
        agent.pending_action = action

        assert agent.has_pending_action() is True

    def test_has_get_pending_preview_method(self, agent):
        """Agent has get_pending_preview method."""
        assert hasattr(agent, 'get_pending_preview')
        assert callable(agent.get_pending_preview)

    def test_get_pending_preview_returns_str_or_none(self, agent):
        """get_pending_preview returns str or None."""
        result = agent.get_pending_preview()
        assert result is None or isinstance(result, str)

    def test_get_pending_preview_none_when_no_action(self, agent):
        """get_pending_preview returns None when no pending action."""
        assert agent.get_pending_preview() is None

    def test_get_pending_preview_returns_preview_string(self, agent):
        """get_pending_preview returns the preview string."""
        action = PendingAction(
            tool_name="request_create_task",
            preview="CREATE TASK\n  Title: Follow up",
            payload={"title": "Follow up"},
        )
        agent.pending_action = action

        preview = agent.get_pending_preview()

        assert isinstance(preview, str)
        assert preview == "CREATE TASK\n  Title: Follow up"

    def test_has_is_confirmation_method(self, agent):
        """Agent has _is_confirmation method."""
        assert hasattr(agent, '_is_confirmation')
        assert callable(agent._is_confirmation)

    def test_is_confirmation_returns_yes_no_or_none(self, agent):
        """_is_confirmation returns 'yes', 'no', or None."""
        # Test yes
        result = agent._is_confirmation("yes")
        assert result in ("yes", "no", None)

    def test_is_confirmation_returns_yes_for_affirmative(self, agent):
        """_is_confirmation returns 'yes' for affirmative messages."""
        affirmative_messages = ["yes", "y", "confirm", "ok", "proceed"]

        for msg in affirmative_messages:
            result = agent._is_confirmation(msg)
            assert result == "yes", f"Expected 'yes' for '{msg}', got {result}"

    def test_is_confirmation_returns_no_for_negative(self, agent):
        """_is_confirmation returns 'no' for negative messages."""
        negative_messages = ["no", "n", "cancel", "stop", "abort"]

        for msg in negative_messages:
            result = agent._is_confirmation(msg)
            assert result == "no", f"Expected 'no' for '{msg}', got {result}"

    def test_is_confirmation_returns_none_for_other(self, agent):
        """_is_confirmation returns None for non-confirmation messages."""
        other_messages = [
            "What are the overdue deals?",
            "Show me tasks",
            "Hello there",
            "Create a new task",
        ]

        for msg in other_messages:
            result = agent._is_confirmation(msg)
            assert result is None, f"Expected None for '{msg}', got {result}"


# =============================================================================
# Integration Contract Tests
# =============================================================================


class TestWriteToolExecutorIntegrationContract:
    """Contract tests for write tool and executor integration."""

    @pytest.fixture
    def executor(self):
        """Create ActionExecutor instance."""
        return ActionExecutor()

    def test_write_tool_result_can_create_pending_action(self):
        """Write tool result data can be used to create PendingAction."""
        tool = RequestCreateTask()
        result = tool.parse_and_execute({"title": "Test task"})
        pending_data = result.data["pending_action"]

        # Should be able to create PendingAction from this data
        action = PendingAction(
            tool_name=pending_data["tool_name"],
            preview=pending_data["preview"],
            payload=pending_data["payload"],
        )

        assert action.tool_name == "request_create_task"
        assert action.preview != ""
        assert "title" in action.payload

    @patch('cmd_center.agent.core.executor.TaskService')
    @patch('cmd_center.agent.core.executor.log_action')
    def test_pending_action_from_tool_can_be_executed(self, mock_log, mock_task_service_class, executor):
        """PendingAction created from tool result can be executed."""
        # Setup mock
        mock_service = MagicMock()
        mock_task = MagicMock()
        mock_task.id = 999
        mock_service.create_task.return_value = mock_task
        mock_task_service_class.return_value = mock_service

        # Create from tool
        tool = RequestCreateTask()
        result = tool.parse_and_execute({"title": "Test task", "priority": "high"})
        pending_data = result.data["pending_action"]

        action = PendingAction(
            tool_name=pending_data["tool_name"],
            preview=pending_data["preview"],
            payload=pending_data["payload"],
        )

        # Execute
        exec_result = executor.execute(action)

        assert exec_result["success"] is True
        assert "result" in exec_result

    def test_all_write_tools_produce_executable_pending_actions(self, executor):
        """All 6 write tools produce PendingActions that can be passed to executor."""
        tools_and_params = [
            (RequestCreateTask, {"title": "Test"}),
            (RequestCreateNote, {"content": "Note", "target_type": "deal", "target_id": 1}),
            (RequestCreateReminder, {"target_type": "deal", "target_id": 1, "remind_at": "2024-03-20T09:00:00Z", "message": "Remind"}),
            (RequestSendEmail, {"to": "test@test.com", "subject": "Test", "body": "Body"}),
            (RequestUpdateDeal, {"deal_id": 1}),
            (RequestAddDealNote, {"deal_id": 1, "content": "Note"}),
        ]

        for tool_class, params in tools_and_params:
            tool = tool_class()
            result = tool.parse_and_execute(params)

            # Create PendingAction from result
            pending_data = result.data["pending_action"]
            action = PendingAction(
                tool_name=pending_data["tool_name"],
                preview=pending_data["preview"],
                payload=pending_data["payload"],
            )

            # Verify executor accepts it (it may fail due to mocked services,
            # but it should not raise TypeError)
            exec_result = executor.execute(action)

            assert isinstance(exec_result, dict)
            assert "success" in exec_result
