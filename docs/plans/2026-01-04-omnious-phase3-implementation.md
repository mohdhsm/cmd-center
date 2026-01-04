# Omnious AI Agent Phase 3: Write Operations Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add write operation tools with confirmation flow, allowing Omnious to create tasks, notes, reminders, send emails, and update Pipedrive deals - all requiring human confirmation before execution.

**Architecture:** Write tools return `PendingAction` objects instead of executing immediately. Agent tracks pending actions and checks for user confirmation on each message. Confirmed actions are executed and logged to the intervention table.

**Tech Stack:** Python, Pydantic, SQLModel, Pipedrive API, Microsoft Graph API

---

## Task 0: Add PendingAction Dataclass to Base

**Files:**
- Modify: `cmd_center/agent/tools/base.py`
- Test: `tests/agent/test_pending_action.py`

**Step 1: Write the failing test**

Create `tests/agent/test_pending_action.py`:

```python
"""Tests for PendingAction dataclass."""

import pytest
from datetime import datetime, timezone

from cmd_center.agent.tools.base import PendingAction


class TestPendingAction:
    """Tests for PendingAction dataclass."""

    def test_pending_action_creation(self):
        """PendingAction can be created with required fields."""
        action = PendingAction(
            tool_name="request_create_task",
            preview="Create task: Follow up with client",
            payload={"title": "Follow up with client", "priority": "high"},
        )

        assert action.tool_name == "request_create_task"
        assert action.preview == "Create task: Follow up with client"
        assert action.payload["title"] == "Follow up with client"
        assert action.created_at is not None

    def test_pending_action_has_timestamp(self):
        """PendingAction automatically sets created_at timestamp."""
        before = datetime.now(timezone.utc)
        action = PendingAction(
            tool_name="test",
            preview="test",
            payload={},
        )
        after = datetime.now(timezone.utc)

        assert before <= action.created_at <= after

    def test_pending_action_equality(self):
        """Two PendingActions with same data are equal."""
        ts = datetime.now(timezone.utc)
        action1 = PendingAction(
            tool_name="test",
            preview="test",
            payload={"a": 1},
            created_at=ts,
        )
        action2 = PendingAction(
            tool_name="test",
            preview="test",
            payload={"a": 1},
            created_at=ts,
        )

        assert action1 == action2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_pending_action.py -v`
Expected: FAIL with "cannot import name 'PendingAction'"

**Step 3: Write minimal implementation**

Add to `cmd_center/agent/tools/base.py`:

```python
from datetime import datetime, timezone

@dataclass
class PendingAction:
    """Represents a write action awaiting user confirmation.

    Write tools return this instead of executing immediately.
    User must confirm before the action is executed.
    """
    tool_name: str
    preview: str  # Human-readable preview of what will happen
    payload: dict  # Data needed to execute the action
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/agent/test_pending_action.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add cmd_center/agent/tools/base.py tests/agent/test_pending_action.py
git commit -m "feat(agent): add PendingAction dataclass for write confirmations"
```

---

## Task 1: Add Confirmation Flow to Agent

**Files:**
- Modify: `cmd_center/agent/core/agent.py`
- Test: `tests/agent/test_confirmation_flow.py`

**Step 1: Write the failing test**

Create `tests/agent/test_confirmation_flow.py`:

```python
"""Tests for agent confirmation flow."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from cmd_center.agent.core.agent import OmniousAgent
from cmd_center.agent.tools.base import PendingAction, ToolResult


class TestConfirmationFlow:
    """Tests for pending action confirmation flow."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    def test_agent_has_pending_action_attribute(self, agent):
        """Agent has pending_action attribute."""
        assert hasattr(agent, 'pending_action')
        assert agent.pending_action is None

    def test_set_pending_action(self, agent):
        """Can set a pending action."""
        action = PendingAction(
            tool_name="request_create_task",
            preview="Create task: Test",
            payload={"title": "Test"},
        )
        agent.pending_action = action

        assert agent.pending_action is not None
        assert agent.pending_action.tool_name == "request_create_task"

    def test_clear_pending_action(self, agent):
        """Can clear pending action."""
        action = PendingAction(
            tool_name="test",
            preview="test",
            payload={},
        )
        agent.pending_action = action
        agent.pending_action = None

        assert agent.pending_action is None

    def test_has_pending_action_method(self, agent):
        """has_pending_action returns correct status."""
        assert agent.has_pending_action() is False

        action = PendingAction(
            tool_name="test",
            preview="test",
            payload={},
        )
        agent.pending_action = action

        assert agent.has_pending_action() is True

    def test_get_pending_preview(self, agent):
        """get_pending_preview returns formatted preview."""
        assert agent.get_pending_preview() is None

        action = PendingAction(
            tool_name="request_create_task",
            preview="Create task: Follow up with client\nPriority: high",
            payload={"title": "Follow up"},
        )
        agent.pending_action = action

        preview = agent.get_pending_preview()
        assert "Create task" in preview
        assert "Follow up" in preview


class TestConfirmationDetection:
    """Tests for detecting user confirmation."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    def test_is_confirmation_yes(self, agent):
        """Detects affirmative confirmations."""
        yes_messages = ["yes", "Yes", "YES", "y", "Y", "confirm", "ok", "proceed", "do it", "go ahead"]

        for msg in yes_messages:
            assert agent._is_confirmation(msg) == "yes", f"Failed for: {msg}"

    def test_is_confirmation_no(self, agent):
        """Detects negative confirmations."""
        no_messages = ["no", "No", "NO", "n", "N", "cancel", "stop", "abort", "never mind"]

        for msg in no_messages:
            assert agent._is_confirmation(msg) == "no", f"Failed for: {msg}"

    def test_is_confirmation_none(self, agent):
        """Returns None for non-confirmation messages."""
        other_messages = [
            "What deals need attention?",
            "Show me overdue tasks",
            "Hello",
        ]

        for msg in other_messages:
            assert agent._is_confirmation(msg) is None, f"Failed for: {msg}"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_confirmation_flow.py -v`
Expected: FAIL with "OmniousAgent has no attribute 'pending_action'"

**Step 3: Write minimal implementation**

Modify `cmd_center/agent/core/agent.py`:

```python
# Add import
from ..tools.base import PendingAction

class OmniousAgent:
    # Add to __init__:
    self.pending_action: Optional[PendingAction] = None

    def has_pending_action(self) -> bool:
        """Check if there's a pending action awaiting confirmation."""
        return self.pending_action is not None

    def get_pending_preview(self) -> Optional[str]:
        """Get preview of pending action for display."""
        if self.pending_action is None:
            return None
        return self.pending_action.preview

    def _is_confirmation(self, message: str) -> Optional[str]:
        """Check if message is a confirmation response.

        Args:
            message: User message

        Returns:
            "yes" if affirmative, "no" if negative, None otherwise
        """
        msg_lower = message.strip().lower()

        yes_words = {"yes", "y", "confirm", "ok", "proceed", "do it", "go ahead", "sure", "yep", "yeah"}
        no_words = {"no", "n", "cancel", "stop", "abort", "never mind", "nope", "nah"}

        if msg_lower in yes_words:
            return "yes"
        if msg_lower in no_words:
            return "no"

        return None
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/agent/test_confirmation_flow.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add cmd_center/agent/core/agent.py tests/agent/test_confirmation_flow.py
git commit -m "feat(agent): add confirmation flow state management"
```

---

## Task 2: Add Pipedrive Write Methods to Client

**Files:**
- Modify: `cmd_center/backend/integrations/pipedrive_client.py`
- Test: `tests/test_pipedrive_client.py`

**Step 1: Write the failing test**

Add to existing test file or create `tests/test_pipedrive_write.py`:

```python
"""Tests for Pipedrive write operations."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from cmd_center.backend.integrations.pipedrive_client import PipedriveClient


class TestPipedriveWriteOperations:
    """Tests for Pipedrive write methods."""

    @pytest.fixture
    def client(self):
        """Create Pipedrive client."""
        return PipedriveClient(
            api_token="test-token",
            api_url="https://api.pipedrive.com/v1",
            api_url_v2="https://api.pipedrive.com/v2"
        )

    @pytest.mark.asyncio
    async def test_update_deal(self, client):
        """update_deal sends PUT request with correct payload."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 123, "title": "Updated Deal"}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'put', new_callable=AsyncMock) as mock_put:
            mock_put.return_value = mock_response

            result = await client.update_deal(123, title="Updated Deal", status="won")

            assert result is not None
            assert result["id"] == 123
            mock_put.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_deal_note(self, client):
        """add_deal_note sends POST request with correct payload."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"id": 456, "content": "Test note"}
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await client.add_deal_note(123, "Test note")

            assert result is not None
            assert result["content"] == "Test note"
            mock_post.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipedrive_write.py -v`
Expected: FAIL with "PipedriveClient has no attribute 'update_deal'"

**Step 3: Write minimal implementation**

Add to `cmd_center/backend/integrations/pipedrive_client.py`:

```python
async def _put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Make PUT request to Pipedrive API."""
    params = {"api_token": self.api_token}
    url = f"{self.api_url}/{endpoint}"
    response = await self.client.put(url, params=params, json=data)
    response.raise_for_status()
    return response.json()

async def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Make POST request to Pipedrive API."""
    params = {"api_token": self.api_token}
    url = f"{self.api_url}/{endpoint}"
    response = await self.client.post(url, params=params, json=data)
    response.raise_for_status()
    return response.json()

async def update_deal(
    self,
    deal_id: int,
    title: Optional[str] = None,
    status: Optional[str] = None,
    stage_id: Optional[int] = None,
    owner_id: Optional[int] = None,
    value: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """Update a deal in Pipedrive.

    Args:
        deal_id: ID of the deal to update
        title: New deal title
        status: New status (open, won, lost, deleted)
        stage_id: New stage ID
        owner_id: New owner user ID
        value: New deal value

    Returns:
        Updated deal data or None on failure
    """
    data = {}
    if title is not None:
        data["title"] = title
    if status is not None:
        data["status"] = status
    if stage_id is not None:
        data["stage_id"] = stage_id
    if owner_id is not None:
        data["user_id"] = owner_id
    if value is not None:
        data["value"] = value

    if not data:
        return None

    result = await self._put(f"deals/{deal_id}", data)

    if result.get("success") and result.get("data"):
        return result["data"]
    return None

async def add_deal_note(
    self,
    deal_id: int,
    content: str,
    pinned: bool = False,
) -> Optional[Dict[str, Any]]:
    """Add a note to a deal.

    Args:
        deal_id: ID of the deal
        content: Note content (can contain HTML)
        pinned: Whether to pin the note

    Returns:
        Created note data or None on failure
    """
    data = {
        "deal_id": deal_id,
        "content": content,
        "pinned_to_deal_flag": 1 if pinned else 0,
    }

    result = await self._post("notes", data)

    if result.get("success") and result.get("data"):
        return result["data"]
    return None
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipedrive_write.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add cmd_center/backend/integrations/pipedrive_client.py tests/test_pipedrive_write.py
git commit -m "feat(pipedrive): add update_deal and add_deal_note methods"
```

---

## Task 3: Create Write Tools Module

**Files:**
- Create: `cmd_center/agent/tools/write_tools.py`
- Test: `tests/agent/test_write_tools.py`

**Step 1: Write the failing test**

Create `tests/agent/test_write_tools.py`:

```python
"""Tests for agent write tools."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from cmd_center.agent.tools.write_tools import (
    RequestCreateTask,
    RequestCreateNote,
    RequestCreateReminder,
    RequestSendEmail,
    RequestUpdateDeal,
    RequestAddDealNote,
)
from cmd_center.agent.tools.base import ToolResult, PendingAction


class TestRequestCreateTask:
    """Tests for RequestCreateTask tool."""

    def test_tool_metadata(self):
        """Tool has correct metadata."""
        tool = RequestCreateTask()
        assert tool.name == "request_create_task"
        assert "task" in tool.description.lower()

    def test_returns_pending_action(self):
        """Tool returns PendingAction instead of executing."""
        tool = RequestCreateTask()
        result = tool.parse_and_execute({
            "title": "Follow up with client",
            "priority": "high",
        })

        assert result.success is True
        assert isinstance(result.data, dict)
        assert "pending_action" in result.data
        assert result.data["pending_action"]["tool_name"] == "request_create_task"
        assert "Follow up" in result.data["pending_action"]["preview"]

    def test_preview_includes_key_fields(self):
        """Preview includes title, priority, assignee if provided."""
        tool = RequestCreateTask()
        result = tool.parse_and_execute({
            "title": "Important task",
            "priority": "critical",
            "assignee_employee_id": 5,
        })

        preview = result.data["pending_action"]["preview"]
        assert "Important task" in preview
        assert "critical" in preview.lower()


class TestRequestCreateNote:
    """Tests for RequestCreateNote tool."""

    def test_tool_metadata(self):
        """Tool has correct metadata."""
        tool = RequestCreateNote()
        assert tool.name == "request_create_note"
        assert "note" in tool.description.lower()

    def test_returns_pending_action(self):
        """Tool returns PendingAction for note creation."""
        tool = RequestCreateNote()
        result = tool.parse_and_execute({
            "content": "Meeting notes: discussed Q1 targets",
            "target_type": "deal",
            "target_id": 123,
        })

        assert result.success is True
        assert "pending_action" in result.data
        assert "Meeting notes" in result.data["pending_action"]["preview"]


class TestRequestSendEmail:
    """Tests for RequestSendEmail tool."""

    def test_tool_metadata(self):
        """Tool has correct metadata."""
        tool = RequestSendEmail()
        assert tool.name == "request_send_email"
        assert "email" in tool.description.lower()

    def test_returns_pending_action(self):
        """Tool returns PendingAction for email sending."""
        tool = RequestSendEmail()
        result = tool.parse_and_execute({
            "to": ["client@example.com"],
            "subject": "Follow-up on proposal",
            "body": "Dear Client, following up on our discussion...",
        })

        assert result.success is True
        assert "pending_action" in result.data
        preview = result.data["pending_action"]["preview"]
        assert "client@example.com" in preview
        assert "Follow-up" in preview


class TestRequestUpdateDeal:
    """Tests for RequestUpdateDeal tool."""

    def test_tool_metadata(self):
        """Tool has correct metadata."""
        tool = RequestUpdateDeal()
        assert tool.name == "request_update_deal"

    def test_returns_pending_action(self):
        """Tool returns PendingAction for deal update."""
        tool = RequestUpdateDeal()
        result = tool.parse_and_execute({
            "deal_id": 123,
            "status": "won",
        })

        assert result.success is True
        assert "pending_action" in result.data
        assert "123" in result.data["pending_action"]["preview"]
        assert "won" in result.data["pending_action"]["preview"].lower()


class TestRequestAddDealNote:
    """Tests for RequestAddDealNote tool."""

    def test_tool_metadata(self):
        """Tool has correct metadata."""
        tool = RequestAddDealNote()
        assert tool.name == "request_add_deal_note"

    def test_returns_pending_action(self):
        """Tool returns PendingAction for adding deal note."""
        tool = RequestAddDealNote()
        result = tool.parse_and_execute({
            "deal_id": 123,
            "content": "Called client, they're interested",
        })

        assert result.success is True
        assert "pending_action" in result.data
        assert "123" in result.data["pending_action"]["preview"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_write_tools.py -v`
Expected: FAIL with "cannot import name 'RequestCreateTask'"

**Step 3: Write minimal implementation**

Create `cmd_center/agent/tools/write_tools.py`:

```python
"""Write tools for agent - all require user confirmation before execution."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult, PendingAction


# ==================== Parameter Models ====================

class CreateTaskParams(BaseModel):
    """Parameters for creating a task."""
    title: str = Field(description="Task title")
    description: Optional[str] = Field(default=None, description="Task description")
    assignee_employee_id: Optional[int] = Field(default=None, description="Employee ID to assign task to")
    priority: str = Field(default="normal", description="Priority: low, normal, high, critical")
    due_at: Optional[str] = Field(default=None, description="Due date in ISO format")
    target_type: Optional[str] = Field(default=None, description="Entity type to link: deal, employee")
    target_id: Optional[int] = Field(default=None, description="Entity ID to link to")


class CreateNoteParams(BaseModel):
    """Parameters for creating an internal note."""
    content: str = Field(description="Note content")
    target_type: Optional[str] = Field(default=None, description="Entity type to link")
    target_id: Optional[int] = Field(default=None, description="Entity ID to link to")
    pinned: bool = Field(default=False, description="Whether to pin the note")


class CreateReminderParams(BaseModel):
    """Parameters for creating a reminder."""
    target_type: str = Field(description="Entity type: task, note, deal")
    target_id: int = Field(description="Entity ID")
    remind_at: str = Field(description="When to remind in ISO format")
    message: Optional[str] = Field(default=None, description="Reminder message")
    channel: str = Field(default="app", description="Channel: app, email, sms")


class SendEmailParams(BaseModel):
    """Parameters for sending an email."""
    to: List[str] = Field(description="Recipient email addresses")
    subject: str = Field(description="Email subject")
    body: str = Field(description="Email body (HTML supported)")
    cc: Optional[List[str]] = Field(default=None, description="CC recipients")
    from_mailbox: str = Field(default="mohammed@gyptech.com.sa", description="Sender mailbox")


class UpdateDealParams(BaseModel):
    """Parameters for updating a Pipedrive deal."""
    deal_id: int = Field(description="Deal ID to update")
    title: Optional[str] = Field(default=None, description="New deal title")
    status: Optional[str] = Field(default=None, description="Status: open, won, lost")
    stage_id: Optional[int] = Field(default=None, description="New stage ID")
    value: Optional[float] = Field(default=None, description="New deal value")


class AddDealNoteParams(BaseModel):
    """Parameters for adding a note to a Pipedrive deal."""
    deal_id: int = Field(description="Deal ID to add note to")
    content: str = Field(description="Note content")
    pinned: bool = Field(default=False, description="Whether to pin the note")


# ==================== Write Tools ====================

class RequestCreateTask(BaseTool):
    """Request to create a task - requires user confirmation."""

    name = "request_create_task"
    description = "Request to create a new task. Returns a preview for user confirmation."
    parameters_model = CreateTaskParams

    def execute(self, params: CreateTaskParams) -> ToolResult:
        """Generate preview for task creation."""
        preview_lines = [
            f"**Create Task**",
            f"Title: {params.title}",
            f"Priority: {params.priority}",
        ]
        if params.description:
            preview_lines.append(f"Description: {params.description[:100]}...")
        if params.assignee_employee_id:
            preview_lines.append(f"Assignee ID: {params.assignee_employee_id}")
        if params.due_at:
            preview_lines.append(f"Due: {params.due_at}")
        if params.target_type and params.target_id:
            preview_lines.append(f"Linked to: {params.target_type} #{params.target_id}")

        preview_lines.append("\nSay 'yes' to confirm or 'no' to cancel.")

        pending = PendingAction(
            tool_name=self.name,
            preview="\n".join(preview_lines),
            payload=params.model_dump(),
        )

        return ToolResult(
            success=True,
            data={
                "pending_action": {
                    "tool_name": pending.tool_name,
                    "preview": pending.preview,
                    "payload": pending.payload,
                }
            }
        )


class RequestCreateNote(BaseTool):
    """Request to create an internal note - requires user confirmation."""

    name = "request_create_note"
    description = "Request to create an internal note. Returns a preview for user confirmation."
    parameters_model = CreateNoteParams

    def execute(self, params: CreateNoteParams) -> ToolResult:
        """Generate preview for note creation."""
        content_preview = params.content[:200] + "..." if len(params.content) > 200 else params.content

        preview_lines = [
            f"**Create Note**",
            f"Content: {content_preview}",
        ]
        if params.target_type and params.target_id:
            preview_lines.append(f"Linked to: {params.target_type} #{params.target_id}")
        if params.pinned:
            preview_lines.append("Pinned: Yes")

        preview_lines.append("\nSay 'yes' to confirm or 'no' to cancel.")

        pending = PendingAction(
            tool_name=self.name,
            preview="\n".join(preview_lines),
            payload=params.model_dump(),
        )

        return ToolResult(
            success=True,
            data={
                "pending_action": {
                    "tool_name": pending.tool_name,
                    "preview": pending.preview,
                    "payload": pending.payload,
                }
            }
        )


class RequestCreateReminder(BaseTool):
    """Request to create a reminder - requires user confirmation."""

    name = "request_create_reminder"
    description = "Request to create a reminder for a task, note, or deal. Returns a preview for user confirmation."
    parameters_model = CreateReminderParams

    def execute(self, params: CreateReminderParams) -> ToolResult:
        """Generate preview for reminder creation."""
        preview_lines = [
            f"**Create Reminder**",
            f"For: {params.target_type} #{params.target_id}",
            f"When: {params.remind_at}",
            f"Channel: {params.channel}",
        ]
        if params.message:
            preview_lines.append(f"Message: {params.message}")

        preview_lines.append("\nSay 'yes' to confirm or 'no' to cancel.")

        pending = PendingAction(
            tool_name=self.name,
            preview="\n".join(preview_lines),
            payload=params.model_dump(),
        )

        return ToolResult(
            success=True,
            data={
                "pending_action": {
                    "tool_name": pending.tool_name,
                    "preview": pending.preview,
                    "payload": pending.payload,
                }
            }
        )


class RequestSendEmail(BaseTool):
    """Request to send an email - requires user confirmation."""

    name = "request_send_email"
    description = "Request to send an email. Returns a preview for user confirmation."
    parameters_model = SendEmailParams

    def execute(self, params: SendEmailParams) -> ToolResult:
        """Generate preview for email sending."""
        body_preview = params.body[:300] + "..." if len(params.body) > 300 else params.body

        preview_lines = [
            f"**Send Email**",
            f"To: {', '.join(params.to)}",
            f"Subject: {params.subject}",
            f"Body:\n{body_preview}",
        ]
        if params.cc:
            preview_lines.insert(2, f"CC: {', '.join(params.cc)}")

        preview_lines.append("\nSay 'yes' to confirm or 'no' to cancel.")

        pending = PendingAction(
            tool_name=self.name,
            preview="\n".join(preview_lines),
            payload=params.model_dump(),
        )

        return ToolResult(
            success=True,
            data={
                "pending_action": {
                    "tool_name": pending.tool_name,
                    "preview": pending.preview,
                    "payload": pending.payload,
                }
            }
        )


class RequestUpdateDeal(BaseTool):
    """Request to update a Pipedrive deal - requires user confirmation."""

    name = "request_update_deal"
    description = "Request to update a Pipedrive deal. Returns a preview for user confirmation."
    parameters_model = UpdateDealParams

    def execute(self, params: UpdateDealParams) -> ToolResult:
        """Generate preview for deal update."""
        preview_lines = [
            f"**Update Pipedrive Deal #{params.deal_id}**",
        ]
        if params.title:
            preview_lines.append(f"New Title: {params.title}")
        if params.status:
            preview_lines.append(f"New Status: {params.status}")
        if params.stage_id:
            preview_lines.append(f"New Stage ID: {params.stage_id}")
        if params.value:
            preview_lines.append(f"New Value: ${params.value:,.2f}")

        preview_lines.append("\nSay 'yes' to confirm or 'no' to cancel.")

        pending = PendingAction(
            tool_name=self.name,
            preview="\n".join(preview_lines),
            payload=params.model_dump(),
        )

        return ToolResult(
            success=True,
            data={
                "pending_action": {
                    "tool_name": pending.tool_name,
                    "preview": pending.preview,
                    "payload": pending.payload,
                }
            }
        )


class RequestAddDealNote(BaseTool):
    """Request to add a note to a Pipedrive deal - requires user confirmation."""

    name = "request_add_deal_note"
    description = "Request to add a note to a Pipedrive deal. Returns a preview for user confirmation."
    parameters_model = AddDealNoteParams

    def execute(self, params: AddDealNoteParams) -> ToolResult:
        """Generate preview for deal note."""
        content_preview = params.content[:200] + "..." if len(params.content) > 200 else params.content

        preview_lines = [
            f"**Add Note to Deal #{params.deal_id}**",
            f"Content: {content_preview}",
        ]
        if params.pinned:
            preview_lines.append("Pinned: Yes")

        preview_lines.append("\nSay 'yes' to confirm or 'no' to cancel.")

        pending = PendingAction(
            tool_name=self.name,
            preview="\n".join(preview_lines),
            payload=params.model_dump(),
        )

        return ToolResult(
            success=True,
            data={
                "pending_action": {
                    "tool_name": pending.tool_name,
                    "preview": pending.preview,
                    "payload": pending.payload,
                }
            }
        )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/agent/test_write_tools.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add cmd_center/agent/tools/write_tools.py tests/agent/test_write_tools.py
git commit -m "feat(agent): add write tools with confirmation flow"
```

---

## Task 4: Create Action Executor Service

**Files:**
- Create: `cmd_center/agent/core/executor.py`
- Test: `tests/agent/test_executor.py`

**Step 1: Write the failing test**

Create `tests/agent/test_executor.py`:

```python
"""Tests for action executor service."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from cmd_center.agent.core.executor import ActionExecutor
from cmd_center.agent.tools.base import PendingAction


class TestActionExecutor:
    """Tests for ActionExecutor service."""

    @pytest.fixture
    def executor(self):
        """Create executor instance."""
        return ActionExecutor(actor="omnious")

    def test_executor_has_execute_method(self, executor):
        """Executor has execute method."""
        assert hasattr(executor, 'execute')
        assert callable(executor.execute)

    @pytest.mark.asyncio
    async def test_execute_create_task(self, executor):
        """Executor can create tasks."""
        action = PendingAction(
            tool_name="request_create_task",
            preview="Create task",
            payload={
                "title": "Test task",
                "priority": "high",
            },
        )

        with patch('cmd_center.agent.core.executor.TaskService') as mock_service:
            mock_instance = MagicMock()
            mock_instance.create_task.return_value = MagicMock(id=1, title="Test task")
            mock_service.return_value = mock_instance

            result = await executor.execute(action)

            assert result["success"] is True
            assert result["action"] == "task_created"

    @pytest.mark.asyncio
    async def test_execute_logs_intervention(self, executor):
        """Executor logs intervention for confirmed action."""
        action = PendingAction(
            tool_name="request_create_task",
            preview="Create task",
            payload={
                "title": "Test task",
                "priority": "normal",
            },
        )

        with patch('cmd_center.agent.core.executor.TaskService') as mock_service:
            mock_instance = MagicMock()
            mock_instance.create_task.return_value = MagicMock(id=1)
            mock_service.return_value = mock_instance

            with patch('cmd_center.agent.core.executor.log_action') as mock_log:
                result = await executor.execute(action)

                mock_log.assert_called_once()
                call_args = mock_log.call_args
                assert call_args.kwargs["actor"] == "omnious"
                assert call_args.kwargs["action_type"] == "agent_confirmed_action"

    @pytest.mark.asyncio
    async def test_execute_unknown_tool_fails(self, executor):
        """Executor returns error for unknown tool."""
        action = PendingAction(
            tool_name="unknown_tool",
            preview="Unknown",
            payload={},
        )

        result = await executor.execute(action)

        assert result["success"] is False
        assert "unknown" in result["error"].lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_executor.py -v`
Expected: FAIL with "cannot import name 'ActionExecutor'"

**Step 3: Write minimal implementation**

Create `cmd_center/agent/core/executor.py`:

```python
"""Action executor for confirmed write operations."""

from typing import Any, Dict

from ..tools.base import PendingAction
from ...backend.services.intervention_service import log_action
from ...backend.services.task_service import TaskService
from ...backend.services.note_service import NoteService
from ...backend.services.reminder_service import ReminderService
from ...backend.models.task_models import TaskCreate
from ...backend.models.note_models import NoteCreate
from ...backend.models.reminder_models import ReminderCreate


class ActionExecutor:
    """Executes confirmed write actions and logs interventions."""

    def __init__(self, actor: str = "omnious"):
        """Initialize executor.

        Args:
            actor: Actor name for intervention logging
        """
        self.actor = actor

    async def execute(self, action: PendingAction) -> Dict[str, Any]:
        """Execute a confirmed action.

        Args:
            action: The pending action to execute

        Returns:
            Dict with success status and result or error
        """
        try:
            result = await self._dispatch(action)

            # Log successful intervention
            log_action(
                actor=self.actor,
                object_type="agent_action",
                object_id=result.get("id", 0),
                action_type="agent_confirmed_action",
                summary=f"Executed {action.tool_name}",
                details={
                    "tool_name": action.tool_name,
                    "payload": action.payload,
                    "result": result,
                },
            )

            return {"success": True, **result}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _dispatch(self, action: PendingAction) -> Dict[str, Any]:
        """Dispatch action to appropriate handler."""
        handlers = {
            "request_create_task": self._execute_create_task,
            "request_create_note": self._execute_create_note,
            "request_create_reminder": self._execute_create_reminder,
            "request_send_email": self._execute_send_email,
            "request_update_deal": self._execute_update_deal,
            "request_add_deal_note": self._execute_add_deal_note,
        }

        handler = handlers.get(action.tool_name)
        if not handler:
            raise ValueError(f"Unknown tool: {action.tool_name}")

        return await handler(action.payload)

    async def _execute_create_task(self, payload: dict) -> Dict[str, Any]:
        """Create a task."""
        from datetime import datetime

        service = TaskService(actor=self.actor)

        # Parse due_at if provided
        due_at = None
        if payload.get("due_at"):
            due_at = datetime.fromisoformat(payload["due_at"])

        task_data = TaskCreate(
            title=payload["title"],
            description=payload.get("description"),
            assignee_employee_id=payload.get("assignee_employee_id"),
            priority=payload.get("priority", "normal"),
            due_at=due_at,
            target_type=payload.get("target_type"),
            target_id=payload.get("target_id"),
        )

        task = service.create_task(task_data, actor=self.actor)
        return {"action": "task_created", "id": task.id, "title": task.title}

    async def _execute_create_note(self, payload: dict) -> Dict[str, Any]:
        """Create an internal note."""
        from datetime import datetime

        service = NoteService(actor=self.actor)

        note_data = NoteCreate(
            content=payload["content"],
            target_type=payload.get("target_type"),
            target_id=payload.get("target_id"),
            pinned=payload.get("pinned", False),
        )

        note = service.create_note(note_data, actor=self.actor)
        return {"action": "note_created", "id": note.id}

    async def _execute_create_reminder(self, payload: dict) -> Dict[str, Any]:
        """Create a reminder."""
        from datetime import datetime

        service = ReminderService(actor=self.actor)

        reminder_data = ReminderCreate(
            target_type=payload["target_type"],
            target_id=payload["target_id"],
            remind_at=datetime.fromisoformat(payload["remind_at"]),
            message=payload.get("message"),
            channel=payload.get("channel", "app"),
        )

        reminder = service.create_reminder(reminder_data, actor=self.actor)
        return {"action": "reminder_created", "id": reminder.id}

    async def _execute_send_email(self, payload: dict) -> Dict[str, Any]:
        """Send an email."""
        from ..tools.base import run_async
        from ...backend.services.msgraph_email_service import get_msgraph_email_service

        service = get_msgraph_email_service()

        success = await service.send_email(
            from_mailbox=payload.get("from_mailbox", "mohammed@gyptech.com.sa"),
            to=payload["to"],
            subject=payload["subject"],
            body=payload["body"],
            cc=payload.get("cc"),
        )

        if success:
            return {"action": "email_sent", "to": payload["to"], "subject": payload["subject"]}
        else:
            raise Exception("Failed to send email")

    async def _execute_update_deal(self, payload: dict) -> Dict[str, Any]:
        """Update a Pipedrive deal."""
        from ...backend.integrations.pipedrive_client import get_pipedrive_client

        client = get_pipedrive_client()

        result = await client.update_deal(
            deal_id=payload["deal_id"],
            title=payload.get("title"),
            status=payload.get("status"),
            stage_id=payload.get("stage_id"),
            value=payload.get("value"),
        )

        if result:
            return {"action": "deal_updated", "id": payload["deal_id"], "changes": result}
        else:
            raise Exception("Failed to update deal")

    async def _execute_add_deal_note(self, payload: dict) -> Dict[str, Any]:
        """Add a note to a Pipedrive deal."""
        from ...backend.integrations.pipedrive_client import get_pipedrive_client

        client = get_pipedrive_client()

        result = await client.add_deal_note(
            deal_id=payload["deal_id"],
            content=payload["content"],
            pinned=payload.get("pinned", False),
        )

        if result:
            return {"action": "deal_note_added", "deal_id": payload["deal_id"], "note_id": result.get("id")}
        else:
            raise Exception("Failed to add deal note")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/agent/test_executor.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add cmd_center/agent/core/executor.py tests/agent/test_executor.py
git commit -m "feat(agent): add ActionExecutor for confirmed write operations"
```

---

## Task 5: Integrate Write Tools into Agent

**Files:**
- Modify: `cmd_center/agent/core/agent.py`
- Test: `tests/agent/test_agent_write_integration.py`

**Step 1: Write the failing test**

Create `tests/agent/test_agent_write_integration.py`:

```python
"""Tests for agent write tool integration."""

import pytest
from unittest.mock import patch, MagicMock

from cmd_center.agent.core.agent import OmniousAgent


class TestWriteToolRegistration:
    """Tests for write tool registration."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    def test_write_tools_registered(self, agent):
        """Write tools are registered."""
        tools = agent.tools.list_tools()
        tool_names = [t["name"] for t in tools]

        expected_write_tools = [
            "request_create_task",
            "request_create_note",
            "request_create_reminder",
            "request_send_email",
            "request_update_deal",
            "request_add_deal_note",
        ]

        for tool in expected_write_tools:
            assert tool in tool_names, f"Missing write tool: {tool}"

    def test_total_tool_count(self, agent):
        """Total tool count is correct (19 read + 6 write = 25)."""
        tools = agent.tools.list_tools()
        assert len(tools) == 25, f"Expected 25 tools, got {len(tools)}"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_agent_write_integration.py -v`
Expected: FAIL with "Missing write tool"

**Step 3: Write minimal implementation**

Modify `cmd_center/agent/core/agent.py`:

```python
# Add import at top
from ..tools.write_tools import (
    RequestCreateTask,
    RequestCreateNote,
    RequestCreateReminder,
    RequestSendEmail,
    RequestUpdateDeal,
    RequestAddDealNote,
)
from .executor import ActionExecutor

# In _register_tools method, add:
    # Write tools (require confirmation)
    self.tools.register(RequestCreateTask())
    self.tools.register(RequestCreateNote())
    self.tools.register(RequestCreateReminder())
    self.tools.register(RequestSendEmail())
    self.tools.register(RequestUpdateDeal())
    self.tools.register(RequestAddDealNote())

# Add executor initialization in __init__:
    self.executor = ActionExecutor(actor="omnious")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/agent/test_agent_write_integration.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add cmd_center/agent/core/agent.py tests/agent/test_agent_write_integration.py
git commit -m "feat(agent): register write tools in agent"
```

---

## Task 6: Implement Confirmation Handling in Chat

**Files:**
- Modify: `cmd_center/agent/core/agent.py`
- Test: `tests/agent/test_chat_confirmation.py`

**Step 1: Write the failing test**

Create `tests/agent/test_chat_confirmation.py`:

```python
"""Tests for confirmation handling in chat."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

from cmd_center.agent.core.agent import OmniousAgent
from cmd_center.agent.tools.base import PendingAction


class TestChatConfirmationHandling:
    """Tests for chat confirmation flow."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    @pytest.mark.asyncio
    async def test_chat_handles_pending_action_from_tool(self, agent):
        """Chat sets pending_action when tool returns one."""
        # Mock API response with tool call
        mock_tool_response = MagicMock()
        mock_tool_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "function": {
                            "name": "request_create_task",
                            "arguments": '{"title": "Test task", "priority": "high"}'
                        }
                    }]
                }
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }

        # Mock final response
        mock_final_response = MagicMock()
        mock_final_response.json.return_value = {
            "choices": [{"message": {"content": "I'll create that task for you."}}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 10}
        }

        with patch.object(agent, '_call_api_with_retry', new_callable=AsyncMock) as mock_api:
            mock_api.side_effect = [mock_tool_response, mock_final_response]

            response = await agent.chat("Create a task to follow up with client")

            # Agent should have set pending action
            assert agent.has_pending_action()
            assert agent.pending_action.tool_name == "request_create_task"

    @pytest.mark.asyncio
    async def test_chat_executes_on_yes(self, agent):
        """Chat executes pending action when user says yes."""
        # Set up pending action
        agent.pending_action = PendingAction(
            tool_name="request_create_task",
            preview="Create task: Test",
            payload={"title": "Test", "priority": "normal"},
        )

        with patch.object(agent.executor, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {"success": True, "action": "task_created", "id": 1}

            response = await agent.chat("yes")

            mock_execute.assert_called_once()
            assert agent.pending_action is None  # Cleared after execution
            assert "created" in response.lower() or "done" in response.lower()

    @pytest.mark.asyncio
    async def test_chat_cancels_on_no(self, agent):
        """Chat cancels pending action when user says no."""
        agent.pending_action = PendingAction(
            tool_name="request_create_task",
            preview="Create task: Test",
            payload={"title": "Test"},
        )

        with patch.object(agent.executor, 'execute', new_callable=AsyncMock) as mock_execute:
            response = await agent.chat("no")

            mock_execute.assert_not_called()
            assert agent.pending_action is None
            assert "cancel" in response.lower() or "won't" in response.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_chat_confirmation.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Modify `cmd_center/agent/core/agent.py` `chat` method:

```python
async def chat(self, message: str) -> str:
    """Send a message and get a response (non-streaming).

    Args:
        message: User's message

    Returns:
        Assistant's response
    """
    # Check for confirmation response first
    if self.has_pending_action():
        confirmation = self._is_confirmation(message)
        if confirmation == "yes":
            result = await self.executor.execute(self.pending_action)
            self.pending_action = None
            if result["success"]:
                return f"Done! {result.get('action', 'Action completed')}. ID: {result.get('id', 'N/A')}"
            else:
                return f"Sorry, there was an error: {result.get('error', 'Unknown error')}"
        elif confirmation == "no":
            self.pending_action = None
            return "No problem, I won't proceed with that action. How else can I help?"

    messages = self._build_messages(message)

    # Add user message to history
    self._add_to_history("user", message)

    # Call LLM with tool handling
    content = await self._call_llm_with_tools(messages)

    # Check if any tool returned a pending action
    # This is handled in _process_tool_calls

    # Add to history
    self._add_to_history("assistant", content)

    return content
```

Also modify `_process_tool_calls`:

```python
async def _process_tool_calls(
    self,
    tool_calls: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Process tool calls and return results."""
    results = []

    for tool_call in tool_calls:
        tool_id = tool_call["id"]
        function = tool_call["function"]
        tool_name = function["name"]

        try:
            arguments = json.loads(function["arguments"])
        except json.JSONDecodeError:
            arguments = {}

        # Execute the tool
        result = self.tools.execute(tool_name, arguments)

        # Check if tool returned a pending action
        if result.success and isinstance(result.data, dict):
            if "pending_action" in result.data:
                pa_data = result.data["pending_action"]
                self.pending_action = PendingAction(
                    tool_name=pa_data["tool_name"],
                    preview=pa_data["preview"],
                    payload=pa_data["payload"],
                )

        # Format result as message
        if result.success:
            content = json.dumps(result.data)
        else:
            content = json.dumps({"error": result.error})

        results.append({
            "role": "tool",
            "tool_call_id": tool_id,
            "content": content
        })

    return results
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/agent/test_chat_confirmation.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add cmd_center/agent/core/agent.py tests/agent/test_chat_confirmation.py
git commit -m "feat(agent): implement confirmation handling in chat"
```

---

## Task 7: Update Golden Tests

**Files:**
- Modify: `tests/agent/test_golden_qa.py`
- Run: All agent tests

**Step 1: Update golden tests**

Add to `tests/agent/test_golden_qa.py`:

```python
# Add new scenarios
GOLDEN_SCENARIOS.extend([
    {
        "id": "create_task",
        "query": "Create a task to follow up with the client",
        "expected_tools": ["request_create_task"],
    },
    {
        "id": "send_email",
        "query": "Send an email to client@example.com about the proposal",
        "expected_tools": ["request_send_email"],
    },
    {
        "id": "update_deal",
        "query": "Mark deal 123 as won",
        "expected_tools": ["request_update_deal"],
    },
])

# Update test_all_tools_registered
def test_all_tools_registered(self):
    """Verify all Phase 1, Phase 2, and Phase 3 tools are registered."""
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
        "get_pending_reminders",
        "get_notes",
        "get_employees",
        "get_employee_details",
        "get_employee_skills",
        # Phase 2 tools
        "get_cashflow_projection",
        "get_ceo_dashboard",
        "get_owner_kpis",
        "search_emails",
        "get_emails",
        "get_expiring_documents",
        "get_unpaid_bonuses",
        "read_knowledge",
        # Phase 3 write tools
        "request_create_task",
        "request_create_note",
        "request_create_reminder",
        "request_send_email",
        "request_update_deal",
        "request_add_deal_note",
    ]

    tool_names = [t["name"] for t in tools]
    for expected in expected_tools:
        assert expected in tool_names, f"Missing tool: {expected}"

    assert len(tools) == 25, f"Expected 25 tools, got {len(tools)}"
```

**Step 2: Run all agent tests**

Run: `pytest tests/agent/ -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/agent/test_golden_qa.py
git commit -m "test(agent): update golden tests for Phase 3 write tools"
```

---

## Task 8: Final Integration Test

**Files:**
- Create: `tests/agent/test_phase3_integration.py`

**Step 1: Create integration test**

```python
"""Integration tests for Phase 3 write operations."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from cmd_center.agent.core.agent import OmniousAgent
from cmd_center.agent.tools.base import PendingAction


class TestPhase3Integration:
    """End-to-end tests for Phase 3 features."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    def test_write_tool_returns_pending_action(self, agent):
        """Write tool execution returns PendingAction."""
        result = agent.tools.execute("request_create_task", {
            "title": "Test task",
            "priority": "high",
        })

        assert result.success
        assert "pending_action" in result.data
        assert result.data["pending_action"]["tool_name"] == "request_create_task"

    def test_confirmation_flow_state_machine(self, agent):
        """Confirmation flow works correctly."""
        # Initially no pending action
        assert not agent.has_pending_action()

        # Set pending action
        agent.pending_action = PendingAction(
            tool_name="request_create_task",
            preview="Create task",
            payload={"title": "Test"},
        )
        assert agent.has_pending_action()
        assert agent.get_pending_preview() == "Create task"

        # Clear on cancel
        agent.pending_action = None
        assert not agent.has_pending_action()

    def test_all_write_tools_exist(self, agent):
        """All 6 write tools are available."""
        write_tools = [
            "request_create_task",
            "request_create_note",
            "request_create_reminder",
            "request_send_email",
            "request_update_deal",
            "request_add_deal_note",
        ]

        for tool in write_tools:
            result = agent.tools.execute(tool, _get_minimal_params(tool))
            assert result.success, f"Tool {tool} failed"
            assert "pending_action" in result.data


def _get_minimal_params(tool_name: str) -> dict:
    """Get minimal valid params for each tool."""
    params = {
        "request_create_task": {"title": "Test"},
        "request_create_note": {"content": "Test note"},
        "request_create_reminder": {
            "target_type": "task",
            "target_id": 1,
            "remind_at": "2026-01-15T10:00:00",
        },
        "request_send_email": {
            "to": ["test@example.com"],
            "subject": "Test",
            "body": "Test body",
        },
        "request_update_deal": {"deal_id": 123, "status": "won"},
        "request_add_deal_note": {"deal_id": 123, "content": "Test note"},
    }
    return params[tool_name]
```

**Step 2: Run integration tests**

Run: `pytest tests/agent/test_phase3_integration.py -v`
Expected: PASS

**Step 3: Run all tests**

Run: `pytest tests/agent/ -v`
Expected: All tests pass

**Step 4: Commit**

```bash
git add tests/agent/test_phase3_integration.py
git commit -m "test(agent): add Phase 3 integration tests"
```

---

## Summary

Phase 3 adds 6 write tools with confirmation flow:

| Tool | Purpose | Service |
|------|---------|---------|
| `request_create_task` | Create task | TaskService |
| `request_create_note` | Create internal note | NoteService |
| `request_create_reminder` | Create reminder | ReminderService |
| `request_send_email` | Send email | MSGraphEmailService |
| `request_update_deal` | Update Pipedrive deal | PipedriveClient |
| `request_add_deal_note` | Add note to deal | PipedriveClient |

All write operations:
1. Return `PendingAction` with preview
2. Require user confirmation ("yes"/"no")
3. Log to intervention table on execution
4. Provide clear feedback on success/failure

Total tools after Phase 3: **25** (19 read + 6 write)
