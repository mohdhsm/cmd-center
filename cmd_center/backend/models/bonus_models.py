"""Pydantic models for Employee Bonus API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Bonus Models
# ============================================================================

class BonusBase(BaseModel):
    """Base bonus fields."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(default=None, max_length=2000)
    amount: float = Field(..., gt=0)
    currency: str = Field(default="SAR", max_length=10)
    bonus_type: str = Field(default="performance")
    conditions: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("bonus_type")
    @classmethod
    def validate_bonus_type(cls, v: str) -> str:
        allowed = {"performance", "project", "annual", "other"}
        if v not in allowed:
            raise ValueError(f"bonus_type must be one of: {allowed}")
        return v


class BonusCreate(BonusBase):
    """Schema for creating a bonus."""
    employee_id: int
    promised_date: datetime
    due_date: Optional[datetime] = None


class BonusUpdate(BaseModel):
    """Schema for updating a bonus."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = Field(default=None, max_length=2000)
    amount: Optional[float] = Field(default=None, gt=0)
    bonus_type: Optional[str] = None
    conditions: Optional[str] = Field(default=None, max_length=2000)
    due_date: Optional[datetime] = None
    status: Optional[str] = None

    @field_validator("bonus_type")
    @classmethod
    def validate_bonus_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"performance", "project", "annual", "other"}
            if v not in allowed:
                raise ValueError(f"bonus_type must be one of: {allowed}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"promised", "approved", "partial", "paid", "cancelled"}
            if v not in allowed:
                raise ValueError(f"status must be one of: {allowed}")
        return v


class BonusResponse(BaseModel):
    """Response model for a bonus."""
    id: int
    employee_id: int
    title: str
    description: Optional[str]
    amount: float
    currency: str
    bonus_type: str
    conditions: Optional[str]
    promised_date: datetime
    due_date: Optional[datetime]
    status: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class BonusWithPayments(BonusResponse):
    """Bonus response with payment history."""
    payments: list["BonusPaymentResponse"] = []
    total_paid: float = 0.0
    remaining: float = 0.0
    employee_name: Optional[str] = None


class BonusListResponse(BaseModel):
    """Paginated list of bonuses."""
    items: list[BonusResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Payment Models
# ============================================================================

class BonusPaymentCreate(BaseModel):
    """Schema for recording a payment."""
    amount: float = Field(..., gt=0)
    payment_date: datetime
    payment_method: Optional[str] = Field(default=None, max_length=100)
    reference: Optional[str] = Field(default=None, max_length=200)


class BonusPaymentResponse(BaseModel):
    """Response model for a bonus payment."""
    id: int
    bonus_id: int
    amount: float
    payment_date: datetime
    payment_method: Optional[str]
    reference: Optional[str]
    recorded_by: Optional[str]
    recorded_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Filter Models
# ============================================================================

class BonusFilters(BaseModel):
    """Query filters for listing bonuses."""
    employee_id: Optional[int] = None
    bonus_type: Optional[str] = None
    status: Optional[str] = None
    due_before: Optional[datetime] = None
    due_after: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


__all__ = [
    "BonusBase",
    "BonusCreate",
    "BonusUpdate",
    "BonusResponse",
    "BonusWithPayments",
    "BonusListResponse",
    "BonusPaymentCreate",
    "BonusPaymentResponse",
    "BonusFilters",
]
