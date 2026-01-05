"""Tests for agent file logging integration."""

import pytest
from unittest.mock import patch, MagicMock

from cmd_center.agent.core.agent import OmniousAgent


class TestAgentLoggingIntegration:
    """Tests for agent file logging."""

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

    def test_agent_has_file_logger(self, agent):
        """Agent has file logger attribute."""
        assert hasattr(agent, 'file_logger')
        assert agent.file_logger is not None

    def test_add_to_history_logs_to_file(self, agent):
        """Adding to history logs to file logger."""
        with patch.object(agent.file_logger, 'log_message') as mock_log:
            agent._add_to_history("user", "Hello")

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args.kwargs["role"] == "user"
            assert call_args.kwargs["content"] == "Hello"

    def test_log_includes_conversation_id(self, agent):
        """Log includes conversation ID when persistence is enabled."""
        agent.conversation_id = 42

        with patch.object(agent.file_logger, 'log_message') as mock_log:
            agent._add_to_history("assistant", "Hi there")

            call_args = mock_log.call_args
            assert call_args.kwargs["conversation_id"] == 42

    def test_log_includes_tools_used(self, agent):
        """Log includes tools used when provided."""
        with patch.object(agent.file_logger, 'log_message') as mock_log:
            agent._add_to_history(
                "assistant",
                "Here are the deals",
                tools_used=["get_overdue_deals"]
            )

            call_args = mock_log.call_args
            assert call_args.kwargs["tools_used"] == ["get_overdue_deals"]
