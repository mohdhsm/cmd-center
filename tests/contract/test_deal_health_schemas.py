"""Contract tests for Deal Health Summary schema validation.

These tests ensure that:
1. DealHealthContext input schema validates correctly
2. DealHealthResult output schema validates correctly
3. All health status values and attributions are handled
4. Edge cases like missing optional fields work correctly
"""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from cmd_center.backend.models.writer_models import (
    DealHealthContext,
    DealHealthResult,
)


class TestDealHealthContextSchema:
    """Test DealHealthContext input schema validation."""

    def test_valid_context(self, sample_deal_health_context):
        """Valid deal health context passes schema validation."""
        result = DealHealthContext.model_validate(sample_deal_health_context)
        assert result.deal_id == 6670
        assert result.deal_title == "Aramco Office Renovation Phase 2"
        assert result.stage_code == "AP"
        assert result.days_in_stage == 12

    def test_context_requires_deal_id(self, sample_deal_health_context):
        """Context requires deal_id field."""
        invalid = {**sample_deal_health_context}
        del invalid["deal_id"]
        with pytest.raises(ValidationError) as exc_info:
            DealHealthContext.model_validate(invalid)
        assert "deal_id" in str(exc_info.value)

    def test_context_requires_deal_title(self, sample_deal_health_context):
        """Context requires deal_title field."""
        invalid = {**sample_deal_health_context}
        del invalid["deal_title"]
        with pytest.raises(ValidationError) as exc_info:
            DealHealthContext.model_validate(invalid)
        assert "deal_title" in str(exc_info.value)

    def test_context_requires_stage(self, sample_deal_health_context):
        """Context requires stage field."""
        invalid = {**sample_deal_health_context}
        del invalid["stage"]
        with pytest.raises(ValidationError) as exc_info:
            DealHealthContext.model_validate(invalid)
        assert "stage" in str(exc_info.value)

    def test_context_requires_stage_code(self, sample_deal_health_context):
        """Context requires stage_code field."""
        invalid = {**sample_deal_health_context}
        del invalid["stage_code"]
        with pytest.raises(ValidationError) as exc_info:
            DealHealthContext.model_validate(invalid)
        assert "stage_code" in str(exc_info.value)

    def test_context_requires_days_in_stage(self, sample_deal_health_context):
        """Context requires days_in_stage field."""
        invalid = {**sample_deal_health_context}
        del invalid["days_in_stage"]
        with pytest.raises(ValidationError) as exc_info:
            DealHealthContext.model_validate(invalid)
        assert "days_in_stage" in str(exc_info.value)

    def test_context_requires_owner_name(self, sample_deal_health_context):
        """Context requires owner_name field."""
        invalid = {**sample_deal_health_context}
        del invalid["owner_name"]
        with pytest.raises(ValidationError) as exc_info:
            DealHealthContext.model_validate(invalid)
        assert "owner_name" in str(exc_info.value)

    def test_context_optional_value_sar(self, sample_deal_health_context):
        """value_sar is optional."""
        data = {**sample_deal_health_context}
        del data["value_sar"]
        result = DealHealthContext.model_validate(data)
        assert result.value_sar is None

    def test_context_optional_last_activity_date(self, sample_deal_health_context):
        """last_activity_date is optional."""
        data = {**sample_deal_health_context}
        del data["last_activity_date"]
        result = DealHealthContext.model_validate(data)
        assert result.last_activity_date is None

    def test_context_optional_days_since_last_note(self, sample_deal_health_context):
        """days_since_last_note is optional."""
        data = {**sample_deal_health_context}
        del data["days_since_last_note"]
        result = DealHealthContext.model_validate(data)
        assert result.days_since_last_note is None

    def test_context_empty_notes_list(self, sample_deal_health_context):
        """Context works with empty notes list."""
        data = {**sample_deal_health_context}
        data["notes"] = []
        result = DealHealthContext.model_validate(data)
        assert result.notes == []

    def test_context_empty_stage_history(self, sample_deal_health_context):
        """Context works with empty stage history."""
        data = {**sample_deal_health_context}
        data["stage_history"] = []
        result = DealHealthContext.model_validate(data)
        assert result.stage_history == []

    def test_context_minimal_required_fields(self):
        """Context works with only required fields."""
        minimal = {
            "deal_id": 1,
            "deal_title": "Test Deal",
            "stage": "Order Received",
            "stage_code": "OR",
            "days_in_stage": 5,
            "owner_name": "Test Owner",
        }
        result = DealHealthContext.model_validate(minimal)
        assert result.deal_id == 1
        assert result.notes == []
        assert result.stage_history == []


class TestDealHealthResultSchema:
    """Test DealHealthResult output schema validation."""

    def test_valid_result(self, sample_deal_health_result):
        """Valid deal health result passes schema validation."""
        result = DealHealthResult.model_validate(sample_deal_health_result)
        assert result.deal_id == 6670
        assert result.health_status == "at_risk"
        assert result.status_flag == "PAYMENT_ISSUE"
        assert result.confidence == 0.85

    def test_valid_healthy_result(self, sample_deal_health_result_healthy):
        """Valid healthy deal result passes validation."""
        result = DealHealthResult.model_validate(sample_deal_health_result_healthy)
        assert result.health_status == "healthy"
        assert result.status_flag is None
        assert result.blockers == []

    def test_valid_critical_result(self, sample_deal_health_result_critical):
        """Valid critical deal result passes validation."""
        result = DealHealthResult.model_validate(sample_deal_health_result_critical)
        assert result.health_status == "critical"
        assert result.status_flag == "SITE_BLOCKED"
        assert len(result.blockers) == 3

    def test_result_requires_health_status(self, sample_deal_health_result):
        """Result requires health_status field."""
        invalid = {**sample_deal_health_result}
        del invalid["health_status"]
        with pytest.raises(ValidationError) as exc_info:
            DealHealthResult.model_validate(invalid)
        assert "health_status" in str(exc_info.value)

    def test_result_requires_summary(self, sample_deal_health_result):
        """Result requires summary field."""
        invalid = {**sample_deal_health_result}
        del invalid["summary"]
        with pytest.raises(ValidationError) as exc_info:
            DealHealthResult.model_validate(invalid)
        assert "summary" in str(exc_info.value)

    def test_result_requires_recommended_action(self, sample_deal_health_result):
        """Result requires recommended_action field."""
        invalid = {**sample_deal_health_result}
        del invalid["recommended_action"]
        with pytest.raises(ValidationError) as exc_info:
            DealHealthResult.model_validate(invalid)
        assert "recommended_action" in str(exc_info.value)

    def test_result_requires_confidence(self, sample_deal_health_result):
        """Result requires confidence field."""
        invalid = {**sample_deal_health_result}
        del invalid["confidence"]
        with pytest.raises(ValidationError) as exc_info:
            DealHealthResult.model_validate(invalid)
        assert "confidence" in str(exc_info.value)

    def test_result_confidence_range_valid(self, sample_deal_health_result):
        """Confidence must be between 0 and 1."""
        data = {**sample_deal_health_result}
        data["confidence"] = 0.5
        result = DealHealthResult.model_validate(data)
        assert result.confidence == 0.5

    def test_result_confidence_at_zero(self, sample_deal_health_result):
        """Confidence can be exactly 0."""
        data = {**sample_deal_health_result}
        data["confidence"] = 0.0
        result = DealHealthResult.model_validate(data)
        assert result.confidence == 0.0

    def test_result_confidence_at_one(self, sample_deal_health_result):
        """Confidence can be exactly 1."""
        data = {**sample_deal_health_result}
        data["confidence"] = 1.0
        result = DealHealthResult.model_validate(data)
        assert result.confidence == 1.0

    def test_result_confidence_below_zero_fails(self, sample_deal_health_result):
        """Confidence below 0 fails validation."""
        invalid = {**sample_deal_health_result}
        invalid["confidence"] = -0.1
        with pytest.raises(ValidationError):
            DealHealthResult.model_validate(invalid)

    def test_result_confidence_above_one_fails(self, sample_deal_health_result):
        """Confidence above 1 fails validation."""
        invalid = {**sample_deal_health_result}
        invalid["confidence"] = 1.1
        with pytest.raises(ValidationError):
            DealHealthResult.model_validate(invalid)

    def test_result_optional_status_flag(self, sample_deal_health_result):
        """status_flag is optional."""
        data = {**sample_deal_health_result}
        data["status_flag"] = None
        result = DealHealthResult.model_validate(data)
        assert result.status_flag is None

    def test_result_optional_communication_gap_days(self, sample_deal_health_result):
        """communication_gap_days is optional."""
        data = {**sample_deal_health_result}
        data["communication_gap_days"] = None
        result = DealHealthResult.model_validate(data)
        assert result.communication_gap_days is None

    def test_result_empty_blockers_list(self, sample_deal_health_result):
        """Result works with empty blockers list."""
        data = {**sample_deal_health_result}
        data["blockers"] = []
        result = DealHealthResult.model_validate(data)
        assert result.blockers == []

    def test_result_default_values(self):
        """Result applies default values correctly."""
        minimal = {
            "health_status": "healthy",
            "summary": "Test summary",
            "recommended_action": "Test action",
            "confidence": 0.9,
        }
        result = DealHealthResult.model_validate(minimal)
        assert result.deal_id == 0  # default
        assert result.days_in_stage == 0  # default
        assert result.stage_threshold_warning == 0  # default
        assert result.stage_threshold_critical == 0  # default
        assert result.communication_assessment == "Unknown"  # default
        assert result.blockers == []  # default
        assert result.attribution == "none"  # default


class TestDealHealthStatusValues:
    """Test various health status and attribution values."""

    @pytest.mark.parametrize("status", ["healthy", "at_risk", "critical", "unknown"])
    def test_health_status_values(self, sample_deal_health_result, status):
        """All expected health status values are accepted."""
        data = {**sample_deal_health_result}
        data["health_status"] = status
        result = DealHealthResult.model_validate(data)
        assert result.health_status == status

    @pytest.mark.parametrize("flag", [
        "AT_RISK", "DELAYED", "PAYMENT_ISSUE", "SITE_BLOCKED",
        "QUEUE_BACKLOG", "PRODUCTION_ISSUE", "DOC_DELAYED", "GR_BLOCKED",
        None
    ])
    def test_status_flag_values(self, sample_deal_health_result, flag):
        """All expected status flag values are accepted."""
        data = {**sample_deal_health_result}
        data["status_flag"] = flag
        result = DealHealthResult.model_validate(data)
        assert result.status_flag == flag

    @pytest.mark.parametrize("attribution", [
        "customer_delay", "employee_gap", "site_blocked",
        "procurement_fault", "partial_delivery", "none"
    ])
    def test_attribution_values(self, sample_deal_health_result, attribution):
        """All expected attribution values are accepted."""
        data = {**sample_deal_health_result}
        data["attribution"] = attribution
        result = DealHealthResult.model_validate(data)
        assert result.attribution == attribution

    @pytest.mark.parametrize("assessment", [
        "Healthy", "Acceptable", "Warning", "Communication Gap", "Unknown"
    ])
    def test_communication_assessment_values(self, sample_deal_health_result, assessment):
        """All expected communication assessment values are accepted."""
        data = {**sample_deal_health_result}
        data["communication_assessment"] = assessment
        result = DealHealthResult.model_validate(data)
        assert result.communication_assessment == assessment


class TestDealHealthStageCodeMapping:
    """Test stage code values match expected codes."""

    @pytest.mark.parametrize("stage_code,stage_name", [
        ("OR", "Order Received"),
        ("APR", "Approved"),
        ("AP", "Awaiting Payment"),
        ("ASR", "Awaiting Site Readiness"),
        ("ER", "Everything Ready"),
        ("UP", "Under Progress"),
        ("MDD", "Awaiting MDD"),
        ("GCC", "Awaiting GCC"),
        ("GR", "Awaiting GR"),
        ("INV", "Invoice Issued"),
        ("UNK", "Unknown Stage"),
    ])
    def test_stage_codes_accepted(self, sample_deal_health_context, stage_code, stage_name):
        """All expected stage codes are accepted in context."""
        data = {**sample_deal_health_context}
        data["stage_code"] = stage_code
        data["stage"] = stage_name
        result = DealHealthContext.model_validate(data)
        assert result.stage_code == stage_code
        assert result.stage == stage_name
