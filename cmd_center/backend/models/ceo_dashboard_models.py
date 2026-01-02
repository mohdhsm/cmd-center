"""CEO Dashboard Pydantic models."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# Status type alias
StatusType = Literal["green", "yellow", "red"]
TrendType = Literal["better", "worse", "stable"]


class CashHealth(BaseModel):
    """Cash health metrics for the CEO dashboard."""

    runway_months: float = Field(description="Projected cash runway in months")
    runway_status: StatusType = Field(description="Status indicator for runway")

    # Aramco collections
    aramco_collected_week: float = Field(default=0.0, description="Aramco collections this week (SAR)")
    aramco_target_week: float = Field(default=0.0, description="Aramco weekly collection target (SAR)")

    # Commercial collections (placeholder for manual input)
    commercial_collected_week: float = Field(default=0.0, description="Commercial collections this week (SAR)")
    commercial_target_week: float = Field(default=0.0, description="Commercial weekly target (SAR)")

    # Totals
    total_collected_week: float = Field(description="Total collections this week (SAR)")
    total_target_week: float = Field(description="Total weekly collection target (SAR)")
    collection_pct: float = Field(description="Collection percentage (collected/target * 100)")

    # Forecast
    predicted_14d: float = Field(description="Predicted collections next 14 days (SAR)")

    # Velocity
    velocity_pct: float = Field(description="Collection velocity as percentage")
    velocity_status: StatusType = Field(description="Status indicator for velocity")


class UrgentDeal(BaseModel):
    """An urgent deal requiring CEO attention."""

    deal_id: int
    title: str
    reason: str = Field(description="Why this deal needs attention, e.g. 'Awaiting GR 23 days'")
    value_sar: float
    stage: str
    owner: str
    days_stuck: int = Field(description="Days in current situation")


class PipelineStage(BaseModel):
    """Stage metrics for pipeline velocity."""

    name: str
    stage_id: int
    avg_days: float = Field(description="Average days deals spend in this stage")
    deal_count: int = Field(description="Number of deals currently in this stage")


class PipelineVelocity(BaseModel):
    """Pipeline velocity metrics."""

    stages: List[PipelineStage] = Field(description="Per-stage velocity metrics")
    current_cycle_days: float = Field(description="Current average total cycle time in days")
    target_cycle_days: float = Field(default=21.0, description="Target cycle time in days")
    trend: TrendType = Field(description="Whether velocity is trending better, worse, or stable")
    trend_pct: float = Field(default=0.0, description="Percentage change vs previous period")


class StrategicPriority(BaseModel):
    """A strategic priority with current vs target metrics."""

    name: str = Field(description="Name of the priority, e.g. 'Cost Reduction'")
    current: float = Field(description="Current value")
    target: float = Field(description="Target value")
    pct: float = Field(description="Percentage of target achieved (current/target * 100)")
    status: StatusType = Field(description="Status indicator")
    unit: str = Field(default="", description="Unit of measurement, e.g. '%', 'SAR', 'K'")


class SalesScorecard(BaseModel):
    """Sales department scorecard metrics (MVP)."""

    pipeline_value: float = Field(description="Total value of open deals (SAR)")
    won_value: float = Field(description="Value of won deals this month (SAR)")
    active_deals_count: int = Field(description="Number of active deals")
    overdue_count: int = Field(description="Number of overdue deals")
    status: StatusType = Field(description="Overall sales health status")


class DepartmentScorecard(BaseModel):
    """Department scorecard section."""

    sales: SalesScorecard
    # Future: delivery and operations to be added
    # delivery: Optional[DeliveryScorecard] = None
    # operations: Optional[OperationsScorecard] = None


class CEODashboardMetrics(BaseModel):
    """Complete CEO Dashboard metrics response."""

    cash_health: CashHealth
    urgent_deals: List[UrgentDeal] = Field(max_length=5, description="Top 5 urgent deals")
    pipeline_velocity: PipelineVelocity
    strategic_priorities: List[StrategicPriority]
    department_scorecard: DepartmentScorecard

    # Metadata
    last_updated: str = Field(description="ISO timestamp of when data was fetched")
    data_freshness: str = Field(default="live", description="Indicates if data is live or cached")
