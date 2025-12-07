"""Dashboard-related Pydantic models."""

from pydantic import BaseModel
from typing import Literal, Optional
from .deal_models import DealBase, PipelineName


class DashboardItem(BaseModel):
    """Dashboard item representing a priority issue or opportunity."""
    
    type: Literal["overdue", "stuck", "compliance", "cashflow"]
    pipeline: PipelineName
    priority: int  # lower = higher priority
    flag: str  # e.g. "Overdue ≥7d", "Missing SDD", "Near invoice"
    deal: Optional[DealBase] = None  # may be None for pure cashflow rows