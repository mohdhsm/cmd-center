"""Integration tests for Phase 3 write operations."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from cmd_center.agent.core.agent import OmniousAgent
from cmd_center.agent.tools.base import PendingAction


class TestPhase3Integration:
    """End-to-end tests for Phase 3 features."""

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

    def test_write_tool_returns_pending_action(self, agent):
        """Write tool execution returns PendingAction."""
        result = agent.tools.execute("request_create_task", {
            "title": "Test task",
            "priority": "high",
        })

        assert result.success
        assert "pending_action" in result.data
        assert result.data["pending_action"]["tool_name"] == "request_create_task"

    def test_confirmation_flow_state_machine(self, agent):
        """Confirmation flow works correctly."""
        # Initially no pending action
        assert not agent.has_pending_action()

        # Set pending action
        agent.pending_action = PendingAction(
            tool_name="request_create_task",
            preview="Create task",
            payload={"title": "Test"},
        )
        assert agent.has_pending_action()
        assert agent.get_pending_preview() == "Create task"

        # Clear on cancel
        agent.pending_action = None
        assert not agent.has_pending_action()

    def test_all_write_tools_exist(self, agent):
        """All 6 write tools are available."""
        write_tools = [
            "request_create_task",
            "request_create_note",
            "request_create_reminder",
            "request_send_email",
            "request_update_deal",
            "request_add_deal_note",
        ]

        for tool in write_tools:
            result = agent.tools.execute(tool, _get_minimal_params(tool))
            assert result.success, f"Tool {tool} failed"
            assert "pending_action" in result.data


def _get_minimal_params(tool_name: str) -> dict:
    """Get minimal valid params for each tool."""
    params = {
        "request_create_task": {"title": "Test"},
        "request_create_note": {
            "content": "Test note",
            "target_type": "deal",
            "target_id": 1,
        },
        "request_create_reminder": {
            "target_type": "deal",
            "target_id": 1,
            "remind_at": "2026-01-15T10:00:00",
            "message": "Test reminder",
        },
        "request_send_email": {
            "to": "test@example.com",
            "subject": "Test",
            "body": "Test body",
        },
        "request_update_deal": {"deal_id": 123, "status": "won"},
        "request_add_deal_note": {"deal_id": 123, "content": "Test note"},
    }
    return params[tool_name]
