"""Task-related tools for the agent."""

from typing import Optional
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult
from ...backend.services.task_service import get_task_service
from ...backend.services.reminder_service import get_reminder_service
from ...backend.services.note_service import get_note_service
from ...backend.models.task_models import TaskFilters
from ...backend.models.note_models import NoteFilters


class GetTasksParams(BaseModel):
    """Parameters for get_tasks tool."""
    status: Optional[str] = Field(
        default=None,
        description="Filter by status: 'open', 'in_progress', 'done', 'cancelled'"
    )
    assignee_id: Optional[int] = Field(
        default=None,
        description="Filter by assignee employee ID"
    )
    is_critical: Optional[bool] = Field(
        default=None,
        description="Filter for critical tasks only"
    )
    limit: int = Field(
        default=20,
        description="Maximum number of tasks to return"
    )


class GetTasks(BaseTool):
    """Get tasks with optional filters."""

    name = "get_tasks"
    description = "Get tasks with optional filtering by status, assignee, or priority. Use this to find specific tasks or get an overview."
    parameters_model = GetTasksParams

    def execute(self, params: GetTasksParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_task_service()
            filters = TaskFilters(
                status=params.status,
                assignee_employee_id=params.assignee_id,
                is_critical=params.is_critical,
                page_size=params.limit,
            )
            result = service.get_tasks(filters)

            tasks_data = [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "is_critical": t.is_critical,
                    "due_at": t.due_at.isoformat() if t.due_at else None,
                    "assignee_employee_id": t.assignee_employee_id,
                }
                for t in result.items
            ]

            return ToolResult(
                success=True,
                data={
                    "tasks": tasks_data,
                    "count": len(tasks_data),
                    "total": result.total,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetOverdueTasksParams(BaseModel):
    """Parameters for get_overdue_tasks tool."""
    limit: int = Field(
        default=20,
        description="Maximum number of tasks to return"
    )


class GetOverdueTasks(BaseTool):
    """Get tasks that are past their due date."""

    name = "get_overdue_tasks"
    description = "Get tasks that are past their due date and not completed. Use this to identify urgent tasks."
    parameters_model = GetOverdueTasksParams

    def execute(self, params: GetOverdueTasksParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_task_service()
            tasks = service.get_overdue_tasks(params.limit)

            tasks_data = [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "is_critical": t.is_critical,
                    "due_at": t.due_at.isoformat() if t.due_at else None,
                    "assignee_employee_id": t.assignee_employee_id,
                }
                for t in tasks
            ]

            return ToolResult(
                success=True,
                data={
                    "tasks": tasks_data,
                    "count": len(tasks_data),
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetPendingRemindersParams(BaseModel):
    """Parameters for get_pending_reminders tool."""
    limit: int = Field(
        default=20,
        description="Maximum number of reminders to return"
    )


class GetPendingReminders(BaseTool):
    """Get pending reminders that haven't been completed."""

    name = "get_pending_reminders"
    description = "Get pending reminders that haven't been completed. Use this to track what needs follow-up."
    parameters_model = GetPendingRemindersParams

    def execute(self, params: GetPendingRemindersParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_reminder_service()
            reminders = service.get_pending_reminders(limit=params.limit)

            reminders_data = [
                {
                    "id": r.id,
                    "target_type": r.target_type,
                    "target_id": r.target_id,
                    "remind_at": r.remind_at.isoformat() if r.remind_at else None,
                    "channel": r.channel,
                    "message": r.message,
                    "status": r.status,
                }
                for r in reminders
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


class GetNotesParams(BaseModel):
    """Parameters for get_notes tool."""
    target_type: Optional[str] = Field(
        default=None,
        description="Filter by target type (e.g., 'deal', 'task', 'employee')"
    )
    target_id: Optional[int] = Field(
        default=None,
        description="Filter by target ID (requires target_type)"
    )
    pinned: Optional[bool] = Field(
        default=None,
        description="Filter for pinned notes only"
    )
    search: Optional[str] = Field(
        default=None,
        description="Search text within note content"
    )
    page_size: int = Field(
        default=20,
        description="Maximum number of notes to return"
    )


class GetNotes(BaseTool):
    """Get notes with optional filters."""

    name = "get_notes"
    description = "Get notes from the system, optionally filtered by target entity or search text. Use to review history, context, and important information."
    parameters_model = GetNotesParams

    def execute(self, params: GetNotesParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_note_service()
            filters = NoteFilters(
                target_type=params.target_type,
                target_id=params.target_id,
                pinned=params.pinned,
                search=params.search,
                page_size=params.page_size,
            )
            result = service.get_notes(filters)

            notes_data = [
                {
                    "id": n.id,
                    "content": n.content[:500] if n.content and len(n.content) > 500 else n.content,
                    "created_by": n.created_by,
                    "target_type": n.target_type,
                    "target_id": n.target_id,
                    "pinned": n.pinned,
                    "tags": n.tags,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in result.items
            ]

            return ToolResult(
                success=True,
                data={
                    "notes": notes_data,
                    "count": len(notes_data),
                    "total": result.total,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
