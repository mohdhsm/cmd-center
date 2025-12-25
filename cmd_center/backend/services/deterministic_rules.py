"""Deterministic rules engine for cashflow predictions.

This module provides pure rule-based predictions for cashflow forecasting
based on stage duration data and business rules.

Rules are derived from the Cashflow Prediction Reference Document.
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

    Uses stage-based duration estimates from the prediction reference document.
    All predictions use "Realistic" estimates by default.
    """

    # Days to invoice by stage (Realistic estimates, excluding production time)
    # Format: stage_name -> days_to_invoice
    STAGE_DAYS_TO_INVOICE = {
        # Order Received - size dependent, using medium estimate as default
        "Order Received": 42,

        # Other stages
        "Approved": 29,
        "Awaiting Payment": 27,
        "Awaiting Site Readiness": 22,
        "Everything Ready": 17,
        "Under Progress": 12,
        "Underprogress": 12,  # Alternative spelling
        "Under progress": 12,
        "Awaiting MDD": 12,
        "Awaiting GCC": 10,
        "Awaiting GR": 7,

        # Alternative stage names
        "Production /Supplying": 12,
        "Production/Supplying": 12,
    }

    # Order Received durations by project size
    ORDER_RECEIVED_BY_SIZE = {
        "small": 36,    # < 100 SQM
        "medium": 42,   # 100-400 SQM
        "large": 50,    # > 400 SQM
    }

    # Payment terms (days after invoice)
    ARAMCO_PAYMENT_DAYS = 7  # Aramco pays quickly after invoice
    COMMERCIAL_PAYMENT_DAYS = 45  # Commercial clients: 30-60 days

    # Confidence levels
    HIGH_CONFIDENCE = 0.85
    MEDIUM_CONFIDENCE = 0.70
    LOW_CONFIDENCE = 0.50

    def predict_deal(
        self,
        deal: DealForPrediction,
        today: datetime,
    ) -> DealPrediction:
        """Generate a deterministic prediction for a deal.

        Args:
            deal: Deal data
            today: Reference date

        Returns:
            DealPrediction with predicted dates and confidence
        """
        assumptions = []
        confidence = self.MEDIUM_CONFIDENCE

        # Step 1: Get base days to invoice from stage
        stage_normalized = deal.stage.strip() if deal.stage else "Unknown"
        base_days = self.STAGE_DAYS_TO_INVOICE.get(stage_normalized)

        if base_days is None:
            # Unknown stage - use conservative estimate
            base_days = 45
            confidence = self.LOW_CONFIDENCE
            assumptions.append(f"Unknown stage '{stage_normalized}', using default 45 days")
        else:
            assumptions.append(f"Stage '{stage_normalized}' estimate: {base_days} days")

        # Step 2: Adjust for deal staleness (stuck deals)
        if deal.days_in_stage > 60:
            delay = 14  # Add 2 weeks for very stuck deals
            base_days += delay
            confidence -= 0.1
            assumptions.append(f"Deal stuck ({deal.days_in_stage} days in stage), added {delay} days")
        elif deal.days_in_stage > 30:
            delay = 7  # Add 1 week for moderately stuck deals
            base_days += delay
            confidence -= 0.05
            assumptions.append(f"Deal slow ({deal.days_in_stage} days in stage), added {delay} days")

        # Step 3: Check if already at late stage
        late_stages = ["Awaiting GR", "Awaiting GCC", "Awaiting MDD"]
        if stage_normalized in late_stages:
            confidence = self.HIGH_CONFIDENCE
            assumptions.append("Late stage - high confidence in estimate")

        # Step 4: Calculate dates
        invoice_date = today + timedelta(days=base_days)

        # Payment date depends on client type (assume Aramco if in Aramco pipeline)
        is_aramco = "aramco" in deal.title.lower() if deal.title else False
        if is_aramco:
            payment_days = self.ARAMCO_PAYMENT_DAYS
            assumptions.append("Aramco deal - quick payment terms")
        else:
            payment_days = self.COMMERCIAL_PAYMENT_DAYS
            assumptions.append("Commercial payment terms (45 days)")

        payment_date = invoice_date + timedelta(days=payment_days)

        # Step 5: Handle special cases
        missing_fields = []

        # Check for invoice already issued
        if stage_normalized.lower() in ["invoice issued", "invoiced", "payment received"]:
            invoice_date = deal.last_stage_change_date or today
            payment_date = invoice_date + timedelta(days=payment_days)
            confidence = 0.95
            assumptions = ["Invoice already issued at stage change"]

        return DealPrediction(
            deal_id=deal.deal_id,
            deal_title=deal.title,
            predicted_invoice_date=invoice_date,
            predicted_payment_date=payment_date,
            confidence=max(0.3, min(0.95, confidence)),  # Clamp confidence
            assumptions=assumptions,
            missing_fields=missing_fields,
            reasoning=f"Deterministic prediction based on stage '{stage_normalized}'",
            owner_name=deal.owner_name,
            stage=deal.stage,
            value_sar=deal.value_sar,
        )

    def precheck_deal(self, deal: DealForPrediction, today: datetime) -> Optional[DealPrediction]:
        """Check if we can make a deterministic prediction.

        This always returns a prediction now (pure deterministic mode).

        Args:
            deal: Deal to check
            today: Reference date

        Returns:
            DealPrediction
        """
        return self.predict_deal(deal, today)

    def apply_overrides(
        self,
        prediction: DealPrediction,
        deal: DealForPrediction,
        today: datetime,
    ) -> DealPrediction:
        """Apply rule-based overrides to a prediction.

        In pure deterministic mode, this just validates and adjusts.

        Args:
            prediction: Current prediction
            deal: Original deal data
            today: Reference date

        Returns:
            Modified prediction
        """
        # Sanity check - invoice date should not be in distant past
        if prediction.predicted_invoice_date:
            days_ago = _days_between(today, prediction.predicted_invoice_date)
            if days_ago > 30:
                # Invoice date is too far in past - likely error
                prediction.predicted_invoice_date = today + timedelta(days=7)
                prediction.confidence = max(0.3, prediction.confidence - 0.2)
                prediction.assumptions.append(
                    "Override: Invoice date was in past, adjusted to near future"
                )

        # Payment should be after invoice
        if prediction.predicted_invoice_date and prediction.predicted_payment_date:
            if prediction.predicted_payment_date <= prediction.predicted_invoice_date:
                prediction.predicted_payment_date = prediction.predicted_invoice_date + timedelta(
                    days=self.COMMERCIAL_PAYMENT_DAYS
                )
                prediction.assumptions.append(
                    "Override: Payment date before invoice, adjusted"
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
        return self.STAGE_DAYS_TO_INVOICE.get(stage)
