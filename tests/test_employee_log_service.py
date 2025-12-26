"""Unit tests for EmployeeLogService."""

from datetime import datetime, timedelta, timezone

import pytest

from cmd_center.backend.services.employee_log_service import EmployeeLogService
from cmd_center.backend.services.employee_service import EmployeeService
from cmd_center.backend.models.employee_log_models import (
    LogEntryCreate,
    LogEntryFilters,
)
from cmd_center.backend.models.employee_models import EmployeeCreate


class TestEmployeeLogService:
    """Test cases for EmployeeLogService."""

    def test_create_log_entry(self, override_db):
        """Creates log entry with category."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = EmployeeLogService(actor="manager")
        data = LogEntryCreate(
            employee_id=employee.id,
            category="achievement",
            title="Completed Major Project",
            content="Successfully delivered the Q4 project on time and under budget.",
            is_positive=True,
        )
        result = service.create_log_entry(data)

        assert result.id is not None
        assert result.category == "achievement"
        assert result.title == "Completed Major Project"
        assert result.is_positive is True
        assert result.logged_by == "manager"

    def test_create_issue_log_with_severity(self, override_db):
        """Creates issue log with severity."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = EmployeeLogService()
        data = LogEntryCreate(
            employee_id=employee.id,
            category="issue",
            title="Late Arrival",
            content="Employee arrived 2 hours late without prior notice.",
            severity="medium",
            is_positive=False,
        )
        result = service.create_log_entry(data)

        assert result.category == "issue"
        assert result.severity == "medium"
        assert result.is_positive is False

    def test_get_logs_by_employee(self, override_db):
        """Returns logs for specific employee."""
        emp_service = EmployeeService()
        emp1 = emp_service.create_employee(EmployeeCreate(full_name="Employee 1", role_title="Dev"))
        emp2 = emp_service.create_employee(EmployeeCreate(full_name="Employee 2", role_title="Dev"))

        service = EmployeeLogService()
        service.create_log_entry(LogEntryCreate(
            employee_id=emp1.id,
            category="achievement",
            title="Emp1 Achievement",
            content="Great work!",
        ))
        service.create_log_entry(LogEntryCreate(
            employee_id=emp2.id,
            category="achievement",
            title="Emp2 Achievement",
            content="Great work!",
        ))

        result = service.get_logs_by_employee(emp1.id)
        assert len(result) == 1
        assert result[0].employee_id == emp1.id

    def test_get_logs_by_category(self, override_db):
        """Filters by category."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = EmployeeLogService()
        service.create_log_entry(LogEntryCreate(
            employee_id=employee.id,
            category="achievement",
            title="Achievement",
            content="Details...",
        ))
        service.create_log_entry(LogEntryCreate(
            employee_id=employee.id,
            category="issue",
            title="Issue",
            content="Details...",
        ))
        service.create_log_entry(LogEntryCreate(
            employee_id=employee.id,
            category="feedback",
            title="Feedback",
            content="Details...",
        ))

        result = service.get_logs_by_category("achievement")
        assert len(result) == 1
        assert result[0].category == "achievement"

    def test_get_log_entries_filter_positive(self, override_db):
        """Filters by is_positive flag."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = EmployeeLogService()
        service.create_log_entry(LogEntryCreate(
            employee_id=employee.id,
            category="achievement",
            title="Positive Log",
            content="Great work!",
            is_positive=True,
        ))
        service.create_log_entry(LogEntryCreate(
            employee_id=employee.id,
            category="issue",
            title="Negative Log",
            content="Issue details...",
            is_positive=False,
        ))

        positive_result = service.get_log_entries(LogEntryFilters(is_positive=True))
        assert positive_result.total == 1
        assert positive_result.items[0].is_positive is True

        negative_result = service.get_log_entries(LogEntryFilters(is_positive=False))
        assert negative_result.total == 1
        assert negative_result.items[0].is_positive is False

    def test_get_log_entries_date_filter(self, override_db):
        """Filters by date range."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = EmployeeLogService()
        now = datetime.now(timezone.utc)

        # Old log
        service.create_log_entry(LogEntryCreate(
            employee_id=employee.id,
            category="achievement",
            title="Old Log",
            content="Details...",
            occurred_at=now - timedelta(days=30),
        ))

        # Recent log
        service.create_log_entry(LogEntryCreate(
            employee_id=employee.id,
            category="achievement",
            title="Recent Log",
            content="Details...",
            occurred_at=now - timedelta(days=5),
        ))

        result = service.get_log_entries(LogEntryFilters(
            from_date=now - timedelta(days=10),
        ))
        assert result.total == 1
        assert result.items[0].title == "Recent Log"

    def test_get_log_entries_search(self, override_db):
        """Search filter returns logs matching title or content."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = EmployeeLogService()
        service.create_log_entry(LogEntryCreate(
            employee_id=employee.id,
            category="achievement",
            title="Project Completion",
            content="Finished the Alpha project.",
        ))
        service.create_log_entry(LogEntryCreate(
            employee_id=employee.id,
            category="feedback",
            title="Client Feedback",
            content="Positive feedback from client.",
        ))

        result = service.get_log_entries(LogEntryFilters(search="project"))
        assert result.total == 1
        assert result.items[0].title == "Project Completion"

    def test_get_recent_issues(self, override_db):
        """Get recent issue logs with employee names."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="John Doe",
            role_title="Developer",
        ))

        service = EmployeeLogService()
        service.create_log_entry(LogEntryCreate(
            employee_id=employee.id,
            category="issue",
            title="Late Arrival",
            content="Arrived late.",
            severity="low",
            is_positive=False,
        ))
        service.create_log_entry(LogEntryCreate(
            employee_id=employee.id,
            category="achievement",
            title="Good Work",  # Not an issue, should be excluded
            content="Great performance.",
            is_positive=True,
        ))

        result = service.get_recent_issues()
        assert len(result) == 1
        assert result[0].category == "issue"
        assert result[0].employee_name == "John Doe"

    def test_get_recent_issues_filter_severity(self, override_db):
        """Filters issues by severity."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = EmployeeLogService()
        service.create_log_entry(LogEntryCreate(
            employee_id=employee.id,
            category="issue",
            title="Low Severity",
            content="Minor issue.",
            severity="low",
            is_positive=False,
        ))
        service.create_log_entry(LogEntryCreate(
            employee_id=employee.id,
            category="issue",
            title="High Severity",
            content="Critical issue.",
            severity="high",
            is_positive=False,
        ))

        result = service.get_recent_issues(severity="high")
        assert len(result) == 1
        assert result[0].severity == "high"

    def test_get_employee_summary(self, override_db):
        """Get summary statistics for an employee's logs."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = EmployeeLogService()
        # Create various logs
        service.create_log_entry(LogEntryCreate(
            employee_id=employee.id,
            category="achievement",
            title="Achievement 1",
            content="...",
            is_positive=True,
        ))
        service.create_log_entry(LogEntryCreate(
            employee_id=employee.id,
            category="achievement",
            title="Achievement 2",
            content="...",
            is_positive=True,
        ))
        service.create_log_entry(LogEntryCreate(
            employee_id=employee.id,
            category="issue",
            title="Issue 1",
            content="...",
            is_positive=False,
        ))
        service.create_log_entry(LogEntryCreate(
            employee_id=employee.id,
            category="milestone",
            title="Milestone 1",
            content="...",
            is_positive=True,
        ))

        result = service.get_employee_summary(employee.id)

        assert result["employee_id"] == employee.id
        assert result["total_logs"] == 4
        assert result["by_category"]["achievement"] == 2
        assert result["by_category"]["issue"] == 1
        assert result["by_category"]["milestone"] == 1
        assert result["positive_count"] == 3
        assert result["negative_count"] == 1

    def test_get_log_entry_with_employee(self, override_db):
        """Get log entry with employee name."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Jane Smith",
            role_title="Manager",
        ))

        service = EmployeeLogService()
        log = service.create_log_entry(LogEntryCreate(
            employee_id=employee.id,
            category="feedback",
            title="Quarterly Review",
            content="Positive feedback from quarterly review.",
        ))

        result = service.get_log_entry_with_employee(log.id)
        assert result is not None
        assert result.employee_name == "Jane Smith"

    def test_logs_pagination(self, override_db):
        """Pagination works correctly."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = EmployeeLogService()
        for i in range(15):
            service.create_log_entry(LogEntryCreate(
                employee_id=employee.id,
                category="other",
                title=f"Log {i}",
                content="Details...",
            ))

        result = service.get_log_entries(LogEntryFilters(page=1, page_size=10))
        assert result.total == 15
        assert len(result.items) == 10

        result2 = service.get_log_entries(LogEntryFilters(page=2, page_size=10))
        assert len(result2.items) == 5
