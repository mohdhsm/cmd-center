"""Integration tests for Employee API endpoints."""

import pytest


class TestEmployeeAPI:
    """Integration tests for /employees endpoints."""

    @pytest.mark.asyncio
    async def test_create_and_get_employee(self, test_client):
        """POST creates employee, GET retrieves it."""
        # Create employee
        response = await test_client.post(
            "/employees",
            json={
                "full_name": "John Doe",
                "role_title": "Software Engineer",
                "department": "Engineering",
                "email": "john@example.com",
            },
        )
        assert response.status_code == 201
        data = response.json()
        employee_id = data["id"]
        assert data["full_name"] == "John Doe"
        assert data["is_active"] is True

        # Get employee
        response = await test_client.get(f"/employees/{employee_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == employee_id
        assert data["full_name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_create_employee_with_manager(self, test_client):
        """Can create employee with reports_to relationship."""
        # Create manager
        response = await test_client.post(
            "/employees",
            json={"full_name": "Manager", "role_title": "Team Lead"},
        )
        manager_id = response.json()["id"]

        # Create employee reporting to manager
        response = await test_client.post(
            "/employees",
            json={
                "full_name": "Employee",
                "role_title": "Developer",
                "reports_to_employee_id": manager_id,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["reports_to_employee_id"] == manager_id

        # Get employee - should include reports_to_name
        response = await test_client.get(f"/employees/{data['id']}")
        data = response.json()
        assert data["reports_to_name"] == "Manager"

    @pytest.mark.asyncio
    async def test_update_employee(self, test_client):
        """PUT updates employee fields."""
        # Create employee
        response = await test_client.post(
            "/employees",
            json={"full_name": "Original", "role_title": "Dev"},
        )
        employee_id = response.json()["id"]

        # Update employee
        response = await test_client.put(
            f"/employees/{employee_id}",
            json={"full_name": "Updated", "department": "Sales"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated"
        assert data["department"] == "Sales"
        assert data["role_title"] == "Dev"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_employee_not_found(self, test_client):
        """PUT returns 404 for non-existent employee."""
        response = await test_client.put(
            "/employees/99999",
            json={"full_name": "Test"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_employee(self, test_client):
        """DELETE soft-deletes employee."""
        # Create employee
        response = await test_client.post(
            "/employees",
            json={"full_name": "To Delete", "role_title": "Dev"},
        )
        employee_id = response.json()["id"]

        # Delete employee
        response = await test_client.delete(f"/employees/{employee_id}")
        assert response.status_code == 204

        # Verify employee is inactive
        response = await test_client.get(f"/employees/{employee_id}")
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    @pytest.mark.asyncio
    async def test_delete_employee_not_found(self, test_client):
        """DELETE returns 404 for non-existent employee."""
        response = await test_client.delete("/employees/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_employees(self, test_client):
        """GET /employees returns paginated list."""
        # Create multiple employees
        for i in range(5):
            await test_client.post(
                "/employees",
                json={"full_name": f"Employee {i}", "role_title": "Dev"},
            )

        response = await test_client.get("/employees")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5

    @pytest.mark.asyncio
    async def test_list_employees_filter_department(self, test_client):
        """Filter employees by department."""
        await test_client.post(
            "/employees",
            json={"full_name": "Eng 1", "role_title": "Dev", "department": "Engineering"},
        )
        await test_client.post(
            "/employees",
            json={"full_name": "Sales 1", "role_title": "Rep", "department": "Sales"},
        )

        response = await test_client.get("/employees?department=Engineering")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["department"] == "Engineering"

    @pytest.mark.asyncio
    async def test_list_employees_filter_active(self, test_client):
        """Filter employees by active status."""
        # Create and delete an employee
        response = await test_client.post(
            "/employees",
            json={"full_name": "Active", "role_title": "Dev"},
        )
        active_id = response.json()["id"]

        response = await test_client.post(
            "/employees",
            json={"full_name": "Inactive", "role_title": "Dev"},
        )
        inactive_id = response.json()["id"]
        await test_client.delete(f"/employees/{inactive_id}")

        response = await test_client.get("/employees?is_active=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == active_id

    @pytest.mark.asyncio
    async def test_list_employees_search(self, test_client):
        """Search employees by name."""
        await test_client.post(
            "/employees",
            json={"full_name": "John Smith", "role_title": "Dev"},
        )
        await test_client.post(
            "/employees",
            json={"full_name": "Jane Doe", "role_title": "Dev"},
        )

        response = await test_client.get("/employees?search=John")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "John" in data["items"][0]["full_name"]

    @pytest.mark.asyncio
    async def test_list_employees_pagination(self, test_client):
        """Pagination works correctly."""
        for i in range(10):
            await test_client.post(
                "/employees",
                json={"full_name": f"Employee {i:02d}", "role_title": "Dev"},
            )

        # Get first page
        response = await test_client.get("/employees?page=1&page_size=3")
        data = response.json()
        assert data["total"] == 10
        assert len(data["items"]) == 3
        assert data["page"] == 1

        # Get second page
        response = await test_client.get("/employees?page=2&page_size=3")
        data = response.json()
        assert len(data["items"]) == 3
        assert data["page"] == 2

    @pytest.mark.asyncio
    async def test_intervention_logged_on_create(self, test_client):
        """Creating employee logs intervention."""
        # Create employee
        await test_client.post(
            "/employees",
            json={"full_name": "Test User", "role_title": "Dev"},
        )

        # Check interventions
        response = await test_client.get(
            "/interventions?object_type=employee&action_type=employee_created"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any("Test User" in i["summary"] for i in data["items"])

    @pytest.mark.asyncio
    async def test_intervention_logged_on_update(self, test_client):
        """Updating employee logs intervention."""
        # Create employee
        response = await test_client.post(
            "/employees",
            json={"full_name": "Original", "role_title": "Dev"},
        )
        employee_id = response.json()["id"]

        # Update employee
        await test_client.put(
            f"/employees/{employee_id}",
            json={"full_name": "Updated"},
        )

        # Check interventions
        response = await test_client.get(
            f"/interventions?object_type=employee&object_id={employee_id}&action_type=employee_updated"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_intervention_logged_on_delete(self, test_client):
        """Deleting employee logs intervention."""
        # Create and delete employee
        response = await test_client.post(
            "/employees",
            json={"full_name": "To Delete", "role_title": "Dev"},
        )
        employee_id = response.json()["id"]
        await test_client.delete(f"/employees/{employee_id}")

        # Check interventions
        response = await test_client.get(
            f"/interventions?object_type=employee&object_id={employee_id}&action_type=employee_deactivated"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


class TestInterventionAPI:
    """Integration tests for /interventions endpoints."""

    @pytest.mark.asyncio
    async def test_list_interventions(self, test_client):
        """GET /interventions returns paginated list."""
        # Create some interventions via employee operations
        await test_client.post(
            "/employees",
            json={"full_name": "Test", "role_title": "Dev"},
        )

        response = await test_client.get("/interventions")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_intervention_by_id(self, test_client):
        """GET /interventions/{id} returns single intervention."""
        # Create an intervention
        await test_client.post(
            "/employees",
            json={"full_name": "Test", "role_title": "Dev"},
        )

        # Get the intervention
        response = await test_client.get("/interventions?page_size=1")
        intervention_id = response.json()["items"][0]["id"]

        response = await test_client.get(f"/interventions/{intervention_id}")
        assert response.status_code == 200
        assert response.json()["id"] == intervention_id

    @pytest.mark.asyncio
    async def test_get_intervention_not_found(self, test_client):
        """GET /interventions/{id} returns 404 for non-existent."""
        response = await test_client.get("/interventions/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_interventions_for_object(self, test_client):
        """GET /interventions/object/{type}/{id} returns history."""
        # Create and update an employee
        response = await test_client.post(
            "/employees",
            json={"full_name": "Original", "role_title": "Dev"},
        )
        employee_id = response.json()["id"]

        await test_client.put(
            f"/employees/{employee_id}",
            json={"full_name": "Updated"},
        )

        # Get interventions for this employee
        response = await test_client.get(
            f"/interventions/object/employee/{employee_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2  # Create + Update

    @pytest.mark.asyncio
    async def test_get_interventions_by_actor(self, test_client):
        """GET /interventions/actor/{actor} returns actor's actions."""
        # Create employee with custom actor
        await test_client.post(
            "/employees?actor=test_user",
            json={"full_name": "Test", "role_title": "Dev"},
        )

        response = await test_client.get("/interventions/actor/test_user")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(i["actor"] == "test_user" for i in data)
