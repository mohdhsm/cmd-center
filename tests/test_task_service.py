"""Unit tests for TaskService."""

import pytest
from datetime import datetime, timedelta, timezone

from cmd_center.backend.services.task_service import TaskService, get_task_service
from cmd_center.backend.services.employee_service import EmployeeService
from cmd_center.backend.services.reminder_service import ReminderService
from cmd_center.backend.models.task_models import TaskCreate, TaskUpdate, TaskFilters
from cmd_center.backend.models.employee_models import EmployeeCreate
from cmd_center.backend.constants import TaskStatus


class TestTaskService:
    """Tests for TaskService CRUD operations."""

    def test_create_task(self, override_db):
        """Creates task with all fields."""
        service = TaskService(actor="test")
        data = TaskCreate(
            title="Follow up with client",
            description="Review proposal and schedule meeting",
            priority="high",
            is_critical=True,
        )

        result = service.create_task(data)

        assert result.id is not None
        assert result.title == "Follow up with client"
        assert result.priority == "high"
        assert result.is_critical is True
        assert result.status == "open"

    def test_create_task_with_target(self, override_db):
        """Creates task linked to a target entity."""
        service = TaskService(actor="test")
        data = TaskCreate(
            title="Deal follow up",
            target_type="deal",
            target_id=123,
        )

        result = service.create_task(data)

        assert result.target_type == "deal"
        assert result.target_id == 123

    def test_create_task_with_assignee(self, override_db):
        """Creates task assigned to an employee."""
        # Create an employee first
        emp_service = EmployeeService(actor="test")
        employee = emp_service.create_employee(
            EmployeeCreate(full_name="John Doe", role_title="Sales Rep")
        )

        service = TaskService(actor="test")
        data = TaskCreate(
            title="Sales task",
            assignee_employee_id=employee.id,
        )

        result = service.create_task(data)

        assert result.assignee_employee_id == employee.id

    def test_create_task_with_reminder(self, override_db):
        """Creates task and associated reminder."""
        service = TaskService(actor="test")
        remind_at = datetime.now(timezone.utc) + timedelta(hours=24)
        data = TaskCreate(
            title="Task with reminder",
            reminder_at=remind_at,
            reminder_channel="email",
        )

        result = service.create_task(data)

        # Verify reminder was created
        reminder_service = ReminderService()
        reminders = reminder_service.get_reminders_for_target("task", result.id)
        assert len(reminders) == 1
        assert reminders[0].channel == "email"

    def test_get_task_by_id(self, override_db):
        """Can retrieve task by ID."""
        service = TaskService(actor="test")
        created = service.create_task(TaskCreate(title="Test Task"))

        result = service.get_task_by_id(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.title == "Test Task"

    def test_get_task_by_id_not_found(self, override_db):
        """Returns None for non-existent task."""
        service = TaskService(actor="test")

        result = service.get_task_by_id(99999)

        assert result is None

    def test_get_task_with_assignee(self, override_db):
        """Get task with assignee name populated."""
        emp_service = EmployeeService(actor="test")
        employee = emp_service.create_employee(
            EmployeeCreate(full_name="Jane Smith", role_title="Manager")
        )

        service = TaskService(actor="test")
        created = service.create_task(TaskCreate(
            title="Assigned task",
            assignee_employee_id=employee.id,
        ))

        result = service.get_task_with_assignee(created.id)

        assert result is not None
        assert result.assignee_name == "Jane Smith"

    def test_complete_task(self, override_db):
        """Completing task sets status and completed_at."""
        service = TaskService(actor="test")
        task = service.create_task(TaskCreate(title="To complete"))

        result = service.complete_task(task.id)

        assert result is not None
        assert result.status == "done"
        assert result.completed_at is not None

    def test_complete_task_cancels_reminders(self, override_db):
        """Completing task cancels pending reminders."""
        service = TaskService(actor="test")
        remind_at = datetime.now(timezone.utc) + timedelta(hours=24)
        task = service.create_task(TaskCreate(
            title="Task with reminder",
            reminder_at=remind_at,
        ))

        service.complete_task(task.id)

        # Verify reminder was cancelled
        reminder_service = ReminderService()
        reminders = reminder_service.get_reminders_for_target("task", task.id, status="pending")
        assert len(reminders) == 0

    def test_cancel_task(self, override_db):
        """Cancel sets status to cancelled and archives."""
        service = TaskService(actor="test")
        task = service.create_task(TaskCreate(title="To cancel"))

        result = service.cancel_task(task.id)

        assert result is True

        # Verify status
        updated = service.get_task_by_id(task.id)
        assert updated.status == "cancelled"
        assert updated.is_archived is True

    def test_update_task(self, override_db):
        """Update changes fields."""
        service = TaskService(actor="test")
        task = service.create_task(TaskCreate(
            title="Original",
            priority="low",
        ))

        result = service.update_task(
            task.id,
            TaskUpdate(title="Updated", priority="high")
        )

        assert result is not None
        assert result.title == "Updated"
        assert result.priority == "high"

    def test_update_task_not_found(self, override_db):
        """Update returns None for non-existent task."""
        service = TaskService(actor="test")

        result = service.update_task(99999, TaskUpdate(title="Test"))

        assert result is None

    def test_get_tasks_filters_by_status(self, override_db):
        """Status filter works."""
        service = TaskService(actor="test")

        service.create_task(TaskCreate(title="Open task"))
        done_task = service.create_task(TaskCreate(title="Done task"))
        service.complete_task(done_task.id)

        result = service.get_tasks(TaskFilters(status="open"))

        assert result.total == 1
        assert result.items[0].status == "open"

    def test_get_tasks_filters_by_priority(self, override_db):
        """Priority filter works."""
        service = TaskService(actor="test")

        service.create_task(TaskCreate(title="Low", priority="low"))
        service.create_task(TaskCreate(title="High", priority="high"))

        result = service.get_tasks(TaskFilters(priority="high"))

        assert result.total == 1
        assert result.items[0].priority == "high"

    def test_get_tasks_filters_by_assignee(self, override_db):
        """Assignee filter works."""
        emp_service = EmployeeService(actor="test")
        emp1 = emp_service.create_employee(EmployeeCreate(full_name="Emp 1", role_title="Dev"))
        emp2 = emp_service.create_employee(EmployeeCreate(full_name="Emp 2", role_title="Dev"))

        service = TaskService(actor="test")
        service.create_task(TaskCreate(title="Task 1", assignee_employee_id=emp1.id))
        service.create_task(TaskCreate(title="Task 2", assignee_employee_id=emp2.id))

        result = service.get_tasks(TaskFilters(assignee_employee_id=emp1.id))

        assert result.total == 1
        assert result.items[0].assignee_employee_id == emp1.id

    def test_get_tasks_filters_by_target(self, override_db):
        """target_type/target_id filter works."""
        service = TaskService(actor="test")

        service.create_task(TaskCreate(title="Deal 1", target_type="deal", target_id=100))
        service.create_task(TaskCreate(title="Deal 2", target_type="deal", target_id=200))
        service.create_task(TaskCreate(title="Employee", target_type="employee", target_id=100))

        result = service.get_tasks(TaskFilters(target_type="deal", target_id=100))

        assert result.total == 1
        assert result.items[0].target_id == 100

    def test_get_overdue_tasks(self, override_db):
        """Returns tasks past due_at."""
        service = TaskService(actor="test")
        now = datetime.now(timezone.utc)

        # Overdue task
        service.create_task(TaskCreate(
            title="Overdue",
            due_at=now - timedelta(days=1),
        ))

        # Future task
        service.create_task(TaskCreate(
            title="Future",
            due_at=now + timedelta(days=1),
        ))

        result = service.get_overdue_tasks()

        assert len(result) == 1
        assert result[0].title == "Overdue"

    def test_get_tasks_for_target(self, override_db):
        """Get all tasks for specific target."""
        service = TaskService(actor="test")

        service.create_task(TaskCreate(title="T1", target_type="deal", target_id=100))
        service.create_task(TaskCreate(title="T2", target_type="deal", target_id=100))
        service.create_task(TaskCreate(title="T3", target_type="deal", target_id=200))

        result = service.get_tasks_for_target("deal", 100)

        assert len(result) == 2
        assert all(t.target_id == 100 for t in result)

    def test_get_tasks_critical_first(self, override_db):
        """Critical tasks sorted to top."""
        service = TaskService(actor="test")

        service.create_task(TaskCreate(title="Normal", is_critical=False))
        service.create_task(TaskCreate(title="Critical", is_critical=True))

        result = service.get_tasks()

        assert result.items[0].is_critical is True
        assert result.items[1].is_critical is False

    def test_get_tasks_pagination(self, override_db):
        """Pagination works correctly."""
        service = TaskService(actor="test")

        for i in range(10):
            service.create_task(TaskCreate(title=f"Task {i}"))

        page1 = service.get_tasks(TaskFilters(page=1, page_size=3))
        assert page1.total == 10
        assert len(page1.items) == 3

        page2 = service.get_tasks(TaskFilters(page=2, page_size=3))
        assert len(page2.items) == 3

        # Different tasks on each page
        page1_ids = {t.id for t in page1.items}
        page2_ids = {t.id for t in page2.items}
        assert page1_ids.isdisjoint(page2_ids)


class TestTaskServiceSingleton:
    """Test singleton pattern."""

    def test_get_task_service_returns_same_instance(self, override_db):
        """get_task_service returns the same instance."""
        import cmd_center.backend.services.task_service as module
        module._task_service = None

        service1 = get_task_service()
        service2 = get_task_service()

        assert service1 is service2
