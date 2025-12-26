"""Integration tests for Tracker Module APIs (Documents, Bonuses, Employee Logs, Skills)."""

from datetime import datetime, timedelta, timezone

import pytest


class TestDocumentAPI:
    """Integration tests for Document API."""

    @pytest.mark.asyncio
    async def test_create_document(self, test_client):
        """POST /documents creates document."""
        response = await test_client.post("/documents", json={
            "title": "Commercial Registration",
            "document_type": "registration",
            "description": "Company commercial registration",
            "reference_number": "CR-12345",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["title"] == "Commercial Registration"
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_get_document(self, test_client):
        """GET /documents/{id} returns document with files."""
        # Create document
        create_resp = await test_client.post("/documents", json={
            "title": "Test Document",
            "document_type": "license",
        })
        doc_id = create_resp.json()["id"]

        # Get document
        response = await test_client.get(f"/documents/{doc_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Document"
        assert "files" in data

    @pytest.mark.asyncio
    async def test_update_document(self, test_client):
        """PUT /documents/{id} updates document."""
        create_resp = await test_client.post("/documents", json={
            "title": "Original Title",
            "document_type": "license",
        })
        doc_id = create_resp.json()["id"]

        response = await test_client.put(f"/documents/{doc_id}", json={
            "title": "Updated Title",
            "status": "renewal_in_progress",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "renewal_in_progress"

    @pytest.mark.asyncio
    async def test_attach_file(self, test_client):
        """POST /documents/{id}/files attaches file."""
        create_resp = await test_client.post("/documents", json={
            "title": "Document with File",
            "document_type": "contract",
        })
        doc_id = create_resp.json()["id"]

        response = await test_client.post(f"/documents/{doc_id}/files", json={
            "filename": "contract.pdf",
            "file_path": "/uploads/contract.pdf",
            "file_type": "application/pdf",
            "file_size": 1024,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "contract.pdf"
        assert data["version"] == 1

    @pytest.mark.asyncio
    async def test_list_documents_pagination(self, test_client):
        """GET /documents supports pagination."""
        # Create multiple documents
        for i in range(15):
            await test_client.post("/documents", json={
                "title": f"Document {i}",
                "document_type": "license",
            })

        response = await test_client.get("/documents?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 15
        assert len(data["items"]) == 10

    @pytest.mark.asyncio
    async def test_get_expiring_documents(self, test_client):
        """GET /documents/expiring returns documents expiring soon."""
        now = datetime.now(timezone.utc)
        expiry = (now + timedelta(days=15)).isoformat()

        await test_client.post("/documents", json={
            "title": "Expiring Document",
            "document_type": "license",
            "expiry_date": expiry,
        })

        response = await test_client.get("/documents/expiring?within_days=30")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


class TestBonusAPI:
    """Integration tests for Bonus API."""

    @pytest.fixture
    async def employee_id(self, test_client):
        """Create an employee and return its ID."""
        response = await test_client.post("/employees", json={
            "full_name": "Test Employee",
            "role_title": "Developer",
        })
        return response.json()["id"]

    @pytest.mark.asyncio
    async def test_create_bonus(self, test_client, employee_id):
        """POST /bonuses creates bonus."""
        response = await test_client.post("/bonuses", json={
            "employee_id": employee_id,
            "title": "Q4 Performance Bonus",
            "amount": 5000.0,
            "currency": "SAR",
            "bonus_type": "performance",
            "promised_date": datetime.now(timezone.utc).isoformat(),
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Q4 Performance Bonus"
        assert data["status"] == "promised"

    @pytest.mark.asyncio
    async def test_bonus_payment_flow(self, test_client, employee_id):
        """Create bonus -> record payment -> status updated."""
        # Create bonus
        create_resp = await test_client.post("/bonuses", json={
            "employee_id": employee_id,
            "title": "Test Bonus",
            "amount": 1000.0,
            "promised_date": datetime.now(timezone.utc).isoformat(),
        })
        bonus_id = create_resp.json()["id"]

        # Record partial payment
        pay_resp = await test_client.post(f"/bonuses/{bonus_id}/payments", json={
            "amount": 500.0,
            "payment_date": datetime.now(timezone.utc).isoformat(),
        })
        assert pay_resp.status_code == 201

        # Check status updated to partial
        bonus_resp = await test_client.get(f"/bonuses/{bonus_id}")
        assert bonus_resp.json()["status"] == "partial"
        assert bonus_resp.json()["total_paid"] == 500.0

        # Record remaining payment
        await test_client.post(f"/bonuses/{bonus_id}/payments", json={
            "amount": 500.0,
            "payment_date": datetime.now(timezone.utc).isoformat(),
        })

        # Check status updated to paid
        bonus_resp = await test_client.get(f"/bonuses/{bonus_id}")
        assert bonus_resp.json()["status"] == "paid"

    @pytest.mark.asyncio
    async def test_approve_bonus(self, test_client, employee_id):
        """POST /bonuses/{id}/approve approves bonus."""
        create_resp = await test_client.post("/bonuses", json={
            "employee_id": employee_id,
            "title": "Pending Bonus",
            "amount": 1000.0,
            "promised_date": datetime.now(timezone.utc).isoformat(),
        })
        bonus_id = create_resp.json()["id"]

        response = await test_client.post(f"/bonuses/{bonus_id}/approve")
        assert response.status_code == 200
        assert response.json()["status"] == "approved"

    @pytest.mark.asyncio
    async def test_cancel_bonus(self, test_client, employee_id):
        """DELETE /bonuses/{id} cancels bonus."""
        create_resp = await test_client.post("/bonuses", json={
            "employee_id": employee_id,
            "title": "To Cancel",
            "amount": 1000.0,
            "promised_date": datetime.now(timezone.utc).isoformat(),
        })
        bonus_id = create_resp.json()["id"]

        response = await test_client.delete(f"/bonuses/{bonus_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"


class TestEmployeeLogAPI:
    """Integration tests for Employee Log API."""

    @pytest.fixture
    async def employee_id(self, test_client):
        """Create an employee and return its ID."""
        response = await test_client.post("/employees", json={
            "full_name": "Test Employee",
            "role_title": "Developer",
        })
        return response.json()["id"]

    @pytest.mark.asyncio
    async def test_create_log_entry(self, test_client, employee_id):
        """POST /employee-logs creates log entry."""
        response = await test_client.post("/employee-logs", json={
            "employee_id": employee_id,
            "category": "achievement",
            "title": "Completed Project",
            "content": "Successfully completed the major project.",
            "is_positive": True,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["category"] == "achievement"
        assert data["is_positive"] is True

    @pytest.mark.asyncio
    async def test_get_logs_by_employee(self, test_client, employee_id):
        """GET /employee-logs/employee/{id} returns employee logs."""
        await test_client.post("/employee-logs", json={
            "employee_id": employee_id,
            "category": "achievement",
            "title": "Achievement Log",
            "content": "Details...",
        })

        response = await test_client.get(f"/employee-logs/employee/{employee_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_get_employee_summary(self, test_client, employee_id):
        """GET /employee-logs/employee/{id}/summary returns statistics."""
        # Create various logs
        await test_client.post("/employee-logs", json={
            "employee_id": employee_id,
            "category": "achievement",
            "title": "Achievement",
            "content": "...",
            "is_positive": True,
        })
        await test_client.post("/employee-logs", json={
            "employee_id": employee_id,
            "category": "issue",
            "title": "Issue",
            "content": "...",
            "is_positive": False,
        })

        response = await test_client.get(f"/employee-logs/employee/{employee_id}/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_logs"] == 2
        assert data["positive_count"] == 1
        assert data["negative_count"] == 1

    @pytest.mark.asyncio
    async def test_get_recent_issues(self, test_client, employee_id):
        """GET /employee-logs/issues returns issue logs."""
        await test_client.post("/employee-logs", json={
            "employee_id": employee_id,
            "category": "issue",
            "title": "Late Arrival",
            "content": "Arrived late.",
            "severity": "low",
            "is_positive": False,
        })

        response = await test_client.get("/employee-logs/issues")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["category"] == "issue"


class TestSkillAPI:
    """Integration tests for Skill API."""

    @pytest.fixture
    async def employee_id(self, test_client):
        """Create an employee and return its ID."""
        response = await test_client.post("/employees", json={
            "full_name": "Test Developer",
            "role_title": "Developer",
        })
        return response.json()["id"]

    @pytest.mark.asyncio
    async def test_create_skill(self, test_client):
        """POST /skills creates skill."""
        response = await test_client.post("/skills", json={
            "name": "Python Programming",
            "description": "Ability to write Python code",
            "category": "Technical",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Python Programming"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_rate_employee_skill(self, test_client, employee_id):
        """POST /skills/ratings creates skill rating."""
        # Create skill
        skill_resp = await test_client.post("/skills", json={
            "name": "Test Skill",
            "category": "Technical",
        })
        skill_id = skill_resp.json()["id"]

        # Rate employee
        response = await test_client.post("/skills/ratings", json={
            "employee_id": employee_id,
            "skill_id": skill_id,
            "rating": 4,
            "notes": "Good proficiency.",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 4

    @pytest.mark.asyncio
    async def test_get_employee_skill_card(self, test_client, employee_id):
        """GET /skills/employee/{id}/card returns skill card."""
        # Create skills
        skill1_resp = await test_client.post("/skills", json={
            "name": "Skill 1",
            "category": "Technical",
        })
        skill2_resp = await test_client.post("/skills", json={
            "name": "Skill 2",
            "category": "Soft Skills",
        })
        skill1_id = skill1_resp.json()["id"]

        # Rate one skill
        await test_client.post("/skills/ratings", json={
            "employee_id": employee_id,
            "skill_id": skill1_id,
            "rating": 5,
        })

        # Get skill card
        response = await test_client.get(f"/skills/employee/{employee_id}/card")
        assert response.status_code == 200
        data = response.json()
        assert data["employee_name"] == "Test Developer"
        assert len(data["skills"]) == 2  # Both skills listed

    @pytest.mark.asyncio
    async def test_skill_rating_history(self, test_client, employee_id):
        """GET /skills/employee/{emp_id}/skill/{skill_id}/history returns rating history."""
        # Create skill
        skill_resp = await test_client.post("/skills", json={
            "name": "Tracked Skill",
            "category": "Technical",
        })
        skill_id = skill_resp.json()["id"]

        # Rate multiple times
        await test_client.post("/skills/ratings", json={
            "employee_id": employee_id,
            "skill_id": skill_id,
            "rating": 2,
        })
        await test_client.post("/skills/ratings", json={
            "employee_id": employee_id,
            "skill_id": skill_id,
            "rating": 3,
        })
        await test_client.post("/skills/ratings", json={
            "employee_id": employee_id,
            "skill_id": skill_id,
            "rating": 4,
        })

        response = await test_client.get(f"/skills/employee/{employee_id}/skill/{skill_id}/history")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Should be ordered by rated_at desc (latest first)
        assert data[0]["rating"] == 4

    @pytest.mark.asyncio
    async def test_deactivate_skill(self, test_client):
        """DELETE /skills/{id} deactivates skill."""
        create_resp = await test_client.post("/skills", json={
            "name": "To Deactivate",
            "category": "General",
        })
        skill_id = create_resp.json()["id"]

        response = await test_client.delete(f"/skills/{skill_id}")
        assert response.status_code == 200
        assert response.json()["is_active"] is False


class TestTrackerInterventionLogging:
    """Test that all tracker operations log interventions."""

    @pytest.mark.asyncio
    async def test_document_operations_log_interventions(self, test_client):
        """Document CRUD operations log interventions."""
        # Create document
        create_resp = await test_client.post("/documents", json={
            "title": "Test Document",
            "document_type": "license",
        })
        doc_id = create_resp.json()["id"]

        # Update document
        await test_client.put(f"/documents/{doc_id}", json={
            "title": "Updated Title",
        })

        # Check interventions
        response = await test_client.get("/interventions?object_type=document")
        assert response.status_code == 200
        data = response.json()
        # Should have at least create and update interventions
        assert data["total"] >= 2

    @pytest.mark.asyncio
    async def test_bonus_operations_log_interventions(self, test_client):
        """Bonus operations log interventions."""
        # Create employee first
        emp_resp = await test_client.post("/employees", json={
            "full_name": "Test Employee",
            "role_title": "Developer",
        })
        employee_id = emp_resp.json()["id"]

        # Create bonus
        bonus_resp = await test_client.post("/bonuses", json={
            "employee_id": employee_id,
            "title": "Test Bonus",
            "amount": 1000.0,
            "promised_date": datetime.now(timezone.utc).isoformat(),
        })
        bonus_id = bonus_resp.json()["id"]

        # Approve bonus
        await test_client.post(f"/bonuses/{bonus_id}/approve")

        # Check interventions
        response = await test_client.get("/interventions?object_type=bonus")
        assert response.status_code == 200
        data = response.json()
        # Should have create and approve interventions
        assert data["total"] >= 2

    @pytest.mark.asyncio
    async def test_skill_operations_log_interventions(self, test_client):
        """Skill operations log interventions."""
        # Create skill
        skill_resp = await test_client.post("/skills", json={
            "name": "Intervention Test Skill",
            "category": "Technical",
        })
        skill_id = skill_resp.json()["id"]

        # Create employee
        emp_resp = await test_client.post("/employees", json={
            "full_name": "Test Employee",
            "role_title": "Developer",
        })
        employee_id = emp_resp.json()["id"]

        # Rate skill
        await test_client.post("/skills/ratings", json={
            "employee_id": employee_id,
            "skill_id": skill_id,
            "rating": 4,
        })

        # Check skill interventions
        skill_interventions = await test_client.get("/interventions?object_type=skill")
        assert skill_interventions.json()["total"] >= 1

        # Check skill_rating interventions
        rating_interventions = await test_client.get("/interventions?object_type=skill_rating")
        assert rating_interventions.json()["total"] >= 1
