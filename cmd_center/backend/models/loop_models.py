"""Pydantic models for Loop Engine API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================================
# Loop Run Models
# ============================================================================

class LoopRunResponse(BaseModel):
    """Response model for a loop run."""
    id: int
    loop_name: str
    started_at: datetime
    finished_at: Optional[datetime]
    status: str
    findings_count: int
    error_message: Optional[str]

    model_config = {"from_attributes": True}


class LoopRunWithFindings(LoopRunResponse):
    """Loop run with its findings."""
    findings: list["LoopFindingResponse"] = []


class LoopRunListResponse(BaseModel):
    """Paginated list of loop runs."""
    items: list[LoopRunResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Loop Finding Models
# ============================================================================

class LoopFindingResponse(BaseModel):
    """Response model for a loop finding."""
    id: int
    loop_run_id: int
    severity: str
    target_type: str
    target_id: int
    message: str
    recommended_action: Optional[str]
    signature: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class LoopFindingListResponse(BaseModel):
    """Paginated list of loop findings."""
    items: list[LoopFindingResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Loop Status Models
# ============================================================================

class LoopInfo(BaseModel):
    """Information about a registered loop."""
    name: str
    description: str
    interval_minutes: int
    last_run: Optional[LoopRunResponse] = None
    is_enabled: bool = True


class LoopStatusResponse(BaseModel):
    """Status of all registered loops."""
    loops: list[LoopInfo]
    total_runs_today: int
    total_findings_today: int


# ============================================================================
# Filter Models
# ============================================================================

class LoopRunFilters(BaseModel):
    """Query filters for listing loop runs."""
    loop_name: Optional[str] = None
    status: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class LoopFindingFilters(BaseModel):
    """Query filters for listing loop findings."""
    loop_name: Optional[str] = None
    severity: Optional[str] = None
    target_type: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


__all__ = [
    "LoopRunResponse",
    "LoopRunWithFindings",
    "LoopRunListResponse",
    "LoopFindingResponse",
    "LoopFindingListResponse",
    "LoopInfo",
    "LoopStatusResponse",
    "LoopRunFilters",
    "LoopFindingFilters",
]
