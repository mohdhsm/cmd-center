"""Financial tools for the agent."""

from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult, run_async
from ...backend.services.cashflow_prediction_service import (
    get_cashflow_prediction_service,
    CashflowPredictionInput,
)


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
