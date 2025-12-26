"""Integration tests for Task API endpoints."""

import pytest
from datetime import datetime, timedelta, timezone


class TestTaskAPI:
    """Integration tests for /tasks endpoints."""

    @pytest.mark.asyncio
    async def test_create_task(self, test_client):
        """POST /tasks creates task."""
        response = await test_client.post(
            "/tasks",
            json={
                "title": "Follow up with client",
                "description": "Review proposal",
                "priority": "high",
                "is_critical": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["title"] == "Follow up with client"
        assert data["priority"] == "high"
        assert data["status"] == "open"

    @pytest.mark.asyncio
    async def test_create_task_with_target(self, test_client):
        """POST /tasks with target creates linked task."""
        response = await test_client.post(
            "/tasks",
            json={
                "title": "Deal task",
                "target_type": "deal",
                "target_id": 123,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["target_type"] == "deal"
        assert data["target_id"] == 123

    @pytest.mark.asyncio
    async def test_create_task_with_reminder(self, test_client):
        """POST /tasks with reminder_at creates task and reminder."""
        remind_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        response = await test_client.post(
            "/tasks",
            json={
                "title": "Task with reminder",
                "reminder_at": remind_at,
                "reminder_channel": "email",
            },
        )
        assert response.status_code == 201
        task_id = response.json()["id"]

        # Verify reminder was created
        response = await test_client.get(f"/reminders/target/task/{task_id}")
        assert response.status_code == 200
        reminders = response.json()
        assert len(reminders) == 1
        assert reminders[0]["channel"] == "email"

    @pytest.mark.asyncio
    async def test_get_task(self, test_client):
        """GET /tasks/{id} returns task with assignee name."""
        # Create employee
        response = await test_client.post(
            "/employees",
            json={"full_name": "John Doe", "role_title": "Sales"},
        )
        emp_id = response.json()["id"]

        # Create task
        response = await test_client.post(
            "/tasks",
            json={
                "title": "Assigned task",
                "assignee_employee_id": emp_id,
            },
        )
        task_id = response.json()["id"]

        # Get task
        response = await test_client.get(f"/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["assignee_name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, test_client):
        """GET /tasks/{id} returns 404 for non-existent."""
        response = await test_client.get("/tasks/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_task(self, test_client):
        """PUT /tasks/{id} updates task."""
        response = await test_client.post(
            "/tasks",
            json={"title": "Original", "priority": "low"},
        )
        task_id = response.json()["id"]

        response = await test_client.put(
            f"/tasks/{task_id}",
            json={"title": "Updated", "priority": "high"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"
        assert data["priority"] == "high"

    @pytest.mark.asyncio
    async def test_complete_task(self, test_client):
        """POST /tasks/{id}/complete updates status and cancels reminders."""
        remind_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        response = await test_client.post(
            "/tasks",
            json={
                "title": "To complete",
                "reminder_at": remind_at,
            },
        )
        task_id = response.json()["id"]

        response = await test_client.post(f"/tasks/{task_id}/complete")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
        assert data["completed_at"] is not None

        # Verify reminders cancelled
        response = await test_client.get(f"/reminders/target/task/{task_id}?status=pending")
        reminders = response.json()
        assert len(reminders) == 0

    @pytest.mark.asyncio
    async def test_cancel_task(self, test_client):
        """DELETE /tasks/{id} cancels task."""
        response = await test_client.post(
            "/tasks",
            json={"title": "To cancel"},
        )
        task_id = response.json()["id"]

        response = await test_client.delete(f"/tasks/{task_id}")
        assert response.status_code == 204

        # Verify cancelled
        response = await test_client.get(f"/tasks/{task_id}")
        data = response.json()
        assert data["status"] == "cancelled"
        assert data["is_archived"] is True

    @pytest.mark.asyncio
    async def test_list_tasks(self, test_client):
        """GET /tasks returns paginated list."""
        for i in range(5):
            await test_client.post(
                "/tasks",
                json={"title": f"Task {i}"},
            )

        response = await test_client.get("/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5

    @pytest.mark.asyncio
    async def test_list_tasks_filter_status(self, test_client):
        """GET /tasks?status=open filters correctly."""
        response = await test_client.post(
            "/tasks",
            json={"title": "Open task"},
        )
        open_id = response.json()["id"]

        response = await test_client.post(
            "/tasks",
            json={"title": "Done task"},
        )
        done_id = response.json()["id"]
        await test_client.post(f"/tasks/{done_id}/complete")

        response = await test_client.get("/tasks?status=open")
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == open_id

    @pytest.mark.asyncio
    async def test_list_overdue_tasks(self, test_client):
        """GET /tasks/overdue returns overdue tasks."""
        now = datetime.now(timezone.utc)

        # Overdue task
        await test_client.post(
            "/tasks",
            json={
                "title": "Overdue",
                "due_at": (now - timedelta(days=1)).isoformat(),
            },
        )

        # Future task
        await test_client.post(
            "/tasks",
            json={
                "title": "Future",
                "due_at": (now + timedelta(days=1)).isoformat(),
            },
        )

        response = await test_client.get("/tasks/overdue")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Overdue"

    @pytest.mark.asyncio
    async def test_get_tasks_for_target(self, test_client):
        """GET /tasks/target/{type}/{id} returns target's tasks."""
        await test_client.post(
            "/tasks",
            json={"title": "T1", "target_type": "deal", "target_id": 100},
        )
        await test_client.post(
            "/tasks",
            json={"title": "T2", "target_type": "deal", "target_id": 100},
        )
        await test_client.post(
            "/tasks",
            json={"title": "T3", "target_type": "deal", "target_id": 200},
        )

        response = await test_client.get("/tasks/target/deal/100")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_intervention_logged_on_create(self, test_client):
        """Creating task logs intervention."""
        await test_client.post(
            "/tasks",
            json={"title": "Test task"},
        )

        response = await test_client.get(
            "/interventions?object_type=task&action_type=task_created"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_intervention_logged_on_complete(self, test_client):
        """Completing task logs intervention."""
        response = await test_client.post(
            "/tasks",
            json={"title": "To complete"},
        )
        task_id = response.json()["id"]

        await test_client.post(f"/tasks/{task_id}/complete")

        response = await test_client.get(
            f"/interventions?object_type=task&object_id={task_id}&action_type=task_completed"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_critical_tasks_first(self, test_client):
        """Critical tasks appear first in list."""
        await test_client.post(
            "/tasks",
            json={"title": "Normal", "is_critical": False},
        )
        await test_client.post(
            "/tasks",
            json={"title": "Critical", "is_critical": True},
        )

        response = await test_client.get("/tasks")
        data = response.json()
        assert data["items"][0]["is_critical"] is True

    @pytest.mark.asyncio
    async def test_pagination(self, test_client):
        """Pagination works correctly."""
        for i in range(10):
            await test_client.post(
                "/tasks",
                json={"title": f"Task {i}"},
            )

        response = await test_client.get("/tasks?page=1&page_size=3")
        data = response.json()
        assert data["total"] == 10
        assert len(data["items"]) == 3
        assert data["page"] == 1

        response = await test_client.get("/tasks?page=2&page_size=3")
        data = response.json()
        assert len(data["items"]) == 3
        assert data["page"] == 2
