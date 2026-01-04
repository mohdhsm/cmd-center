"""Financial tools for the agent."""

from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult, run_async
from ...backend.services.cashflow_prediction_service import (
    get_cashflow_prediction_service,
    CashflowPredictionInput,
)
from ...backend.services.ceo_dashboard_service import get_ceo_dashboard_service


class GetCashflowProjectionParams(BaseModel):
    """Parameters for get_cashflow_projection tool."""

    pipeline_name: str = Field(
        default="Aramco Projects",
        description="Pipeline to analyze: 'Aramco Projects' or 'Commercial'",
    )
    horizon_days: int = Field(
        default=90,
        description="Prediction horizon in days (30-365)",
    )
    granularity: str = Field(
        default="month",
        description="Grouping granularity: 'week' or 'month'",
    )


class GetCashflowProjection(BaseTool):
    """Get cashflow projection for a pipeline."""

    name = "get_cashflow_projection"
    description = (
        "Get projected cashflow for a pipeline including per-deal predictions, "
        "aggregated forecasts by period, and confidence scores. "
        "Use this to forecast expected revenue and identify payment timelines."
    )
    parameters_model = GetCashflowProjectionParams

    def execute(self, params: GetCashflowProjectionParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_cashflow_prediction_service()

            input_data = CashflowPredictionInput(
                pipeline_name=params.pipeline_name,
                horizon_days=params.horizon_days,
                granularity=params.granularity,
            )

            # The service's predict_cashflow is async, so we need to run it
            result = run_async(service.predict_cashflow(input_data))

            # Transform per-deal predictions
            predictions = [
                {
                    "deal_id": p.deal_id,
                    "deal_title": p.deal_title,
                    "predicted_invoice_date": (
                        p.predicted_invoice_date.isoformat()
                        if p.predicted_invoice_date
                        else None
                    ),
                    "predicted_payment_date": (
                        p.predicted_payment_date.isoformat()
                        if p.predicted_payment_date
                        else None
                    ),
                    "confidence": p.confidence,
                    "owner_name": p.owner_name,
                    "stage": p.stage,
                    "value_sar": p.value_sar,
                }
                for p in result.per_deal_predictions
            ]

            # Transform aggregated forecast
            aggregated = [
                {
                    "period": b.period,
                    "expected_invoice_value_sar": b.expected_invoice_value_sar,
                    "deal_count": b.deal_count,
                    "comment": b.comment,
                }
                for b in result.aggregated_forecast
            ]

            return ToolResult(
                success=True,
                data={
                    "predictions": predictions,
                    "aggregated_forecast": aggregated,
                    "warnings": result.warnings,
                    "assumptions_used": result.assumptions_used,
                    "metadata": {
                        "generated_at": result.metadata.generated_at.isoformat(),
                        "horizon_days": result.metadata.horizon_days,
                        "deals_analyzed": result.metadata.deals_analyzed,
                        "deals_with_predictions": result.metadata.deals_with_predictions,
                        "avg_confidence": result.metadata.avg_confidence,
                    },
                    "pipeline_name": params.pipeline_name,
                    "granularity": params.granularity,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetCEODashboardParams(BaseModel):
    """Parameters for get_ceo_dashboard tool."""

    pass  # No parameters needed - returns full dashboard


class GetCEODashboard(BaseTool):
    """Get CEO dashboard metrics overview."""

    name = "get_ceo_dashboard"
    description = (
        "Get executive dashboard metrics including cash health, runway status, "
        "urgent deals requiring attention, pipeline velocity, strategic priorities, "
        "and department scorecards. Use this for a high-level business overview."
    )
    parameters_model = GetCEODashboardParams

    def execute(self, params: GetCEODashboardParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_ceo_dashboard_service()

            # The service's get_dashboard_metrics is async, so we need to run it
            result = run_async(service.get_dashboard_metrics())

            # Transform cash health
            cash_health = {
                "runway_months": result.cash_health.runway_months,
                "runway_status": result.cash_health.runway_status,
                "aramco_collected_week": result.cash_health.aramco_collected_week,
                "aramco_target_week": result.cash_health.aramco_target_week,
                "commercial_collected_week": result.cash_health.commercial_collected_week,
                "commercial_target_week": result.cash_health.commercial_target_week,
                "total_collected_week": result.cash_health.total_collected_week,
                "total_target_week": result.cash_health.total_target_week,
                "collection_pct": result.cash_health.collection_pct,
                "predicted_14d": result.cash_health.predicted_14d,
                "velocity_pct": result.cash_health.velocity_pct,
                "velocity_status": result.cash_health.velocity_status,
            }

            # Transform urgent deals
            urgent_deals = [
                {
                    "deal_id": deal.deal_id,
                    "title": deal.title,
                    "reason": deal.reason,
                    "value_sar": deal.value_sar,
                    "stage": deal.stage,
                    "owner": deal.owner,
                    "days_stuck": deal.days_stuck,
                }
                for deal in result.urgent_deals
            ]

            # Transform pipeline velocity
            pipeline_velocity = {
                "stages": [
                    {
                        "name": stage.name,
                        "stage_id": stage.stage_id,
                        "avg_days": stage.avg_days,
                        "deal_count": stage.deal_count,
                    }
                    for stage in result.pipeline_velocity.stages
                ],
                "current_cycle_days": result.pipeline_velocity.current_cycle_days,
                "target_cycle_days": result.pipeline_velocity.target_cycle_days,
                "trend": result.pipeline_velocity.trend,
                "trend_pct": result.pipeline_velocity.trend_pct,
            }

            # Transform strategic priorities
            strategic_priorities = [
                {
                    "name": priority.name,
                    "current": priority.current,
                    "target": priority.target,
                    "pct": priority.pct,
                    "status": priority.status,
                    "unit": priority.unit,
                }
                for priority in result.strategic_priorities
            ]

            # Transform department scorecard
            department_scorecard = {
                "sales": {
                    "pipeline_value": result.department_scorecard.sales.pipeline_value,
                    "won_value": result.department_scorecard.sales.won_value,
                    "active_deals_count": result.department_scorecard.sales.active_deals_count,
                    "overdue_count": result.department_scorecard.sales.overdue_count,
                    "status": result.department_scorecard.sales.status,
                }
            }

            return ToolResult(
                success=True,
                data={
                    "metrics": {
                        "cash_health": cash_health,
                        "urgent_deals": urgent_deals,
                        "pipeline_velocity": pipeline_velocity,
                        "strategic_priorities": strategic_priorities,
                        "department_scorecard": department_scorecard,
                        "last_updated": result.last_updated,
                        "data_freshness": result.data_freshness,
                    }
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
