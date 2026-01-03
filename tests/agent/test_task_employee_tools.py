"""Tests for task and employee tools."""

import pytest
from unittest.mock import Mock, patch
from cmd_center.agent.tools.task_tools import GetTasks, GetOverdueTasks
from cmd_center.agent.tools.employee_tools import GetEmployees, GetEmployeeDetails


class TestGetTasks:
    """Test GetTasks tool."""

    def test_tool_name(self):
        """Tool has correct name."""
        tool = GetTasks()
        assert tool.name == "get_tasks"

    @patch("cmd_center.agent.tools.task_tools.get_task_service")
    def test_execute_returns_tasks(self, mock_get_service):
        """Execute returns tasks from service."""
        mock_service = Mock()
        mock_service.get_tasks.return_value = Mock(
            items=[
                Mock(id=1, title="Task 1", status="open", priority="high", is_critical=False, due_at=None, assignee_employee_id=1),
                Mock(id=2, title="Task 2", status="done", priority="low", is_critical=False, due_at=None, assignee_employee_id=2),
            ],
            total=2,
        )
        mock_get_service.return_value = mock_service

        tool = GetTasks()
        result = tool.parse_and_execute({})

        assert result.success is True
        assert len(result.data["tasks"]) == 2


class TestGetOverdueTasks:
    """Test GetOverdueTasks tool."""

    def test_tool_name(self):
        """Tool has correct name."""
        tool = GetOverdueTasks()
        assert tool.name == "get_overdue_tasks"

    @patch("cmd_center.agent.tools.task_tools.get_task_service")
    def test_execute_returns_overdue_tasks(self, mock_get_service):
        """Execute returns overdue tasks."""
        mock_service = Mock()
        mock_service.get_overdue_tasks.return_value = [
            Mock(id=1, title="Overdue Task", status="open", priority="high", is_critical=True, due_at=None, assignee_employee_id=1),
        ]
        mock_get_service.return_value = mock_service

        tool = GetOverdueTasks()
        result = tool.parse_and_execute({})

        assert result.success is True


class TestGetEmployees:
    """Test GetEmployees tool."""

    def test_tool_name(self):
        """Tool has correct name."""
        tool = GetEmployees()
        assert tool.name == "get_employees"

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
