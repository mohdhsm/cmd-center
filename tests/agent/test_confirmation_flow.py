"""Tests for agent confirmation flow."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from cmd_center.agent.core.agent import OmniousAgent
from cmd_center.agent.tools.base import PendingAction


class TestConfirmationFlow:
    """Tests for pending action confirmation flow."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    def test_agent_has_pending_action_attribute(self, agent):
        """Agent has pending_action attribute."""
        assert hasattr(agent, 'pending_action')
        assert agent.pending_action is None

    def test_set_pending_action(self, agent):
        """Can set a pending action."""
        action = PendingAction(
            tool_name="request_create_task",
            preview="Create task: Test",
            payload={"title": "Test"},
        )
        agent.pending_action = action

        assert agent.pending_action is not None
        assert agent.pending_action.tool_name == "request_create_task"

    def test_clear_pending_action(self, agent):
        """Can clear pending action."""
        action = PendingAction(
            tool_name="test",
            preview="test",
            payload={},
        )
        agent.pending_action = action
        agent.pending_action = None

        assert agent.pending_action is None

    def test_has_pending_action_method(self, agent):
        """has_pending_action returns correct status."""
        assert agent.has_pending_action() is False

        action = PendingAction(
            tool_name="test",
            preview="test",
            payload={},
        )
        agent.pending_action = action

        assert agent.has_pending_action() is True

    def test_get_pending_preview(self, agent):
        """get_pending_preview returns formatted preview."""
        assert agent.get_pending_preview() is None

        action = PendingAction(
            tool_name="request_create_task",
            preview="Create task: Follow up with client\nPriority: high",
            payload={"title": "Follow up"},
        )
        agent.pending_action = action

        preview = agent.get_pending_preview()
        assert "Create task" in preview
        assert "Follow up" in preview


class TestConfirmationDetection:
    """Tests for detecting user confirmation."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    def test_is_confirmation_yes(self, agent):
        """Detects affirmative confirmations."""
        yes_messages = ["yes", "Yes", "YES", "y", "Y", "confirm", "ok", "proceed", "do it", "go ahead"]

        for msg in yes_messages:
            assert agent._is_confirmation(msg) == "yes", f"Failed for: {msg}"

    def test_is_confirmation_no(self, agent):
        """Detects negative confirmations."""
        no_messages = ["no", "No", "NO", "n", "N", "cancel", "stop", "abort", "never mind"]

        for msg in no_messages:
            assert agent._is_confirmation(msg) == "no", f"Failed for: {msg}"

    def test_is_confirmation_none(self, agent):
        """Returns None for non-confirmation messages."""
        other_messages = [
            "What deals need attention?",
            "Show me overdue tasks",
            "Hello",
        ]

        for msg in other_messages:
            assert agent._is_confirmation(msg) is None, f"Failed for: {msg}"
