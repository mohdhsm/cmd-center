"""Integration tests for Loops API."""

from datetime import datetime, timedelta, timezone

import pytest


class TestLoopsAPI:
    """Integration tests for Loop API endpoints."""

    @pytest.fixture(autouse=True)
    def setup_loops(self, override_db):
        """Register test loops before each test."""
        # Import and register loops
        from cmd_center.backend.services.loop_engine import loop_registry
        from cmd_center.backend.services.loops import (
            DocsExpiryLoop,
            BonusDueLoop,
            TaskOverdueLoop,
            ReminderProcessingLoop,
        )

        # Clear and re-register for clean test state
        loop_registry._loops.clear()
        loop_registry.register(DocsExpiryLoop())
        loop_registry.register(BonusDueLoop())
        loop_registry.register(TaskOverdueLoop())
        loop_registry.register(ReminderProcessingLoop())

    @pytest.mark.asyncio
    async def test_get_loops_status(self, test_client):
        """GET /loops/status returns all registered loops."""
        response = await test_client.get("/loops/status")
        assert response.status_code == 200

        data = response.json()
        assert "loops" in data
        assert len(data["loops"]) == 4  # All 4 loops registered
        assert "total_runs_today" in data
        assert "total_findings_today" in data

        # Check loop info
        loop_names = [l["name"] for l in data["loops"]]
        assert "docs_expiry" in loop_names
        assert "bonus_due" in loop_names
        assert "task_overdue" in loop_names
        assert "reminder_processing" in loop_names

    @pytest.mark.asyncio
    async def test_run_specific_loop(self, test_client):
        """POST /loops/{name}/run triggers specific loop."""
        response = await test_client.post("/loops/docs_expiry/run")
        assert response.status_code == 200

        data = response.json()
        assert data["loop_name"] == "docs_expiry"
        assert data["status"] == "completed"
        assert data["finished_at"] is not None

    @pytest.mark.asyncio
    async def test_run_nonexistent_loop(self, test_client):
        """POST /loops/{name}/run returns 404 for unknown loop."""
        response = await test_client.post("/loops/nonexistent/run")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_run_all_loops(self, test_client):
        """POST /loops/run-all triggers all enabled loops."""
        response = await test_client.post("/loops/run-all")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 4  # All 4 loops ran
        assert all(r["status"] == "completed" for r in data)

    @pytest.mark.asyncio
    async def test_list_loop_runs(self, test_client):
        """GET /loops/runs lists loop runs."""
        # Run a loop first
        await test_client.post("/loops/docs_expiry/run")
        await test_client.post("/loops/bonus_due/run")

        response = await test_client.get("/loops/runs")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

    @pytest.mark.asyncio
    async def test_list_loop_runs_filter_by_name(self, test_client):
        """GET /loops/runs filters by loop_name."""
        # Run both loops
        await test_client.post("/loops/docs_expiry/run")
        await test_client.post("/loops/bonus_due/run")

        response = await test_client.get("/loops/runs?loop_name=docs_expiry")
        assert response.status_code == 200

        data = response.json()
        assert all(r["loop_name"] == "docs_expiry" for r in data["items"])

    @pytest.mark.asyncio
    async def test_get_loop_run_by_id(self, test_client):
        """GET /loops/runs/{id} returns run with findings."""
        # Run a loop
        run_response = await test_client.post("/loops/docs_expiry/run")
        run_id = run_response.json()["id"]

        response = await test_client.get(f"/loops/runs/{run_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == run_id
        assert "findings" in data

    @pytest.mark.asyncio
    async def test_get_loop_run_not_found(self, test_client):
        """GET /loops/runs/{id} returns 404 for unknown run."""
        response = await test_client.get("/loops/runs/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_findings(self, test_client):
        """GET /loops/findings lists all findings."""
        # Create a document that will generate a finding
        now = datetime.now(timezone.utc)
        await test_client.post("/documents", json={
            "title": "Expiring Doc",
            "document_type": "license",
            "expiry_date": (now + timedelta(days=10)).isoformat(),
        })

        # Run the loop
        await test_client.post("/loops/docs_expiry/run")

        response = await test_client.get("/loops/findings")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_list_findings_filter_by_severity(self, test_client):
        """GET /loops/findings filters by severity."""
        # Create critical document (expiring in 5 days)
        now = datetime.now(timezone.utc)
        await test_client.post("/documents", json={
            "title": "Critical Doc",
            "document_type": "license",
            "expiry_date": (now + timedelta(days=5)).isoformat(),
        })

        await test_client.post("/loops/docs_expiry/run")

        response = await test_client.get("/loops/findings?severity=critical")
        assert response.status_code == 200

        data = response.json()
        assert all(f["severity"] == "critical" for f in data["items"])

    @pytest.mark.asyncio
    async def test_list_findings_filter_by_target_type(self, test_client):
        """GET /loops/findings filters by target_type."""
        # Create expiring document
        now = datetime.now(timezone.utc)
        await test_client.post("/documents", json={
            "title": "Test Doc",
            "document_type": "license",
            "expiry_date": (now + timedelta(days=15)).isoformat(),
        })

        await test_client.post("/loops/docs_expiry/run")

        response = await test_client.get("/loops/findings?target_type=document")
        assert response.status_code == 200

        data = response.json()
        assert all(f["target_type"] == "document" for f in data["items"])


class TestLoopEndToEnd:
    """End-to-end tests for loop workflows."""

    @pytest.fixture(autouse=True)
    def setup_loops(self, override_db):
        """Register test loops before each test."""
        from cmd_center.backend.services.loop_engine import loop_registry
        from cmd_center.backend.services.loops import (
            DocsExpiryLoop,
            BonusDueLoop,
            TaskOverdueLoop,
            ReminderProcessingLoop,
        )

        loop_registry._loops.clear()
        loop_registry.register(DocsExpiryLoop())
        loop_registry.register(BonusDueLoop())
        loop_registry.register(TaskOverdueLoop())
        loop_registry.register(ReminderProcessingLoop())

    @pytest.mark.asyncio
    async def test_docs_expiry_loop_end_to_end(self, test_client):
        """Create expiring doc -> run loop -> finding created."""
        now = datetime.now(timezone.utc)

        # Create document expiring in 10 days
        doc_response = await test_client.post("/documents", json={
            "title": "Expiring License",
            "document_type": "license",
            "expiry_date": (now + timedelta(days=10)).isoformat(),
        })
        doc_id = doc_response.json()["id"]

        # Run the loop
        run_response = await test_client.post("/loops/docs_expiry/run")
        assert run_response.status_code == 200
        assert run_response.json()["findings_count"] >= 1

        # Check findings
        findings_response = await test_client.get(
            f"/loops/findings?target_type=document"
        )
        findings = findings_response.json()["items"]
        doc_findings = [f for f in findings if f["target_id"] == doc_id]
        assert len(doc_findings) >= 1

    @pytest.mark.asyncio
    async def test_reminder_processing_end_to_end(self, test_client):
        """Create pending reminder -> run loop -> reminder sent."""
        now = datetime.now(timezone.utc)

        # Create reminder due in the past
        reminder_response = await test_client.post("/reminders", json={
            "target_type": "test",
            "target_id": 1,
            "remind_at": (now - timedelta(minutes=5)).isoformat(),
            "channel": "in_app",
            "message": "Test reminder",
        })
        reminder_id = reminder_response.json()["id"]

        # Verify it's pending
        check_response = await test_client.get(f"/reminders/{reminder_id}")
        assert check_response.json()["status"] == "pending"

        # Run the loop
        run_response = await test_client.post("/loops/reminder_processing/run")
        assert run_response.status_code == 200

        # Verify reminder was sent
        check_response = await test_client.get(f"/reminders/{reminder_id}")
        assert check_response.json()["status"] == "sent"
        assert check_response.json()["sent_at"] is not None

    @pytest.mark.asyncio
    async def test_loop_runs_logged(self, test_client):
        """All loop runs create LoopRun records."""
        # Run all loops
        await test_client.post("/loops/run-all")

        # Check runs are recorded
        runs_response = await test_client.get("/loops/runs")
        data = runs_response.json()

        assert data["total"] >= 4
        loop_names = set(r["loop_name"] for r in data["items"])
        assert "docs_expiry" in loop_names
        assert "bonus_due" in loop_names
        assert "task_overdue" in loop_names
        assert "reminder_processing" in loop_names
