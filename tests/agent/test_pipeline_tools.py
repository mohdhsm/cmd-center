"""Tests for pipeline tools."""

import pytest
from unittest.mock import Mock, patch
from cmd_center.agent.tools.pipeline_tools import (
    GetOverdueDeals,
    GetStuckDeals,
    GetDealDetails,
    GetDealNotes,
)


class TestGetOverdueDeals:
    """Test GetOverdueDeals tool."""

    def test_tool_name(self):
        """Tool has correct name."""
        tool = GetOverdueDeals()
        assert tool.name == "get_overdue_deals"

    def test_tool_description(self):
        """Tool has description."""
        tool = GetOverdueDeals()
        assert "overdue" in tool.description.lower()

    def test_schema_has_pipeline_param(self):
        """Schema includes pipeline parameter."""
        tool = GetOverdueDeals()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "pipeline" in props

    @patch("cmd_center.agent.tools.pipeline_tools.get_deal_health_service")
    def test_execute_returns_deals(self, mock_get_service):
        """Execute returns deals from service."""
        mock_service = Mock()
        mock_service.get_overdue_deals.return_value = [
            Mock(id=1, title="Deal 1", owner="Alice", stage="OR", overdue_days=10, value=1000),
            Mock(id=2, title="Deal 2", owner="Bob", stage="UP", overdue_days=5, value=2000),
        ]
        mock_get_service.return_value = mock_service

        tool = GetOverdueDeals()
        result = tool.parse_and_execute({"pipeline": "aramco"})

        assert result.success is True
        assert len(result.data["deals"]) == 2


class TestGetStuckDeals:
    """Test GetStuckDeals tool."""

    def test_tool_name(self):
        """Tool has correct name."""
        tool = GetStuckDeals()
        assert tool.name == "get_stuck_deals"

    @patch("cmd_center.agent.tools.pipeline_tools.get_deal_health_service")
    def test_execute_returns_stuck_deals(self, mock_get_service):
        """Execute returns stuck deals."""
        mock_service = Mock()
        mock_service.get_stuck_deals.return_value = []
        mock_get_service.return_value = mock_service

        tool = GetStuckDeals()
        result = tool.parse_and_execute({"min_days": 30})

        assert result.success is True


class TestGetDealDetails:
    """Test GetDealDetails tool."""

    def test_tool_name(self):
        """Tool has correct name."""
        tool = GetDealDetails()
        assert tool.name == "get_deal_details"

    def test_schema_requires_deal_id(self):
        """Schema requires deal_id parameter."""
        tool = GetDealDetails()
        schema = tool.get_openai_schema()
        required = schema["function"]["parameters"].get("required", [])
        assert "deal_id" in required

    @patch("cmd_center.agent.tools.pipeline_tools.get_deal_health_service")
    def test_execute_with_valid_deal(self, mock_get_service):
        """Execute returns deal details."""
        mock_service = Mock()
        mock_service.get_deal_detail.return_value = Mock(
            id=123,
            title="Test Deal",
            pipeline="Aramco Projects",
            stage="Under Progress",
            owner="Alice",
            org_name="Test Org",
            value_sar=50000,
            notes_count=5,
            activities_count=10,
            email_messages_count=3,
        )
        mock_get_service.return_value = mock_service

        tool = GetDealDetails()
        result = tool.parse_and_execute({"deal_id": 123})

        assert result.success is True
        assert result.data["deal"]["id"] == 123


class TestGetDealNotes:
    """Test GetDealNotes tool."""

    def test_tool_name(self):
        """Tool has correct name."""
        tool = GetDealNotes()
        assert tool.name == "get_deal_notes"

    @patch("cmd_center.agent.tools.pipeline_tools.get_deal_health_service")
    def test_execute_returns_notes(self, mock_get_service):
        """Execute returns deal notes."""
        from datetime import datetime, timezone
        mock_service = Mock()
        mock_service.get_deal_notes.return_value = [
            Mock(content="Note 1", author="Alice", date=datetime.now(timezone.utc)),
            Mock(content="Note 2", author="Bob", date=datetime.now(timezone.utc)),
        ]
        mock_get_service.return_value = mock_service

        tool = GetDealNotes()
        result = tool.parse_and_execute({"deal_id": 123, "limit": 5})

        assert result.success is True
        assert len(result.data["notes"]) == 2
