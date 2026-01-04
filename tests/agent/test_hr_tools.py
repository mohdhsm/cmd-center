"""Tests for HR tools."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from cmd_center.agent.tools.hr_tools import GetUnpaidBonuses, GetUnpaidBonusesParams
from cmd_center.agent.tools.base import ToolResult


class TestGetUnpaidBonuses:
    """Tests for the GetUnpaidBonuses tool."""

    def test_tool_has_correct_name(self):
        """Tool should have the correct name for registration."""
        tool = GetUnpaidBonuses()
        assert tool.name == "get_unpaid_bonuses"

    def test_tool_has_description(self):
        """Tool should have a meaningful description."""
        tool = GetUnpaidBonuses()
        assert len(tool.description) > 20
        assert "bonus" in tool.description.lower() or "unpaid" in tool.description.lower()

    def test_params_have_employee_id_optional(self):
        """Parameters should have optional employee_id field."""
        params = GetUnpaidBonusesParams()
        assert params.employee_id is None

        params_with_id = GetUnpaidBonusesParams(employee_id=42)
        assert params_with_id.employee_id == 42

    def test_params_have_limit_with_default(self):
        """Parameters should have optional limit field with default."""
        params = GetUnpaidBonusesParams()
        assert params.limit == 50  # default

        params_with_limit = GetUnpaidBonusesParams(limit=10)
        assert params_with_limit.limit == 10

    @patch("cmd_center.agent.tools.hr_tools.get_bonus_service")
    def test_execute_returns_unpaid_bonuses(self, mock_get_service):
        """Execute should return unpaid bonuses from the service."""
        # Arrange
        mock_service = MagicMock()
        now = datetime.now(timezone.utc)

        mock_bonus = MagicMock()
        mock_bonus.id = 1
        mock_bonus.employee_id = 10
        mock_bonus.title = "Q4 Performance Bonus"
        mock_bonus.description = "Outstanding Q4 performance"
        mock_bonus.amount = 5000.0
        mock_bonus.currency = "SAR"
        mock_bonus.bonus_type = "performance"
        mock_bonus.status = "promised"
        mock_bonus.promised_date = now
        mock_bonus.due_date = now
        mock_bonus.created_at = now
        mock_bonus.updated_at = now

        mock_service.get_unpaid_bonuses.return_value = [mock_bonus]
        mock_get_service.return_value = mock_service

        # Act
        tool = GetUnpaidBonuses()
        result = tool.execute(GetUnpaidBonusesParams())

        # Assert
        assert result.success is True
        assert "bonuses" in result.data
        assert len(result.data["bonuses"]) == 1
        assert result.data["bonuses"][0]["id"] == 1
        assert result.data["bonuses"][0]["title"] == "Q4 Performance Bonus"
        assert result.data["bonuses"][0]["amount"] == 5000.0
        assert result.data["bonuses"][0]["status"] == "promised"

    @patch("cmd_center.agent.tools.hr_tools.get_bonus_service")
    def test_execute_includes_count_and_total_amount(self, mock_get_service):
        """Execute should include count and total amount in response."""
        # Arrange
        mock_service = MagicMock()
        now = datetime.now(timezone.utc)

        bonuses = []
        for i in range(3):
            mock_bonus = MagicMock()
            mock_bonus.id = i + 1
            mock_bonus.employee_id = 10
            mock_bonus.title = f"Bonus {i + 1}"
            mock_bonus.description = None
            mock_bonus.amount = 1000.0 * (i + 1)  # 1000, 2000, 3000
            mock_bonus.currency = "SAR"
            mock_bonus.bonus_type = "performance"
            mock_bonus.status = "approved"
            mock_bonus.promised_date = now
            mock_bonus.due_date = now
            mock_bonus.created_at = now
            mock_bonus.updated_at = None
            bonuses.append(mock_bonus)

        mock_service.get_unpaid_bonuses.return_value = bonuses
        mock_get_service.return_value = mock_service

        # Act
        tool = GetUnpaidBonuses()
        result = tool.execute(GetUnpaidBonusesParams())

        # Assert
        assert result.success is True
        assert result.data["count"] == 3
        assert result.data["total_amount"] == 6000.0  # 1000 + 2000 + 3000

    @patch("cmd_center.agent.tools.hr_tools.get_bonus_service")
    def test_execute_passes_employee_id_to_service(self, mock_get_service):
        """Execute should pass employee_id filter to the service."""
        # Arrange
        mock_service = MagicMock()
        mock_service.get_unpaid_bonuses.return_value = []
        mock_get_service.return_value = mock_service

        # Act
        tool = GetUnpaidBonuses()
        tool.execute(GetUnpaidBonusesParams(employee_id=42))

        # Assert
        mock_service.get_unpaid_bonuses.assert_called_once_with(employee_id=42, limit=50)

    @patch("cmd_center.agent.tools.hr_tools.get_bonus_service")
    def test_execute_passes_limit_to_service(self, mock_get_service):
        """Execute should pass limit to the service."""
        # Arrange
        mock_service = MagicMock()
        mock_service.get_unpaid_bonuses.return_value = []
        mock_get_service.return_value = mock_service

        # Act
        tool = GetUnpaidBonuses()
        tool.execute(GetUnpaidBonusesParams(limit=10))

        # Assert
        mock_service.get_unpaid_bonuses.assert_called_once_with(employee_id=None, limit=10)

    @patch("cmd_center.agent.tools.hr_tools.get_bonus_service")
    def test_execute_handles_empty_list(self, mock_get_service):
        """Execute should handle empty bonus list gracefully."""
        # Arrange
        mock_service = MagicMock()
        mock_service.get_unpaid_bonuses.return_value = []
        mock_get_service.return_value = mock_service

        # Act
        tool = GetUnpaidBonuses()
        result = tool.execute(GetUnpaidBonusesParams())

        # Assert
        assert result.success is True
        assert result.data["bonuses"] == []
        assert result.data["count"] == 0
        assert result.data["total_amount"] == 0

    @patch("cmd_center.agent.tools.hr_tools.get_bonus_service")
    def test_execute_handles_service_error(self, mock_get_service):
        """Execute should return error result when service fails."""
        # Arrange
        mock_get_service.side_effect = Exception("Database connection failed")

        # Act
        tool = GetUnpaidBonuses()
        result = tool.execute(GetUnpaidBonusesParams())

        # Assert
        assert result.success is False
        assert "Database connection failed" in result.error

    def test_tool_generates_valid_openai_schema(self):
        """Tool should generate a valid OpenAI function schema."""
        tool = GetUnpaidBonuses()
        schema = tool.get_openai_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "get_unpaid_bonuses"
        assert "description" in schema["function"]
        assert "parameters" in schema["function"]
        assert schema["function"]["parameters"]["type"] == "object"

    @patch("cmd_center.agent.tools.hr_tools.get_bonus_service")
    def test_parse_and_execute_works(self, mock_get_service):
        """parse_and_execute should work with raw arguments dict."""
        # Arrange
        mock_service = MagicMock()
        mock_service.get_unpaid_bonuses.return_value = []
        mock_get_service.return_value = mock_service

        # Act
        tool = GetUnpaidBonuses()
        result = tool.parse_and_execute({"employee_id": 5})

        # Assert
        assert result.success is True
        mock_service.get_unpaid_bonuses.assert_called_once_with(employee_id=5, limit=50)
