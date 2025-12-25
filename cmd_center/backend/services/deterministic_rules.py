"""Deterministic rules engine for cashflow predictions.

This module provides rule-based overrides and pre-checks
that can supplement or override LLM predictions.
"""

from datetime import datetime, timedelta
from typing import Optional
from ..models.cashflow_models import DealForPrediction, DealPrediction


def _normalize_datetime(dt: datetime) -> datetime:
    """Strip timezone info for consistent comparisons."""
    if dt is None:
        return None
    return dt.replace(tzinfo=None) if dt.tzinfo else dt


def _days_between(dt1: datetime, dt2: datetime) -> int:
    """Calculate days between two dates, handling timezone mismatches."""
    return (_normalize_datetime(dt1) - _normalize_datetime(dt2)).days


class DeterministicRules:
    """Rule-based prediction logic for cashflow.

    These rules provide:
    1. Pre-checks: Return prediction without calling LLM if certain conditions met
    2. Post-processing: Override low-confidence LLM predictions with rule-based estimates
    3. Validation: Sanity-check LLM predictions
    """

    # Stage-based average cycle times (in days)
    STAGE_CYCLE_TIMES = {
        "Order Received": 10,  # 7-14 days to invoice approval
        "Under Progress": 22,  # 14-30 days to invoice
        "Underprogress": 22,  # Alternative spelling
        "Awaiting GR": 5,  # 3-7 days to invoice
        "Awaiting MDD": 21,  # ~3 weeks
        "Production /Supplying": 45,  # 30-60 days to invoice
        "Production/Supplying": 45,
    }

    # Payment terms (days after invoice)
    DEFAULT_PAYMENT_TERMS = 37  # 30-45 days average

    def precheck_deal(self, deal: DealForPrediction, today: datetime) -> Optional[DealPrediction]:
        """Check if we can make a deterministic prediction without LLM.

        Args:
            deal: Deal to check
            today: Reference date

        Returns:
            DealPrediction if deterministic rule applies, None otherwise
        """
        # Rule 1: If stage indicates already invoiced
        if "invoice" in deal.stage.lower() and "await" not in deal.stage.lower():
            # Assume invoice was issued at stage change
            invoice_date = deal.last_stage_change_date or today
            payment_date = invoice_date + timedelta(days=self.DEFAULT_PAYMENT_TERMS)

            return DealPrediction(
                deal_id=deal.deal_id,
                deal_title=deal.title,
                predicted_invoice_date=invoice_date,
                predicted_payment_date=payment_date,
                confidence=0.95,
                assumptions=["Stage indicates invoice already issued at stage change"],
                missing_fields=[],
                reasoning="Deterministic: Invoice stage detected",
            )

        # Rule 2: If deal is in a known stage with no recent activity
        if deal.stage in self.STAGE_CYCLE_TIMES and deal.days_in_stage > 60:
            # Deal is stuck - add delay
            base_days = self.STAGE_CYCLE_TIMES[deal.stage]
            delay_days = 14  # Add 2 weeks for stuck deals

            invoice_date = today + timedelta(days=base_days + delay_days)
            payment_date = invoice_date + timedelta(days=self.DEFAULT_PAYMENT_TERMS)

            return DealPrediction(
                deal_id=deal.deal_id,
                deal_title=deal.title,
                predicted_invoice_date=invoice_date,
                predicted_payment_date=payment_date,
                confidence=0.6,
                assumptions=[
                    f"Stage '{deal.stage}' typical cycle: {base_days} days",
                    f"Deal stuck ({deal.days_in_stage} days) - added {delay_days} days delay",
                ],
                missing_fields=["Recent activity data"],
                reasoning="Deterministic: Stage-based estimate with stuck penalty",
            )

        # No deterministic rule applies
        return None

    def apply_overrides(
        self,
        prediction: DealPrediction,
        deal: DealForPrediction,
        today: datetime,
    ) -> DealPrediction:
        """Apply rule-based overrides to LLM prediction.

        Args:
            prediction: LLM prediction
            deal: Original deal data
            today: Reference date

        Returns:
            Modified prediction (may be unchanged)
        """
        # Override 1: If confidence is very low, use stage-based estimate
        if prediction.confidence < 0.4 and deal.stage in self.STAGE_CYCLE_TIMES:
            base_days = self.STAGE_CYCLE_TIMES[deal.stage]

            # Adjust for deal staleness
            if deal.days_in_stage > 30:
                base_days += 7

            invoice_date = today + timedelta(days=base_days)
            payment_date = invoice_date + timedelta(days=self.DEFAULT_PAYMENT_TERMS)

            prediction.predicted_invoice_date = invoice_date
            prediction.predicted_payment_date = payment_date
            prediction.confidence = 0.5
            prediction.assumptions.append(
                f"Override: Low LLM confidence, using stage average ({base_days} days)"
            )

        # Override 2: Sanity check - invoice date should not be in distant past
        if prediction.predicted_invoice_date:
            days_ago = (today - prediction.predicted_invoice_date).days
            if days_ago > 30:
                # Invoice date is too far in past - likely error
                prediction.predicted_invoice_date = today + timedelta(days=7)
                prediction.confidence = max(0.3, prediction.confidence - 0.2)
                prediction.assumptions.append(
                    "Override: Invoice date was in past, adjusted to near future"
                )

        # Override 3: Payment should be after invoice
        if prediction.predicted_invoice_date and prediction.predicted_payment_date:
            if prediction.predicted_payment_date <= prediction.predicted_invoice_date:
                prediction.predicted_payment_date = prediction.predicted_invoice_date + timedelta(
                    days=self.DEFAULT_PAYMENT_TERMS
                )
                prediction.assumptions.append(
                    "Override: Payment date before invoice, adjusted to invoice + 37 days"
                )

        return prediction

    def validate_prediction(self, prediction: DealPrediction, today: datetime) -> list[str]:
        """Validate a prediction and return warnings.

        Args:
            prediction: Prediction to validate
            today: Reference date

        Returns:
            List of warning messages (empty if valid)
        """
        warnings = []

        # Check 1: Invoice date reasonableness
        if prediction.predicted_invoice_date:
            days_from_now = _days_between(prediction.predicted_invoice_date, today)
            if days_from_now > 365:
                warnings.append(f"Invoice date is {days_from_now} days in future (>1 year)")
            if days_from_now < -30:
                warnings.append(f"Invoice date is {-days_from_now} days in past")

        # Check 2: Payment date reasonableness
        if prediction.predicted_payment_date:
            days_from_now = _days_between(prediction.predicted_payment_date, today)
            if days_from_now > 400:
                warnings.append(f"Payment date is {days_from_now} days in future (>400 days)")

        # Check 3: Invoice-payment gap
        if prediction.predicted_invoice_date and prediction.predicted_payment_date:
            gap_days = _days_between(prediction.predicted_payment_date, prediction.predicted_invoice_date)
            if gap_days < 0:
                warnings.append("Payment date is before invoice date")
            elif gap_days > 90:
                warnings.append(f"Payment gap is {gap_days} days (>90 days)")

        # Check 4: Confidence score
        if prediction.confidence < 0.3:
            warnings.append(f"Very low confidence: {prediction.confidence:.2f}")

        return warnings

    def get_stage_estimate(self, stage: str) -> Optional[int]:
        """Get estimated days to invoice for a stage.

        Args:
            stage: Stage name

        Returns:
            Days estimate or None if unknown stage
        """
        return self.STAGE_CYCLE_TIMES.get(stage)
