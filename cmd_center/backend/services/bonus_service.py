"""Bonus service for employee bonus tracking.

This service manages employee bonuses and their payments.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select, func

from .. import db
from ..db import EmployeeBonus, EmployeeBonusPayment, Employee
from ..models.bonus_models import (
    BonusCreate,
    BonusUpdate,
    BonusResponse,
    BonusWithPayments,
    BonusListResponse,
    BonusFilters,
    BonusPaymentCreate,
    BonusPaymentResponse,
)
from ..constants import ActionType, BonusStatus
from .intervention_service import log_action

logger = logging.getLogger(__name__)


class BonusService:
    """Service for employee bonus CRUD operations."""

    def __init__(self, actor: str = "system"):
        self.actor = actor

    def create_bonus(
        self,
        data: BonusCreate,
        actor: Optional[str] = None,
    ) -> BonusResponse:
        """Create a new bonus for an employee."""
        actor = actor or self.actor

        with Session(db.engine) as session:
            bonus = EmployeeBonus(
                employee_id=data.employee_id,
                title=data.title,
                description=data.description,
                amount=data.amount,
                currency=data.currency,
                bonus_type=data.bonus_type,
                conditions=data.conditions,
                promised_date=data.promised_date,
                due_date=data.due_date,
                status=BonusStatus.PROMISED.value,
            )
            session.add(bonus)
            session.commit()
            session.refresh(bonus)

            log_action(
                actor=actor,
                object_type="bonus",
                object_id=bonus.id,
                action_type=ActionType.BONUS_CREATED.value,
                summary=f"Created bonus: {bonus.title} for employee {bonus.employee_id}",
                details={
                    "amount": bonus.amount,
                    "currency": bonus.currency,
                    "bonus_type": bonus.bonus_type,
                },
            )

            logger.info(f"Created bonus: {bonus.title} (ID: {bonus.id})")

            return BonusResponse.model_validate(bonus)

    def get_bonus_by_id(self, bonus_id: int) -> Optional[BonusResponse]:
        """Get a bonus by ID."""
        with Session(db.engine) as session:
            bonus = session.get(EmployeeBonus, bonus_id)
            if bonus:
                return BonusResponse.model_validate(bonus)
            return None

    def get_bonus_with_payments(self, bonus_id: int) -> Optional[BonusWithPayments]:
        """Get a bonus with its payment history."""
        with Session(db.engine) as session:
            bonus = session.get(EmployeeBonus, bonus_id)
            if not bonus:
                return None

            # Get payments
            payments_query = (
                select(EmployeeBonusPayment)
                .where(EmployeeBonusPayment.bonus_id == bonus_id)
                .order_by(EmployeeBonusPayment.payment_date.desc())
            )
            payments = session.exec(payments_query).all()

            # Calculate totals
            total_paid = sum(p.amount for p in payments)
            remaining = bonus.amount - total_paid

            # Get employee name
            employee_name = None
            if bonus.employee_id:
                employee = session.get(Employee, bonus.employee_id)
                if employee:
                    employee_name = employee.full_name

            return BonusWithPayments(
                id=bonus.id,
                employee_id=bonus.employee_id,
                title=bonus.title,
                description=bonus.description,
                amount=bonus.amount,
                currency=bonus.currency,
                bonus_type=bonus.bonus_type,
                conditions=bonus.conditions,
                promised_date=bonus.promised_date,
                due_date=bonus.due_date,
                status=bonus.status,
                approved_by=bonus.approved_by,
                approved_at=bonus.approved_at,
                created_at=bonus.created_at,
                updated_at=bonus.updated_at,
                payments=[BonusPaymentResponse.model_validate(p) for p in payments],
                total_paid=total_paid,
                remaining=remaining,
                employee_name=employee_name,
            )

    def get_bonuses(
        self,
        filters: Optional[BonusFilters] = None,
    ) -> BonusListResponse:
        """Get paginated list of bonuses."""
        if filters is None:
            filters = BonusFilters()

        with Session(db.engine) as session:
            query = select(EmployeeBonus)

            if filters.employee_id is not None:
                query = query.where(EmployeeBonus.employee_id == filters.employee_id)
            if filters.bonus_type:
                query = query.where(EmployeeBonus.bonus_type == filters.bonus_type)
            if filters.status:
                query = query.where(EmployeeBonus.status == filters.status)
            if filters.due_before:
                query = query.where(EmployeeBonus.due_date <= filters.due_before)
            if filters.due_after:
                query = query.where(EmployeeBonus.due_date >= filters.due_after)

            count_query = select(func.count()).select_from(query.subquery())
            total = session.exec(count_query).one()

            query = query.order_by(EmployeeBonus.due_date.asc().nullslast())
            query = query.offset((filters.page - 1) * filters.page_size)
            query = query.limit(filters.page_size)

            bonuses = session.exec(query).all()

            return BonusListResponse(
                items=[BonusResponse.model_validate(b) for b in bonuses],
                total=total,
                page=filters.page,
                page_size=filters.page_size,
            )

    def get_unpaid_bonuses(
        self,
        employee_id: Optional[int] = None,
        limit: int = 50,
    ) -> list[BonusResponse]:
        """Get bonuses that are not fully paid."""
        with Session(db.engine) as session:
            query = (
                select(EmployeeBonus)
                .where(EmployeeBonus.status != BonusStatus.PAID.value)
                .where(EmployeeBonus.status != BonusStatus.CANCELLED.value)
            )

            if employee_id is not None:
                query = query.where(EmployeeBonus.employee_id == employee_id)

            query = query.order_by(EmployeeBonus.due_date.asc().nullslast()).limit(limit)
            bonuses = session.exec(query).all()

            return [BonusResponse.model_validate(b) for b in bonuses]

    def get_due_bonuses(
        self,
        within_days: int = 30,
        limit: int = 50,
    ) -> list[BonusResponse]:
        """Get bonuses due within specified days."""
        now = datetime.now(timezone.utc)
        from datetime import timedelta
        cutoff = now + timedelta(days=within_days)

        with Session(db.engine) as session:
            query = (
                select(EmployeeBonus)
                .where(EmployeeBonus.due_date >= now)
                .where(EmployeeBonus.due_date <= cutoff)
                .where(EmployeeBonus.status != BonusStatus.PAID.value)
                .where(EmployeeBonus.status != BonusStatus.CANCELLED.value)
                .order_by(EmployeeBonus.due_date.asc())
                .limit(limit)
            )
            bonuses = session.exec(query).all()

            return [BonusResponse.model_validate(b) for b in bonuses]

    def update_bonus(
        self,
        bonus_id: int,
        data: BonusUpdate,
        actor: Optional[str] = None,
    ) -> Optional[BonusResponse]:
        """Update a bonus."""
        actor = actor or self.actor

        with Session(db.engine) as session:
            bonus = session.get(EmployeeBonus, bonus_id)
            if not bonus:
                return None

            changes = {}

            if data.title is not None:
                changes["title"] = {"from": bonus.title, "to": data.title}
                bonus.title = data.title
            if data.description is not None:
                bonus.description = data.description
            if data.amount is not None:
                changes["amount"] = {"from": bonus.amount, "to": data.amount}
                bonus.amount = data.amount
            if data.bonus_type is not None:
                changes["bonus_type"] = {"from": bonus.bonus_type, "to": data.bonus_type}
                bonus.bonus_type = data.bonus_type
            if data.conditions is not None:
                bonus.conditions = data.conditions
            if data.due_date is not None:
                changes["due_date"] = {
                    "from": bonus.due_date.isoformat() if bonus.due_date else None,
                    "to": data.due_date.isoformat(),
                }
                bonus.due_date = data.due_date
            if data.status is not None:
                changes["status"] = {"from": bonus.status, "to": data.status}
                bonus.status = data.status

            bonus.updated_at = datetime.now(timezone.utc)

            session.add(bonus)
            session.commit()
            session.refresh(bonus)

            if changes:
                log_action(
                    actor=actor,
                    object_type="bonus",
                    object_id=bonus.id,
                    action_type=ActionType.BONUS_UPDATED.value,
                    summary=f"Updated bonus: {bonus.title}",
                    details={"changes": changes},
                )

            return BonusResponse.model_validate(bonus)

    def approve_bonus(
        self,
        bonus_id: int,
        actor: Optional[str] = None,
    ) -> Optional[BonusResponse]:
        """Approve a bonus."""
        actor = actor or self.actor

        with Session(db.engine) as session:
            bonus = session.get(EmployeeBonus, bonus_id)
            if not bonus:
                return None

            old_status = bonus.status
            bonus.status = BonusStatus.APPROVED.value
            bonus.approved_by = actor
            bonus.approved_at = datetime.now(timezone.utc)
            bonus.updated_at = datetime.now(timezone.utc)

            session.add(bonus)
            session.commit()
            session.refresh(bonus)

            log_action(
                actor=actor,
                object_type="bonus",
                object_id=bonus.id,
                action_type=ActionType.BONUS_APPROVED.value,
                summary=f"Approved bonus: {bonus.title}",
                details={"old_status": old_status},
            )

            return BonusResponse.model_validate(bonus)

    def record_payment(
        self,
        bonus_id: int,
        data: BonusPaymentCreate,
        actor: Optional[str] = None,
    ) -> Optional[BonusPaymentResponse]:
        """Record a payment for a bonus."""
        actor = actor or self.actor

        with Session(db.engine) as session:
            bonus = session.get(EmployeeBonus, bonus_id)
            if not bonus:
                return None

            # Calculate existing total BEFORE adding new payment (avoids autoflush issue)
            payments_query = select(func.sum(EmployeeBonusPayment.amount)).where(
                EmployeeBonusPayment.bonus_id == bonus_id
            )
            existing_total = session.exec(payments_query).one() or 0
            new_total = existing_total + data.amount

            payment = EmployeeBonusPayment(
                bonus_id=bonus_id,
                amount=data.amount,
                payment_date=data.payment_date,
                payment_method=data.payment_method,
                reference=data.reference,
                recorded_by=actor,
            )
            session.add(payment)

            # Update bonus status based on payment
            if new_total >= bonus.amount:
                bonus.status = BonusStatus.PAID.value
            elif new_total > 0:
                bonus.status = BonusStatus.PARTIAL.value

            bonus.updated_at = datetime.now(timezone.utc)
            session.add(bonus)

            session.commit()
            session.refresh(payment)

            log_action(
                actor=actor,
                object_type="bonus",
                object_id=bonus.id,
                action_type=ActionType.BONUS_PAYMENT_RECORDED.value,
                summary=f"Recorded payment of {data.amount} {bonus.currency} for bonus: {bonus.title}",
                details={
                    "payment_amount": data.amount,
                    "total_paid": new_total,
                    "remaining": bonus.amount - new_total,
                    "new_status": bonus.status,
                },
            )

            logger.info(f"Recorded payment for bonus {bonus_id}: {data.amount}")

            return BonusPaymentResponse.model_validate(payment)

    def get_bonus_payments(self, bonus_id: int) -> list[BonusPaymentResponse]:
        """Get all payments for a bonus."""
        with Session(db.engine) as session:
            query = (
                select(EmployeeBonusPayment)
                .where(EmployeeBonusPayment.bonus_id == bonus_id)
                .order_by(EmployeeBonusPayment.payment_date.desc())
            )
            payments = session.exec(query).all()

            return [BonusPaymentResponse.model_validate(p) for p in payments]

    def cancel_bonus(
        self,
        bonus_id: int,
        actor: Optional[str] = None,
    ) -> Optional[BonusResponse]:
        """Cancel a bonus."""
        actor = actor or self.actor

        with Session(db.engine) as session:
            bonus = session.get(EmployeeBonus, bonus_id)
            if not bonus:
                return None

            old_status = bonus.status
            bonus.status = BonusStatus.CANCELLED.value
            bonus.updated_at = datetime.now(timezone.utc)

            session.add(bonus)
            session.commit()
            session.refresh(bonus)

            log_action(
                actor=actor,
                object_type="bonus",
                object_id=bonus.id,
                action_type=ActionType.BONUS_CANCELLED.value,
                summary=f"Cancelled bonus: {bonus.title}",
                details={"old_status": old_status},
            )

            return BonusResponse.model_validate(bonus)


# Singleton pattern
_bonus_service: Optional[BonusService] = None


def get_bonus_service() -> BonusService:
    global _bonus_service
    if _bonus_service is None:
        _bonus_service = BonusService()
    return _bonus_service


__all__ = [
    "BonusService",
    "get_bonus_service",
]
