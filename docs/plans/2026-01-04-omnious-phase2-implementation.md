# Omnious Agent Phase 2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expand Omnious with additional read tools, knowledge base, and conversation persistence.

**Architecture:** Add 11 new tools following Phase 1 patterns (Pydantic params, BaseTool, ToolRegistry). Create markdown-based knowledge base with index navigation. Add SQLModel persistence for conversation history.

**Tech Stack:** Python 3.11+, Pydantic, SQLModel, nest-asyncio, existing service layer

---

## Prerequisites

Before starting, ensure:
- OpenRouter API key is configured in `.env`
- Phase 1 is complete and all tests pass
- Install: `pip install nest-asyncio`

**IMPORTANT: Virtual Environment**

Always activate the virtual environment before running any commands:
```bash
source venv/bin/activate
```

Then run tests with:
```bash
source venv/bin/activate && pytest tests/agent/ -v
```

Or install packages with:
```bash
source venv/bin/activate && pip install nest-asyncio
```

**Verify these service methods exist with expected signatures:**

```python
# Task 1 - Cashflow (verify CashflowPredictionInput exists or adjust)
from cmd_center.backend.services.cashflow_prediction_service import get_cashflow_prediction_service

# Task 2 - CEO Dashboard
from cmd_center.backend.services.ceo_dashboard_service import get_ceo_dashboard_service

# Task 3 - Email (verify method signatures)
from cmd_center.backend.services.msgraph_email_service import get_msgraph_email_service
# Expected: service.search_emails(query, limit) -> async
# Expected: service.get_emails(folder, limit) -> async

# Task 4 - Skills
from cmd_center.backend.services.skill_service import get_skill_service

# Task 5 - Owner KPIs (verify async)
from cmd_center.backend.services.owner_kpi_service import get_owner_kpi_service

# Task 6 - Documents
from cmd_center.backend.services.document_service import get_document_service

# Task 7 - Bonuses
from cmd_center.backend.services.bonus_service import get_bonus_service

# Task 8 - Reminders
from cmd_center.backend.services.reminder_service import get_reminder_service

# Task 9 - Notes
from cmd_center.backend.services.note_service import get_note_service
```

If any service doesn't exist or has different method signatures, adjust the tool implementation accordingly.

---

## Task 0: Add Async Helper to Base Tools (Critical)

**Files:**
- Modify: `cmd_center/agent/tools/base.py`

**Why:** The current plan uses `asyncio.run()` inside synchronous `execute()` methods. This will crash when called from the Textual TUI because there's already a running event loop. This helper handles both cases.

**Step 1: Add the run_async helper**

```python
# Add to cmd_center/agent/tools/base.py
import asyncio
from typing import Coroutine, TypeVar

T = TypeVar('T')

def run_async(coro: Coroutine[None, None, T]) -> T:
    """Run async code from sync context, handling existing event loops.

    This is needed because Textual TUI runs its own event loop,
    so we can't use asyncio.run() directly.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop - safe to use asyncio.run()
        return asyncio.run(coro)

    # Already in async context - use nest_asyncio
    import nest_asyncio
    nest_asyncio.apply()
    return loop.run_until_complete(coro)
```

**Step 2: Run existing tests to verify no regression**

Run: `pytest tests/agent/ -v`
Expected: All existing tests still pass

**Step 3: Commit**

```bash
git add cmd_center/agent/tools/base.py
git commit -m "feat(agent): add run_async helper for event loop compatibility"
```

---

## Task 1: Add Cashflow Projection Tool

**Files:**
- Create: `cmd_center/agent/tools/financial_tools.py`
- Create: `tests/agent/test_financial_tools.py`
- Modify: `cmd_center/agent/tools/__init__.py`

**Step 1: Write the failing test**

```python
# tests/agent/test_financial_tools.py
"""Tests for financial tools."""

import pytest
from unittest.mock import patch, MagicMock

from cmd_center.agent.tools.financial_tools import GetCashflowProjection, GetCashflowProjectionParams
from cmd_center.agent.tools.base import ToolResult


class TestGetCashflowProjection:
    """Tests for GetCashflowProjection tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = GetCashflowProjection()
        assert tool.name == "get_cashflow_projection"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = GetCashflowProjection()
        assert len(tool.description) > 20

    def test_params_have_months_field(self):
        """Parameters include months field with default."""
        params = GetCashflowProjectionParams()
        assert params.months == 6  # default

    @patch("cmd_center.agent.tools.financial_tools.get_cashflow_prediction_service")
    def test_execute_returns_projection_data(self, mock_get_service):
        """Execute returns cashflow projection data."""
        mock_service = MagicMock()
        mock_result = MagicMock()
        mock_result.monthly_projections = [
            MagicMock(month="2026-01", projected_revenue=100000, projected_expenses=80000)
        ]
        mock_result.summary = MagicMock(total_projected_revenue=600000)
        mock_service.predict_cashflow.return_value = mock_result
        mock_get_service.return_value = mock_service

        tool = GetCashflowProjection()
        params = GetCashflowProjectionParams(months=6)
        result = tool.execute(params)

        assert result.success is True
        assert "projections" in result.data

    @patch("cmd_center.agent.tools.financial_tools.get_cashflow_prediction_service")
    def test_execute_handles_error(self, mock_get_service):
        """Execute handles service errors gracefully."""
        mock_get_service.side_effect = Exception("Service unavailable")

        tool = GetCashflowProjection()
        params = GetCashflowProjectionParams()
        result = tool.execute(params)

        assert result.success is False
        assert "Service unavailable" in result.error
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_financial_tools.py -v`
Expected: FAIL with "cannot import name 'GetCashflowProjection'"

**Step 3: Write minimal implementation**

```python
# cmd_center/agent/tools/financial_tools.py
"""Financial tools for the agent."""

from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult
from ...backend.services.cashflow_prediction_service import get_cashflow_prediction_service
from ...backend.services.cashflow_prediction_service import CashflowPredictionInput


class GetCashflowProjectionParams(BaseModel):
    """Parameters for get_cashflow_projection tool."""
    months: int = Field(
        default=6,
        description="Number of months to project (1-12)"
    )


class GetCashflowProjection(BaseTool):
    """Get cashflow projection for upcoming months."""

    name = "get_cashflow_projection"
    description = "Get projected cashflow for the next N months including revenue, expenses, and net cashflow predictions."
    parameters_model = GetCashflowProjectionParams

    def execute(self, params: GetCashflowProjectionParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_cashflow_prediction_service()
            input_data = CashflowPredictionInput(months=params.months)
            result = service.predict_cashflow(input_data)

            projections = [
                {
                    "month": p.month,
                    "projected_revenue": p.projected_revenue,
                    "projected_expenses": p.projected_expenses,
                    "net_cashflow": p.projected_revenue - p.projected_expenses,
                }
                for p in result.monthly_projections
            ]

            return ToolResult(
                success=True,
                data={
                    "projections": projections,
                    "summary": {
                        "total_projected_revenue": result.summary.total_projected_revenue,
                        "total_projected_expenses": result.summary.total_projected_expenses,
                        "average_monthly_net": result.summary.average_monthly_net,
                    },
                    "months": params.months,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

**Step 4: Register tool in __init__.py**

```python
# Add to cmd_center/agent/tools/__init__.py
from .financial_tools import GetCashflowProjection

# Add to TOOLS list:
GetCashflowProjection,
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/agent/test_financial_tools.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add cmd_center/agent/tools/financial_tools.py tests/agent/test_financial_tools.py cmd_center/agent/tools/__init__.py
git commit -m "feat(agent): add get_cashflow_projection tool"
```

---

## Task 2: Add CEO Dashboard Tool

**Files:**
- Modify: `cmd_center/agent/tools/financial_tools.py`
- Modify: `tests/agent/test_financial_tools.py`

**Step 1: Write the failing test**

```python
# Add to tests/agent/test_financial_tools.py
from cmd_center.agent.tools.financial_tools import GetCEODashboard, GetCEODashboardParams


class TestGetCEODashboard:
    """Tests for GetCEODashboard tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = GetCEODashboard()
        assert tool.name == "get_ceo_dashboard"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = GetCEODashboard()
        assert len(tool.description) > 20

    @patch("cmd_center.agent.tools.financial_tools.get_ceo_dashboard_service")
    def test_execute_returns_dashboard_metrics(self, mock_get_service):
        """Execute returns CEO dashboard metrics."""
        mock_service = MagicMock()
        mock_metrics = MagicMock()
        mock_metrics.total_pipeline_value = 5000000
        mock_metrics.deals_won_this_month = 3
        mock_metrics.deals_lost_this_month = 1
        mock_metrics.active_deals_count = 25
        mock_service.get_dashboard_metrics.return_value = mock_metrics
        mock_get_service.return_value = mock_service

        tool = GetCEODashboard()
        params = GetCEODashboardParams()
        result = tool.execute(params)

        assert result.success is True
        assert "metrics" in result.data

    @patch("cmd_center.agent.tools.financial_tools.get_ceo_dashboard_service")
    def test_execute_handles_error(self, mock_get_service):
        """Execute handles service errors gracefully."""
        mock_get_service.side_effect = Exception("Dashboard unavailable")

        tool = GetCEODashboard()
        params = GetCEODashboardParams()
        result = tool.execute(params)

        assert result.success is False
        assert "Dashboard unavailable" in result.error
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_financial_tools.py::TestGetCEODashboard -v`
Expected: FAIL with "cannot import name 'GetCEODashboard'"

**Step 3: Write minimal implementation**

```python
# Add to cmd_center/agent/tools/financial_tools.py
from ...backend.services.ceo_dashboard_service import get_ceo_dashboard_service


class GetCEODashboardParams(BaseModel):
    """Parameters for get_ceo_dashboard tool."""
    pass  # No parameters needed


class GetCEODashboard(BaseTool):
    """Get CEO dashboard metrics overview."""

    name = "get_ceo_dashboard"
    description = "Get executive dashboard metrics including pipeline value, deals won/lost, revenue trends, and team performance."
    parameters_model = GetCEODashboardParams

    def execute(self, params: GetCEODashboardParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_ceo_dashboard_service()
            metrics = service.get_dashboard_metrics()

            return ToolResult(
                success=True,
                data={
                    "metrics": {
                        "total_pipeline_value": metrics.total_pipeline_value,
                        "deals_won_this_month": metrics.deals_won_this_month,
                        "deals_lost_this_month": metrics.deals_lost_this_month,
                        "active_deals_count": metrics.active_deals_count,
                        "win_rate": metrics.win_rate,
                        "average_deal_size": metrics.average_deal_size,
                        "revenue_this_month": metrics.revenue_this_month,
                        "revenue_target": metrics.revenue_target,
                    }
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

**Step 4: Register tool**

```python
# Add to cmd_center/agent/tools/__init__.py
from .financial_tools import GetCashflowProjection, GetCEODashboard

# Add GetCEODashboard to TOOLS list
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/agent/test_financial_tools.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add cmd_center/agent/tools/financial_tools.py tests/agent/test_financial_tools.py cmd_center/agent/tools/__init__.py
git commit -m "feat(agent): add get_ceo_dashboard tool"
```

---

## Task 3: Add Email Tools (Search and Get)

**Files:**
- Create: `cmd_center/agent/tools/email_tools.py`
- Create: `tests/agent/test_email_tools.py`
- Modify: `cmd_center/agent/tools/__init__.py`

**Step 1: Write the failing tests**

```python
# tests/agent/test_email_tools.py
"""Tests for email tools."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from cmd_center.agent.tools.email_tools import (
    SearchEmails, SearchEmailsParams,
    GetEmails, GetEmailsParams,
)
from cmd_center.agent.tools.base import ToolResult


class TestSearchEmails:
    """Tests for SearchEmails tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = SearchEmails()
        assert tool.name == "search_emails"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = SearchEmails()
        assert len(tool.description) > 20

    def test_params_require_query(self):
        """Parameters require query field."""
        params = SearchEmailsParams(query="project update")
        assert params.query == "project update"

    @patch("cmd_center.agent.tools.email_tools.get_msgraph_email_service")
    def test_execute_returns_email_results(self, mock_get_service):
        """Execute returns email search results."""
        mock_service = MagicMock()
        mock_service.search_emails = AsyncMock(return_value=[
            MagicMock(
                id="1",
                subject="Project Update",
                sender="john@example.com",
                received_at="2026-01-01T10:00:00Z",
                snippet="Here is the update..."
            )
        ])
        mock_get_service.return_value = mock_service

        tool = SearchEmails()
        params = SearchEmailsParams(query="project", limit=10)
        result = tool.execute(params)

        assert result.success is True
        assert "emails" in result.data


class TestGetEmails:
    """Tests for GetEmails tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = GetEmails()
        assert tool.name == "get_emails"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = GetEmails()
        assert len(tool.description) > 20

    @patch("cmd_center.agent.tools.email_tools.get_msgraph_email_service")
    def test_execute_returns_recent_emails(self, mock_get_service):
        """Execute returns recent emails."""
        mock_service = MagicMock()
        mock_service.get_emails = AsyncMock(return_value=[
            MagicMock(
                id="1",
                subject="Meeting Tomorrow",
                sender="boss@example.com",
                received_at="2026-01-04T09:00:00Z",
                snippet="Don't forget..."
            )
        ])
        mock_get_service.return_value = mock_service

        tool = GetEmails()
        params = GetEmailsParams(limit=20)
        result = tool.execute(params)

        assert result.success is True
        assert "emails" in result.data
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_email_tools.py -v`
Expected: FAIL with "No module named 'cmd_center.agent.tools.email_tools'"

**Step 3: Write minimal implementation**

```python
# cmd_center/agent/tools/email_tools.py
"""Email tools for the agent."""

from typing import Optional
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult, run_async
from ...backend.services.msgraph_email_service import get_msgraph_email_service


class SearchEmailsParams(BaseModel):
    """Parameters for search_emails tool."""
    query: str = Field(description="Search query for emails")
    limit: int = Field(default=10, description="Maximum number of results")


class SearchEmails(BaseTool):
    """Search emails by keyword or phrase."""

    name = "search_emails"
    description = "Search through emails using keywords. Returns matching emails with subject, sender, date, and snippet."
    parameters_model = SearchEmailsParams

    def execute(self, params: SearchEmailsParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_msgraph_email_service()
            # Use run_async helper for event loop compatibility
            emails = run_async(service.search_emails(params.query, params.limit))

            emails_data = [
                {
                    "id": e.id,
                    "subject": e.subject,
                    "sender": e.sender,
                    "received_at": str(e.received_at),
                    "snippet": e.snippet[:200] if e.snippet else None,
                }
                for e in emails
            ]

            return ToolResult(
                success=True,
                data={
                    "emails": emails_data,
                    "count": len(emails_data),
                    "query": params.query,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetEmailsParams(BaseModel):
    """Parameters for get_emails tool."""
    limit: int = Field(default=20, description="Maximum number of emails to return")
    folder: Optional[str] = Field(default="inbox", description="Email folder to read from")


class GetEmails(BaseTool):
    """Get recent emails from inbox."""

    name = "get_emails"
    description = "Get recent emails from inbox or specified folder. Returns emails with subject, sender, date, and preview."
    parameters_model = GetEmailsParams

    def execute(self, params: GetEmailsParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_msgraph_email_service()
            # Use run_async helper for event loop compatibility
            emails = run_async(service.get_emails(params.folder, params.limit))

            emails_data = [
                {
                    "id": e.id,
                    "subject": e.subject,
                    "sender": e.sender,
                    "received_at": str(e.received_at),
                    "snippet": e.snippet[:200] if e.snippet else None,
                    "is_read": e.is_read,
                }
                for e in emails
            ]

            return ToolResult(
                success=True,
                data={
                    "emails": emails_data,
                    "count": len(emails_data),
                    "folder": params.folder,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

**Step 4: Register tools**

```python
# Add to cmd_center/agent/tools/__init__.py
from .email_tools import SearchEmails, GetEmails

# Add to TOOLS list
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/agent/test_email_tools.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add cmd_center/agent/tools/email_tools.py tests/agent/test_email_tools.py cmd_center/agent/tools/__init__.py
git commit -m "feat(agent): add search_emails and get_emails tools"
```

---

## Task 4: Add Employee Skills Tool

**Files:**
- Modify: `cmd_center/agent/tools/employee_tools.py`
- Create: `tests/agent/test_employee_tools.py`

**Step 1: Write the failing test**

```python
# tests/agent/test_employee_tools.py
"""Tests for employee tools."""

import pytest
from unittest.mock import patch, MagicMock

from cmd_center.agent.tools.employee_tools import (
    GetEmployees, GetEmployeesParams,
    GetEmployeeDetails, GetEmployeeDetailsParams,
    GetEmployeeSkills, GetEmployeeSkillsParams,
)
from cmd_center.agent.tools.base import ToolResult


class TestGetEmployeeSkills:
    """Tests for GetEmployeeSkills tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = GetEmployeeSkills()
        assert tool.name == "get_employee_skills"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = GetEmployeeSkills()
        assert len(tool.description) > 20

    def test_params_require_employee_id(self):
        """Parameters require employee_id field."""
        params = GetEmployeeSkillsParams(employee_id=5)
        assert params.employee_id == 5

    @patch("cmd_center.agent.tools.employee_tools.get_skill_service")
    def test_execute_returns_skill_data(self, mock_get_service):
        """Execute returns employee skill data."""
        mock_service = MagicMock()
        mock_skill_card = MagicMock()
        mock_skill_card.employee_name = "John Doe"
        mock_skill_card.skills = [
            MagicMock(skill_name="Python", rating=4, category="Technical")
        ]
        mock_service.get_employee_skill_card.return_value = mock_skill_card
        mock_get_service.return_value = mock_service

        tool = GetEmployeeSkills()
        params = GetEmployeeSkillsParams(employee_id=5)
        result = tool.execute(params)

        assert result.success is True
        assert "skills" in result.data

    @patch("cmd_center.agent.tools.employee_tools.get_skill_service")
    def test_execute_handles_not_found(self, mock_get_service):
        """Execute handles employee not found."""
        mock_service = MagicMock()
        mock_service.get_employee_skill_card.return_value = None
        mock_get_service.return_value = mock_service

        tool = GetEmployeeSkills()
        params = GetEmployeeSkillsParams(employee_id=999)
        result = tool.execute(params)

        assert result.success is False
        assert "not found" in result.error.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_employee_tools.py::TestGetEmployeeSkills -v`
Expected: FAIL with "cannot import name 'GetEmployeeSkills'"

**Step 3: Write minimal implementation**

```python
# Add to cmd_center/agent/tools/employee_tools.py
from ...backend.services.skill_service import get_skill_service


class GetEmployeeSkillsParams(BaseModel):
    """Parameters for get_employee_skills tool."""
    employee_id: int = Field(description="The ID of the employee")


class GetEmployeeSkills(BaseTool):
    """Get skills and ratings for an employee."""

    name = "get_employee_skills"
    description = "Get an employee's skill card including all skills, ratings, and categories. Use to understand team capabilities."
    parameters_model = GetEmployeeSkillsParams

    def execute(self, params: GetEmployeeSkillsParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_skill_service()
            skill_card = service.get_employee_skill_card(params.employee_id)

            if skill_card is None:
                return ToolResult(
                    success=False,
                    error=f"Employee {params.employee_id} not found"
                )

            skills_data = [
                {
                    "skill_name": s.skill_name,
                    "rating": s.rating,
                    "category": s.category,
                }
                for s in skill_card.skills
            ]

            return ToolResult(
                success=True,
                data={
                    "employee_name": skill_card.employee_name,
                    "employee_id": params.employee_id,
                    "skills": skills_data,
                    "skill_count": len(skills_data),
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

**Step 4: Register tool**

```python
# Add to cmd_center/agent/tools/__init__.py
from .employee_tools import GetEmployees, GetEmployeeDetails, GetEmployeeSkills
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/agent/test_employee_tools.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add cmd_center/agent/tools/employee_tools.py tests/agent/test_employee_tools.py cmd_center/agent/tools/__init__.py
git commit -m "feat(agent): add get_employee_skills tool"
```

---

## Task 5: Add Owner KPIs Tool

**Files:**
- Modify: `cmd_center/agent/tools/employee_tools.py`
- Modify: `tests/agent/test_employee_tools.py`

**Step 1: Write the failing test**

```python
# Add to tests/agent/test_employee_tools.py
from unittest.mock import AsyncMock  # Add AsyncMock import at top

from cmd_center.agent.tools.employee_tools import GetOwnerKPIs, GetOwnerKPIsParams


class TestGetOwnerKPIs:
    """Tests for GetOwnerKPIs tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = GetOwnerKPIs()
        assert tool.name == "get_owner_kpis"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = GetOwnerKPIs()
        assert len(tool.description) > 20

    @patch("cmd_center.agent.tools.employee_tools.get_owner_kpi_service")
    def test_execute_returns_kpi_data(self, mock_get_service):
        """Execute returns owner KPI data."""
        mock_service = MagicMock()
        mock_service.get_owner_kpis = AsyncMock(return_value=[
            MagicMock(
                owner_name="John Doe",
                deals_count=10,
                total_value=500000,
                win_rate=0.35
            )
        ])
        mock_get_service.return_value = mock_service

        tool = GetOwnerKPIs()
        params = GetOwnerKPIsParams()
        result = tool.execute(params)

        assert result.success is True
        assert "kpis" in result.data
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_employee_tools.py::TestGetOwnerKPIs -v`
Expected: FAIL with "cannot import name 'GetOwnerKPIs'"

**Step 3: Write minimal implementation**

```python
# Add to cmd_center/agent/tools/employee_tools.py
from .base import run_async  # Add to existing imports
from ...backend.services.owner_kpi_service import get_owner_kpi_service


class GetOwnerKPIsParams(BaseModel):
    """Parameters for get_owner_kpis tool."""
    pass  # No parameters - gets all owners


class GetOwnerKPIs(BaseTool):
    """Get KPI metrics for all deal owners."""

    name = "get_owner_kpis"
    description = "Get key performance indicators for all deal owners including deals count, value, and win rate."
    parameters_model = GetOwnerKPIsParams

    def execute(self, params: GetOwnerKPIsParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_owner_kpi_service()
            # Use run_async helper for event loop compatibility
            kpis = run_async(service.get_owner_kpis())

            kpis_data = [
                {
                    "owner_name": k.owner_name,
                    "deals_count": k.deals_count,
                    "total_value": k.total_value,
                    "win_rate": k.win_rate,
                    "average_deal_size": k.average_deal_size,
                }
                for k in kpis
            ]

            return ToolResult(
                success=True,
                data={
                    "kpis": kpis_data,
                    "count": len(kpis_data),
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

**Step 4: Register tool and run tests**

**Step 5: Commit**

```bash
git add cmd_center/agent/tools/employee_tools.py tests/agent/test_employee_tools.py cmd_center/agent/tools/__init__.py
git commit -m "feat(agent): add get_owner_kpis tool"
```

---

## Task 6: Add Document Expiry Tool

**Files:**
- Create: `cmd_center/agent/tools/document_tools.py`
- Create: `tests/agent/test_document_tools.py`
- Modify: `cmd_center/agent/tools/__init__.py`

**Step 1: Write the failing test**

```python
# tests/agent/test_document_tools.py
"""Tests for document tools."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import date

from cmd_center.agent.tools.document_tools import GetExpiringDocuments, GetExpiringDocumentsParams
from cmd_center.agent.tools.base import ToolResult


class TestGetExpiringDocuments:
    """Tests for GetExpiringDocuments tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = GetExpiringDocuments()
        assert tool.name == "get_expiring_documents"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = GetExpiringDocuments()
        assert len(tool.description) > 20

    def test_params_have_days_field(self):
        """Parameters have days_until_expiry field."""
        params = GetExpiringDocumentsParams(days_until_expiry=30)
        assert params.days_until_expiry == 30

    @patch("cmd_center.agent.tools.document_tools.get_document_service")
    def test_execute_returns_expiring_documents(self, mock_get_service):
        """Execute returns documents expiring soon."""
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.documents = [
            MagicMock(
                id=1,
                title="Safety Certificate",
                employee_name="John Doe",
                expiry_date=date(2026, 2, 1),
                document_type="certificate"
            )
        ]
        mock_response.total = 1
        mock_service.get_documents.return_value = mock_response
        mock_get_service.return_value = mock_service

        tool = GetExpiringDocuments()
        params = GetExpiringDocumentsParams(days_until_expiry=30)
        result = tool.execute(params)

        assert result.success is True
        assert "documents" in result.data
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_document_tools.py -v`
Expected: FAIL with "No module named 'cmd_center.agent.tools.document_tools'"

**Step 3: Write minimal implementation**

```python
# cmd_center/agent/tools/document_tools.py
"""Document tools for the agent."""

from datetime import date, timedelta
from typing import Optional
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult
from ...backend.services.document_service import get_document_service, DocumentFilters


class GetExpiringDocumentsParams(BaseModel):
    """Parameters for get_expiring_documents tool."""
    days_until_expiry: int = Field(
        default=30,
        description="Find documents expiring within this many days"
    )
    employee_id: Optional[int] = Field(
        default=None,
        description="Filter by specific employee ID"
    )


class GetExpiringDocuments(BaseTool):
    """Get documents that are expiring soon."""

    name = "get_expiring_documents"
    description = "Get documents (certificates, IDs, permits) that are expiring within a specified number of days. Use to track compliance."
    parameters_model = GetExpiringDocumentsParams

    def execute(self, params: GetExpiringDocumentsParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_document_service()
            expiry_date = date.today() + timedelta(days=params.days_until_expiry)

            filters = DocumentFilters(
                expiry_before=expiry_date,
                employee_id=params.employee_id,
            )
            response = service.get_documents(filters)

            documents_data = [
                {
                    "id": d.id,
                    "title": d.title,
                    "employee_name": d.employee_name,
                    "expiry_date": str(d.expiry_date),
                    "document_type": d.document_type,
                    "days_until_expiry": (d.expiry_date - date.today()).days,
                }
                for d in response.documents
            ]

            return ToolResult(
                success=True,
                data={
                    "documents": documents_data,
                    "count": len(documents_data),
                    "days_checked": params.days_until_expiry,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

**Step 4: Register tool**

**Step 5: Run test to verify it passes**

**Step 6: Commit**

```bash
git add cmd_center/agent/tools/document_tools.py tests/agent/test_document_tools.py cmd_center/agent/tools/__init__.py
git commit -m "feat(agent): add get_expiring_documents tool"
```

---

## Task 7: Add Unpaid Bonuses Tool

**Files:**
- Create: `cmd_center/agent/tools/hr_tools.py`
- Create: `tests/agent/test_hr_tools.py`
- Modify: `cmd_center/agent/tools/__init__.py`

**Step 1: Write the failing test**

```python
# tests/agent/test_hr_tools.py
"""Tests for HR tools."""

import pytest
from unittest.mock import patch, MagicMock

from cmd_center.agent.tools.hr_tools import GetUnpaidBonuses, GetUnpaidBonusesParams
from cmd_center.agent.tools.base import ToolResult


class TestGetUnpaidBonuses:
    """Tests for GetUnpaidBonuses tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = GetUnpaidBonuses()
        assert tool.name == "get_unpaid_bonuses"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = GetUnpaidBonuses()
        assert len(tool.description) > 20

    @patch("cmd_center.agent.tools.hr_tools.get_bonus_service")
    def test_execute_returns_unpaid_bonuses(self, mock_get_service):
        """Execute returns unpaid bonus records."""
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.bonuses = [
            MagicMock(
                id=1,
                employee_name="John Doe",
                amount=5000,
                reason="Q4 Performance",
                status="pending"
            )
        ]
        mock_response.total = 1
        mock_service.get_bonuses.return_value = mock_response
        mock_get_service.return_value = mock_service

        tool = GetUnpaidBonuses()
        params = GetUnpaidBonusesParams()
        result = tool.execute(params)

        assert result.success is True
        assert "bonuses" in result.data
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_hr_tools.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# cmd_center/agent/tools/hr_tools.py
"""HR tools for the agent."""

from typing import Optional
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult
from ...backend.services.bonus_service import get_bonus_service, BonusFilters


class GetUnpaidBonusesParams(BaseModel):
    """Parameters for get_unpaid_bonuses tool."""
    employee_id: Optional[int] = Field(
        default=None,
        description="Filter by specific employee ID"
    )


class GetUnpaidBonuses(BaseTool):
    """Get bonuses that haven't been paid yet."""

    name = "get_unpaid_bonuses"
    description = "Get pending/unpaid bonus records. Use to track outstanding compensation."
    parameters_model = GetUnpaidBonusesParams

    def execute(self, params: GetUnpaidBonusesParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_bonus_service()
            filters = BonusFilters(
                status="pending",
                employee_id=params.employee_id,
            )
            response = service.get_bonuses(filters)

            bonuses_data = [
                {
                    "id": b.id,
                    "employee_name": b.employee_name,
                    "amount": b.amount,
                    "reason": b.reason,
                    "status": b.status,
                    "created_at": str(b.created_at) if b.created_at else None,
                }
                for b in response.bonuses
            ]

            return ToolResult(
                success=True,
                data={
                    "bonuses": bonuses_data,
                    "count": len(bonuses_data),
                    "total_amount": sum(b.amount for b in response.bonuses),
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

**Step 4-6: Register, test, commit**

```bash
git commit -m "feat(agent): add get_unpaid_bonuses tool"
```

---

## Task 8: Add Pending Reminders Tool

**Files:**
- Modify: `cmd_center/agent/tools/task_tools.py`
- Create: `tests/agent/test_task_tools.py`

**Step 1: Write the failing test**

```python
# tests/agent/test_task_tools.py
"""Tests for task tools."""

import pytest
from unittest.mock import patch, MagicMock

from cmd_center.agent.tools.task_tools import (
    GetTasks, GetTasksParams,
    GetOverdueTasks, GetOverdueTasksParams,
    GetPendingReminders, GetPendingRemindersParams,
)
from cmd_center.agent.tools.base import ToolResult


class TestGetPendingReminders:
    """Tests for GetPendingReminders tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = GetPendingReminders()
        assert tool.name == "get_pending_reminders"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = GetPendingReminders()
        assert len(tool.description) > 20

    @patch("cmd_center.agent.tools.task_tools.get_reminder_service")
    def test_execute_returns_pending_reminders(self, mock_get_service):
        """Execute returns pending reminders."""
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.reminders = [
            MagicMock(
                id=1,
                title="Follow up with client",
                due_date="2026-01-05",
                priority="high"
            )
        ]
        mock_service.get_reminders.return_value = mock_response
        mock_get_service.return_value = mock_service

        tool = GetPendingReminders()
        params = GetPendingRemindersParams()
        result = tool.execute(params)

        assert result.success is True
        assert "reminders" in result.data
```

**Step 2: Run test to verify it fails**

**Step 3: Write minimal implementation**

```python
# Add to cmd_center/agent/tools/task_tools.py
from ...backend.services.reminder_service import get_reminder_service, ReminderFilters


class GetPendingRemindersParams(BaseModel):
    """Parameters for get_pending_reminders tool."""
    limit: int = Field(default=20, description="Maximum reminders to return")


class GetPendingReminders(BaseTool):
    """Get pending reminders."""

    name = "get_pending_reminders"
    description = "Get pending reminders that haven't been completed. Use to track what needs follow-up."
    parameters_model = GetPendingRemindersParams

    def execute(self, params: GetPendingRemindersParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_reminder_service()
            filters = ReminderFilters(status="pending", limit=params.limit)
            response = service.get_reminders(filters)

            reminders_data = [
                {
                    "id": r.id,
                    "title": r.title,
                    "due_date": str(r.due_date) if r.due_date else None,
                    "priority": r.priority,
                    "related_deal_id": r.related_deal_id,
                }
                for r in response.reminders
            ]

            return ToolResult(
                success=True,
                data={
                    "reminders": reminders_data,
                    "count": len(reminders_data),
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

**Step 4-6: Register, test, commit**

```bash
git commit -m "feat(agent): add get_pending_reminders tool"
```

---

## Task 9: Add Notes Tool

**Files:**
- Modify: `cmd_center/agent/tools/task_tools.py`
- Modify: `tests/agent/test_task_tools.py`

**Step 1: Write the failing test**

```python
# Add to tests/agent/test_task_tools.py
from cmd_center.agent.tools.task_tools import GetNotes, GetNotesParams


class TestGetNotes:
    """Tests for GetNotes tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = GetNotes()
        assert tool.name == "get_notes"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = GetNotes()
        assert len(tool.description) > 20

    @patch("cmd_center.agent.tools.task_tools.get_note_service")
    def test_execute_returns_notes(self, mock_get_service):
        """Execute returns notes."""
        mock_service = MagicMock()
        mock_response = MagicMock()
        mock_response.notes = [
            MagicMock(
                id=1,
                content="Important meeting notes",
                author="John Doe",
                created_at="2026-01-03T14:00:00Z"
            )
        ]
        mock_service.get_notes.return_value = mock_response
        mock_get_service.return_value = mock_service

        tool = GetNotes()
        params = GetNotesParams(limit=10)
        result = tool.execute(params)

        assert result.success is True
        assert "notes" in result.data
```

**Step 2-6: Implement, test, commit**

```python
# Add to cmd_center/agent/tools/task_tools.py
from ...backend.services.note_service import get_note_service, NoteFilters


class GetNotesParams(BaseModel):
    """Parameters for get_notes tool."""
    deal_id: Optional[int] = Field(default=None, description="Filter by deal ID")
    limit: int = Field(default=20, description="Maximum notes to return")


class GetNotes(BaseTool):
    """Get notes, optionally filtered by deal."""

    name = "get_notes"
    description = "Get notes from the system, optionally filtered by deal. Use to review history and context."
    parameters_model = GetNotesParams

    def execute(self, params: GetNotesParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_note_service()
            filters = NoteFilters(deal_id=params.deal_id, limit=params.limit)
            response = service.get_notes(filters)

            notes_data = [
                {
                    "id": n.id,
                    "content": n.content[:500] if n.content else None,
                    "author": n.author,
                    "created_at": str(n.created_at) if n.created_at else None,
                    "deal_id": n.deal_id,
                }
                for n in response.notes
            ]

            return ToolResult(
                success=True,
                data={
                    "notes": notes_data,
                    "count": len(notes_data),
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

```bash
git commit -m "feat(agent): add get_notes tool"
```

---

## Task 10: Create Knowledge Base Structure

**Files:**
- Create: `cmd_center/agent/knowledge/_index.md`
- Create: `cmd_center/agent/knowledge/company_overview.md`
- Create: `cmd_center/agent/knowledge/company_structure.md`
- Create: `cmd_center/agent/knowledge/products_services.md`
- Create: `cmd_center/agent/knowledge/employees_rolecard.md`
- Create: `cmd_center/agent/knowledge/procedures.md`
- Create: `cmd_center/agent/knowledge/workflows.md`
- Create: `cmd_center/agent/knowledge/strategy.md`

**Step 1: Create knowledge directory and index**

```markdown
<!-- cmd_center/agent/knowledge/_index.md -->
# Omnious Knowledge Base Index

This index helps Omnious navigate company knowledge. Each file covers a specific domain.

## Available Knowledge Files

| File | Description | When to Use |
|------|-------------|-------------|
| company_overview.md | Company background, mission, history | General company questions |
| company_structure.md | Org chart, departments, reporting | "Who reports to..." questions |
| products_services.md | What GypTech offers | Product/service inquiries |
| employees_rolecard.md | Employee roles and responsibilities | "What does X do?" |
| procedures.md | Internal procedures | "How do we..." questions |
| workflows.md | Business workflows | Process questions |
| strategy.md | Company strategy and goals | Strategic direction questions |

## Usage

To find information, read the relevant file based on the query topic.
```

**Step 2: Create all 7 knowledge files with placeholders**

```markdown
<!-- cmd_center/agent/knowledge/company_overview.md -->
# Company Overview

## About GypTech

[Company description to be filled in]

## Mission

[Mission statement]

## History

[Key milestones]
```

```markdown
<!-- cmd_center/agent/knowledge/company_structure.md -->
# Company Structure

## Departments

[Department list]

## Leadership

[Leadership team]

## Reporting Structure

[Org chart description]
```

```markdown
<!-- cmd_center/agent/knowledge/products_services.md -->
# Products and Services

## Core Products

[Product list]

## Services Offered

[Services list]
```

```markdown
<!-- cmd_center/agent/knowledge/employees_rolecard.md -->
# Employee Role Cards

## Leadership Team

[Leadership roles and responsibilities]

## Department Heads

[Department head roles]

## Key Personnel

[Key employee responsibilities]
```

```markdown
<!-- cmd_center/agent/knowledge/procedures.md -->
# Company Procedures

## Sales Procedures

[Sales process steps]

## Project Procedures

[Project management procedures]

## HR Procedures

[HR procedures]
```

```markdown
<!-- cmd_center/agent/knowledge/workflows.md -->
# Business Workflows

## Deal Workflow

[Deal progression workflow]

## Approval Workflow

[Approval process]

## Invoice Workflow

[Invoicing process]
```

```markdown
<!-- cmd_center/agent/knowledge/strategy.md -->
# Company Strategy

## Vision

[Company vision]

## Strategic Goals

[Key strategic goals]

## Growth Plans

[Growth strategy]
```

**Step 3: Commit**

```bash
git add cmd_center/agent/knowledge/
git commit -m "feat(agent): add knowledge base structure with 7 topic files"
```

---

## Task 11: Add Knowledge Tool

**Files:**
- Create: `cmd_center/agent/tools/knowledge_tools.py`
- Create: `tests/agent/test_knowledge_tools.py`
- Modify: `cmd_center/agent/tools/__init__.py`

**Step 1: Write the failing test**

```python
# tests/agent/test_knowledge_tools.py
"""Tests for knowledge tools."""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from cmd_center.agent.tools.knowledge_tools import ReadKnowledge, ReadKnowledgeParams
from cmd_center.agent.tools.base import ToolResult


class TestReadKnowledge:
    """Tests for ReadKnowledge tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = ReadKnowledge()
        assert tool.name == "read_knowledge"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = ReadKnowledge()
        assert len(tool.description) > 20

    def test_params_require_topic(self):
        """Parameters require topic field."""
        params = ReadKnowledgeParams(topic="company_overview")
        assert params.topic == "company_overview"

    def test_execute_returns_knowledge_content(self):
        """Execute returns knowledge file content."""
        mock_content = "# Company Overview\n\nGypTech is a leading..."

        with patch("builtins.open", mock_open(read_data=mock_content)):
            with patch.object(Path, "exists", return_value=True):
                tool = ReadKnowledge()
                params = ReadKnowledgeParams(topic="company_overview")
                result = tool.execute(params)

                assert result.success is True
                assert "content" in result.data

    def test_execute_handles_missing_file(self):
        """Execute handles missing knowledge file."""
        with patch.object(Path, "exists", return_value=False):
            tool = ReadKnowledge()
            params = ReadKnowledgeParams(topic="nonexistent")
            result = tool.execute(params)

            assert result.success is False
            assert "not found" in result.error.lower()

    def test_list_topics_returns_available_files(self):
        """List topics returns available knowledge files."""
        tool = ReadKnowledge()
        params = ReadKnowledgeParams(topic="_index")

        with patch("builtins.open", mock_open(read_data="# Index\n\n| File |")):
            with patch.object(Path, "exists", return_value=True):
                result = tool.execute(params)
                assert result.success is True
```

**Step 2: Run test to verify it fails**

**Step 3: Write minimal implementation**

```python
# cmd_center/agent/tools/knowledge_tools.py
"""Knowledge base tools for the agent."""

from pathlib import Path
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult


KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"


class ReadKnowledgeParams(BaseModel):
    """Parameters for read_knowledge tool."""
    topic: str = Field(
        description="Knowledge topic to read. Use '_index' to see available topics."
    )


class ReadKnowledge(BaseTool):
    """Read from the company knowledge base."""

    name = "read_knowledge"
    description = "Read company knowledge on a specific topic. Use topic='_index' to see all available topics. Topics include: company_overview, company_structure, products_services, employees_rolecard, procedures, workflows, strategy."
    parameters_model = ReadKnowledgeParams

    def execute(self, params: ReadKnowledgeParams) -> ToolResult:
        """Execute the tool."""
        try:
            # Sanitize topic name
            topic = params.topic.replace("/", "").replace("\\", "")
            if not topic.endswith(".md"):
                topic = f"{topic}.md"

            file_path = KNOWLEDGE_DIR / topic

            if not file_path.exists():
                available = [f.stem for f in KNOWLEDGE_DIR.glob("*.md")]
                return ToolResult(
                    success=False,
                    error=f"Knowledge topic '{params.topic}' not found. Available topics: {available}"
                )

            content = file_path.read_text()

            return ToolResult(
                success=True,
                data={
                    "topic": params.topic,
                    "content": content,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

**Step 4-6: Register, test, commit**

```bash
git commit -m "feat(agent): add read_knowledge tool for knowledge base"
```

---

## Task 12: Create Persistence Models

**Files:**
- Create: `cmd_center/agent/persistence/__init__.py`
- Create: `cmd_center/agent/persistence/models.py`
- Create: `tests/agent/test_persistence_models.py`

**Step 1: Write the failing test**

```python
# tests/agent/test_persistence_models.py
"""Tests for persistence models."""

import pytest
from datetime import datetime

from cmd_center.agent.persistence.models import AgentConversation, AgentMessage


class TestAgentConversation:
    """Tests for AgentConversation model."""

    def test_has_required_fields(self):
        """Model has all required fields."""
        conv = AgentConversation(title="Test Conversation")
        assert conv.title == "Test Conversation"
        assert conv.id is None  # Not yet persisted
        assert conv.created_at is not None
        assert conv.updated_at is not None

    def test_has_messages_relationship(self):
        """Model has messages relationship."""
        conv = AgentConversation(title="Test")
        assert hasattr(conv, "messages")


class TestAgentMessage:
    """Tests for AgentMessage model."""

    def test_has_required_fields(self):
        """Model has all required fields."""
        msg = AgentMessage(
            conversation_id=1,
            role="user",
            content="Hello"
        )
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.conversation_id == 1
        assert msg.created_at is not None

    def test_role_accepts_valid_values(self):
        """Role accepts user, assistant, system."""
        for role in ["user", "assistant", "system"]:
            msg = AgentMessage(conversation_id=1, role=role, content="test")
            assert msg.role == role

    def test_has_optional_tool_fields(self):
        """Model has optional tool-related fields."""
        msg = AgentMessage(
            conversation_id=1,
            role="assistant",
            content=None,
            tool_calls=[{"name": "get_deals", "args": {}}]
        )
        assert msg.tool_calls is not None
```

**Step 2: Run test to verify it fails**

**Step 3: Write minimal implementation**

```python
# cmd_center/agent/persistence/__init__.py
"""Persistence package for agent conversations."""

from .models import AgentConversation, AgentMessage
from .conversation_store import ConversationStore

__all__ = ["AgentConversation", "AgentMessage", "ConversationStore"]
```

```python
# cmd_center/agent/persistence/models.py
"""SQLModel models for agent conversation persistence."""

from datetime import datetime
from typing import Optional, List, Any
from sqlmodel import SQLModel, Field, Relationship
import json


class AgentConversation(SQLModel, table=True):
    """A conversation with the agent."""

    __tablename__ = "agent_conversations"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(default="New Conversation")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship to messages
    messages: List["AgentMessage"] = Relationship(back_populates="conversation")


class AgentMessage(SQLModel, table=True):
    """A message in an agent conversation."""

    __tablename__ = "agent_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="agent_conversations.id")
    role: str = Field(description="user, assistant, or system")
    content: Optional[str] = Field(default=None)
    tool_calls_json: Optional[str] = Field(default=None)
    tool_results_json: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship back to conversation
    conversation: Optional[AgentConversation] = Relationship(back_populates="messages")

    @property
    def tool_calls(self) -> Optional[List[Any]]:
        """Get tool calls as parsed JSON."""
        if self.tool_calls_json:
            return json.loads(self.tool_calls_json)
        return None

    @tool_calls.setter
    def tool_calls(self, value: Optional[List[Any]]) -> None:
        """Set tool calls from list."""
        if value is not None:
            self.tool_calls_json = json.dumps(value)
        else:
            self.tool_calls_json = None

    @property
    def tool_results(self) -> Optional[List[Any]]:
        """Get tool results as parsed JSON."""
        if self.tool_results_json:
            return json.loads(self.tool_results_json)
        return None

    @tool_results.setter
    def tool_results(self, value: Optional[List[Any]]) -> None:
        """Set tool results from list."""
        if value is not None:
            self.tool_results_json = json.dumps(value)
        else:
            self.tool_results_json = None
```

**Step 4: Register models with database**

Add the imports to `cmd_center/backend/db.py` (or wherever models are registered):

```python
# Add at the top with other imports
from cmd_center.agent.persistence.models import AgentConversation, AgentMessage
```

The tables will be created automatically when `SQLModel.metadata.create_all(engine)` is called on app startup.

Alternatively, if using Alembic, create a migration:
```bash
alembic revision --autogenerate -m "Add agent conversation tables"
alembic upgrade head
```

**Step 5: Run tests**

**Step 6: Commit**

```bash
git add cmd_center/agent/persistence/ tests/agent/test_persistence_models.py cmd_center/backend/db.py
git commit -m "feat(agent): add AgentConversation and AgentMessage models"
```

---

## Task 13: Create ConversationStore

**Files:**
- Create: `cmd_center/agent/persistence/conversation_store.py`
- Create: `tests/agent/test_conversation_store.py`

**Step 1: Write the failing test**

```python
# tests/agent/test_conversation_store.py
"""Tests for ConversationStore."""

import pytest
from unittest.mock import MagicMock, patch

from cmd_center.agent.persistence.conversation_store import ConversationStore
from cmd_center.agent.persistence.models import AgentConversation, AgentMessage


class TestConversationStore:
    """Tests for ConversationStore."""

    def test_create_conversation(self):
        """Can create a new conversation."""
        with patch("cmd_center.agent.persistence.conversation_store.Session") as MockSession:
            mock_session = MagicMock()
            MockSession.return_value.__enter__ = MagicMock(return_value=mock_session)
            MockSession.return_value.__exit__ = MagicMock(return_value=False)

            store = ConversationStore()
            conv = store.create_conversation("Test Chat")

            assert conv.title == "Test Chat"
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    def test_add_message(self):
        """Can add a message to conversation."""
        with patch("cmd_center.agent.persistence.conversation_store.Session") as MockSession:
            mock_session = MagicMock()
            MockSession.return_value.__enter__ = MagicMock(return_value=mock_session)
            MockSession.return_value.__exit__ = MagicMock(return_value=False)

            store = ConversationStore()
            msg = store.add_message(
                conversation_id=1,
                role="user",
                content="Hello"
            )

            assert msg.role == "user"
            assert msg.content == "Hello"
            mock_session.add.assert_called()

    def test_get_conversation_messages(self):
        """Can retrieve messages for a conversation."""
        with patch("cmd_center.agent.persistence.conversation_store.Session") as MockSession:
            mock_session = MagicMock()
            mock_session.exec.return_value.all.return_value = [
                AgentMessage(id=1, conversation_id=1, role="user", content="Hi")
            ]
            MockSession.return_value.__enter__ = MagicMock(return_value=mock_session)
            MockSession.return_value.__exit__ = MagicMock(return_value=False)

            store = ConversationStore()
            messages = store.get_messages(conversation_id=1)

            assert len(messages) == 1
            assert messages[0].content == "Hi"

    def test_list_conversations(self):
        """Can list all conversations."""
        with patch("cmd_center.agent.persistence.conversation_store.Session") as MockSession:
            mock_session = MagicMock()
            mock_session.exec.return_value.all.return_value = [
                AgentConversation(id=1, title="Chat 1"),
                AgentConversation(id=2, title="Chat 2"),
            ]
            MockSession.return_value.__enter__ = MagicMock(return_value=mock_session)
            MockSession.return_value.__exit__ = MagicMock(return_value=False)

            store = ConversationStore()
            convs = store.list_conversations()

            assert len(convs) == 2
```

**Step 2: Run test to verify it fails**

**Step 3: Write minimal implementation**

```python
# cmd_center/agent/persistence/conversation_store.py
"""Conversation storage for the agent."""

from typing import List, Optional
from sqlmodel import Session, select

from .models import AgentConversation, AgentMessage
from ...backend.db import engine  # Adjust import path as needed


class ConversationStore:
    """Store for agent conversations."""

    def create_conversation(self, title: str = "New Conversation") -> AgentConversation:
        """Create a new conversation."""
        with Session(engine) as session:
            conv = AgentConversation(title=title)
            session.add(conv)
            session.commit()
            session.refresh(conv)
            return conv

    def get_conversation(self, conversation_id: int) -> Optional[AgentConversation]:
        """Get a conversation by ID."""
        with Session(engine) as session:
            return session.get(AgentConversation, conversation_id)

    def list_conversations(self, limit: int = 50) -> List[AgentConversation]:
        """List recent conversations."""
        with Session(engine) as session:
            statement = select(AgentConversation).order_by(
                AgentConversation.updated_at.desc()
            ).limit(limit)
            return session.exec(statement).all()

    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: Optional[str] = None,
        tool_calls: Optional[list] = None,
        tool_results: Optional[list] = None,
    ) -> AgentMessage:
        """Add a message to a conversation."""
        with Session(engine) as session:
            msg = AgentMessage(
                conversation_id=conversation_id,
                role=role,
                content=content,
            )
            if tool_calls:
                msg.tool_calls = tool_calls
            if tool_results:
                msg.tool_results = tool_results

            session.add(msg)

            # Update conversation's updated_at
            conv = session.get(AgentConversation, conversation_id)
            if conv:
                from datetime import datetime
                conv.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(msg)
            return msg

    def get_messages(self, conversation_id: int) -> List[AgentMessage]:
        """Get all messages for a conversation."""
        with Session(engine) as session:
            statement = select(AgentMessage).where(
                AgentMessage.conversation_id == conversation_id
            ).order_by(AgentMessage.created_at)
            return session.exec(statement).all()

    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation and its messages."""
        with Session(engine) as session:
            conv = session.get(AgentConversation, conversation_id)
            if not conv:
                return False

            # Delete messages first
            statement = select(AgentMessage).where(
                AgentMessage.conversation_id == conversation_id
            )
            for msg in session.exec(statement).all():
                session.delete(msg)

            session.delete(conv)
            session.commit()
            return True
```

**Step 4-6: Test, commit**

```bash
git commit -m "feat(agent): add ConversationStore for persistence"
```

---

## Task 14: Wire Persistence to Agent

**Files:**
- Modify: `cmd_center/agent/core/agent.py`
- Modify: `tests/agent/test_agent_core.py`

**Step 1: Write the failing test**

```python
# Add to tests/agent/test_agent_core.py
class TestAgentPersistence:
    """Tests for agent conversation persistence."""

    def test_agent_can_save_conversation(self):
        """Agent can persist conversation to database."""
        with patch("cmd_center.agent.core.agent.ConversationStore") as MockStore:
            mock_store = MagicMock()
            mock_conv = MagicMock(id=1)
            mock_store.create_conversation.return_value = mock_conv
            MockStore.return_value = mock_store

            agent = OmniousAgent(persist=True)
            agent.start_new_conversation("Test Chat")

            mock_store.create_conversation.assert_called_with("Test Chat")
            assert agent.conversation_id == 1

    def test_agent_saves_messages_when_persisting(self):
        """Agent saves messages to database when persist=True."""
        with patch("cmd_center.agent.core.agent.ConversationStore") as MockStore:
            mock_store = MagicMock()
            mock_conv = MagicMock(id=1)
            mock_store.create_conversation.return_value = mock_conv
            MockStore.return_value = mock_store

            agent = OmniousAgent(persist=True)
            agent.start_new_conversation()
            agent._add_to_history("user", "Hello")

            mock_store.add_message.assert_called()

    def test_agent_can_load_conversation(self):
        """Agent can load existing conversation."""
        with patch("cmd_center.agent.core.agent.ConversationStore") as MockStore:
            mock_store = MagicMock()
            mock_store.get_messages.return_value = [
                MagicMock(role="user", content="Previous message")
            ]
            MockStore.return_value = mock_store

            agent = OmniousAgent(persist=True)
            agent.load_conversation(1)

            assert len(agent.conversation_history) == 1
```

**Step 2: Run test to verify it fails**

**Step 3: Modify agent.py to support persistence**

Update the `OmniousAgent.__init__` method with complete code:

```python
# cmd_center/agent/core/agent.py

from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..persistence.conversation_store import ConversationStore


class OmniousAgent:
    """The Omnious AI Agent."""

    def __init__(self, persist: bool = False):
        """Initialize the agent.

        Args:
            persist: If True, save conversations to database
        """
        from ...backend.integrations.config import get_settings

        settings = get_settings()
        self.api_key = settings.openrouter_api_key
        self.api_url = settings.openrouter_api_url or "https://openrouter.ai/api/v1"
        self.model = settings.llm_model or "anthropic/claude-sonnet-4"

        self.tools = ToolRegistry()
        self.metrics = MetricsTracker()
        self.conversation_history: List[dict] = []

        # Persistence support (Phase 2)
        self.persist = persist
        self.conversation_id: Optional[int] = None
        self._store: Optional["ConversationStore"] = None
        if persist:
            from ..persistence.conversation_store import ConversationStore
            self._store = ConversationStore()

        self._register_tools()

    def start_new_conversation(self, title: str = "New Conversation") -> int:
        """Start a new conversation, optionally persisting.

        Returns:
            Conversation ID if persisting, 0 otherwise.
        """
        self.clear_conversation()
        if self._store:
            conv = self._store.create_conversation(title)
            self.conversation_id = conv.id
            return conv.id
        return 0

    def load_conversation(self, conversation_id: int) -> None:
        """Load an existing conversation from database.

        Args:
            conversation_id: ID of conversation to load.

        Raises:
            ValueError: If persistence not enabled.
        """
        if not self._store:
            raise ValueError("Persistence not enabled")

        messages = self._store.get_messages(conversation_id)
        self.conversation_id = conversation_id
        self.conversation_history = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.content  # Skip tool-only messages for history
        ]

    def _add_to_history(self, role: str, content: str) -> None:
        """Add message to history (and persist if enabled)."""
        self.conversation_history.append({"role": role, "content": content})
        if self._store and self.conversation_id:
            self._store.add_message(
                conversation_id=self.conversation_id,
                role=role,
                content=content
            )
```

**Step 4-6: Test, commit**

```bash
git commit -m "feat(agent): wire persistence to agent with save/load"
```

---

## Task 15: Update Tool Registration and Golden Tests

**Files:**
- Modify: `cmd_center/agent/tools/__init__.py`
- Modify: `tests/agent/test_golden_qa.py`

**Step 1: Ensure all new tools are registered**

```python
# cmd_center/agent/tools/__init__.py
"""Agent tools package."""

from .base import BaseTool, ToolResult, run_async
from .registry import ToolRegistry

# Pipeline tools
from .pipeline_tools import (
    GetOverdueDeals,
    GetStuckDeals,
    GetDealDetails,
    GetDealNotes,
)

# Task tools
from .task_tools import (
    GetTasks,
    GetOverdueTasks,
    GetPendingReminders,
    GetNotes,
)

# Employee tools
from .employee_tools import (
    GetEmployees,
    GetEmployeeDetails,
    GetEmployeeSkills,
    GetOwnerKPIs,
)

# Financial tools
from .financial_tools import (
    GetCashflowProjection,
    GetCEODashboard,
)

# Email tools
from .email_tools import (
    SearchEmails,
    GetEmails,
)

# Document tools
from .document_tools import (
    GetExpiringDocuments,
)

# HR tools
from .hr_tools import (
    GetUnpaidBonuses,
)

# Knowledge tools
from .knowledge_tools import (
    ReadKnowledge,
)


# All tools to register
TOOLS = [
    # Phase 1 tools (8)
    GetOverdueDeals,
    GetStuckDeals,
    GetDealDetails,
    GetDealNotes,
    GetTasks,
    GetOverdueTasks,
    GetEmployees,
    GetEmployeeDetails,
    # Phase 2 tools (11)
    GetCashflowProjection,
    GetCEODashboard,
    SearchEmails,
    GetEmails,
    GetEmployeeSkills,
    GetOwnerKPIs,
    GetExpiringDocuments,
    GetUnpaidBonuses,
    GetPendingReminders,
    GetNotes,
    ReadKnowledge,
]


def get_tool_registry() -> ToolRegistry:
    """Get a configured tool registry with all tools."""
    registry = ToolRegistry()
    for tool_class in TOOLS:
        registry.register(tool_class())
    return registry
```

**Step 2: Add Phase 2 golden test scenarios**

```python
# Update tests/agent/test_golden_qa.py

PHASE_1_GOLDEN_SCENARIOS = [
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

PHASE_2_GOLDEN_SCENARIOS = [
    {
        "id": "cashflow_question",
        "query": "What's our cashflow projection for the next 3 months?",
        "expected_tools": ["get_cashflow_projection"],
    },
    {
        "id": "ceo_dashboard",
        "query": "Give me the executive summary",
        "expected_tools": ["get_ceo_dashboard"],
    },
    {
        "id": "email_search",
        "query": "Find emails about the Aramco contract",
        "expected_tools": ["search_emails"],
    },
    {
        "id": "recent_emails",
        "query": "What are my latest emails?",
        "expected_tools": ["get_emails"],
    },
    {
        "id": "employee_skills",
        "query": "What are Ahmed's skills?",
        "expected_tools": ["get_employee_skills"],
    },
    {
        "id": "team_performance",
        "query": "How is the sales team performing?",
        "expected_tools": ["get_owner_kpis"],
    },
    {
        "id": "expiring_documents",
        "query": "What documents are expiring this month?",
        "expected_tools": ["get_expiring_documents"],
    },
    {
        "id": "unpaid_bonuses",
        "query": "Are there any unpaid bonuses?",
        "expected_tools": ["get_unpaid_bonuses"],
    },
    {
        "id": "pending_reminders",
        "query": "What reminders do I have pending?",
        "expected_tools": ["get_pending_reminders"],
    },
    {
        "id": "company_knowledge",
        "query": "What products does GypTech offer?",
        "expected_tools": ["read_knowledge"],
    },
]

# Combine all scenarios
GOLDEN_SCENARIOS = PHASE_1_GOLDEN_SCENARIOS + PHASE_2_GOLDEN_SCENARIOS


def test_all_phase2_tools_registered(self):
    """Verify all Phase 2 tools are registered."""
    agent = OmniousAgent()
    tools = agent.tools.list_tools()

    expected_tools = [
        # Phase 1 (8)
        "get_overdue_deals",
        "get_stuck_deals",
        "get_deal_details",
        "get_deal_notes",
        "get_tasks",
        "get_overdue_tasks",
        "get_employees",
        "get_employee_details",
        # Phase 2 (11)
        "get_cashflow_projection",
        "get_ceo_dashboard",
        "search_emails",
        "get_emails",
        "get_employee_skills",
        "get_owner_kpis",
        "get_expiring_documents",
        "get_unpaid_bonuses",
        "get_pending_reminders",
        "get_notes",
        "read_knowledge",
    ]

    tool_names = [t["name"] for t in tools]
    for expected in expected_tools:
        assert expected in tool_names, f"Missing tool: {expected}"

    assert len(tools) == 19, f"Expected 19 tools, got {len(tools)}"
```

**Step 3: Run all tests**

Run: `pytest tests/agent/ -v`
Expected: All tests pass

**Step 4: Commit**

```bash
git add cmd_center/agent/tools/__init__.py tests/agent/test_golden_qa.py
git commit -m "feat(agent): register all Phase 2 tools (19 total) and add golden scenarios"
```

---

## Summary

**Phase 2 adds:**
- 11 new read tools:
  - Financial: get_cashflow_projection, get_ceo_dashboard
  - Email: search_emails, get_emails
  - Employee: get_employee_skills, get_owner_kpis
  - Compliance: get_expiring_documents, get_unpaid_bonuses
  - Tasks: get_pending_reminders, get_notes
  - Knowledge: read_knowledge
- Knowledge base with 7 markdown files
- Conversation persistence with SQLModel (AgentConversation, AgentMessage tables)

**Total tools after Phase 2:** 19 (8 from Phase 1 + 11 new)

**New capabilities:**
- Query financial projections and CEO dashboard
- Search and read emails
- Look up employee skills and owner KPIs
- Track expiring documents and unpaid bonuses
- View pending reminders and notes
- Access company knowledge base
- Persist and reload conversation history

**New files:** ~20
**New tests:** ~60
**Tasks:** 16 (including Task 0)
