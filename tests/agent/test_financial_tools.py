"""Tests for financial tools."""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock

from cmd_center.agent.tools.financial_tools import (
    GetCashflowProjection,
    GetCashflowProjectionParams,
    GetCEODashboard,
    GetCEODashboardParams,
)


class TestGetCashflowProjection:
    """Tests for GetCashflowProjection tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = GetCashflowProjection()
        assert tool.name == "get_cashflow_projection"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = GetCashflowProjection()
        assert len(tool.description) > 20
        assert "cashflow" in tool.description.lower()

    def test_params_have_pipeline_field_with_default(self):
        """Parameters include pipeline field with default."""
        params = GetCashflowProjectionParams()
        assert params.pipeline_name == "Aramco Projects"

    def test_params_have_horizon_days_field_with_default(self):
        """Parameters include horizon_days field with default."""
        params = GetCashflowProjectionParams()
        assert params.horizon_days == 90

    def test_params_have_granularity_field_with_default(self):
        """Parameters include granularity field with default."""
        params = GetCashflowProjectionParams()
        assert params.granularity == "month"

    def test_schema_has_pipeline_param(self):
        """Schema includes pipeline parameter."""
        tool = GetCashflowProjection()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "pipeline_name" in props

    @patch("cmd_center.agent.tools.financial_tools.get_cashflow_prediction_service")
    def test_execute_returns_projection_data(self, mock_get_service):
        """Execute returns cashflow projection data."""
        from datetime import datetime

        # Setup mock service
        mock_service = Mock()
        mock_prediction = Mock(
            deal_id=1,
            deal_title="Test Deal",
            predicted_invoice_date=datetime(2026, 2, 15),
            predicted_payment_date=datetime(2026, 3, 15),
            confidence=0.8,
            owner_name="Alice",
            stage="Under Progress",
            value_sar=100000.0,
        )
        mock_bucket = Mock(
            period="2026-02",
            expected_invoice_value_sar=100000.0,
            deal_count=1,
        )
        mock_metadata = Mock(
            generated_at=datetime.now(),
            horizon_days=90,
            deals_analyzed=5,
            deals_with_predictions=3,
            avg_confidence=0.75,
        )
        mock_result = Mock(
            per_deal_predictions=[mock_prediction],
            aggregated_forecast=[mock_bucket],
            warnings=[],
            assumptions_used=["Standard stage durations applied"],
            metadata=mock_metadata,
        )

        # Make predict_cashflow return an awaitable
        async_mock = AsyncMock(return_value=mock_result)
        mock_service.predict_cashflow = async_mock
        mock_get_service.return_value = mock_service

        tool = GetCashflowProjection()
        params = GetCashflowProjectionParams(
            pipeline_name="Aramco Projects",
            horizon_days=90,
        )
        result = tool.execute(params)

        assert result.success is True
        assert "predictions" in result.data
        assert "aggregated_forecast" in result.data
        assert "metadata" in result.data
        assert len(result.data["predictions"]) == 1
        assert result.data["predictions"][0]["deal_id"] == 1

    @patch("cmd_center.agent.tools.financial_tools.get_cashflow_prediction_service")
    def test_execute_handles_error(self, mock_get_service):
        """Execute handles service errors gracefully."""
        mock_get_service.side_effect = Exception("Service unavailable")

        tool = GetCashflowProjection()
        params = GetCashflowProjectionParams()
        result = tool.execute(params)

        assert result.success is False
        assert "Service unavailable" in result.error

    @patch("cmd_center.agent.tools.financial_tools.get_cashflow_prediction_service")
    def test_execute_with_commercial_pipeline(self, mock_get_service):
        """Execute works with commercial pipeline."""
        from datetime import datetime

        mock_service = Mock()
        mock_result = Mock(
            per_deal_predictions=[],
            aggregated_forecast=[],
            warnings=[],
            assumptions_used=[],
            metadata=Mock(
                generated_at=datetime.now(),
                horizon_days=90,
                deals_analyzed=0,
                deals_with_predictions=0,
                avg_confidence=0.0,
            ),
        )
        async_mock = AsyncMock(return_value=mock_result)
        mock_service.predict_cashflow = async_mock
        mock_get_service.return_value = mock_service

        tool = GetCashflowProjection()
        result = tool.parse_and_execute({
            "pipeline_name": "Commercial",
            "horizon_days": 60,
        })

        assert result.success is True
        # Verify the service was called with correct params
        mock_service.predict_cashflow.assert_called_once()

    @patch("cmd_center.agent.tools.financial_tools.get_cashflow_prediction_service")
    def test_execute_includes_warnings(self, mock_get_service):
        """Execute includes warnings from service."""
        from datetime import datetime

        mock_service = Mock()
        mock_result = Mock(
            per_deal_predictions=[],
            aggregated_forecast=[],
            warnings=["Deal 123: Low activity count"],
            assumptions_used=[],
            metadata=Mock(
                generated_at=datetime.now(),
                horizon_days=90,
                deals_analyzed=1,
                deals_with_predictions=0,
                avg_confidence=0.0,
            ),
        )
        async_mock = AsyncMock(return_value=mock_result)
        mock_service.predict_cashflow = async_mock
        mock_get_service.return_value = mock_service

        tool = GetCashflowProjection()
        result = tool.parse_and_execute({})

        assert result.success is True
        assert "warnings" in result.data
        assert "Deal 123: Low activity count" in result.data["warnings"]


class TestGetCEODashboard:
    """Tests for GetCEODashboard tool."""

    def test_tool_has_correct_name(self):
        """Tool has expected name."""
        tool = GetCEODashboard()
        assert tool.name == "get_ceo_dashboard"

    def test_tool_has_description(self):
        """Tool has non-empty description."""
        tool = GetCEODashboard()
        assert len(tool.description) > 20

    @patch("cmd_center.agent.tools.financial_tools.get_ceo_dashboard_service")
    def test_execute_returns_dashboard_metrics(self, mock_get_service):
        """Execute returns CEO dashboard metrics."""
        mock_service = MagicMock()

        # Create mock nested objects to match the actual CEODashboardMetrics structure
        mock_cash_health = MagicMock()
        mock_cash_health.runway_months = 3.5
        mock_cash_health.runway_status = "green"
        mock_cash_health.aramco_collected_week = 150000.0
        mock_cash_health.aramco_target_week = 200000.0
        mock_cash_health.commercial_collected_week = 0.0
        mock_cash_health.commercial_target_week = 100000.0
        mock_cash_health.total_collected_week = 150000.0
        mock_cash_health.total_target_week = 300000.0
        mock_cash_health.collection_pct = 50.0
        mock_cash_health.predicted_14d = 300000.0
        mock_cash_health.velocity_pct = 50.0
        mock_cash_health.velocity_status = "yellow"

        mock_urgent_deal = MagicMock()
        mock_urgent_deal.deal_id = 123
        mock_urgent_deal.title = "Test Deal"
        mock_urgent_deal.reason = "No update 10d"
        mock_urgent_deal.value_sar = 500000.0
        mock_urgent_deal.stage = "Under Progress"
        mock_urgent_deal.owner = "Alice"
        mock_urgent_deal.days_stuck = 10

        mock_pipeline_stage = MagicMock()
        mock_pipeline_stage.name = "Order Received"
        mock_pipeline_stage.stage_id = 27
        mock_pipeline_stage.avg_days = 5.0
        mock_pipeline_stage.deal_count = 3

        mock_pipeline_velocity = MagicMock()
        mock_pipeline_velocity.stages = [mock_pipeline_stage]
        mock_pipeline_velocity.current_cycle_days = 18.0
        mock_pipeline_velocity.target_cycle_days = 21.0
        mock_pipeline_velocity.trend = "better"
        mock_pipeline_velocity.trend_pct = -14.3

        mock_strategic_priority = MagicMock()
        mock_strategic_priority.name = "Cost Reduction"
        mock_strategic_priority.current = 15.0
        mock_strategic_priority.target = 20.0
        mock_strategic_priority.pct = 75.0
        mock_strategic_priority.status = "yellow"
        mock_strategic_priority.unit = "%"

        mock_sales_scorecard = MagicMock()
        mock_sales_scorecard.pipeline_value = 5000000.0
        mock_sales_scorecard.won_value = 1000000.0
        mock_sales_scorecard.active_deals_count = 25
        mock_sales_scorecard.overdue_count = 3
        mock_sales_scorecard.status = "yellow"

        mock_department_scorecard = MagicMock()
        mock_department_scorecard.sales = mock_sales_scorecard

        mock_metrics = MagicMock()
        mock_metrics.cash_health = mock_cash_health
        mock_metrics.urgent_deals = [mock_urgent_deal]
        mock_metrics.pipeline_velocity = mock_pipeline_velocity
        mock_metrics.strategic_priorities = [mock_strategic_priority]
        mock_metrics.department_scorecard = mock_department_scorecard
        mock_metrics.last_updated = "2026-01-04T12:00:00"
        mock_metrics.data_freshness = "live"

        # Make get_dashboard_metrics return an awaitable
        async_mock = AsyncMock(return_value=mock_metrics)
        mock_service.get_dashboard_metrics = async_mock
        mock_get_service.return_value = mock_service

        tool = GetCEODashboard()
        params = GetCEODashboardParams()
        result = tool.execute(params)

        assert result.success is True
        assert "metrics" in result.data
        metrics = result.data["metrics"]

        # Verify cash health is present
        assert "cash_health" in metrics
        assert metrics["cash_health"]["runway_months"] == 3.5

        # Verify urgent deals is present
        assert "urgent_deals" in metrics
        assert len(metrics["urgent_deals"]) == 1
        assert metrics["urgent_deals"][0]["deal_id"] == 123

        # Verify pipeline velocity is present
        assert "pipeline_velocity" in metrics
        assert metrics["pipeline_velocity"]["current_cycle_days"] == 18.0

        # Verify strategic priorities is present
        assert "strategic_priorities" in metrics
        assert len(metrics["strategic_priorities"]) == 1

        # Verify department scorecard is present
        assert "department_scorecard" in metrics

    @patch("cmd_center.agent.tools.financial_tools.get_ceo_dashboard_service")
    def test_execute_handles_error(self, mock_get_service):
        """Execute handles service errors gracefully."""
        mock_get_service.side_effect = Exception("Dashboard unavailable")

        tool = GetCEODashboard()
        params = GetCEODashboardParams()
        result = tool.execute(params)

        assert result.success is False
        assert "Dashboard unavailable" in result.error
