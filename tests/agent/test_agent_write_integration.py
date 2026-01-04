"""Tests for agent write tool integration."""

import pytest
from unittest.mock import patch, MagicMock

from cmd_center.agent.core.agent import OmniousAgent


class TestWriteToolRegistration:
    """Tests for write tool registration."""

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

    def test_write_tools_registered(self, agent):
        """Write tools are registered."""
        tools = agent.tools.list_tools()
        tool_names = [t["name"] for t in tools]

        expected_write_tools = [
            "request_create_task",
            "request_create_note",
            "request_create_reminder",
            "request_send_email",
            "request_update_deal",
            "request_add_deal_note",
        ]

        for tool in expected_write_tools:
            assert tool in tool_names, f"Missing write tool: {tool}"

    def test_total_tool_count(self, agent):
        """Total tool count is correct (19 read + 6 write = 25)."""
        tools = agent.tools.list_tools()
        assert len(tools) == 25, f"Expected 25 tools, got {len(tools)}"

    def test_agent_has_executor(self, agent):
        """Agent has executor instance."""
        assert hasattr(agent, 'executor')
        assert agent.executor is not None
