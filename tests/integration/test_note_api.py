"""Integration tests for Internal Note API endpoints."""

import pytest
from datetime import datetime, timedelta, timezone


class TestNoteAPI:
    """Integration tests for /notes endpoints."""

    @pytest.mark.asyncio
    async def test_create_note(self, test_client):
        """POST /notes creates note."""
        response = await test_client.post(
            "/notes",
            json={
                "content": "Important note about this deal",
                "pinned": True,
                "tags": "important,followup",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["content"] == "Important note about this deal"
        assert data["pinned"] is True
        assert data["tags"] == "important,followup"

    @pytest.mark.asyncio
    async def test_create_note_for_deal(self, test_client):
        """POST /notes creates note linked to deal."""
        response = await test_client.post(
            "/notes",
            json={
                "content": "Note for deal",
                "target_type": "deal",
                "target_id": 123,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["target_type"] == "deal"
        assert data["target_id"] == 123

    @pytest.mark.asyncio
    async def test_create_note_with_review(self, test_client):
        """Note with review_at creates reminder."""
        review_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        response = await test_client.post(
            "/notes",
            json={
                "content": "Review this later",
                "review_at": review_at,
                "reminder_channel": "email",
            },
        )
        assert response.status_code == 201
        note_id = response.json()["id"]

        # Verify reminder was created
        response = await test_client.get(f"/reminders/target/note/{note_id}")
        assert response.status_code == 200
        reminders = response.json()
        assert len(reminders) == 1
        assert reminders[0]["channel"] == "email"

    @pytest.mark.asyncio
    async def test_get_note(self, test_client):
        """GET /notes/{id} returns note."""
        response = await test_client.post(
            "/notes",
            json={"content": "Test note"},
        )
        note_id = response.json()["id"]

        response = await test_client.get(f"/notes/{note_id}")
        assert response.status_code == 200
        assert response.json()["content"] == "Test note"

    @pytest.mark.asyncio
    async def test_get_note_not_found(self, test_client):
        """GET /notes/{id} returns 404 for non-existent."""
        response = await test_client.get("/notes/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_note(self, test_client):
        """PUT /notes/{id} updates note."""
        response = await test_client.post(
            "/notes",
            json={"content": "Original", "pinned": False},
        )
        note_id = response.json()["id"]

        response = await test_client.put(
            f"/notes/{note_id}",
            json={"content": "Updated", "pinned": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated"
        assert data["pinned"] is True

    @pytest.mark.asyncio
    async def test_archive_note(self, test_client):
        """DELETE /notes/{id} archives note and cancels reminders."""
        review_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        response = await test_client.post(
            "/notes",
            json={
                "content": "To archive",
                "review_at": review_at,
            },
        )
        note_id = response.json()["id"]

        response = await test_client.delete(f"/notes/{note_id}")
        assert response.status_code == 204

        # Verify archived
        response = await test_client.get(f"/notes/{note_id}")
        assert response.json()["is_archived"] is True

        # Verify reminders cancelled
        response = await test_client.get(f"/reminders/target/note/{note_id}?status=pending")
        reminders = response.json()
        assert len(reminders) == 0

    @pytest.mark.asyncio
    async def test_list_notes(self, test_client):
        """GET /notes returns paginated list."""
        for i in range(5):
            await test_client.post(
                "/notes",
                json={"content": f"Note {i}"},
            )

        response = await test_client.get("/notes")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5

    @pytest.mark.asyncio
    async def test_pinned_notes_first(self, test_client):
        """GET /notes returns pinned first."""
        await test_client.post(
            "/notes",
            json={"content": "Normal"},
        )
        await test_client.post(
            "/notes",
            json={"content": "Pinned", "pinned": True},
        )
        await test_client.post(
            "/notes",
            json={"content": "Normal 2"},
        )

        response = await test_client.get("/notes")
        data = response.json()
        assert data["items"][0]["pinned"] is True

    @pytest.mark.asyncio
    async def test_list_pinned_notes(self, test_client):
        """GET /notes/pinned returns only pinned notes."""
        await test_client.post(
            "/notes",
            json={"content": "Normal"},
        )
        await test_client.post(
            "/notes",
            json={"content": "Pinned 1", "pinned": True},
        )
        await test_client.post(
            "/notes",
            json={"content": "Pinned 2", "pinned": True},
        )

        response = await test_client.get("/notes/pinned")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(n["pinned"] for n in data)

    @pytest.mark.asyncio
    async def test_filter_by_target(self, test_client):
        """GET /notes?target_type=deal&target_id=100 filters correctly."""
        await test_client.post(
            "/notes",
            json={"content": "N1", "target_type": "deal", "target_id": 100},
        )
        await test_client.post(
            "/notes",
            json={"content": "N2", "target_type": "deal", "target_id": 100},
        )
        await test_client.post(
            "/notes",
            json={"content": "N3", "target_type": "deal", "target_id": 200},
        )

        response = await test_client.get("/notes?target_type=deal&target_id=100")
        data = response.json()
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_filter_by_tags(self, test_client):
        """GET /notes?tags=important filters correctly."""
        await test_client.post(
            "/notes",
            json={"content": "N1", "tags": "important,urgent"},
        )
        await test_client.post(
            "/notes",
            json={"content": "N2", "tags": "followup"},
        )

        response = await test_client.get("/notes?tags=important")
        data = response.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_search_notes(self, test_client):
        """GET /notes?search=client searches content."""
        await test_client.post(
            "/notes",
            json={"content": "Meeting notes from client call"},
        )
        await test_client.post(
            "/notes",
            json={"content": "Internal memo"},
        )

        response = await test_client.get("/notes?search=client")
        data = response.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_get_notes_for_target(self, test_client):
        """GET /notes/target/{type}/{id} returns target's notes."""
        await test_client.post(
            "/notes",
            json={"content": "N1", "target_type": "deal", "target_id": 100},
        )
        await test_client.post(
            "/notes",
            json={"content": "N2", "target_type": "deal", "target_id": 100, "pinned": True},
        )
        await test_client.post(
            "/notes",
            json={"content": "N3", "target_type": "deal", "target_id": 200},
        )

        response = await test_client.get("/notes/target/deal/100")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Pinned should be first
        assert data[0]["pinned"] is True

    @pytest.mark.asyncio
    async def test_intervention_logged_on_create(self, test_client):
        """Creating note logs intervention."""
        await test_client.post(
            "/notes",
            json={"content": "Test note"},
        )

        response = await test_client.get(
            "/interventions?object_type=note&action_type=note_added"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_intervention_logged_on_archive(self, test_client):
        """Archiving note logs intervention."""
        response = await test_client.post(
            "/notes",
            json={"content": "To archive"},
        )
        note_id = response.json()["id"]

        await test_client.delete(f"/notes/{note_id}")

        response = await test_client.get(
            f"/interventions?object_type=note&object_id={note_id}&action_type=note_archived"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_pagination(self, test_client):
        """Pagination works correctly."""
        for i in range(10):
            await test_client.post(
                "/notes",
                json={"content": f"Note {i}"},
            )

        response = await test_client.get("/notes?page=1&page_size=3")
        data = response.json()
        assert data["total"] == 10
        assert len(data["items"]) == 3
        assert data["page"] == 1

        response = await test_client.get("/notes?page=2&page_size=3")
        data = response.json()
        assert len(data["items"]) == 3
        assert data["page"] == 2
