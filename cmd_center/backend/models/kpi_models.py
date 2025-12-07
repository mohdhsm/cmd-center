"""KPI-related Pydantic models."""

from pydantic import BaseModel
from typing import Optional

OwnerName = str


class OwnerKPI(BaseModel):
    """Owner (salesperson) KPI metrics."""
    
    owner: OwnerName
    activities_count: int
    projects_count: int
    estimated_value_sar: float
    moved_to_production_count: int
    overdue_deals_count: int
    stuck_deals_count: int


class OwnerKPIWithComment(OwnerKPI):
    """Owner KPI with optional LLM commentary."""
    
    commentary: Optional[str] = None