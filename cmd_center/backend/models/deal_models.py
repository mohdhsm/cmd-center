"""Deal-related Pydantic models."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Type aliases
PipelineName = str
StageName = str
OwnerName = str
OrgName = str


class DealBase(BaseModel):
    """Base model for Pipedrive deals."""
    
    id: int
    title: str
    pipeline: PipelineName
    stage: StageName
    owner: OwnerName
    org_name: Optional[OrgName] = None
    value_sar: Optional[float] = None
    
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    last_activity_time: Optional[datetime] = None


class OverdueDeal(DealBase):
    """Deal with overdue activities."""
    
    overdue_days: int


class StuckDeal(DealBase):
    """Deal stuck in the same stage."""
    
    days_in_stage: int


class OrderReceivedAnalysis(DealBase):
    """Order received deal with LLM analysis."""
    
    days_in_stage: int
    end_user_identified: Optional[bool] = None
    end_user_requests_count: Optional[int] = None


class ComplianceStatus(DealBase):
    """Deal compliance check status."""
    
    survey_checklist_present: Optional[bool] = None
    quality_docs_present: Optional[bool] = None
    comment: Optional[str] = None


class DealSummary(DealBase):
    """Deal with LLM-generated summary."""
    
    last_activity_date: Optional[datetime] = None
    llm_summary: str
    next_action: Optional[str] = None


class DealNote(BaseModel):
    """Note associated with a deal."""
    
    id: int
    date: datetime
    author: Optional[str] = None
    content: str


class DealSearchResult(DealBase):
    """Search result for deals (currently same as DealBase)."""
    
    pass