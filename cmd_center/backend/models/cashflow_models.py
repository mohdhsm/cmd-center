"""Cashflow-related Pydantic models."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

PeriodLabel = str  # e.g. "2026-W01" or "2026-01"


class CashflowBucket(BaseModel):
    """Cashflow projection bucket (by period)."""

    period: PeriodLabel
    expected_invoice_value_sar: float
    deal_count: int
    comment: Optional[str] = None


# ============================================================================
# LLM-POWERED CASHFLOW PREDICTION MODELS
# ============================================================================

# ========== INPUT MODELS ==========

class DealForPrediction(BaseModel):
    """Deal data prepared for cashflow prediction."""
    deal_id: int = Field(..., description="Deal ID")
    title: str = Field(..., description="Deal title")
    stage: str = Field(..., description="Current stage name")
    stage_id: int = Field(..., description="Stage ID")
    value_sar: float = Field(..., description="Deal value in SAR")
    owner_name: str = Field(..., description="Deal owner name")
    days_in_stage: int = Field(..., description="Days in current stage")
    last_stage_change_date: Optional[datetime] = Field(None, description="Last stage change timestamp")
    last_update_date: Optional[datetime] = Field(None, description="Last update timestamp")
    recent_notes: list[str] = Field(default_factory=list, description="Recent notes (max 5)")
    activities_count: int = Field(default=0, description="Total activities")
    done_activities_count: int = Field(default=0, description="Completed activities")


class PredictionOptions(BaseModel):
    """Options for cashflow prediction."""
    horizon_days: int = Field(default=90, description="Prediction horizon in days")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence to include")
    include_assumptions: bool = Field(default=True, description="Include reasoning/assumptions")
    use_deterministic_overrides: bool = Field(default=True, description="Apply rule-based overrides")


class CashflowPredictionInput(BaseModel):
    """Input for cashflow prediction request."""
    pipeline_name: str = Field(..., description="Pipeline to analyze")
    horizon_days: int = Field(default=90, description="Prediction horizon")
    granularity: str = Field(default="week", description="Grouping: week or month")
    today_date: Optional[datetime] = Field(None, description="Reference date (defaults to now)")
    assumptions_flags: Optional[dict] = Field(None, description="Optional assumptions/overrides")


class ForecastOptions(BaseModel):
    """Options for forecast table generation."""
    group_by: str = Field(default="week", description="Grouping: week, month, owner, stage")
    include_confidence_bands: bool = Field(default=True, description="Include confidence ranges")
    currency: str = Field(default="SAR", description="Currency code")


# ========== OUTPUT MODELS ==========

class DealPrediction(BaseModel):
    """Prediction for a single deal."""
    deal_id: int = Field(..., description="Deal ID")
    deal_title: str = Field(..., description="Deal title")
    predicted_invoice_date: Optional[datetime] = Field(None, description="Predicted invoice date")
    predicted_payment_date: Optional[datetime] = Field(None, description="Predicted payment date")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    assumptions: list[str] = Field(default_factory=list, description="Assumptions made")
    missing_fields: list[str] = Field(default_factory=list, description="Missing data fields")
    reasoning: Optional[str] = Field(None, description="LLM explanation")
    # Additional context fields for display
    owner_name: Optional[str] = Field(None, description="Deal owner name")
    stage: Optional[str] = Field(None, description="Current stage name")
    value_sar: Optional[float] = Field(None, description="Deal value in SAR")


class PredictionMetadata(BaseModel):
    """Metadata about prediction run."""
    generated_at: datetime = Field(..., description="Prediction generation timestamp")
    horizon_days: int = Field(..., description="Prediction horizon used")
    deals_analyzed: int = Field(..., description="Total deals analyzed")
    deals_with_predictions: int = Field(..., description="Deals with valid predictions")
    avg_confidence: float = Field(..., description="Average confidence score")


class CashflowPredictionResult(BaseModel):
    """Complete cashflow prediction result."""
    per_deal_predictions: list[DealPrediction] = Field(..., description="Individual deal predictions")
    aggregated_forecast: list[CashflowBucket] = Field(..., description="Aggregated by period")
    warnings: list[str] = Field(default_factory=list, description="Warnings/notes")
    assumptions_used: list[str] = Field(default_factory=list, description="Global assumptions")
    metadata: PredictionMetadata = Field(..., description="Prediction metadata")


# ========== FORECAST TABLE MODELS ==========

class ForecastPeriod(BaseModel):
    """Forecast data for a single period."""
    period: str = Field(..., description="Period label (2025-W01 or 2025-01)")
    invoice_value_sar: float = Field(..., description="Expected invoice value")
    payment_value_sar: float = Field(..., description="Expected payment value")
    deal_count: int = Field(..., description="Number of deals")
    avg_confidence: float = Field(..., description="Average confidence for period")


class ForecastTotals(BaseModel):
    """Total forecast values."""
    total_invoice_value_sar: float = Field(..., description="Total invoice value")
    total_payment_value_sar: float = Field(..., description="Total payment value")
    total_deals: int = Field(..., description="Total deals")


class ForecastTable(BaseModel):
    """Formatted forecast table."""
    periods: list[ForecastPeriod] = Field(..., description="Forecast by period")
    totals: ForecastTotals = Field(..., description="Totals")
    group_by: str = Field(..., description="Grouping method used")


class AssumptionsReport(BaseModel):
    """Report of assumptions used in predictions."""
    global_assumptions: list[str] = Field(..., description="Global assumptions applied to all deals")
    per_deal_assumptions: dict[int, list[str]] = Field(..., description="Deal-specific assumptions (deal_id -> assumptions)")
    confidence_distribution: dict[str, int] = Field(..., description="Confidence buckets (high/medium/low -> count)")