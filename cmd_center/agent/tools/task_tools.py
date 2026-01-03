"""Task-related tools for the agent."""

from typing import Optional
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult
from ...backend.services.task_service import get_task_service
from ...backend.models.task_models import TaskFilters


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
