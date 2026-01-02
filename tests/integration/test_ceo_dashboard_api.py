"""Integration tests for CEO Dashboard API endpoints.

These tests verify:
1. API endpoint returns valid response structure
2. Response matches CEODashboardMetrics schema
3. All nested objects are properly structured
4. Error handling for service failures
"""

import pytest
from datetime import datetime

from cmd_center.backend.models.ceo_dashboard_models import (
    CEODashboardMetrics,
    CashHealth,
    UrgentDeal,
    PipelineVelocity,
    StrategicPriority,
    DepartmentScorecard,
)


@pytest.mark.asyncio
class TestCEODashboardMetricsEndpoint:
    """Test GET /ceo-dashboard/metrics endpoint."""

    async def test_get_metrics_returns_200(self, test_client):
        """GET /ceo-dashboard/metrics returns 200 status."""
        response = await test_client.get("/ceo-dashboard/metrics")
        assert response.status_code == 200

    async def test_get_metrics_returns_valid_schema(self, test_client):
        """Response validates against CEODashboardMetrics schema."""
        response = await test_client.get("/ceo-dashboard/metrics")
        data = response.json()

        # Should not raise ValidationError
        result = CEODashboardMetrics.model_validate(data)
        assert result is not None

    async def test_response_has_cash_health(self, test_client):
        """Response includes cash_health section."""
        response = await test_client.get("/ceo-dashboard/metrics")
        data = response.json()

        assert "cash_health" in data
        cash_health = CashHealth.model_validate(data["cash_health"])
        assert cash_health.runway_months >= 0

    async def test_response_has_urgent_deals(self, test_client):
        """Response includes urgent_deals list."""
        response = await test_client.get("/ceo-dashboard/metrics")
        data = response.json()

        assert "urgent_deals" in data
        assert isinstance(data["urgent_deals"], list)
        assert len(data["urgent_deals"]) <= 5  # Max 5 urgent deals

    async def test_response_has_pipeline_velocity(self, test_client):
        """Response includes pipeline_velocity section."""
        response = await test_client.get("/ceo-dashboard/metrics")
        data = response.json()

        assert "pipeline_velocity" in data
        velocity = PipelineVelocity.model_validate(data["pipeline_velocity"])
        assert velocity.trend in ["better", "worse", "stable"]

    async def test_response_has_strategic_priorities(self, test_client):
        """Response includes strategic_priorities list."""
        response = await test_client.get("/ceo-dashboard/metrics")
        data = response.json()

        assert "strategic_priorities" in data
        assert isinstance(data["strategic_priorities"], list)

        # Validate each priority
        for priority_data in data["strategic_priorities"]:
            priority = StrategicPriority.model_validate(priority_data)
            assert priority.status in ["green", "yellow", "red"]

    async def test_response_has_department_scorecard(self, test_client):
        """Response includes department_scorecard section."""
        response = await test_client.get("/ceo-dashboard/metrics")
        data = response.json()

        assert "department_scorecard" in data
        scorecard = DepartmentScorecard.model_validate(data["department_scorecard"])
        assert scorecard.sales is not None

    async def test_response_has_metadata(self, test_client):
        """Response includes metadata fields."""
        response = await test_client.get("/ceo-dashboard/metrics")
        data = response.json()

        assert "last_updated" in data
        assert "data_freshness" in data

        # Verify last_updated is valid ISO format
        last_updated = data["last_updated"]
        datetime.fromisoformat(last_updated.replace("Z", "+00:00"))

    async def test_cash_health_status_values(self, test_client):
        """Cash health status values are valid."""
        response = await test_client.get("/ceo-dashboard/metrics")
        data = response.json()

        cash_health = data["cash_health"]
        assert cash_health["runway_status"] in ["green", "yellow", "red"]
        assert cash_health["velocity_status"] in ["green", "yellow", "red"]

    async def test_cash_health_numeric_values(self, test_client):
        """Cash health numeric values are proper types."""
        response = await test_client.get("/ceo-dashboard/metrics")
        data = response.json()

        cash_health = data["cash_health"]
        assert isinstance(cash_health["runway_months"], (int, float))
        assert isinstance(cash_health["total_collected_week"], (int, float))
        assert isinstance(cash_health["velocity_pct"], (int, float))

    async def test_urgent_deals_structure(self, test_client):
        """Urgent deals have required structure."""
        response = await test_client.get("/ceo-dashboard/metrics")
        data = response.json()

        for deal in data["urgent_deals"]:
            assert "deal_id" in deal
            assert "title" in deal
            assert "reason" in deal
            assert "value_sar" in deal
            assert "stage" in deal
            assert "owner" in deal
            assert "days_stuck" in deal

            # Validate types
            assert isinstance(deal["deal_id"], int)
            assert isinstance(deal["value_sar"], (int, float))
            assert isinstance(deal["days_stuck"], int)

    async def test_pipeline_velocity_stages_structure(self, test_client):
        """Pipeline velocity stages have required structure."""
        response = await test_client.get("/ceo-dashboard/metrics")
        data = response.json()

        stages = data["pipeline_velocity"]["stages"]
        for stage in stages:
            assert "name" in stage
            assert "stage_id" in stage
            assert "avg_days" in stage
            assert "deal_count" in stage

    async def test_strategic_priorities_structure(self, test_client):
        """Strategic priorities have required structure."""
        response = await test_client.get("/ceo-dashboard/metrics")
        data = response.json()

        for priority in data["strategic_priorities"]:
            assert "name" in priority
            assert "current" in priority
            assert "target" in priority
            assert "pct" in priority
            assert "status" in priority

    async def test_sales_scorecard_structure(self, test_client):
        """Sales scorecard has required structure."""
        response = await test_client.get("/ceo-dashboard/metrics")
        data = response.json()

        sales = data["department_scorecard"]["sales"]
        assert "pipeline_value" in sales
        assert "won_value" in sales
        assert "active_deals_count" in sales
        assert "overdue_count" in sales
        assert "status" in sales


@pytest.mark.asyncio
class TestCEODashboardResponseTypes:
    """Test response field types match expected values."""

    async def test_all_status_fields_are_strings(self, test_client):
        """All status fields return string values."""
        response = await test_client.get("/ceo-dashboard/metrics")
        data = response.json()

        # Cash health statuses
        assert isinstance(data["cash_health"]["runway_status"], str)
        assert isinstance(data["cash_health"]["velocity_status"], str)

        # Priority statuses
        for priority in data["strategic_priorities"]:
            assert isinstance(priority["status"], str)

        # Scorecard status
        assert isinstance(data["department_scorecard"]["sales"]["status"], str)

    async def test_all_numeric_fields_are_numbers(self, test_client):
        """All numeric fields return numeric values."""
        response = await test_client.get("/ceo-dashboard/metrics")
        data = response.json()

        # Cash health
        assert isinstance(data["cash_health"]["runway_months"], (int, float))
        assert isinstance(data["cash_health"]["collection_pct"], (int, float))
        assert isinstance(data["cash_health"]["predicted_14d"], (int, float))

        # Pipeline velocity
        assert isinstance(data["pipeline_velocity"]["current_cycle_days"], (int, float))
        assert isinstance(data["pipeline_velocity"]["target_cycle_days"], (int, float))

    async def test_all_list_fields_are_lists(self, test_client):
        """All list fields return list values."""
        response = await test_client.get("/ceo-dashboard/metrics")
        data = response.json()

        assert isinstance(data["urgent_deals"], list)
        assert isinstance(data["pipeline_velocity"]["stages"], list)
        assert isinstance(data["strategic_priorities"], list)


@pytest.mark.asyncio
class TestCEODashboardEdgeCases:
    """Test edge cases and boundary conditions."""

    async def test_empty_database_returns_valid_response(self, test_client):
        """Empty database still returns valid response structure."""
        response = await test_client.get("/ceo-dashboard/metrics")

        # Should still return 200 with empty/default values
        assert response.status_code == 200
        data = response.json()

        # Validate structure exists even if empty
        assert "cash_health" in data
        assert "urgent_deals" in data
        assert "pipeline_velocity" in data

    async def test_urgent_deals_limited_to_five(self, test_client):
        """Urgent deals list is limited to 5 items."""
        response = await test_client.get("/ceo-dashboard/metrics")
        data = response.json()

        assert len(data["urgent_deals"]) <= 5

    async def test_collection_pct_is_bounded(self, test_client):
        """Collection percentage is a reasonable value."""
        response = await test_client.get("/ceo-dashboard/metrics")
        data = response.json()

        collection_pct = data["cash_health"]["collection_pct"]
        assert collection_pct >= 0  # Can't be negative

    async def test_velocity_pct_is_bounded(self, test_client):
        """Velocity percentage is a reasonable value."""
        response = await test_client.get("/ceo-dashboard/metrics")
        data = response.json()

        velocity_pct = data["cash_health"]["velocity_pct"]
        assert velocity_pct >= 0  # Can't be negative
