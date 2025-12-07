"""Cashflow-related Pydantic models."""

from pydantic import BaseModel
from typing import Optional

PeriodLabel = str  # e.g. "2026-W01" or "2026-01"


class CashflowBucket(BaseModel):
    """Cashflow projection bucket (by period)."""
    
    period: PeriodLabel
    expected_invoice_value_sar: float
    deal_count: int
    comment: Optional[str] = None