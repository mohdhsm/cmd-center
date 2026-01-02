"""Fixtures for TUI screen integration tests.

All sample data fixtures are validated against Pydantic schemas to ensure
test data matches API contracts. This catches field name mismatches early.
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import schemas for validation
from cmd_center.backend.models.employee_models import EmployeeResponse
from cmd_center.backend.models.task_models import TaskResponse
from cmd_center.backend.models.note_models import NoteResponse
from cmd_center.backend.models.document_models import DocumentResponse
from cmd_center.backend.models.bonus_models import BonusResponse
from cmd_center.backend.models.employee_log_models import LogEntryResponse
from cmd_center.backend.models.skill_models import SkillResponse


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
    """Sample employee data for tests - validated against EmployeeResponse schema."""
    now = datetime.now(timezone.utc)
    data = [
        {
            "id": 1,
            "full_name": "Ahmed Al-Farsi",
            "email": "ahmed@company.com",
            "role_title": "Sales Manager",
            "department": "sales",
            "is_active": True,
            "reports_to_employee_id": None,
            "pipedrive_owner_id": None,
            "created_at": now.isoformat(),
            "updated_at": None,
        },
        {
            "id": 2,
            "full_name": "Faris Hassan",
            "email": "faris@company.com",
            "role_title": "Engineer",
            "department": "engineering",
            "is_active": True,
            "reports_to_employee_id": 1,
            "pipedrive_owner_id": None,
            "created_at": now.isoformat(),
            "updated_at": None,
        },
        {
            "id": 3,
            "full_name": "Sara Ahmed",
            "email": "sara@company.com",
            "role_title": "HR Manager",
            "department": "operations",
            "is_active": False,
            "reports_to_employee_id": None,
            "pipedrive_owner_id": None,
            "created_at": now.isoformat(),
            "updated_at": None,
        },
    ]
    # Validate against schema
    for emp in data:
        EmployeeResponse.model_validate(emp)
    return data


@pytest.fixture
def sample_tasks():
    """Sample task data for tests - validated against TaskResponse schema."""
    now = datetime.now(timezone.utc)
    data = [
        {
            "id": 1,
            "title": "Complete quarterly report",
            "description": "Finish the Q4 report",
            "status": "open",
            "priority": "high",
            "assignee_employee_id": 1,
            "created_by": "ceo_agent",
            "is_critical": True,
            "due_at": (now + timedelta(days=2)).isoformat(),
            "completed_at": None,
            "target_type": None,
            "target_id": None,
            "is_archived": False,
            "created_at": now.isoformat(),
            "updated_at": None,
        },
        {
            "id": 2,
            "title": "Review code changes",
            "description": "Review PR #123",
            "status": "in_progress",
            "priority": "medium",
            "assignee_employee_id": 2,
            "created_by": "ceo_agent",
            "is_critical": False,
            "due_at": (now + timedelta(days=5)).isoformat(),
            "completed_at": None,
            "target_type": "employee",
            "target_id": 2,
            "is_archived": False,
            "created_at": now.isoformat(),
            "updated_at": None,
        },
        {
            "id": 3,
            "title": "Old completed task",
            "description": "This is done",
            "status": "done",
            "priority": "low",
            "assignee_employee_id": 1,
            "created_by": "ceo_agent",
            "is_critical": False,
            "due_at": (now - timedelta(days=1)).isoformat(),
            "completed_at": (now - timedelta(days=2)).isoformat(),
            "target_type": None,
            "target_id": None,
            "is_archived": False,
            "created_at": (now - timedelta(days=10)).isoformat(),
            "updated_at": (now - timedelta(days=2)).isoformat(),
        },
    ]
    # Validate against schema
    for task in data:
        TaskResponse.model_validate(task)
    return data


@pytest.fixture
def sample_notes():
    """Sample note data for tests - validated against NoteResponse schema."""
    now = datetime.now(timezone.utc)
    data = [
        {
            "id": 1,
            "content": "Important meeting notes from client call",
            "created_by": "ceo_agent",
            "target_type": "deal",
            "target_id": 100,
            "pinned": True,
            "tags": "client,important",
            "review_at": (now + timedelta(days=7)).isoformat(),
            "is_archived": False,
            "created_at": now.isoformat(),
            "updated_at": None,
        },
        {
            "id": 2,
            "content": "Follow up on employee performance",
            "created_by": "ceo_agent",
            "target_type": "employee",
            "target_id": 2,
            "pinned": False,
            "tags": "hr,review",
            "review_at": None,
            "is_archived": False,
            "created_at": now.isoformat(),
            "updated_at": None,
        },
    ]
    # Validate against schema
    for note in data:
        NoteResponse.model_validate(note)
    return data


@pytest.fixture
def sample_documents():
    """Sample document data for tests - validated against DocumentResponse schema."""
    now = datetime.now(timezone.utc)
    data = [
        {
            "id": 1,
            "title": "Business License",
            "document_type": "license",
            "description": "Main business operating license",
            "issue_date": (now - timedelta(days=365)).isoformat(),
            "expiry_date": (now + timedelta(days=30)).isoformat(),
            "status": "active",
            "reference_number": "BL-2024-001",
            "issuing_authority": "Ministry of Commerce",
            "responsible_employee_id": 1,
            "created_at": now.isoformat(),
            "updated_at": None,
        },
        {
            "id": 2,
            "title": "Insurance Policy",
            "document_type": "insurance",
            "description": "Company liability insurance",
            "issue_date": (now - timedelta(days=180)).isoformat(),
            "expiry_date": (now + timedelta(days=5)).isoformat(),
            "status": "active",
            "reference_number": "INS-2024-002",
            "issuing_authority": "Saudi Insurance Co",
            "responsible_employee_id": 2,
            "created_at": now.isoformat(),
            "updated_at": None,
        },
        {
            "id": 3,
            "title": "Expired Contract",
            "document_type": "contract",
            "description": "Vendor service agreement",
            "issue_date": (now - timedelta(days=400)).isoformat(),
            "expiry_date": (now - timedelta(days=10)).isoformat(),
            "status": "expired",
            "reference_number": "CTR-2023-003",
            "issuing_authority": None,
            "responsible_employee_id": 1,
            "created_at": (now - timedelta(days=400)).isoformat(),
            "updated_at": None,
        },
    ]
    # Validate against schema
    for doc in data:
        DocumentResponse.model_validate(doc)
    return data


@pytest.fixture
def sample_bonuses():
    """Sample bonus data for tests - validated against BonusResponse schema.

    Note: status 'pending' was changed to 'promised' to match API schema.
    This was Bug #12 in the original bug fixes.
    """
    now = datetime.now(timezone.utc)
    data = [
        {
            "id": 1,
            "title": "Q4 Performance Bonus",
            "description": "Bonus for Q4 sales targets",
            "employee_id": 1,
            "amount": 5000.0,
            "currency": "SAR",
            "bonus_type": "performance",
            "conditions": "Achieve 120% of Q4 target",
            "promised_date": (now - timedelta(days=30)).isoformat(),
            "due_date": (now + timedelta(days=15)).isoformat(),
            "status": "promised",  # Not 'pending' - that was Bug #12
            "approved_by": None,
            "approved_at": None,
            "created_at": now.isoformat(),
            "updated_at": None,
        },
        {
            "id": 2,
            "title": "Project Completion Bonus",
            "description": "Bonus for completing Project X",
            "employee_id": 2,
            "amount": 3000.0,
            "currency": "SAR",
            "bonus_type": "project",
            "conditions": None,
            "promised_date": (now - timedelta(days=45)).isoformat(),
            "due_date": (now + timedelta(days=7)).isoformat(),
            "status": "partial",
            "approved_by": "CEO",
            "approved_at": (now - timedelta(days=10)).isoformat(),
            "created_at": (now - timedelta(days=45)).isoformat(),
            "updated_at": (now - timedelta(days=10)).isoformat(),
        },
    ]
    # Validate against schema
    for bonus in data:
        BonusResponse.model_validate(bonus)
    return data


@pytest.fixture
def sample_employee_logs():
    """Sample employee log data for tests - validated against LogEntryResponse schema.

    Note: Field names changed from original buggy version:
    - 'summary' -> 'title' (Bug #5)
    - 'details' -> 'content'
    - 'logged_at' -> 'occurred_at'
    - Category values must be valid (Bug #7)
    """
    now = datetime.now(timezone.utc)
    data = [
        {
            "id": 1,
            "employee_id": 1,
            "category": "achievement",  # Valid: achievement, issue, feedback, milestone, other
            "title": "Exceeded sales target by 20%",
            "content": "Great performance this quarter - closed 5 major deals",
            "severity": "low",
            "is_positive": True,
            "logged_by": "ceo_agent",
            "occurred_at": now.isoformat(),
            "created_at": now.isoformat(),
        },
        {
            "id": 2,
            "employee_id": 2,
            "category": "issue",  # Valid: not 'performance_review' (Bug #7)
            "title": "Missed deadline on project",
            "content": "Needs follow-up to understand root cause",
            "severity": "medium",  # Valid: low, medium, high - not 'critical' (Bug #7)
            "is_positive": False,
            "logged_by": "ceo_agent",
            "occurred_at": now.isoformat(),
            "created_at": now.isoformat(),
        },
    ]
    # Validate against schema
    for log in data:
        LogEntryResponse.model_validate(log)
    return data


@pytest.fixture
def sample_skills():
    """Sample skill data for tests - validated against SkillResponse schema."""
    now = datetime.now(timezone.utc)
    data = [
        {
            "id": 1,
            "name": "Python",
            "category": "technical",
            "description": "Python programming",
            "is_active": True,
            "created_at": now.isoformat(),
        },
        {
            "id": 2,
            "name": "SQL",
            "category": "technical",
            "description": "Database queries",
            "is_active": True,
            "created_at": now.isoformat(),
        },
        {
            "id": 3,
            "name": "Leadership",
            "category": "soft",
            "description": "Team leadership",
            "is_active": True,
            "created_at": now.isoformat(),
        },
    ]
    # Validate against schema
    for skill in data:
        SkillResponse.model_validate(skill)
    return data


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


def _wrap_paginated(items: list, page_size: int = 50) -> dict:
    """Wrap a list in paginated response format."""
    return {
        "items": items,
        "total": len(items),
        "page": 1,
        "page_size": page_size,
    }


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
    """Configure mock client with common responses.

    All list responses are wrapped in paginated format to match API responses.
    """
    if employees is not None:
        mock_client.set_response("/employees", _wrap_paginated(employees))
    if tasks is not None:
        mock_client.set_response("/tasks", _wrap_paginated(tasks))
    if notes is not None:
        mock_client.set_response("/notes", _wrap_paginated(notes))
    if documents is not None:
        mock_client.set_response("/documents", _wrap_paginated(documents))
    if bonuses is not None:
        mock_client.set_response("/bonuses", _wrap_paginated(bonuses))
    if employee_logs is not None:
        mock_client.set_response("/employee-logs", _wrap_paginated(employee_logs))
    if skills is not None:
        mock_client.set_response("/skills", {"items": skills, "total": len(skills)})
    if loop_status is not None:
        mock_client.set_response("/loops/status", {
            "loops": loop_status,
            "total_runs_today": 0,
            "total_findings_today": 0,
        })
    if findings is not None:
        mock_client.set_response("/loops/findings", _wrap_paginated(findings, page_size=20))
    if loop_runs is not None:
        mock_client.set_response("/loops/runs", _wrap_paginated(loop_runs, page_size=20))
    return mock_client
