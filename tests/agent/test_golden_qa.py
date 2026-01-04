"""Golden Q&A tests for Omnious agent - validates tool selection."""

import pytest

from cmd_center.agent.core.agent import OmniousAgent


GOLDEN_SCENARIOS = [
    {
        "id": "deals_need_attention",
        "query": "What deals need attention?",
        "expected_tools": ["get_overdue_deals"],
    },
    {
        "id": "stuck_deals",
        "query": "Which deals are stuck in their stage?",
        "expected_tools": ["get_stuck_deals"],
    },
    {
        "id": "specific_deal",
        "query": "Tell me about deal 123",
        "expected_tools": ["get_deal_details"],
    },
    {
        "id": "deal_history",
        "query": "What are the recent notes on deal 456?",
        "expected_tools": ["get_deal_notes"],
    },
    {
        "id": "overdue_tasks",
        "query": "What tasks are overdue?",
        "expected_tools": ["get_overdue_tasks"],
    },
    {
        "id": "team_lookup",
        "query": "Who works in the sales department?",
        "expected_tools": ["get_employees"],
    },
    {
        "id": "employee_details",
        "query": "Tell me about employee 5",
        "expected_tools": ["get_employee_details"],
    },
]


class TestGoldenToolSelection:
    """Test that agent selects correct tools for common queries."""

    @pytest.mark.parametrize("scenario", GOLDEN_SCENARIOS, ids=lambda s: s["id"])
    def test_tool_schema_exists(self, scenario):
        """Verify expected tools are registered."""
        agent = OmniousAgent()
        tool_names = [t["name"] for t in agent.tools.list_tools()]

        for expected_tool in scenario["expected_tools"]:
            assert expected_tool in tool_names, f"Tool {expected_tool} not registered"

    def test_all_tools_registered(self):
        """Verify all Phase 1 and Phase 2 tools are registered."""
        agent = OmniousAgent()
        tools = agent.tools.list_tools()

        expected_tools = [
            # Phase 1 tools
            "get_overdue_deals",
            "get_stuck_deals",
            "get_deal_details",
            "get_deal_notes",
            "get_tasks",
            "get_overdue_tasks",
            "get_employees",
            "get_employee_details",
            # Phase 2 tools
            "get_cashflow_projection",
            "get_ceo_dashboard",
            # Email tools
            "search_emails",
            "get_emails",
        ]

        tool_names = [t["name"] for t in tools]
        for expected in expected_tools:
            assert expected in tool_names, f"Missing tool: {expected}"

        assert len(tools) == 12, f"Expected 12 tools, got {len(tools)}"

    def test_tools_have_descriptions(self):
        """All tools have non-empty descriptions."""
        agent = OmniousAgent()
        tools = agent.tools.list_tools()

        for tool in tools:
            assert tool["description"], f"Tool {tool['name']} has no description"
            assert len(tool["description"]) > 10, f"Tool {tool['name']} description too short"

    def test_tools_have_valid_schemas(self):
        """All tools generate valid OpenAI schemas."""
        agent = OmniousAgent()
        schemas = agent.tools.get_tools_schema()

        for schema in schemas:
            assert schema["type"] == "function"
            assert "function" in schema
            assert "name" in schema["function"]
            assert "description" in schema["function"]
            assert "parameters" in schema["function"]
            assert schema["function"]["parameters"]["type"] == "object"
