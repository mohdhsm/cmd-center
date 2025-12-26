"""Unit tests for BonusService."""

from datetime import datetime, timedelta, timezone

import pytest

from cmd_center.backend.services.bonus_service import BonusService
from cmd_center.backend.services.employee_service import EmployeeService
from cmd_center.backend.models.bonus_models import (
    BonusCreate,
    BonusUpdate,
    BonusFilters,
    BonusPaymentCreate,
)
from cmd_center.backend.models.employee_models import EmployeeCreate
from cmd_center.backend.constants import BonusStatus


class TestBonusService:
    """Test cases for BonusService."""

    def test_create_bonus(self, override_db):
        """Creates bonus with all fields."""
        # Create an employee first
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = BonusService(actor="test_user")
        data = BonusCreate(
            employee_id=employee.id,
            title="Q4 Performance Bonus",
            description="Bonus for excellent Q4 performance",
            amount=5000.0,
            currency="SAR",
            bonus_type="performance",
            promised_date=datetime.now(timezone.utc),
            due_date=datetime.now(timezone.utc) + timedelta(days=30),
        )
        result = service.create_bonus(data)

        assert result.id is not None
        assert result.title == "Q4 Performance Bonus"
        assert result.amount == 5000.0
        assert result.status == BonusStatus.PROMISED.value

    def test_get_bonus_by_id(self, override_db):
        """Can retrieve bonus by ID."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = BonusService()
        created = service.create_bonus(BonusCreate(
            employee_id=employee.id,
            title="Test Bonus",
            amount=1000.0,
            promised_date=datetime.now(timezone.utc),
        ))

        result = service.get_bonus_by_id(created.id)
        assert result is not None
        assert result.id == created.id

    def test_get_bonus_with_payments(self, override_db):
        """Get bonus with payment history."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = BonusService()
        bonus = service.create_bonus(BonusCreate(
            employee_id=employee.id,
            title="Test Bonus",
            amount=1000.0,
            promised_date=datetime.now(timezone.utc),
        ))

        # Record a payment
        service.record_payment(bonus.id, BonusPaymentCreate(
            amount=500.0,
            payment_date=datetime.now(timezone.utc),
        ))

        result = service.get_bonus_with_payments(bonus.id)
        assert result is not None
        assert len(result.payments) == 1
        assert result.total_paid == 500.0
        assert result.remaining == 500.0

    def test_record_payment_updates_status_to_partial(self, override_db):
        """Records payment and updates status to partial."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = BonusService()
        bonus = service.create_bonus(BonusCreate(
            employee_id=employee.id,
            title="Test Bonus",
            amount=1000.0,
            promised_date=datetime.now(timezone.utc),
        ))

        service.record_payment(bonus.id, BonusPaymentCreate(
            amount=500.0,
            payment_date=datetime.now(timezone.utc),
        ))

        result = service.get_bonus_by_id(bonus.id)
        assert result.status == BonusStatus.PARTIAL.value

    def test_record_payment_updates_status_to_paid(self, override_db):
        """Full payment updates status to paid."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = BonusService()
        bonus = service.create_bonus(BonusCreate(
            employee_id=employee.id,
            title="Test Bonus",
            amount=1000.0,
            promised_date=datetime.now(timezone.utc),
        ))

        service.record_payment(bonus.id, BonusPaymentCreate(
            amount=1000.0,
            payment_date=datetime.now(timezone.utc),
        ))

        result = service.get_bonus_by_id(bonus.id)
        assert result.status == BonusStatus.PAID.value

    def test_get_unpaid_bonuses(self, override_db):
        """Returns bonuses with status != paid."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = BonusService()

        # Create unpaid bonus
        unpaid = service.create_bonus(BonusCreate(
            employee_id=employee.id,
            title="Unpaid Bonus",
            amount=1000.0,
            promised_date=datetime.now(timezone.utc),
        ))

        # Create paid bonus
        paid = service.create_bonus(BonusCreate(
            employee_id=employee.id,
            title="Paid Bonus",
            amount=500.0,
            promised_date=datetime.now(timezone.utc),
        ))
        service.record_payment(paid.id, BonusPaymentCreate(
            amount=500.0,
            payment_date=datetime.now(timezone.utc),
        ))

        result = service.get_unpaid_bonuses()
        assert len(result) == 1
        assert result[0].title == "Unpaid Bonus"

    def test_get_bonuses_by_employee(self, override_db):
        """Returns bonuses for specific employee."""
        emp_service = EmployeeService()
        emp1 = emp_service.create_employee(EmployeeCreate(full_name="Employee 1", role_title="Dev"))
        emp2 = emp_service.create_employee(EmployeeCreate(full_name="Employee 2", role_title="Dev"))

        service = BonusService()
        service.create_bonus(BonusCreate(
            employee_id=emp1.id,
            title="Bonus for Emp1",
            amount=1000.0,
            promised_date=datetime.now(timezone.utc),
        ))
        service.create_bonus(BonusCreate(
            employee_id=emp2.id,
            title="Bonus for Emp2",
            amount=2000.0,
            promised_date=datetime.now(timezone.utc),
        ))

        result = service.get_bonuses(BonusFilters(employee_id=emp1.id))
        assert result.total == 1
        assert result.items[0].employee_id == emp1.id

    def test_get_due_bonuses(self, override_db):
        """Returns bonuses due within specified days."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = BonusService()
        now = datetime.now(timezone.utc)

        # Due in 15 days (should be included)
        service.create_bonus(BonusCreate(
            employee_id=employee.id,
            title="Due Soon",
            amount=1000.0,
            promised_date=now,
            due_date=now + timedelta(days=15),
        ))

        # Due in 45 days (should be excluded for 30-day check)
        service.create_bonus(BonusCreate(
            employee_id=employee.id,
            title="Not Due Soon",
            amount=1000.0,
            promised_date=now,
            due_date=now + timedelta(days=45),
        ))

        result = service.get_due_bonuses(within_days=30)
        assert len(result) == 1
        assert result[0].title == "Due Soon"

    def test_update_bonus(self, override_db):
        """Update changes fields and sets updated_at."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = BonusService()
        created = service.create_bonus(BonusCreate(
            employee_id=employee.id,
            title="Original Title",
            amount=1000.0,
            promised_date=datetime.now(timezone.utc),
        ))

        result = service.update_bonus(created.id, BonusUpdate(
            title="Updated Title",
            amount=1500.0,
        ))

        assert result is not None
        assert result.title == "Updated Title"
        assert result.amount == 1500.0
        assert result.updated_at is not None

    def test_approve_bonus(self, override_db):
        """Approve sets status and approved fields."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = BonusService(actor="manager")
        bonus = service.create_bonus(BonusCreate(
            employee_id=employee.id,
            title="Pending Approval",
            amount=1000.0,
            promised_date=datetime.now(timezone.utc),
        ))

        result = service.approve_bonus(bonus.id)

        assert result.status == BonusStatus.APPROVED.value
        assert result.approved_by == "manager"
        assert result.approved_at is not None

    def test_cancel_bonus(self, override_db):
        """Cancel sets status to cancelled."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = BonusService()
        bonus = service.create_bonus(BonusCreate(
            employee_id=employee.id,
            title="To Cancel",
            amount=1000.0,
            promised_date=datetime.now(timezone.utc),
        ))

        result = service.cancel_bonus(bonus.id)
        assert result.status == BonusStatus.CANCELLED.value

    def test_get_bonus_payments(self, override_db):
        """Get all payments for a bonus."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = BonusService()
        bonus = service.create_bonus(BonusCreate(
            employee_id=employee.id,
            title="Test Bonus",
            amount=1000.0,
            promised_date=datetime.now(timezone.utc),
        ))

        service.record_payment(bonus.id, BonusPaymentCreate(
            amount=300.0,
            payment_date=datetime.now(timezone.utc),
        ))
        service.record_payment(bonus.id, BonusPaymentCreate(
            amount=400.0,
            payment_date=datetime.now(timezone.utc),
        ))

        payments = service.get_bonus_payments(bonus.id)
        assert len(payments) == 2

    def test_bonuses_pagination(self, override_db):
        """Pagination works correctly."""
        emp_service = EmployeeService()
        employee = emp_service.create_employee(EmployeeCreate(
            full_name="Test Employee",
            role_title="Developer",
        ))

        service = BonusService()
        for i in range(15):
            service.create_bonus(BonusCreate(
                employee_id=employee.id,
                title=f"Bonus {i}",
                amount=1000.0,
                promised_date=datetime.now(timezone.utc),
            ))

        result = service.get_bonuses(BonusFilters(page=1, page_size=10))
        assert result.total == 15
        assert len(result.items) == 10

        result2 = service.get_bonuses(BonusFilters(page=2, page_size=10))
        assert len(result2.items) == 5
