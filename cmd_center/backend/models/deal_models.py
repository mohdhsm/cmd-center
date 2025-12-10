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
    next_activity_date: Optional[datetime] = None
    
    # Counts for quick overview
    file_count: int = 0
    notes_count: int = 0
    activities_count: int = 0
    done_activities_count: int = 0
    email_messages_count: int = 0


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


class DealActivity(BaseModel):
    """Activity associated with a deal."""
    
    id: int
    deal_id: int
    type: str
    subject: Optional[str] = None
    note: Optional[str] = None
    due_date: Optional[datetime] = None
    due_time: Optional[str] = None
    done: bool = False
    mark_as_done_time: Optional[datetime] = None
    add_time: Optional[datetime] = None


class DealFile(BaseModel):
    """File attachment associated with a deal."""
    
    id: int
    deal_id: int
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    file_url: Optional[str] = None
    add_time: Optional[datetime] = None


class DealComment(BaseModel):
    """Comment on a deal or other object."""
    
    id: int
    object_id: int
    object_type: str  # e.g., "deal", "activity"
    content: Optional[str] = None
    add_time: Optional[datetime] = None
    user_id: Optional[int] = None


class DealSearchResult(DealBase):
    """Search result for deals (currently same as DealBase)."""
    
    pass