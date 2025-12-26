"""API endpoints for employee bonus tracking."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

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
from ..services.bonus_service import get_bonus_service

router = APIRouter(prefix="/bonuses", tags=["bonuses"])


@router.post("", response_model=BonusResponse, status_code=201)
def create_bonus(data: BonusCreate) -> BonusResponse:
    """Create a new bonus for an employee."""
    service = get_bonus_service()
    return service.create_bonus(data)


@router.get("", response_model=BonusListResponse)
def list_bonuses(
    employee_id: Optional[int] = Query(None),
    bonus_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> BonusListResponse:
    """List bonuses with filters."""
    service = get_bonus_service()
    filters = BonusFilters(
        employee_id=employee_id,
        bonus_type=bonus_type,
        status=status,
        page=page,
        page_size=page_size,
    )
    return service.get_bonuses(filters)


@router.get("/unpaid", response_model=list[BonusResponse])
def get_unpaid_bonuses(
    employee_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100),
) -> list[BonusResponse]:
    """Get bonuses that are not fully paid."""
    service = get_bonus_service()
    return service.get_unpaid_bonuses(employee_id=employee_id, limit=limit)


@router.get("/due", response_model=list[BonusResponse])
def get_due_bonuses(
    within_days: int = Query(30, ge=1),
    limit: int = Query(50, ge=1, le=100),
) -> list[BonusResponse]:
    """Get bonuses due within specified days."""
    service = get_bonus_service()
    return service.get_due_bonuses(within_days=within_days, limit=limit)


@router.get("/{bonus_id}", response_model=BonusWithPayments)
def get_bonus(bonus_id: int) -> BonusWithPayments:
    """Get a bonus by ID with payment history."""
    service = get_bonus_service()
    bonus = service.get_bonus_with_payments(bonus_id)
    if not bonus:
        raise HTTPException(status_code=404, detail="Bonus not found")
    return bonus


@router.put("/{bonus_id}", response_model=BonusResponse)
def update_bonus(bonus_id: int, data: BonusUpdate) -> BonusResponse:
    """Update a bonus."""
    service = get_bonus_service()
    bonus = service.update_bonus(bonus_id, data)
    if not bonus:
        raise HTTPException(status_code=404, detail="Bonus not found")
    return bonus


@router.post("/{bonus_id}/approve", response_model=BonusResponse)
def approve_bonus(bonus_id: int) -> BonusResponse:
    """Approve a bonus."""
    service = get_bonus_service()
    bonus = service.approve_bonus(bonus_id)
    if not bonus:
        raise HTTPException(status_code=404, detail="Bonus not found")
    return bonus


@router.post("/{bonus_id}/payments", response_model=BonusPaymentResponse, status_code=201)
def record_payment(bonus_id: int, data: BonusPaymentCreate) -> BonusPaymentResponse:
    """Record a payment for a bonus."""
    service = get_bonus_service()
    payment = service.record_payment(bonus_id, data)
    if not payment:
        raise HTTPException(status_code=404, detail="Bonus not found")
    return payment


@router.get("/{bonus_id}/payments", response_model=list[BonusPaymentResponse])
def get_bonus_payments(bonus_id: int) -> list[BonusPaymentResponse]:
    """Get all payments for a bonus."""
    service = get_bonus_service()
    return service.get_bonus_payments(bonus_id)


@router.delete("/{bonus_id}", response_model=BonusResponse)
def cancel_bonus(bonus_id: int) -> BonusResponse:
    """Cancel a bonus."""
    service = get_bonus_service()
    bonus = service.cancel_bonus(bonus_id)
    if not bonus:
        raise HTTPException(status_code=404, detail="Bonus not found")
    return bonus
