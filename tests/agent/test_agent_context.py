"""Tests for agent context management integration."""

import pytest
from unittest.mock import patch, MagicMock

from cmd_center.agent.core.agent import OmniousAgent


class TestAgentContextIntegration:
    """Tests for agent context management."""

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

    def test_agent_has_context_manager(self, agent):
        """Agent has context manager attribute."""
        assert hasattr(agent, 'context_manager')
        assert agent.context_manager is not None

    def test_add_to_history_tracks_context(self, agent):
        """Adding to history tracks context tokens."""
        agent._add_to_history("user", "Hello world")
        assert agent.context_manager.total_tokens > 0

    def test_clear_conversation_clears_context(self, agent):
        """Clearing conversation clears context."""
        agent._add_to_history("user", "Hello")
        agent.clear_conversation()
        assert agent.context_manager.total_tokens == 0

    def test_get_context_warning(self, agent):
        """Agent can get context warning."""
        assert agent.get_context_warning() is None

    def test_get_context_usage(self, agent):
        """Agent can get context usage summary."""
        agent._add_to_history("user", "Hello")
        usage = agent.get_context_usage()
        assert "token" in usage.lower() or "/" in usage
