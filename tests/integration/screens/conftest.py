"""Fixtures for TUI screen integration tests."""

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class MockResponse:
    """Mock HTTP response."""

    def __init__(self, json_data: Any, status_code: int = 200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data


class MockAsyncClient:
    """Mock httpx.AsyncClient with configurable responses."""

    def __init__(self):
        self.responses: dict[str, MockResponse] = {}
        self.calls: list[tuple[str, str, dict]] = []  # (method, url, kwargs)

    def set_response(self, url_pattern: str, data: Any, status_code: int = 200):
        """Set response for a URL pattern."""
        self.responses[url_pattern] = MockResponse(data, status_code)

    def _find_response(self, url: str) -> MockResponse:
        """Find matching response for URL."""
        for pattern, response in self.responses.items():
            if pattern in url:
                return response
        return MockResponse([], 200)  # Default empty response

    async def get(self, url: str, **kwargs) -> MockResponse:
        self.calls.append(("GET", url, kwargs))
        return self._find_response(url)

    async def post(self, url: str, **kwargs) -> MockResponse:
        self.calls.append(("POST", url, kwargs))
        return self._find_response(url)

    async def patch(self, url: str, **kwargs) -> MockResponse:
        self.calls.append(("PATCH", url, kwargs))
        return self._find_response(url)

    async def delete(self, url: str, **kwargs) -> MockResponse:
        self.calls.append(("DELETE", url, kwargs))
        return self._find_response(url)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


@pytest.fixture
def mock_client():
    """Create a mock HTTP client."""
    return MockAsyncClient()


@pytest.fixture
def sample_employees():
    """Sample employee data for tests."""
    return [
        {
            "id": 1,
            "full_name": "Ahmed Al-Farsi",
            "email": "ahmed@company.com",
            "role_title": "Sales Manager",
            "department": "sales",
            "is_active": True,
            "manager_id": None,
        },
        {
            "id": 2,
            "full_name": "Faris Hassan",
            "email": "faris@company.com",
            "role_title": "Engineer",
            "department": "engineering",
            "is_active": True,
            "manager_id": 1,
        },
        {
            "id": 3,
            "full_name": "Sara Ahmed",
            "email": "sara@company.com",
            "role_title": "HR Manager",
            "department": "operations",
            "is_active": False,
            "manager_id": None,
        },
    ]


@pytest.fixture
def sample_tasks():
    """Sample task data for tests."""
    now = datetime.now(timezone.utc)
    return [
        {
            "id": 1,
            "title": "Complete quarterly report",
            "description": "Finish the Q4 report",
            "status": "open",
            "priority": "high",
            "assignee_employee_id": 1,
            "is_critical": True,
            "due_at": (now + timedelta(days=2)).isoformat(),
            "created_at": now.isoformat(),
        },
        {
            "id": 2,
            "title": "Review code changes",
            "description": "Review PR #123",
            "status": "in_progress",
            "priority": "medium",
            "assignee_employee_id": 2,
            "is_critical": False,
            "due_at": (now + timedelta(days=5)).isoformat(),
            "created_at": now.isoformat(),
        },
        {
            "id": 3,
            "title": "Old completed task",
            "description": "This is done",
            "status": "done",
            "priority": "low",
            "assignee_employee_id": 1,
            "is_critical": False,
            "due_at": (now - timedelta(days=1)).isoformat(),
            "created_at": (now - timedelta(days=10)).isoformat(),
        },
    ]


@pytest.fixture
def sample_notes():
    """Sample note data for tests."""
    now = datetime.now(timezone.utc)
    return [
        {
            "id": 1,
            "content": "Important meeting notes from client call",
            "target_type": "deal",
            "target_id": 100,
            "pinned": True,
            "tags": "client,important",
            "review_at": (now + timedelta(days=7)).isoformat(),
            "created_at": now.isoformat(),
        },
        {
            "id": 2,
            "content": "Follow up on employee performance",
            "target_type": "employee",
            "target_id": 2,
            "pinned": False,
            "tags": "hr,review",
            "review_at": None,
            "created_at": now.isoformat(),
        },
    ]


@pytest.fixture
def sample_documents():
    """Sample document data for tests."""
    now = datetime.now(timezone.utc)
    return [
        {
            "id": 1,
            "title": "Business License",
            "document_type": "license",
            "status": "active",
            "expiry_date": (now + timedelta(days=30)).isoformat(),
            "responsible_employee_id": 1,
        },
        {
            "id": 2,
            "title": "Insurance Policy",
            "document_type": "insurance",
            "status": "active",
            "expiry_date": (now + timedelta(days=5)).isoformat(),
            "responsible_employee_id": 2,
        },
        {
            "id": 3,
            "title": "Expired Contract",
            "document_type": "contract",
            "status": "expired",
            "expiry_date": (now - timedelta(days=10)).isoformat(),
            "responsible_employee_id": 1,
        },
    ]


@pytest.fixture
def sample_bonuses():
    """Sample bonus data for tests."""
    now = datetime.now(timezone.utc)
    return [
        {
            "id": 1,
            "title": "Q4 Performance Bonus",
            "employee_id": 1,
            "amount": 5000.0,
            "currency": "SAR",
            "status": "pending",
            "paid_amount": 0.0,
            "due_date": (now + timedelta(days=15)).isoformat(),
        },
        {
            "id": 2,
            "title": "Project Completion Bonus",
            "employee_id": 2,
            "amount": 3000.0,
            "currency": "SAR",
            "status": "partial",
            "paid_amount": 1500.0,
            "due_date": (now + timedelta(days=7)).isoformat(),
        },
    ]


@pytest.fixture
def sample_employee_logs():
    """Sample employee log data for tests."""
    now = datetime.now(timezone.utc)
    return [
        {
            "id": 1,
            "employee_id": 1,
            "category": "achievement",
            "severity": "low",
            "summary": "Exceeded sales target by 20%",
            "details": "Great performance this quarter",
            "logged_at": now.isoformat(),
        },
        {
            "id": 2,
            "employee_id": 2,
            "category": "issue",
            "severity": "medium",
            "summary": "Missed deadline on project",
            "details": "Needs follow-up",
            "logged_at": now.isoformat(),
        },
    ]


@pytest.fixture
def sample_skills():
    """Sample skill data for tests."""
    return [
        {"id": 1, "name": "Python", "category": "technical", "description": "Python programming"},
        {"id": 2, "name": "SQL", "category": "technical", "description": "Database queries"},
        {"id": 3, "name": "Leadership", "category": "soft", "description": "Team leadership"},
    ]


@pytest.fixture
def sample_loop_status():
    """Sample loop status data for tests."""
    now = datetime.now(timezone.utc)
    return [
        {
            "name": "docs_expiry",
            "description": "Check document expiry",
            "interval_minutes": 360,
            "last_run_at": (now - timedelta(hours=2)).isoformat(),
            "last_status": "completed",
            "last_findings_count": 3,
        },
        {
            "name": "bonus_due",
            "description": "Check bonus due dates",
            "interval_minutes": 720,
            "last_run_at": (now - timedelta(hours=5)).isoformat(),
            "last_status": "completed",
            "last_findings_count": 1,
        },
        {
            "name": "task_overdue",
            "description": "Check overdue tasks",
            "interval_minutes": 60,
            "last_run_at": (now - timedelta(minutes=15)).isoformat(),
            "last_status": "completed",
            "last_findings_count": 5,
        },
    ]


@pytest.fixture
def sample_findings():
    """Sample findings data for tests."""
    now = datetime.now(timezone.utc)
    return [
        {
            "id": 1,
            "loop_name": "docs_expiry",
            "severity": "critical",
            "target_type": "document",
            "target_id": 3,
            "message": "Document 'Expired Contract' has expired",
            "recommended_action": "Renew immediately",
            "created_at": now.isoformat(),
        },
        {
            "id": 2,
            "loop_name": "task_overdue",
            "severity": "warning",
            "target_type": "task",
            "target_id": 1,
            "message": "Task is due soon",
            "recommended_action": "Follow up with assignee",
            "created_at": now.isoformat(),
        },
    ]


@pytest.fixture
def sample_loop_runs():
    """Sample loop run history for tests."""
    now = datetime.now(timezone.utc)
    return [
        {
            "id": 1,
            "loop_name": "docs_expiry",
            "started_at": (now - timedelta(hours=2)).isoformat(),
            "finished_at": (now - timedelta(hours=2) + timedelta(seconds=5)).isoformat(),
            "status": "completed",
            "findings_count": 3,
        },
        {
            "id": 2,
            "loop_name": "task_overdue",
            "started_at": (now - timedelta(minutes=15)).isoformat(),
            "finished_at": (now - timedelta(minutes=15) + timedelta(seconds=2)).isoformat(),
            "status": "completed",
            "findings_count": 5,
        },
    ]


def setup_mock_client(
    mock_client: MockAsyncClient,
    employees=None,
    tasks=None,
    notes=None,
    documents=None,
    bonuses=None,
    employee_logs=None,
    skills=None,
    loop_status=None,
    findings=None,
    loop_runs=None,
):
    """Configure mock client with common responses."""
    if employees is not None:
        mock_client.set_response("/employees", employees)
    if tasks is not None:
        mock_client.set_response("/tasks", tasks)
    if notes is not None:
        mock_client.set_response("/notes", notes)
    if documents is not None:
        mock_client.set_response("/documents", documents)
    if bonuses is not None:
        mock_client.set_response("/bonuses", bonuses)
    if employee_logs is not None:
        mock_client.set_response("/employee-logs", employee_logs)
    if skills is not None:
        mock_client.set_response("/skills", skills)
    if loop_status is not None:
        mock_client.set_response("/loops/status", loop_status)
    if findings is not None:
        mock_client.set_response("/loops/findings", findings)
    if loop_runs is not None:
        mock_client.set_response("/loops/runs", loop_runs)
    return mock_client
