"""Contract tests for CEO Dashboard API response schema validation.

These tests ensure that:
1. Sample test data matches actual API response schemas
2. All nested models validate correctly
3. Status types and trend types are properly constrained
4. Response models can validate real API data
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from cmd_center.backend.models.ceo_dashboard_models import (
    CashHealth,
    UrgentDeal,
    PipelineStage,
    PipelineVelocity,
    StrategicPriority,
    SalesScorecard,
    DepartmentScorecard,
    CEODashboardMetrics,
)


class TestCashHealthSchema:
    """Test CashHealth response schema validation."""

    def test_valid_cash_health(self, sample_cash_health_response):
        """Valid cash health data passes schema validation."""
        result = CashHealth.model_validate(sample_cash_health_response)
        assert result.runway_months == 4.2
        assert result.runway_status == "green"
        assert result.velocity_pct == 65.0

    def test_cash_health_requires_runway_months(self):
        """CashHealth requires runway_months field."""
        invalid = {
            "runway_status": "green",
            "total_collected_week": 125000,
            "total_target_week": 200000,
            "collection_pct": 62.5,
            "predicted_14d": 340000,
            "velocity_pct": 65,
            "velocity_status": "yellow",
        }
        with pytest.raises(ValidationError) as exc_info:
            CashHealth.model_validate(invalid)
        assert "runway_months" in str(exc_info.value)

    def test_cash_health_status_must_be_valid(self):
        """CashHealth status must be green, yellow, or red."""
        invalid = {
            "runway_months": 4.2,
            "runway_status": "blue",  # Invalid status
            "total_collected_week": 125000,
            "total_target_week": 200000,
            "collection_pct": 62.5,
            "predicted_14d": 340000,
            "velocity_pct": 65,
            "velocity_status": "green",
        }
        with pytest.raises(ValidationError) as exc_info:
            CashHealth.model_validate(invalid)
        assert "runway_status" in str(exc_info.value)

    def test_cash_health_defaults_optional_fields(self):
        """CashHealth uses defaults for optional aramco/commercial fields."""
        minimal = {
            "runway_months": 3.0,
            "runway_status": "yellow",
            "total_collected_week": 100000,
            "total_target_week": 200000,
            "collection_pct": 50.0,
            "predicted_14d": 200000,
            "velocity_pct": 50.0,
            "velocity_status": "yellow",
        }
        result = CashHealth.model_validate(minimal)
        assert result.aramco_collected_week == 0.0
        assert result.commercial_collected_week == 0.0


class TestUrgentDealSchema:
    """Test UrgentDeal response schema validation."""

    def test_valid_urgent_deal(self, sample_urgent_deal_response):
        """Valid urgent deal data passes schema validation."""
        result = UrgentDeal.model_validate(sample_urgent_deal_response)
        assert result.deal_id == 1001
        assert result.title == "Aramco Maintenance Contract"
        assert result.days_stuck == 23

    def test_urgent_deal_requires_deal_id(self):
        """UrgentDeal requires deal_id field."""
        invalid = {
            "title": "Test Deal",
            "reason": "Awaiting GR 10 days",
            "value_sar": 50000,
            "stage": "Awaiting GR",
            "owner": "Ahmed",
            "days_stuck": 10,
        }
        with pytest.raises(ValidationError) as exc_info:
            UrgentDeal.model_validate(invalid)
        assert "deal_id" in str(exc_info.value)

    def test_urgent_deal_requires_all_fields(self):
        """UrgentDeal requires all mandatory fields."""
        invalid = {"deal_id": 1, "title": "Test"}
        with pytest.raises(ValidationError) as exc_info:
            UrgentDeal.model_validate(invalid)
        # Should fail on multiple missing fields
        error_str = str(exc_info.value)
        assert "reason" in error_str or "value_sar" in error_str


class TestPipelineStageSchema:
    """Test PipelineStage response schema validation."""

    def test_valid_pipeline_stage(self, sample_pipeline_stage_response):
        """Valid pipeline stage data passes schema validation."""
        result = PipelineStage.model_validate(sample_pipeline_stage_response)
        assert result.name == "Order Received"
        assert result.avg_days == 5.2
        assert result.deal_count == 8

    def test_pipeline_stage_requires_stage_id(self):
        """PipelineStage requires stage_id field."""
        invalid = {
            "name": "Test Stage",
            "avg_days": 5.0,
            "deal_count": 3,
        }
        with pytest.raises(ValidationError) as exc_info:
            PipelineStage.model_validate(invalid)
        assert "stage_id" in str(exc_info.value)


class TestPipelineVelocitySchema:
    """Test PipelineVelocity response schema validation."""

    def test_valid_pipeline_velocity(self, sample_pipeline_velocity_response):
        """Valid pipeline velocity data passes schema validation."""
        result = PipelineVelocity.model_validate(sample_pipeline_velocity_response)
        assert len(result.stages) == 4
        assert result.current_cycle_days == 35.0
        assert result.trend == "worse"

    def test_pipeline_velocity_trend_must_be_valid(self):
        """PipelineVelocity trend must be better, worse, or stable."""
        invalid = {
            "stages": [],
            "current_cycle_days": 20.0,
            "target_cycle_days": 21.0,
            "trend": "improving",  # Invalid trend
        }
        with pytest.raises(ValidationError) as exc_info:
            PipelineVelocity.model_validate(invalid)
        assert "trend" in str(exc_info.value)

    def test_pipeline_velocity_defaults_target(self):
        """PipelineVelocity uses default for target_cycle_days."""
        minimal = {
            "stages": [],
            "current_cycle_days": 20.0,
            "trend": "better",
        }
        result = PipelineVelocity.model_validate(minimal)
        assert result.target_cycle_days == 21.0


class TestStrategicPrioritySchema:
    """Test StrategicPriority response schema validation."""

    def test_valid_strategic_priority(self, sample_strategic_priority_response):
        """Valid strategic priority data passes schema validation."""
        result = StrategicPriority.model_validate(sample_strategic_priority_response)
        assert result.name == "Cost Reduction"
        assert result.pct == 75.0
        assert result.status == "yellow"

    def test_strategic_priority_requires_target(self):
        """StrategicPriority requires target field."""
        invalid = {
            "name": "Test Priority",
            "current": 50.0,
            "pct": 50.0,
            "status": "yellow",
        }
        with pytest.raises(ValidationError) as exc_info:
            StrategicPriority.model_validate(invalid)
        assert "target" in str(exc_info.value)

    def test_strategic_priority_status_must_be_valid(self):
        """StrategicPriority status must be valid."""
        invalid = {
            "name": "Test",
            "current": 50.0,
            "target": 100.0,
            "pct": 50.0,
            "status": "orange",  # Invalid
        }
        with pytest.raises(ValidationError) as exc_info:
            StrategicPriority.model_validate(invalid)
        assert "status" in str(exc_info.value)


class TestSalesScorecardSchema:
    """Test SalesScorecard response schema validation."""

    def test_valid_sales_scorecard(self, sample_sales_scorecard_response):
        """Valid sales scorecard data passes schema validation."""
        result = SalesScorecard.model_validate(sample_sales_scorecard_response)
        assert result.pipeline_value == 2100000.0
        assert result.won_value == 450000.0
        assert result.status == "green"

    def test_sales_scorecard_requires_all_fields(self):
        """SalesScorecard requires all mandatory fields."""
        invalid = {"pipeline_value": 1000000, "status": "green"}
        with pytest.raises(ValidationError) as exc_info:
            SalesScorecard.model_validate(invalid)
        error_str = str(exc_info.value)
        assert "won_value" in error_str or "active_deals_count" in error_str


class TestDepartmentScorecardSchema:
    """Test DepartmentScorecard response schema validation."""

    def test_valid_department_scorecard(
        self, sample_sales_scorecard_response
    ):
        """Valid department scorecard passes validation."""
        data = {"sales": sample_sales_scorecard_response}
        result = DepartmentScorecard.model_validate(data)
        assert result.sales.pipeline_value == 2100000.0

    def test_department_scorecard_requires_sales(self):
        """DepartmentScorecard requires sales field."""
        invalid = {}
        with pytest.raises(ValidationError) as exc_info:
            DepartmentScorecard.model_validate(invalid)
        assert "sales" in str(exc_info.value)


class TestCEODashboardMetricsSchema:
    """Test complete CEODashboardMetrics response schema validation."""

    def test_valid_ceo_dashboard_metrics(self, sample_ceo_dashboard_response):
        """Valid CEO dashboard response passes schema validation."""
        result = CEODashboardMetrics.model_validate(sample_ceo_dashboard_response)
        assert result.cash_health.runway_months == 4.2
        assert len(result.urgent_deals) == 2
        assert result.pipeline_velocity.trend == "worse"
        assert len(result.strategic_priorities) == 3
        assert result.department_scorecard.sales.status == "green"

    def test_ceo_dashboard_requires_all_sections(self):
        """CEODashboardMetrics requires all major sections."""
        invalid = {
            "cash_health": {},  # Invalid nested
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        with pytest.raises(ValidationError):
            CEODashboardMetrics.model_validate(invalid)

    def test_urgent_deals_max_length(self, sample_ceo_dashboard_response):
        """CEODashboardMetrics limits urgent_deals to 5."""
        # Add more than 5 urgent deals
        data = sample_ceo_dashboard_response.copy()
        data["urgent_deals"] = [
            {
                "deal_id": i,
                "title": f"Deal {i}",
                "reason": "Test",
                "value_sar": 10000,
                "stage": "Test",
                "owner": "Test",
                "days_stuck": 10,
            }
            for i in range(10)
        ]
        with pytest.raises(ValidationError) as exc_info:
            CEODashboardMetrics.model_validate(data)
        assert "urgent_deals" in str(exc_info.value)

    def test_ceo_dashboard_metadata_fields(self, sample_ceo_dashboard_response):
        """CEODashboardMetrics includes metadata fields."""
        result = CEODashboardMetrics.model_validate(sample_ceo_dashboard_response)
        assert result.last_updated is not None
        assert result.data_freshness == "live"


class TestStatusTypeValidation:
    """Test StatusType literal validation across models."""

    @pytest.mark.parametrize("status", ["green", "yellow", "red"])
    def test_valid_status_values(self, status):
        """All valid status values are accepted."""
        data = {
            "runway_months": 3.0,
            "runway_status": status,
            "total_collected_week": 100000,
            "total_target_week": 200000,
            "collection_pct": 50.0,
            "predicted_14d": 200000,
            "velocity_pct": 50.0,
            "velocity_status": status,
        }
        result = CashHealth.model_validate(data)
        assert result.runway_status == status

    @pytest.mark.parametrize("invalid_status", ["blue", "orange", "GREEN", "Red", ""])
    def test_invalid_status_values_rejected(self, invalid_status):
        """Invalid status values are rejected."""
        data = {
            "runway_months": 3.0,
            "runway_status": invalid_status,
            "total_collected_week": 100000,
            "total_target_week": 200000,
            "collection_pct": 50.0,
            "predicted_14d": 200000,
            "velocity_pct": 50.0,
            "velocity_status": "green",
        }
        with pytest.raises(ValidationError):
            CashHealth.model_validate(data)


class TestTrendTypeValidation:
    """Test TrendType literal validation."""

    @pytest.mark.parametrize("trend", ["better", "worse", "stable"])
    def test_valid_trend_values(self, trend):
        """All valid trend values are accepted."""
        data = {
            "stages": [],
            "current_cycle_days": 20.0,
            "trend": trend,
        }
        result = PipelineVelocity.model_validate(data)
        assert result.trend == trend

    @pytest.mark.parametrize("invalid_trend", ["improving", "declining", "BETTER", ""])
    def test_invalid_trend_values_rejected(self, invalid_trend):
        """Invalid trend values are rejected."""
        data = {
            "stages": [],
            "current_cycle_days": 20.0,
            "trend": invalid_trend,
        }
        with pytest.raises(ValidationError):
            PipelineVelocity.model_validate(data)
