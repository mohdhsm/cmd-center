"""Unit tests for EmployeeService."""

import pytest
from datetime import datetime, timezone

from cmd_center.backend.db import Employee
from cmd_center.backend.services.employee_service import EmployeeService
from cmd_center.backend.models.employee_models import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeFilters,
)


class TestEmployeeService:
    """Unit tests for EmployeeService CRUD operations."""

    def test_create_employee(self, override_db):
        """Creating employee returns valid Employee with ID."""
        service = EmployeeService(actor="test")
        data = EmployeeCreate(
            full_name="John Doe",
            role_title="Software Engineer",
            department="Engineering",
            email="john@example.com",
        )

        result = service.create_employee(data)

        assert result.id is not None
        assert result.full_name == "John Doe"
        assert result.role_title == "Software Engineer"
        assert result.department == "Engineering"
        assert result.email == "john@example.com"
        assert result.is_active is True

    def test_get_employee_by_id(self, override_db):
        """Can retrieve employee by ID."""
        service = EmployeeService(actor="test")
        data = EmployeeCreate(full_name="Jane Doe", role_title="Designer")
        created = service.create_employee(data)

        result = service.get_employee_by_id(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.full_name == "Jane Doe"

    def test_get_employee_by_id_not_found(self, override_db):
        """Returns None for non-existent employee."""
        service = EmployeeService(actor="test")

        result = service.get_employee_by_id(99999)

        assert result is None

    def test_get_employees_filters_by_department(self, override_db):
        """Department filter returns only matching employees."""
        service = EmployeeService(actor="test")

        # Create employees in different departments
        service.create_employee(EmployeeCreate(
            full_name="Eng 1", role_title="Dev", department="Engineering"
        ))
        service.create_employee(EmployeeCreate(
            full_name="Eng 2", role_title="Dev", department="Engineering"
        ))
        service.create_employee(EmployeeCreate(
            full_name="Sales 1", role_title="Rep", department="Sales"
        ))

        result = service.get_employees(EmployeeFilters(department="Engineering"))

        assert result.total == 2
        assert all(e.department == "Engineering" for e in result.items)

    def test_get_employees_filters_active_only(self, override_db):
        """is_active filter excludes inactive employees."""
        service = EmployeeService(actor="test")

        # Create active and inactive employees
        active = service.create_employee(EmployeeCreate(
            full_name="Active", role_title="Dev"
        ))
        inactive = service.create_employee(EmployeeCreate(
            full_name="Inactive", role_title="Dev"
        ))
        service.delete_employee(inactive.id)  # Soft delete

        result = service.get_employees(EmployeeFilters(is_active=True))

        assert result.total == 1
        assert result.items[0].full_name == "Active"

    def test_get_employees_search_by_name(self, override_db):
        """Search filter matches employee names."""
        service = EmployeeService(actor="test")

        service.create_employee(EmployeeCreate(
            full_name="John Smith", role_title="Dev"
        ))
        service.create_employee(EmployeeCreate(
            full_name="Jane Doe", role_title="Dev"
        ))
        service.create_employee(EmployeeCreate(
            full_name="Johnny Appleseed", role_title="Dev"
        ))

        result = service.get_employees(EmployeeFilters(search="John"))

        assert result.total == 2
        names = [e.full_name for e in result.items]
        assert "John Smith" in names
        assert "Johnny Appleseed" in names

    def test_update_employee(self, override_db):
        """Update changes fields and sets updated_at."""
        service = EmployeeService(actor="test")
        data = EmployeeCreate(full_name="Original Name", role_title="Dev")
        created = service.create_employee(data)

        update_data = EmployeeUpdate(
            full_name="Updated Name",
            department="New Department",
        )
        result = service.update_employee(created.id, update_data)

        assert result is not None
        assert result.full_name == "Updated Name"
        assert result.department == "New Department"
        assert result.role_title == "Dev"  # Unchanged
        assert result.updated_at is not None

    def test_update_employee_partial(self, override_db):
        """Partial update only changes specified fields."""
        service = EmployeeService(actor="test")
        data = EmployeeCreate(
            full_name="Full Name",
            role_title="Dev",
            department="Engineering",
            email="test@example.com",
        )
        created = service.create_employee(data)

        # Only update email
        result = service.update_employee(
            created.id,
            EmployeeUpdate(email="new@example.com"),
        )

        assert result.email == "new@example.com"
        assert result.full_name == "Full Name"
        assert result.department == "Engineering"

    def test_update_employee_not_found(self, override_db):
        """Update returns None for non-existent employee."""
        service = EmployeeService(actor="test")

        result = service.update_employee(99999, EmployeeUpdate(full_name="Test"))

        assert result is None

    def test_soft_delete_employee(self, override_db):
        """Delete sets is_active=False, doesn't remove record."""
        service = EmployeeService(actor="test")
        data = EmployeeCreate(full_name="To Delete", role_title="Dev")
        created = service.create_employee(data)

        deleted = service.delete_employee(created.id)

        assert deleted is True

        # Record still exists but is inactive
        employee = service.get_employee_by_id(created.id)
        assert employee is not None
        assert employee.is_active is False

    def test_soft_delete_not_found(self, override_db):
        """Delete returns False for non-existent employee."""
        service = EmployeeService(actor="test")

        result = service.delete_employee(99999)

        assert result is False

    def test_get_employee_with_reports_to(self, override_db):
        """Can retrieve employee with manager relationship."""
        service = EmployeeService(actor="test")

        # Create manager
        manager = service.create_employee(EmployeeCreate(
            full_name="Manager", role_title="Team Lead"
        ))

        # Create employee reporting to manager
        employee_data = EmployeeCreate(
            full_name="Employee",
            role_title="Dev",
            reports_to_employee_id=manager.id,
        )
        employee = service.create_employee(employee_data)

        # Get with aggregates to check reports_to_name
        result = service.get_employee_with_aggregates(employee.id)

        assert result is not None
        assert result.reports_to_employee_id == manager.id
        assert result.reports_to_name == "Manager"

    def test_get_employee_by_pipedrive_owner_id(self, override_db):
        """Can find employee by Pipedrive owner ID."""
        service = EmployeeService(actor="test")

        # Create employee with Pipedrive link
        data = EmployeeCreate(
            full_name="Pipedrive User",
            role_title="Sales Rep",
            pipedrive_owner_id=12345,
        )
        created = service.create_employee(data)

        result = service.get_employee_by_pipedrive_owner_id(12345)

        assert result is not None
        assert result.id == created.id
        assert result.pipedrive_owner_id == 12345

    def test_get_employee_by_pipedrive_owner_id_not_found(self, override_db):
        """Returns None when Pipedrive owner ID not linked."""
        service = EmployeeService(actor="test")

        result = service.get_employee_by_pipedrive_owner_id(99999)

        assert result is None

    def test_pagination(self, override_db):
        """Pagination works correctly."""
        service = EmployeeService(actor="test")

        # Create 10 employees
        for i in range(10):
            service.create_employee(EmployeeCreate(
                full_name=f"Employee {i:02d}",
                role_title="Dev",
            ))

        # Get page 1
        page1 = service.get_employees(EmployeeFilters(page=1, page_size=3))
        assert page1.total == 10
        assert len(page1.items) == 3
        assert page1.page == 1

        # Get page 2
        page2 = service.get_employees(EmployeeFilters(page=2, page_size=3))
        assert page2.total == 10
        assert len(page2.items) == 3
        assert page2.page == 2

        # Different employees on each page
        page1_ids = {e.id for e in page1.items}
        page2_ids = {e.id for e in page2.items}
        assert page1_ids.isdisjoint(page2_ids)
