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
    deal_id:int 
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


# ============================================================================
# STAGE HISTORY MODELS
# ============================================================================

class StageTransition(BaseModel):
    """Single stage transition event."""

    stage_id: int
    stage_name: str
    entered_at: datetime
    left_at: Optional[datetime] = None
    duration_hours: Optional[float] = None
    is_current: bool = False
    transition_user_id: Optional[int] = None
    transition_source: Optional[str] = None


class DealStageHistory(BaseModel):
    """Complete stage history for a deal."""

    deal_id: int
    deal_title: str
    pipeline_name: str
    current_stage: str
    transitions: list[StageTransition]
    total_transitions: int
    first_stage_entry: datetime
    last_transition: Optional[datetime] = None


class StagePerformanceMetrics(BaseModel):
    """Analytics for a specific stage."""

    stage_id: int
    stage_name: str
    total_deals: int
    current_deals: int
    avg_duration_hours: float
    median_duration_hours: float
    min_duration_hours: float
    max_duration_hours: float
    p95_duration_hours: float
    stuck_threshold_hours: int
    stuck_deals_count: int
    analysis_period_days: int


# ============================================================================
# CEO RADAR SUMMARY MODELS
# ============================================================================

# ============ OVERDUE SUMMARY MODELS ============

class OverdueSnapshot(BaseModel):
    """Executive snapshot for overdue deals."""
    overdue_now_count: int
    overdue_now_sar: float
    overdue_soon_count: int  # next 7-14 days
    overdue_soon_sar: float
    worst_overdue: list  # Top 5: [{deal_id, title, days, sar}]


class PMOverduePerformance(BaseModel):
    """PM performance metrics for overdue."""
    pm_name: str
    overdue_now_count: int
    overdue_now_sar: float
    due_soon_count: int
    due_soon_sar: float
    avg_days_overdue: float
    updated_this_week_count: int
    has_next_activity_count: int
    risk_score: float


class CEOInterventionDeal(BaseModel):
    """Deal requiring CEO intervention."""
    deal_id: int
    title: str
    pm_name: str
    stage: str
    overdue_by_days: Optional[int] = None
    days_in_stage: Optional[int] = None
    days_since_update: int
    last_note_snippet: Optional[str] = None
    next_activity_date: Optional[str] = None
    next_activity_exists: bool


class OverdueSummaryResponse(BaseModel):
    """Complete overdue summary modal data."""
    snapshot: OverdueSnapshot
    pm_performance: list[PMOverduePerformance]
    intervention_list: list[CEOInterventionDeal]


# ============ STUCK SUMMARY MODELS ============

class StuckSnapshot(BaseModel):
    """Executive snapshot for stuck deals."""
    stuck_no_updates_count: int
    stuck_no_updates_sar: float
    bucket_30_45_count: int
    bucket_30_45_sar: float
    bucket_46_60_count: int
    bucket_46_60_sar: float
    bucket_60_plus_count: int
    bucket_60_plus_sar: float
    no_activity_count: int
    oldest_stuck: list  # Top 5: [{deal_id, title, days_in_stage, sar}]


class PMStuckControl(BaseModel):
    """PM stuck control metrics."""
    pm_name: str
    stuck_count: int
    stuck_sar: float
    stuck_no_activity_sar: float
    avg_days_in_stage: float
    median_days_since_update: float
    recovery_rate_30d: Optional[float] = None  # % of deals that moved out of stuck stages in last 30d


class WorstStuckDeal(BaseModel):
    """Worst stuck deal details."""
    deal_id: int
    title: str
    pm_name: str
    stage: str
    days_in_stage: int
    last_update_age: int
    last_note_snippet: Optional[str] = None
    blocking_flag: Optional[str] = None  # TODO: LLM-detected
    suggested_next_step: Optional[str] = None  # TODO: LLM


class StageBottleneck(BaseModel):
    """Stage-level bottleneck data."""
    stage_name: str
    stuck_count: int
    stuck_sar: float


class StuckSummaryResponse(BaseModel):
    """Complete stuck summary modal data."""
    snapshot: StuckSnapshot
    pm_control: list[PMStuckControl]
    worst_deals: list[WorstStuckDeal]
    stage_bottlenecks: list[StageBottleneck]
    top_bottleneck_stage: str


# ============ ORDER RECEIVED SUMMARY MODELS ============

class OrderReceivedSnapshot(BaseModel):
    """Executive snapshot for Order Received."""
    open_count: int
    open_sar: float
    bucket_0_7_count: int
    bucket_0_7_sar: float
    bucket_8_14_count: int
    bucket_8_14_sar: float
    bucket_15_30_count: int
    bucket_15_30_sar: float
    bucket_30_plus_count: int
    bucket_30_plus_sar: float
    oldest_deal: dict  # {deal_id, title, age_days}
    conversion_rate_30d: Optional[float] = None  # % of deals that moved to Approved in last 30d


class PMPipelineAcceleration(BaseModel):
    """PM pipeline acceleration metrics."""
    pm_name: str
    open_count: int
    open_sar: float
    avg_age_days: float
    pct_end_user_identified: float
    pct_next_activity_scheduled: float
    approved_30d_count: Optional[int] = None  # Deals moved to Approved in last 30d
    approved_30d_sar: Optional[float] = None  # SAR of deals moved to Approved in last 30d


class BlockersChecklistSummary(BaseModel):
    """Missing items summary."""
    missing_end_user_count: int
    missing_site_contact_count: Optional[int] = None  # TODO: field key unknown
    missing_po_count: Optional[int] = None  # TODO: field key unknown
    missing_dates_count: Optional[int] = None  # TODO: field key unknown
    missing_product_type_count: Optional[int] = None  # TODO: field key unknown
    missing_quantity_count: Optional[int] = None  # TODO: field key unknown
    missing_next_activity_count: int


class FastWinDeal(BaseModel):
    """Fast win opportunity."""
    deal_id: int
    title: str
    pm_name: str
    value_sar: float
    age_days: int
    missing_items: list[str]  # e.g., ["End user", "PO reference"]
    suggested_action: str


class OrderReceivedSummaryResponse(BaseModel):
    """Complete Order Received summary modal data."""
    snapshot: OrderReceivedSnapshot
    pm_acceleration: list[PMPipelineAcceleration]
    blockers_checklist: BlockersChecklistSummary
    fast_wins: list[FastWinDeal]