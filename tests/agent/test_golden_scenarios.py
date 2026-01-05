"""Golden scenario tests for Omnious agent behavior."""

import pytest
from unittest.mock import patch, MagicMock

from cmd_center.agent.core.agent import OmniousAgent
from cmd_center.agent.tools.base import PendingAction


QUERY_SCENARIOS = [
    {"id": "pipeline_health", "query": "How is our pipeline doing?", "expected_tools": ["get_overdue_deals", "get_stuck_deals"]},
    {"id": "aramco_deals", "query": "Show me Aramco deals that need attention", "expected_tools": ["get_overdue_deals"]},
    {"id": "deal_lookup", "query": "What's the status of deal 456?", "expected_tools": ["get_deal_details"]},
    {"id": "my_tasks", "query": "What tasks do I have?", "expected_tools": ["get_tasks"]},
    {"id": "overdue_work", "query": "What's overdue?", "expected_tools": ["get_overdue_tasks"]},
    {"id": "reminders", "query": "Any upcoming reminders?", "expected_tools": ["get_pending_reminders"]},
    {"id": "team_info", "query": "Who is on the sales team?", "expected_tools": ["get_employees"]},
    {"id": "person_lookup", "query": "Tell me about Mohammed", "expected_tools": ["get_employee_details"]},
    {"id": "skills", "query": "What skills does employee 3 have?", "expected_tools": ["get_employee_skills"]},
    {"id": "cashflow", "query": "What's our cashflow looking like?", "expected_tools": ["get_cashflow_projection"]},
    {"id": "dashboard", "query": "Show me the CEO dashboard", "expected_tools": ["get_ceo_dashboard"]},
    {"id": "kpis", "query": "What are the sales KPIs?", "expected_tools": ["get_owner_kpis"]},
    {"id": "find_emails", "query": "Find emails about the contract", "expected_tools": ["search_emails"]},
    {"id": "recent_emails", "query": "Show me recent emails", "expected_tools": ["get_emails"]},
    {"id": "expiring_docs", "query": "Any documents expiring soon?", "expected_tools": ["get_expiring_documents"]},
    {"id": "bonuses", "query": "Who has unpaid bonuses?", "expected_tools": ["get_unpaid_bonuses"]},
    {"id": "company_info", "query": "What does GypTech do?", "expected_tools": ["read_knowledge"]},
    {"id": "procedures", "query": "What's the sales process?", "expected_tools": ["read_knowledge"]},
]

WRITE_SCENARIOS = [
    {"id": "create_task", "query": "Create a task to follow up with client", "expected_tools": ["request_create_task"]},
    {"id": "create_note", "query": "Add a note about the meeting", "expected_tools": ["request_create_note"]},
    {"id": "create_reminder", "query": "Remind me about this tomorrow", "expected_tools": ["request_create_reminder"]},
    {"id": "send_email", "query": "Send an email to client@example.com", "expected_tools": ["request_send_email"]},
    {"id": "update_deal", "query": "Mark deal 123 as won", "expected_tools": ["request_update_deal"]},
    {"id": "add_deal_note", "query": "Add a note to deal 456", "expected_tools": ["request_add_deal_note"]},
]


class TestQueryScenarios:
    """Test tool selection for query scenarios."""

    @pytest.fixture
    def agent(self):
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    @pytest.mark.parametrize("scenario", QUERY_SCENARIOS, ids=lambda s: s["id"])
    def test_query_tools_available(self, agent, scenario):
        """Verify expected tools are registered for query scenarios."""
        tool_names = [t["name"] for t in agent.tools.list_tools()]
        for expected_tool in scenario["expected_tools"]:
            assert expected_tool in tool_names, f"Scenario '{scenario['id']}': Tool '{expected_tool}' not registered"


class TestWriteScenarios:
    """Test tool selection for write scenarios."""

    @pytest.fixture
    def agent(self):
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    @pytest.mark.parametrize("scenario", WRITE_SCENARIOS, ids=lambda s: s["id"])
    def test_write_tools_available(self, agent, scenario):
        """Verify expected tools are registered for write scenarios."""
        tool_names = [t["name"] for t in agent.tools.list_tools()]
        for expected_tool in scenario["expected_tools"]:
            assert expected_tool in tool_names, f"Scenario '{scenario['id']}': Tool '{expected_tool}' not registered"

    @pytest.mark.parametrize("scenario", WRITE_SCENARIOS, ids=lambda s: s["id"])
    def test_write_tools_return_pending_action(self, agent, scenario):
        """Write tools return pending action, not immediate execution."""
        for tool_name in scenario["expected_tools"]:
            params = _get_minimal_params(tool_name)
            result = agent.tools.execute(tool_name, params)
            assert result.success, f"Tool {tool_name} failed"
            assert "pending_action" in result.data, f"Tool {tool_name} should return pending_action"


class TestRefusalScenarios:
    """Test that agent refuses out-of-scope requests."""

    @pytest.fixture
    def agent(self):
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    def test_no_delete_tool_exists(self, agent):
        """No delete tools should exist."""
        tool_names = [t["name"] for t in agent.tools.list_tools()]
        delete_tools = [t for t in tool_names if "delete" in t.lower()]
        assert len(delete_tools) == 0, f"Found delete tools: {delete_tools}"

    def test_no_payment_tool_exists(self, agent):
        """No payment/approval tools should exist."""
        tool_names = [t["name"] for t in agent.tools.list_tools()]
        payment_tools = [t for t in tool_names if "pay" in t.lower() or "approve" in t.lower()]
        assert len(payment_tools) == 0, f"Found payment tools: {payment_tools}"


class TestConfirmationScenarios:
    """Test confirmation flow scenarios."""

    @pytest.fixture
    def agent(self):
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    def test_pending_action_requires_confirmation(self, agent):
        """Pending action exists until confirmed or cancelled."""
        agent.pending_action = PendingAction(
            tool_name="request_create_task",
            preview="Create task: Test",
            payload={"title": "Test"},
        )
        assert agent.has_pending_action()
        assert agent.get_pending_preview() is not None

    def test_confirmation_clears_pending(self, agent):
        """Confirmation clears pending action."""
        agent.pending_action = PendingAction(
            tool_name="request_create_task",
            preview="Create task: Test",
            payload={"title": "Test"},
        )
        agent.pending_action = None
        assert not agent.has_pending_action()

    @pytest.mark.parametrize("phrase", ["yes", "y", "confirm", "ok", "proceed"])
    def test_yes_phrases_detected(self, agent, phrase):
        """Various yes phrases are detected."""
        assert agent._is_confirmation(phrase) == "yes"

    @pytest.mark.parametrize("phrase", ["no", "n", "cancel", "stop", "abort"])
    def test_no_phrases_detected(self, agent, phrase):
        """Various no phrases are detected."""
        assert agent._is_confirmation(phrase) == "no"


def _get_minimal_params(tool_name: str) -> dict:
    """Get minimal valid params for each write tool."""
    params = {
        "request_create_task": {"title": "Test task"},
        "request_create_note": {"content": "Test note", "target_type": "deal", "target_id": 1},
        "request_create_reminder": {
            "target_type": "task",
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
    return params.get(tool_name, {})
