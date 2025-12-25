"""Cashflow Prediction Service with LLM-powered date prediction.

This service provides intelligent cashflow forecasting by:
1. Preparing deal data for prediction
2. Using LLM to predict invoice/payment dates
3. Applying deterministic rules for validation
4. Aggregating predictions into forecast tables
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict
from sqlmodel import Session, select

from ..db import get_session, Deal
from ..constants import PIPELINE_NAME_TO_ID
from ..models.cashflow_models import (
    DealForPrediction,
    PredictionOptions,
    CashflowPredictionInput,
    ForecastOptions,
    DealPrediction,
    PredictionMetadata,
    CashflowPredictionResult,
    ForecastPeriod,
    ForecastTotals,
    ForecastTable,
    AssumptionsReport,
    CashflowBucket,
)
from ..integrations.llm_client import get_llm_client, LLMClient, LLMError
from .prompt_registry import get_prompt_registry, PromptRegistry
from .deterministic_rules import DeterministicRules
from .db_queries import get_notes_for_deal

logger = logging.getLogger(__name__)


class CashflowPredictionService:
    """Service for LLM-powered cashflow prediction."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        prompt_registry: Optional[PromptRegistry] = None,
        rules_engine: Optional[DeterministicRules] = None,
    ):
        self.llm = llm_client or get_llm_client()
        self.prompts = prompt_registry or get_prompt_registry()
        self.rules = rules_engine or DeterministicRules()

    # ========================================================================
    # MAIN PREDICTION METHODS
    # ========================================================================

    async def predict_cashflow(
        self,
        input_data: CashflowPredictionInput,
    ) -> CashflowPredictionResult:
        """Predict cashflow for a pipeline.

        Args:
            input_data: Prediction input parameters

        Returns:
            CashflowPredictionResult with per-deal predictions and aggregated forecast

        Raises:
            ValueError: If pipeline not found
            LLMError: On LLM failures
        """
        today = input_data.today_date or datetime.now()

        # Get pipeline ID
        pipeline_id = PIPELINE_NAME_TO_ID.get(input_data.pipeline_name)
        if not pipeline_id:
            raise ValueError(f"Unknown pipeline: {input_data.pipeline_name}")

        # Load deals from database
        deals_for_prediction = await self._load_deals(pipeline_id, today)

        logger.info(
            f"Loaded {len(deals_for_prediction)} deals for cashflow prediction",
            extra={"pipeline": input_data.pipeline_name}
        )

        # Make predictions
        # NOTE: Deterministic overrides disabled - using LLM with comprehensive rules
        options = PredictionOptions(
            horizon_days=input_data.horizon_days,
            use_deterministic_overrides=False,  # Disabled - LLM handles all predictions
        )

        predictions = await self.predict_deal_dates(deals_for_prediction, options, today)

        # Filter by horizon
        predictions = self._filter_by_horizon(predictions, today, input_data.horizon_days)

        # Generate aggregated forecast
        aggregated = self._aggregate_predictions(
            predictions,
            input_data.granularity,
            today,
        )

        # Collect assumptions
        global_assumptions = self._collect_global_assumptions(predictions)
        warnings = self._collect_warnings(predictions, today)

        # Generate metadata
        metadata = PredictionMetadata(
            generated_at=datetime.now(),
            horizon_days=input_data.horizon_days,
            deals_analyzed=len(deals_for_prediction),
            deals_with_predictions=len([p for p in predictions if p.predicted_invoice_date]),
            avg_confidence=sum(p.confidence for p in predictions) / len(predictions) if predictions else 0.0,
        )

        return CashflowPredictionResult(
            per_deal_predictions=predictions,
            aggregated_forecast=aggregated,
            warnings=warnings,
            assumptions_used=global_assumptions,
            metadata=metadata,
        )

    async def predict_deal_dates(
        self,
        deals: list[DealForPrediction],
        options: PredictionOptions,
        today: Optional[datetime] = None,
    ) -> list[DealPrediction]:
        """Predict invoice and payment dates for deals.

        Args:
            deals: Deals to predict
            options: Prediction options
            today: Reference date (defaults to now)

        Returns:
            List of DealPrediction
        """
        today = today or datetime.now()
        predictions = []

        # NOTE: Deterministic pre-checks disabled - LLM handles all predictions with comprehensive rules
        # if options.use_deterministic_overrides:
        #     for deal in deals:
        #         deterministic_pred = self.rules.precheck_deal(deal, today)
        #         if deterministic_pred:
        #             predictions.append(deterministic_pred)
        #             deals = [d for d in deals if d.deal_id != deal.deal_id]
        #
        #     if predictions:
        #         logger.info(f"Applied deterministic rules to {len(predictions)} deals")

        # Use LLM for all deals
        if deals:
            try:
                llm_predictions = await self._predict_with_llm(deals, today, options.horizon_days)
                predictions.extend(llm_predictions)
            except LLMError as e:
                logger.error(f"LLM prediction failed: {e}")
                # Fallback to deterministic for all
                for deal in deals:
                    fallback = self._fallback_prediction(deal, today)
                    predictions.append(fallback)

        # NOTE: Deterministic overrides disabled - LLM predictions are used as-is
        # if options.use_deterministic_overrides:
        #     predictions = [
        #         self.rules.apply_overrides(pred, deal, today)
        #         for pred, deal in zip(predictions, deals)
        #     ]

        # Filter by confidence threshold
        if options.confidence_threshold > 0:
            before_count = len(predictions)
            predictions = [p for p in predictions if p.confidence >= options.confidence_threshold]
            if len(predictions) < before_count:
                logger.info(
                    f"Filtered {before_count - len(predictions)} predictions below threshold {options.confidence_threshold}"
                )

        return predictions

    def generate_forecast_table(
        self,
        predictions: list[DealPrediction],
        options: ForecastOptions,
    ) -> ForecastTable:
        """Generate formatted forecast table from predictions.

        Args:
            predictions: Deal predictions
            options: Forecast options

        Returns:
            ForecastTable with periods and totals
        """
        periods_data = defaultdict(lambda: {
            "invoice_value": 0.0,
            "payment_value": 0.0,
            "deal_count": 0,
            "confidences": [],
        })

        for pred in predictions:
            # Group by invoice period
            if pred.predicted_invoice_date:
                invoice_period = self._get_period_label(
                    pred.predicted_invoice_date,
                    options.group_by
                )
                periods_data[invoice_period]["invoice_value"] += 0  # Value not in prediction
                periods_data[invoice_period]["deal_count"] += 1
                periods_data[invoice_period]["confidences"].append(pred.confidence)

            # Group by payment period
            if pred.predicted_payment_date:
                payment_period = self._get_period_label(
                    pred.predicted_payment_date,
                    options.group_by
                )
                periods_data[payment_period]["payment_value"] += 0  # Value not in prediction

        # Convert to ForecastPeriod objects
        periods = []
        for period_label, data in sorted(periods_data.items()):
            avg_confidence = (
                sum(data["confidences"]) / len(data["confidences"])
                if data["confidences"] else 0.0
            )

            periods.append(ForecastPeriod(
                period=period_label,
                invoice_value_sar=data["invoice_value"],
                payment_value_sar=data["payment_value"],
                deal_count=data["deal_count"],
                avg_confidence=avg_confidence,
            ))

        # Calculate totals
        totals = ForecastTotals(
            total_invoice_value_sar=sum(p.invoice_value_sar for p in periods),
            total_payment_value_sar=sum(p.payment_value_sar for p in periods),
            total_deals=sum(p.deal_count for p in periods),
        )

        return ForecastTable(
            periods=periods,
            totals=totals,
            group_by=options.group_by,
        )

    def explain_assumptions(self, predictions: list[DealPrediction]) -> AssumptionsReport:
        """Generate report explaining assumptions used.

        Args:
            predictions: Deal predictions

        Returns:
            AssumptionsReport
        """
        # Collect global assumptions (common across many deals)
        assumption_counts = defaultdict(int)
        for pred in predictions:
            for assumption in pred.assumptions:
                assumption_counts[assumption] += 1

        # Global = mentioned in >20% of deals
        threshold = len(predictions) * 0.2
        global_assumptions = [
            assumption for assumption, count in assumption_counts.items()
            if count >= threshold
        ]

        # Per-deal assumptions
        per_deal_assumptions = {
            pred.deal_id: pred.assumptions
            for pred in predictions
        }

        # Confidence distribution
        confidence_distribution = {
            "high": len([p for p in predictions if p.confidence >= 0.7]),
            "medium": len([p for p in predictions if 0.4 <= p.confidence < 0.7]),
            "low": len([p for p in predictions if p.confidence < 0.4]),
        }

        return AssumptionsReport(
            global_assumptions=global_assumptions,
            per_deal_assumptions=per_deal_assumptions,
            confidence_distribution=confidence_distribution,
        )

    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================

    async def _load_deals(
        self,
        pipeline_id: int,
        today: datetime,
    ) -> list[DealForPrediction]:
        """Load deals from database for prediction.

        Args:
            pipeline_id: Pipeline ID
            today: Reference date

        Returns:
            List of DealForPrediction
        """
        with next(get_session()) as session:
            # Query open deals
            stmt = (
                select(Deal)
                .where(Deal.pipeline_id == pipeline_id)
                .where(Deal.status == "open")
            )
            deals = session.exec(stmt).all()

            # Convert to DealForPrediction
            deals_for_prediction = []
            for deal in deals:
                # Calculate days in stage
                days_in_stage = 0
                if deal.stage_change_time:
                    days_in_stage = (today - deal.stage_change_time).days

                # Get recent notes
                notes = get_notes_for_deal(deal.id, limit=5)
                recent_notes = [note.content for note in notes if note.content]

                deals_for_prediction.append(DealForPrediction(
                    deal_id=deal.id,
                    title=deal.title,
                    stage=deal.stage_id,  # TODO: Map to stage name
                    stage_id=deal.stage_id,
                    value_sar=deal.value or 0.0,
                    owner_name=deal.owner_name or "Unknown",
                    days_in_stage=days_in_stage,
                    last_stage_change_date=deal.stage_change_time,
                    last_update_date=deal.update_time,
                    recent_notes=recent_notes,
                    activities_count=deal.activities_count,
                    done_activities_count=deal.done_activities_count,
                ))

        return deals_for_prediction

    async def _predict_with_llm(
        self,
        deals: list[DealForPrediction],
        today: datetime,
        horizon_days: int,
    ) -> list[DealPrediction]:
        """Use LLM to predict dates for deals.

        Args:
            deals: Deals to predict
            today: Reference date
            horizon_days: Prediction horizon

        Returns:
            List of DealPrediction
        """
        # Render prompt
        system_prompt, user_prompt = self.prompts.render_prompt(
            "cashflow.predict_dates.v1",
            {
                "today_date": today.isoformat(),
                "horizon_days": horizon_days,
                "deals": [deal.model_dump() for deal in deals],
            }
        )

        # Get config
        config = self.prompts.get_prompt_config("cashflow.predict_dates.v1")

        # Call LLM with structured output
        # We expect: {"predictions": [...]}
        from pydantic import BaseModel

        class PredictionsResponse(BaseModel):
            predictions: list[DealPrediction]

        result = await self.llm.generate_structured_completion(
            schema=PredictionsResponse,
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=config["max_tokens"],
            temperature=config["temperature"],
            fallback_on_validation_error=True,
        )

        return result.predictions

    def _fallback_prediction(
        self,
        deal: DealForPrediction,
        today: datetime,
    ) -> DealPrediction:
        """Generate fallback prediction when LLM fails.

        Args:
            deal: Deal data
            today: Reference date

        Returns:
            DealPrediction with low confidence
        """
        # Use stage-based estimate if available
        stage_estimate = self.rules.get_stage_estimate(deal.stage)
        if stage_estimate:
            invoice_date = today + timedelta(days=stage_estimate)
        else:
            # Default: 30 days
            invoice_date = today + timedelta(days=30)

        payment_date = invoice_date + timedelta(days=self.rules.DEFAULT_PAYMENT_TERMS)

        return DealPrediction(
            deal_id=deal.deal_id,
            deal_title=deal.title,
            predicted_invoice_date=invoice_date,
            predicted_payment_date=payment_date,
            confidence=0.3,
            assumptions=["Fallback: LLM error, using stage estimate or default 30 days"],
            missing_fields=["LLM prediction unavailable"],
            reasoning="Fallback prediction due to LLM error",
        )

    def _filter_by_horizon(
        self,
        predictions: list[DealPrediction],
        today: datetime,
        horizon_days: int,
    ) -> list[DealPrediction]:
        """Filter predictions outside horizon.

        Args:
            predictions: All predictions
            today: Reference date
            horizon_days: Horizon in days

        Returns:
            Filtered predictions
        """
        cutoff = today + timedelta(days=horizon_days)

        filtered = []
        for pred in predictions:
            # Keep if invoice or payment within horizon
            if pred.predicted_invoice_date and pred.predicted_invoice_date <= cutoff:
                filtered.append(pred)
            elif pred.predicted_payment_date and pred.predicted_payment_date <= cutoff:
                filtered.append(pred)

        return filtered

    def _aggregate_predictions(
        self,
        predictions: list[DealPrediction],
        granularity: str,
        today: datetime,
    ) -> list[CashflowBucket]:
        """Aggregate predictions into periods.

        Args:
            predictions: Deal predictions
            granularity: "week" or "month"
            today: Reference date

        Returns:
            List of CashflowBucket
        """
        # Group by period
        buckets = defaultdict(lambda: {"value": 0.0, "count": 0})

        for pred in predictions:
            if pred.predicted_invoice_date:
                period = self._get_period_label(pred.predicted_invoice_date, granularity)
                # Note: We don't have deal value in prediction
                buckets[period]["count"] += 1

        # Convert to CashflowBucket
        result = []
        for period, data in sorted(buckets.items()):
            result.append(CashflowBucket(
                period=period,
                expected_invoice_value_sar=data["value"],
                deal_count=data["count"],
                comment=f"{data['count']} deals expected to invoice",
            ))

        return result

    def _get_period_label(self, date: datetime, granularity: str) -> str:
        """Get period label for a date.

        Args:
            date: Date to label
            granularity: "week" or "month"

        Returns:
            Period label like "2025-W01" or "2025-01"
        """
        if granularity == "week":
            year = date.isocalendar()[0]
            week = date.isocalendar()[1]
            return f"{year}-W{week:02d}"
        else:
            return date.strftime("%Y-%m")

    def _collect_global_assumptions(self, predictions: list[DealPrediction]) -> list[str]:
        """Collect common assumptions across predictions."""
        assumption_counts = defaultdict(int)
        for pred in predictions:
            for assumption in pred.assumptions:
                assumption_counts[assumption] += 1

        # Global = mentioned in >20% of deals
        threshold = max(1, len(predictions) * 0.2)
        return [
            assumption for assumption, count in assumption_counts.items()
            if count >= threshold
        ]

    def _collect_warnings(self, predictions: list[DealPrediction], today: datetime) -> list[str]:
        """Collect validation warnings."""
        warnings = []

        for pred in predictions:
            pred_warnings = self.rules.validate_prediction(pred, today)
            for warning in pred_warnings:
                warnings.append(f"Deal {pred.deal_id}: {warning}")

        return warnings[:10]  # Limit to top 10


# Global service instance
_cashflow_prediction_service: Optional[CashflowPredictionService] = None


def get_cashflow_prediction_service() -> CashflowPredictionService:
    """Get or create cashflow prediction service singleton."""
    global _cashflow_prediction_service
    if _cashflow_prediction_service is None:
        _cashflow_prediction_service = CashflowPredictionService()
    return _cashflow_prediction_service
