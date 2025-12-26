"""Integration tests for Reminder API endpoints."""

import pytest
from datetime import datetime, timedelta, timezone


class TestReminderAPI:
    """Integration tests for /reminders endpoints."""

    @pytest.mark.asyncio
    async def test_create_reminder(self, test_client):
        """POST /reminders creates reminder."""
        remind_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        response = await test_client.post(
            "/reminders",
            json={
                "target_type": "task",
                "target_id": 123,
                "remind_at": remind_at,
                "channel": "email",
                "message": "Don't forget!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["target_type"] == "task"
        assert data["target_id"] == 123
        assert data["channel"] == "email"
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_reminder_default_channel(self, test_client):
        """POST /reminders uses default channel."""
        remind_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        response = await test_client.post(
            "/reminders",
            json={
                "target_type": "note",
                "target_id": 456,
                "remind_at": remind_at,
            },
        )
        assert response.status_code == 201
        assert response.json()["channel"] == "in_app"

    @pytest.mark.asyncio
    async def test_get_reminder(self, test_client):
        """GET /reminders/{id} returns reminder."""
        # Create reminder
        remind_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        response = await test_client.post(
            "/reminders",
            json={
                "target_type": "task",
                "target_id": 1,
                "remind_at": remind_at,
            },
        )
        reminder_id = response.json()["id"]

        # Get reminder
        response = await test_client.get(f"/reminders/{reminder_id}")
        assert response.status_code == 200
        assert response.json()["id"] == reminder_id

    @pytest.mark.asyncio
    async def test_get_reminder_not_found(self, test_client):
        """GET /reminders/{id} returns 404 for non-existent."""
        response = await test_client.get("/reminders/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_reminders(self, test_client):
        """GET /reminders returns paginated list."""
        # Create reminders
        for i in range(5):
            remind_at = (datetime.now(timezone.utc) + timedelta(hours=i+1)).isoformat()
            await test_client.post(
                "/reminders",
                json={
                    "target_type": "task",
                    "target_id": i,
                    "remind_at": remind_at,
                },
            )

        response = await test_client.get("/reminders")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5

    @pytest.mark.asyncio
    async def test_list_pending_reminders(self, test_client):
        """GET /reminders/pending returns pending only."""
        now = datetime.now(timezone.utc)

        # Create past reminder (should be returned)
        past_time = (now - timedelta(hours=1)).isoformat()
        await test_client.post(
            "/reminders",
            json={
                "target_type": "task",
                "target_id": 1,
                "remind_at": past_time,
            },
        )

        # Create future reminder (should not be returned)
        future_time = (now + timedelta(hours=24)).isoformat()
        await test_client.post(
            "/reminders",
            json={
                "target_type": "task",
                "target_id": 2,
                "remind_at": future_time,
            },
        )

        response = await test_client.get("/reminders/pending")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["target_id"] == 1

    @pytest.mark.asyncio
    async def test_dismiss_reminder(self, test_client):
        """POST /reminders/{id}/dismiss updates status."""
        # Create reminder
        remind_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        response = await test_client.post(
            "/reminders",
            json={
                "target_type": "task",
                "target_id": 1,
                "remind_at": remind_at,
            },
        )
        reminder_id = response.json()["id"]

        # Dismiss reminder
        response = await test_client.post(f"/reminders/{reminder_id}/dismiss")
        assert response.status_code == 200
        assert response.json()["status"] == "dismissed"

    @pytest.mark.asyncio
    async def test_cancel_reminder(self, test_client):
        """DELETE /reminders/{id} cancels reminder."""
        # Create reminder
        remind_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        response = await test_client.post(
            "/reminders",
            json={
                "target_type": "task",
                "target_id": 1,
                "remind_at": remind_at,
            },
        )
        reminder_id = response.json()["id"]

        # Cancel reminder
        response = await test_client.delete(f"/reminders/{reminder_id}")
        assert response.status_code == 204

        # Verify cancelled
        response = await test_client.get(f"/reminders/{reminder_id}")
        assert response.json()["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_reminder_not_found(self, test_client):
        """DELETE /reminders/{id} returns 404 for non-existent."""
        response = await test_client.delete("/reminders/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_reminders_for_target(self, test_client):
        """GET /reminders/target/{type}/{id} returns target's reminders."""
        now = datetime.now(timezone.utc)

        # Create reminders for same target
        for i in range(3):
            await test_client.post(
                "/reminders",
                json={
                    "target_type": "task",
                    "target_id": 100,
                    "remind_at": (now + timedelta(hours=i+1)).isoformat(),
                },
            )

        # Create reminder for different target
        await test_client.post(
            "/reminders",
            json={
                "target_type": "task",
                "target_id": 200,
                "remind_at": (now + timedelta(hours=1)).isoformat(),
            },
        )

        response = await test_client.get("/reminders/target/task/100")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(r["target_id"] == 100 for r in data)

    @pytest.mark.asyncio
    async def test_cancel_reminders_for_target(self, test_client):
        """DELETE /reminders/target/{type}/{id} cancels all target's reminders."""
        now = datetime.now(timezone.utc)

        # Create reminders for same target
        for i in range(3):
            await test_client.post(
                "/reminders",
                json={
                    "target_type": "task",
                    "target_id": 100,
                    "remind_at": (now + timedelta(hours=i+1)).isoformat(),
                },
            )

        response = await test_client.delete("/reminders/target/task/100")
        assert response.status_code == 200
        assert response.json()["cancelled"] == 3

    @pytest.mark.asyncio
    async def test_filter_by_status(self, test_client):
        """GET /reminders?status=pending filters correctly."""
        now = datetime.now(timezone.utc)

        # Create and dismiss one reminder
        response = await test_client.post(
            "/reminders",
            json={
                "target_type": "task",
                "target_id": 1,
                "remind_at": (now + timedelta(hours=1)).isoformat(),
            },
        )
        dismissed_id = response.json()["id"]
        await test_client.post(f"/reminders/{dismissed_id}/dismiss")

        # Create another pending reminder
        await test_client.post(
            "/reminders",
            json={
                "target_type": "task",
                "target_id": 2,
                "remind_at": (now + timedelta(hours=2)).isoformat(),
            },
        )

        response = await test_client.get("/reminders?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_filter_by_channel(self, test_client):
        """GET /reminders?channel=email filters correctly."""
        now = datetime.now(timezone.utc)

        await test_client.post(
            "/reminders",
            json={
                "target_type": "task",
                "target_id": 1,
                "remind_at": (now + timedelta(hours=1)).isoformat(),
                "channel": "email",
            },
        )
        await test_client.post(
            "/reminders",
            json={
                "target_type": "task",
                "target_id": 2,
                "remind_at": (now + timedelta(hours=1)).isoformat(),
                "channel": "in_app",
            },
        )

        response = await test_client.get("/reminders?channel=email")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["channel"] == "email"

    @pytest.mark.asyncio
    async def test_reminder_creation_logs_intervention(self, test_client):
        """Creating reminder logs intervention."""
        remind_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        await test_client.post(
            "/reminders",
            json={
                "target_type": "task",
                "target_id": 123,
                "remind_at": remind_at,
            },
        )

        response = await test_client.get(
            "/interventions?object_type=reminder&action_type=reminder_created"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_reminder_dismissal_logs_intervention(self, test_client):
        """Dismissing reminder logs intervention."""
        remind_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        response = await test_client.post(
            "/reminders",
            json={
                "target_type": "task",
                "target_id": 1,
                "remind_at": remind_at,
            },
        )
        reminder_id = response.json()["id"]

        await test_client.post(f"/reminders/{reminder_id}/dismiss")

        response = await test_client.get(
            f"/interventions?object_type=reminder&object_id={reminder_id}&action_type=reminder_dismissed"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_update_reminder(self, test_client):
        """PUT /reminders/{id} updates reminder."""
        now = datetime.now(timezone.utc)
        remind_at = (now + timedelta(hours=24)).isoformat()
        response = await test_client.post(
            "/reminders",
            json={
                "target_type": "task",
                "target_id": 1,
                "remind_at": remind_at,
                "channel": "in_app",
            },
        )
        reminder_id = response.json()["id"]

        # Update reminder
        new_time = (now + timedelta(hours=48)).isoformat()
        response = await test_client.put(
            f"/reminders/{reminder_id}",
            json={
                "remind_at": new_time,
                "channel": "email",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == "email"

    @pytest.mark.asyncio
    async def test_pagination(self, test_client):
        """Pagination works correctly."""
        now = datetime.now(timezone.utc)

        # Create 10 reminders
        for i in range(10):
            await test_client.post(
                "/reminders",
                json={
                    "target_type": "task",
                    "target_id": i,
                    "remind_at": (now + timedelta(hours=i+1)).isoformat(),
                },
            )

        # Get first page
        response = await test_client.get("/reminders?page=1&page_size=3")
        data = response.json()
        assert data["total"] == 10
        assert len(data["items"]) == 3
        assert data["page"] == 1

        # Get second page
        response = await test_client.get("/reminders?page=2&page_size=3")
        data = response.json()
        assert len(data["items"]) == 3
        assert data["page"] == 2
