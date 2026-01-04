"""Tests for financial tools."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from cmd_center.agent.tools.financial_tools import (
    GetCashflowProjection,
    GetCashflowProjectionParams,
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
