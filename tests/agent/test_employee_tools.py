"""Tests for employee tools including skills."""

import pytest
from unittest.mock import Mock, patch
from cmd_center.agent.tools.employee_tools import (
    GetEmployees,
    GetEmployeeDetails,
    GetEmployeeSkills,
)


class TestGetEmployees:
    """Test GetEmployees tool."""

    def test_tool_name(self):
        """Tool has correct name."""
        tool = GetEmployees()
        assert tool.name == "get_employees"

    def test_tool_description_length(self):
        """Tool has description > 20 chars."""
        tool = GetEmployees()
        assert len(tool.description) > 20

    @patch("cmd_center.agent.tools.employee_tools.get_employee_service")
    def test_execute_returns_employees(self, mock_get_service):
        """Execute returns employees."""
        mock_service = Mock()
        mock_service.get_employees.return_value = Mock(
            items=[
                Mock(id=1, full_name="Alice", role_title="Manager", department="sales", email="alice@test.com"),
                Mock(id=2, full_name="Bob", role_title="Engineer", department="operations", email="bob@test.com"),
            ],
            total=2,
        )
        mock_get_service.return_value = mock_service

        tool = GetEmployees()
        result = tool.parse_and_execute({})

        assert result.success is True
        assert len(result.data["employees"]) == 2


class TestGetEmployeeDetails:
    """Test GetEmployeeDetails tool."""

    def test_tool_name(self):
        """Tool has correct name."""
        tool = GetEmployeeDetails()
        assert tool.name == "get_employee_details"

    def test_tool_description_length(self):
        """Tool has description > 20 chars."""
        tool = GetEmployeeDetails()
        assert len(tool.description) > 20

    def test_schema_requires_employee_id(self):
        """Schema requires employee_id parameter."""
        tool = GetEmployeeDetails()
        schema = tool.get_openai_schema()
        required = schema["function"]["parameters"].get("required", [])
        assert "employee_id" in required

    @patch("cmd_center.agent.tools.employee_tools.get_employee_service")
    def test_execute_returns_employee(self, mock_get_service):
        """Execute returns employee details."""
        mock_service = Mock()
        mock_service.get_employee_by_id.return_value = Mock(
            id=1,
            full_name="Alice",
            role_title="Sales Manager",
            department="sales",
            email="alice@example.com",
            phone="+1234567890",
            is_active=True,
        )
        mock_get_service.return_value = mock_service

        tool = GetEmployeeDetails()
        result = tool.parse_and_execute({"employee_id": 1})

        assert result.success is True
        assert result.data["employee"]["full_name"] == "Alice"

    @patch("cmd_center.agent.tools.employee_tools.get_employee_service")
    def test_execute_handles_not_found(self, mock_get_service):
        """Execute returns error when employee not found."""
        mock_service = Mock()
        mock_service.get_employee_by_id.return_value = None
        mock_get_service.return_value = mock_service

        tool = GetEmployeeDetails()
        result = tool.parse_and_execute({"employee_id": 999})

        assert result.success is False
        assert "not found" in result.error.lower()


class TestGetEmployeeSkills:
    """Test GetEmployeeSkills tool."""

    def test_tool_name(self):
        """Tool has correct name."""
        tool = GetEmployeeSkills()
        assert tool.name == "get_employee_skills"

    def test_tool_description_length(self):
        """Tool has description > 20 chars."""
        tool = GetEmployeeSkills()
        assert len(tool.description) > 20

    def test_schema_requires_employee_id(self):
        """Schema requires employee_id parameter."""
        tool = GetEmployeeSkills()
        schema = tool.get_openai_schema()
        required = schema["function"]["parameters"].get("required", [])
        assert "employee_id" in required

    @patch("cmd_center.agent.tools.employee_tools.get_skill_service")
    def test_execute_returns_skill_data(self, mock_get_service):
        """Execute returns skill data from service."""
        mock_service = Mock()
        mock_service.get_employee_skill_card.return_value = Mock(
            employee_id=1,
            employee_name="Alice Smith",
            skills=[
                Mock(skill_id=1, skill_name="Python", rating=4, category="Technical"),
                Mock(skill_id=2, skill_name="Communication", rating=5, category="Soft Skills"),
            ],
        )
        mock_get_service.return_value = mock_service

        tool = GetEmployeeSkills()
        result = tool.parse_and_execute({"employee_id": 1})

        assert result.success is True
        assert result.data["employee_name"] == "Alice Smith"
        assert result.data["employee_id"] == 1
        assert result.data["skill_count"] == 2
        assert len(result.data["skills"]) == 2
        # Check skill data structure
        skill_names = [s["skill_name"] for s in result.data["skills"]]
        assert "Python" in skill_names
        assert "Communication" in skill_names

    @patch("cmd_center.agent.tools.employee_tools.get_skill_service")
    def test_execute_handles_not_found(self, mock_get_service):
        """Execute returns error when employee not found."""
        mock_service = Mock()
        mock_service.get_employee_skill_card.return_value = None
        mock_get_service.return_value = mock_service

        tool = GetEmployeeSkills()
        result = tool.parse_and_execute({"employee_id": 999})

        assert result.success is False
        assert "not found" in result.error.lower()

    @patch("cmd_center.agent.tools.employee_tools.get_skill_service")
    def test_execute_handles_exception(self, mock_get_service):
        """Execute handles exceptions gracefully."""
        mock_service = Mock()
        mock_service.get_employee_skill_card.side_effect = Exception("Database error")
        mock_get_service.return_value = mock_service

        tool = GetEmployeeSkills()
        result = tool.parse_and_execute({"employee_id": 1})

        assert result.success is False
        assert "Database error" in result.error
