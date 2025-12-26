"""API endpoints for Task management."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..models.task_models import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskWithAssignee,
    TaskListResponse,
    TaskFilters,
)
from ..services.task_service import TaskService

router = APIRouter()


@router.get("", response_model=TaskListResponse)
def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assignee_employee_id: Optional[int] = Query(None, description="Filter by assignee"),
    is_critical: Optional[bool] = Query(None, description="Filter critical tasks"),
    target_type: Optional[str] = Query(None, description="Filter by target type"),
    target_id: Optional[int] = Query(None, description="Filter by target ID"),
    is_archived: Optional[bool] = Query(False, description="Include archived tasks"),
    due_before: Optional[datetime] = Query(None, description="Filter due before date"),
    due_after: Optional[datetime] = Query(None, description="Filter due after date"),
    search: Optional[str] = Query(None, description="Search in title"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> TaskListResponse:
    """List tasks with optional filters."""
    filters = TaskFilters(
        status=status,
        priority=priority,
        assignee_employee_id=assignee_employee_id,
        is_critical=is_critical,
        target_type=target_type,
        target_id=target_id,
        is_archived=is_archived,
        due_before=due_before,
        due_after=due_after,
        search=search,
        page=page,
        page_size=page_size,
    )
    service = TaskService()
    return service.get_tasks(filters)


@router.get("/overdue", response_model=list[TaskResponse])
def list_overdue_tasks(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of tasks"),
) -> list[TaskResponse]:
    """List overdue tasks (past due date, not completed)."""
    service = TaskService()
    return service.get_overdue_tasks(limit=limit)


@router.get("/{task_id}", response_model=TaskWithAssignee)
def get_task(task_id: int) -> TaskWithAssignee:
    """Get a single task by ID with assignee name."""
    service = TaskService()
    task = service.get_task_with_assignee(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(
    data: TaskCreate,
    actor: Optional[str] = Query("system", description="Who is creating the task"),
) -> TaskResponse:
    """Create a new task, optionally with a reminder."""
    service = TaskService()
    return service.create_task(data, actor=actor)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    data: TaskUpdate,
    actor: Optional[str] = Query("system", description="Who is updating"),
) -> TaskResponse:
    """Update a task."""
    service = TaskService()
    task = service.update_task(task_id, data, actor=actor)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: int,
    actor: Optional[str] = Query("system", description="Who is completing"),
) -> TaskResponse:
    """Mark a task as complete and cancel pending reminders."""
    service = TaskService()
    task = service.complete_task(task_id, actor=actor)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=204)
def cancel_task(
    task_id: int,
    actor: Optional[str] = Query("system", description="Who is cancelling"),
) -> None:
    """Cancel a task and its pending reminders."""
    service = TaskService()
    if not service.cancel_task(task_id, actor=actor):
        raise HTTPException(status_code=404, detail="Task not found")


@router.get("/target/{target_type}/{target_id}", response_model=list[TaskResponse])
def get_tasks_for_target(
    target_type: str,
    target_id: int,
    include_archived: bool = Query(False, description="Include archived tasks"),
) -> list[TaskResponse]:
    """Get all tasks for a specific target entity."""
    service = TaskService()
    return service.get_tasks_for_target(target_type, target_id, include_archived)
