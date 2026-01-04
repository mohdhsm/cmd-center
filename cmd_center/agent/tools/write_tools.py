"""Write tools that return PendingAction for user confirmation.

These tools request write operations but don't execute them immediately.
They return a PendingAction that the user must confirm before execution.
"""

from typing import Optional
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult, PendingAction


# ============================================================================
# Parameter Models
# ============================================================================


class CreateTaskParams(BaseModel):
    """Parameters for creating a task."""

    title: str = Field(description="Title of the task")
    description: Optional[str] = Field(
        default=None, description="Detailed description of the task"
    )
    priority: Optional[str] = Field(
        default="medium",
        description="Priority level: 'low', 'medium', or 'high'",
    )
    assignee_employee_id: Optional[int] = Field(
        default=None, description="Employee ID to assign the task to"
    )
    due_at: Optional[str] = Field(
        default=None, description="Due date/time in ISO format (e.g., 2024-03-15T10:00:00Z)"
    )
    target_type: Optional[str] = Field(
        default=None, description="Type of target: 'deal', 'person', 'organization'"
    )
    target_id: Optional[int] = Field(
        default=None, description="ID of the target (deal, person, or organization)"
    )


class CreateNoteParams(BaseModel):
    """Parameters for creating an internal note."""

    content: str = Field(description="Content of the note")
    target_type: str = Field(
        description="Type of target: 'deal', 'person', 'organization'"
    )
    target_id: int = Field(description="ID of the target entity")
    pinned: Optional[bool] = Field(
        default=False, description="Whether to pin the note"
    )


class CreateReminderParams(BaseModel):
    """Parameters for creating a reminder."""

    target_type: str = Field(
        description="Type of target: 'deal', 'person', 'organization'"
    )
    target_id: int = Field(description="ID of the target entity")
    remind_at: str = Field(
        description="When to remind in ISO format (e.g., 2024-03-20T09:00:00Z)"
    )
    message: str = Field(description="Reminder message")
    channel: Optional[str] = Field(
        default="app", description="Notification channel: 'app', 'email', or 'sms'"
    )


class SendEmailParams(BaseModel):
    """Parameters for sending an email."""

    to: str = Field(description="Recipient email address")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body content")
    cc: Optional[str] = Field(default=None, description="CC email address")
    from_mailbox: Optional[str] = Field(
        default=None, description="Sender mailbox to use"
    )


class UpdateDealParams(BaseModel):
    """Parameters for updating a Pipedrive deal."""

    deal_id: int = Field(description="ID of the deal to update")
    title: Optional[str] = Field(default=None, description="New deal title")
    status: Optional[str] = Field(
        default=None, description="New status: 'open', 'won', or 'lost'"
    )
    stage_id: Optional[int] = Field(default=None, description="New stage ID")
    value: Optional[float] = Field(default=None, description="New deal value")


class AddDealNoteParams(BaseModel):
    """Parameters for adding a note to a Pipedrive deal."""

    deal_id: int = Field(description="ID of the deal to add note to")
    content: str = Field(description="Content of the note")
    pinned: Optional[bool] = Field(
        default=False, description="Whether to pin the note"
    )


# ============================================================================
# Write Tools
# ============================================================================


class RequestCreateTask(BaseTool):
    """Request to create a new task. Returns a preview for user confirmation."""

    name = "request_create_task"
    description = "Request to create a new task. Returns a preview for user confirmation before the task is actually created."
    parameters_model = CreateTaskParams

    def execute(self, params: CreateTaskParams) -> ToolResult:
        """Generate pending action for task creation."""
        preview_lines = [
            "CREATE TASK",
            f"  Title: {params.title}",
        ]

        if params.description:
            preview_lines.append(f"  Description: {params.description}")
        if params.priority:
            preview_lines.append(f"  Priority: {params.priority}")
        if params.assignee_employee_id:
            preview_lines.append(f"  Assignee ID: {params.assignee_employee_id}")
        if params.due_at:
            preview_lines.append(f"  Due: {params.due_at}")
        if params.target_type and params.target_id:
            preview_lines.append(f"  Target: {params.target_type} #{params.target_id}")

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
            },
        )


class RequestCreateNote(BaseTool):
    """Request to create an internal note. Returns a preview for user confirmation."""

    name = "request_create_note"
    description = "Request to create an internal note attached to a deal, person, or organization. Returns a preview for user confirmation."
    parameters_model = CreateNoteParams

    def execute(self, params: CreateNoteParams) -> ToolResult:
        """Generate pending action for note creation."""
        content_preview = params.content[:100] + "..." if len(params.content) > 100 else params.content

        preview_lines = [
            "CREATE NOTE",
            f"  Target: {params.target_type} #{params.target_id}",
            f"  Content: {content_preview}",
        ]

        if params.pinned:
            preview_lines.append("  Pinned: Yes")

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
            },
        )


class RequestCreateReminder(BaseTool):
    """Request to create a reminder. Returns a preview for user confirmation."""

    name = "request_create_reminder"
    description = "Request to create a reminder for a deal, person, or organization. Returns a preview for user confirmation."
    parameters_model = CreateReminderParams

    def execute(self, params: CreateReminderParams) -> ToolResult:
        """Generate pending action for reminder creation."""
        preview_lines = [
            "CREATE REMINDER",
            f"  Target: {params.target_type} #{params.target_id}",
            f"  When: {params.remind_at}",
            f"  Message: {params.message}",
        ]

        if params.channel:
            preview_lines.append(f"  Channel: {params.channel}")

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
            },
        )


class RequestSendEmail(BaseTool):
    """Request to send an email. Returns a preview for user confirmation."""

    name = "request_send_email"
    description = "Request to send an email. Returns a preview for user confirmation before the email is sent."
    parameters_model = SendEmailParams

    def execute(self, params: SendEmailParams) -> ToolResult:
        """Generate pending action for email sending."""
        body_preview = params.body[:150] + "..." if len(params.body) > 150 else params.body

        preview_lines = [
            "SEND EMAIL",
            f"  To: {params.to}",
            f"  Subject: {params.subject}",
        ]

        if params.cc:
            preview_lines.append(f"  CC: {params.cc}")
        if params.from_mailbox:
            preview_lines.append(f"  From: {params.from_mailbox}")

        preview_lines.append(f"  Body: {body_preview}")

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
            },
        )


class RequestUpdateDeal(BaseTool):
    """Request to update a Pipedrive deal. Returns a preview for user confirmation."""

    name = "request_update_deal"
    description = "Request to update a Pipedrive deal. Returns a preview for user confirmation before changes are applied."
    parameters_model = UpdateDealParams

    def execute(self, params: UpdateDealParams) -> ToolResult:
        """Generate pending action for deal update."""
        preview_lines = [
            "UPDATE DEAL",
            f"  Deal ID: {params.deal_id}",
        ]

        if params.title:
            preview_lines.append(f"  New Title: {params.title}")
        if params.status:
            preview_lines.append(f"  New Status: {params.status}")
        if params.stage_id:
            preview_lines.append(f"  New Stage ID: {params.stage_id}")
        if params.value is not None:
            preview_lines.append(f"  New Value: {params.value}")

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
            },
        )


class RequestAddDealNote(BaseTool):
    """Request to add a note to a Pipedrive deal. Returns a preview for user confirmation."""

    name = "request_add_deal_note"
    description = "Request to add a note to a Pipedrive deal. Returns a preview for user confirmation."
    parameters_model = AddDealNoteParams

    def execute(self, params: AddDealNoteParams) -> ToolResult:
        """Generate pending action for adding deal note."""
        content_preview = params.content[:100] + "..." if len(params.content) > 100 else params.content

        preview_lines = [
            "ADD DEAL NOTE",
            f"  Deal ID: {params.deal_id}",
            f"  Content: {content_preview}",
        ]

        if params.pinned:
            preview_lines.append("  Pinned: Yes")

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
            },
        )
