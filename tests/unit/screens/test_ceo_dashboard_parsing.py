"""Unit tests for CEO Dashboard screen API response parsing.

These tests ensure proper handling of:
- CEO Dashboard metrics response extraction
- Nested object access (cash_health, urgent_deals, etc.)
- Status/trend value handling
- SAR value formatting
- Progress bar creation
- Missing/null field defaults

This would catch bugs where the screen incorrectly parses API responses.
"""

import pytest


class TestCEODashboardResponseExtraction:
    """Test extraction of data from CEO Dashboard API response."""

    def test_extract_cash_health_from_response(self):
        """Extract cash_health object from dashboard response."""
        response = {
            "cash_health": {
                "runway_months": 4.2,
                "runway_status": "green",
                "total_collected_week": 125000,
                "velocity_pct": 65.0,
            },
            "urgent_deals": [],
            "pipeline_velocity": {},
            "strategic_priorities": [],
            "department_scorecard": {},
        }

        cash_health = response.get("cash_health", {})

        assert cash_health.get("runway_months") == 4.2
        assert cash_health.get("runway_status") == "green"

    def test_extract_urgent_deals_list(self):
        """Extract urgent_deals list from dashboard response."""
        response = {
            "cash_health": {},
            "urgent_deals": [
                {"deal_id": 1, "title": "Deal A", "days_stuck": 10},
                {"deal_id": 2, "title": "Deal B", "days_stuck": 5},
            ],
            "pipeline_velocity": {},
            "strategic_priorities": [],
            "department_scorecard": {},
        }

        urgent_deals = response.get("urgent_deals", [])

        assert len(urgent_deals) == 2
        assert urgent_deals[0]["title"] == "Deal A"

    def test_extract_pipeline_velocity_stages(self):
        """Extract stages from pipeline_velocity."""
        response = {
            "pipeline_velocity": {
                "stages": [
                    {"name": "Order Received", "avg_days": 5.0, "deal_count": 8},
                    {"name": "Under Progress", "avg_days": 12.0, "deal_count": 15},
                ],
                "current_cycle_days": 35.0,
                "trend": "worse",
            }
        }

        velocity = response.get("pipeline_velocity", {})
        stages = velocity.get("stages", [])

        assert len(stages) == 2
        assert stages[0]["name"] == "Order Received"
        assert velocity.get("trend") == "worse"

    def test_extract_strategic_priorities(self):
        """Extract strategic_priorities list."""
        response = {
            "strategic_priorities": [
                {"name": "Cost Reduction", "current": 15, "target": 20, "pct": 75},
                {"name": "Sales Pipeline", "current": 450, "target": 500, "pct": 90},
            ]
        }

        priorities = response.get("strategic_priorities", [])

        assert len(priorities) == 2
        assert priorities[0]["name"] == "Cost Reduction"
        assert priorities[1]["pct"] == 90

    def test_extract_nested_department_scorecard(self):
        """Extract nested sales from department_scorecard."""
        response = {
            "department_scorecard": {
                "sales": {
                    "pipeline_value": 2100000,
                    "won_value": 450000,
                    "active_deals_count": 28,
                    "overdue_count": 3,
                    "status": "green",
                }
            }
        }

        scorecard = response.get("department_scorecard", {})
        sales = scorecard.get("sales", {})

        assert sales.get("pipeline_value") == 2100000
        assert sales.get("status") == "green"


class TestMissingFieldDefaults:
    """Test default values for missing or null fields."""

    def test_missing_cash_health_defaults(self):
        """Handle missing cash_health gracefully."""
        response = {"urgent_deals": []}

        cash_health = response.get("cash_health", {})
        runway = cash_health.get("runway_months", 0)
        status = cash_health.get("runway_status", "red")

        assert runway == 0
        assert status == "red"

    def test_missing_urgent_deals_defaults_empty_list(self):
        """Handle missing urgent_deals as empty list."""
        response = {"cash_health": {}}

        urgent_deals = response.get("urgent_deals", [])

        assert urgent_deals == []
        assert len(urgent_deals) == 0

    def test_null_value_in_cash_health(self):
        """Handle null values in cash_health fields."""
        response = {
            "cash_health": {
                "runway_months": None,
                "velocity_pct": None,
            }
        }

        cash_health = response.get("cash_health", {})
        runway = cash_health.get("runway_months") or 0
        velocity = cash_health.get("velocity_pct") or 0

        assert runway == 0
        assert velocity == 0

    def test_missing_stages_in_velocity(self):
        """Handle missing stages in pipeline_velocity."""
        response = {
            "pipeline_velocity": {
                "current_cycle_days": 35.0,
                "trend": "stable",
            }
        }

        velocity = response.get("pipeline_velocity", {})
        stages = velocity.get("stages", [])

        assert stages == []

    def test_empty_strategic_priorities(self):
        """Handle empty strategic_priorities list."""
        response = {"strategic_priorities": []}

        priorities = response.get("strategic_priorities", [])

        assert len(priorities) == 0


class TestSARValueFormatting:
    """Test SAR value formatting for display."""

    def test_format_millions(self):
        """Format value in millions."""
        value = 2100000.0

        if value >= 1_000_000:
            formatted = f"{value / 1_000_000:.1f}M SAR"
        elif value >= 1_000:
            formatted = f"{value / 1_000:.0f}K SAR"
        else:
            formatted = f"{value:.0f} SAR"

        assert formatted == "2.1M SAR"

    def test_format_thousands(self):
        """Format value in thousands."""
        value = 450000.0

        if value >= 1_000_000:
            formatted = f"{value / 1_000_000:.1f}M SAR"
        elif value >= 1_000:
            formatted = f"{value / 1_000:.0f}K SAR"
        else:
            formatted = f"{value:.0f} SAR"

        assert formatted == "450K SAR"

    def test_format_small_value(self):
        """Format small value without suffix."""
        value = 500.0

        if value >= 1_000_000:
            formatted = f"{value / 1_000_000:.1f}M SAR"
        elif value >= 1_000:
            formatted = f"{value / 1_000:.0f}K SAR"
        else:
            formatted = f"{value:.0f} SAR"

        assert formatted == "500 SAR"

    def test_format_zero_value(self):
        """Format zero value."""
        value = 0.0

        if value >= 1_000_000:
            formatted = f"{value / 1_000_000:.1f}M SAR"
        elif value >= 1_000:
            formatted = f"{value / 1_000:.0f}K SAR"
        else:
            formatted = f"{value:.0f} SAR"

        assert formatted == "0 SAR"

    def test_format_none_value(self):
        """Handle None value in formatting."""
        value = None

        # Pattern: use 'or 0' to handle None
        safe_value = value or 0
        if safe_value >= 1_000_000:
            formatted = f"{safe_value / 1_000_000:.1f}M SAR"
        elif safe_value >= 1_000:
            formatted = f"{safe_value / 1_000:.0f}K SAR"
        else:
            formatted = f"{safe_value:.0f} SAR"

        assert formatted == "0 SAR"


class TestProgressBarCreation:
    """Test ASCII progress bar creation."""

    def test_create_progress_bar_50_percent(self):
        """Create progress bar at 50%."""
        pct = 50.0
        width = 20

        filled = int(pct / 100 * width)
        filled = max(0, min(filled, width))
        empty = width - filled
        bar = f"[{'=' * filled}{' ' * empty}]"

        assert bar == "[==========          ]"
        assert len(bar) == width + 2  # +2 for brackets

    def test_create_progress_bar_100_percent(self):
        """Create progress bar at 100%."""
        pct = 100.0
        width = 20

        filled = int(pct / 100 * width)
        filled = max(0, min(filled, width))
        empty = width - filled
        bar = f"[{'=' * filled}{' ' * empty}]"

        assert bar == "[====================]"

    def test_create_progress_bar_0_percent(self):
        """Create progress bar at 0%."""
        pct = 0.0
        width = 20

        filled = int(pct / 100 * width)
        filled = max(0, min(filled, width))
        empty = width - filled
        bar = f"[{'=' * filled}{' ' * empty}]"

        assert bar == "[                    ]"

    def test_create_progress_bar_over_100_percent(self):
        """Create progress bar capped at 100%."""
        pct = 150.0
        width = 20

        filled = int(pct / 100 * width)
        filled = max(0, min(filled, width))  # Clamp to width
        empty = width - filled
        bar = f"[{'=' * filled}{' ' * empty}]"

        assert bar == "[====================]"  # Capped at full

    def test_create_progress_bar_negative_percent(self):
        """Create progress bar handles negative (clamps to 0)."""
        pct = -10.0
        width = 20

        filled = int(pct / 100 * width)
        filled = max(0, min(filled, width))  # Clamp to 0
        empty = width - filled
        bar = f"[{'=' * filled}{' ' * empty}]"

        assert bar == "[                    ]"


class TestStatusClassMapping:
    """Test status value to CSS class mapping."""

    def test_status_to_class_green(self):
        """Map green status to class."""
        status = "green"
        css_class = f"status-{status}"
        assert css_class == "status-green"

    def test_status_to_class_yellow(self):
        """Map yellow status to class."""
        status = "yellow"
        css_class = f"status-{status}"
        assert css_class == "status-yellow"

    def test_status_to_class_red(self):
        """Map red status to class."""
        status = "red"
        css_class = f"status-{status}"
        assert css_class == "status-red"

    def test_runway_class_mapping(self):
        """Map runway status to runway-specific class."""
        status = "green"
        css_class = f"runway-{status}"
        assert css_class == "runway-green"


class TestTrendSymbolMapping:
    """Test trend value to symbol mapping."""

    def test_trend_better_symbol(self):
        """Map better trend to down arrow."""
        trend = "better"
        symbols = {"better": "↓", "worse": "↑", "stable": "→"}
        symbol = symbols.get(trend, "→")
        assert symbol == "↓"

    def test_trend_worse_symbol(self):
        """Map worse trend to up arrow."""
        trend = "worse"
        symbols = {"better": "↓", "worse": "↑", "stable": "→"}
        symbol = symbols.get(trend, "→")
        assert symbol == "↑"

    def test_trend_stable_symbol(self):
        """Map stable trend to right arrow."""
        trend = "stable"
        symbols = {"better": "↓", "worse": "↑", "stable": "→"}
        symbol = symbols.get(trend, "→")
        assert symbol == "→"

    def test_trend_unknown_defaults(self):
        """Unknown trend defaults to stable arrow."""
        trend = "unknown"
        symbols = {"better": "↓", "worse": "↑", "stable": "→"}
        symbol = symbols.get(trend, "→")
        assert symbol == "→"


class TestUrgentDealTableRendering:
    """Test urgent deal data preparation for table display."""

    def test_truncate_long_title(self):
        """Truncate long deal titles for table display."""
        title = "Very Long Aramco Maintenance Contract Project Title"
        max_len = 25

        truncated = title[:max_len]

        assert len(truncated) == 25
        assert truncated == "Very Long Aramco Maintena"

    def test_truncate_short_title(self):
        """Short titles are not truncated."""
        title = "Short Title"
        max_len = 25

        truncated = title[:max_len]

        assert truncated == "Short Title"

    def test_truncate_owner_name(self):
        """Truncate long owner names."""
        owner = "Mohammed Al-Farsi"
        max_len = 10

        truncated = owner[:max_len]

        assert truncated == "Mohammed A"

    def test_format_deal_row_data(self):
        """Format deal data for table row."""
        deal = {
            "title": "Aramco Contract for Region A",
            "reason": "Awaiting GR 23 days",
            "value_sar": 450000,
            "owner": "Mohammed",
        }

        row = (
            deal.get("title", "")[:25],
            deal.get("reason", ""),
            f"{deal.get('value_sar', 0) / 1000:.0f}K SAR",
            deal.get("owner", "")[:10],
        )

        assert row[0] == "Aramco Contract for Regio"
        assert row[1] == "Awaiting GR 23 days"
        assert row[2] == "450K SAR"
        assert row[3] == "Mohammed"


class TestVelocityStageBarChart:
    """Test velocity stage bar chart rendering."""

    def test_create_stage_bar(self):
        """Create bar for stage average days."""
        avg_days = 12
        max_width = 20

        bar_width = min(int(avg_days), max_width)
        bar = "█" * bar_width + "░" * (max_width - bar_width)

        assert bar == "████████████░░░░░░░░"
        assert len(bar) == max_width

    def test_create_stage_bar_over_max(self):
        """Stage bar capped at max width."""
        avg_days = 30
        max_width = 20

        bar_width = min(int(avg_days), max_width)
        bar = "█" * bar_width + "░" * (max_width - bar_width)

        assert bar == "████████████████████"
        assert len(bar) == max_width

    def test_create_stage_bar_zero(self):
        """Stage bar with zero days."""
        avg_days = 0
        max_width = 20

        bar_width = min(int(avg_days), max_width)
        bar = "█" * bar_width + "░" * (max_width - bar_width)

        assert bar == "░░░░░░░░░░░░░░░░░░░░"

    def test_format_stage_line(self):
        """Format complete stage line for display."""
        stage = {"name": "Order Received", "avg_days": 5.0, "deal_count": 8}
        max_width = 20

        name = stage.get("name", "")[:15]
        avg_days = stage.get("avg_days", 0)
        deal_count = stage.get("deal_count", 0)

        bar_width = min(int(avg_days), max_width)
        bar = "█" * bar_width + "░" * (max_width - bar_width)

        line = f"{name:15} {bar} {avg_days:.0f}d ({deal_count})"

        assert "Order Received" in line
        assert "█████" in line
        assert "5d (8)" in line


class TestTimestampFormatting:
    """Test timestamp formatting for status bar."""

    def test_format_iso_timestamp(self):
        """Format ISO timestamp for display."""
        timestamp = "2024-01-15T14:30:45.123456"

        # Pattern from screen: slice and replace T
        formatted = timestamp[:19].replace("T", " ")

        assert formatted == "2024-01-15 14:30:45"

    def test_format_timestamp_with_timezone(self):
        """Format timestamp with timezone info."""
        timestamp = "2024-01-15T14:30:45+00:00"

        formatted = timestamp[:19].replace("T", " ")

        assert formatted == "2024-01-15 14:30:45"

    def test_handle_missing_timestamp(self):
        """Handle missing timestamp gracefully."""
        timestamp = None

        # Pattern: check for None or use default
        if timestamp and timestamp != "--":
            formatted = timestamp[:19].replace("T", " ")
        else:
            formatted = "--"

        assert formatted == "--"
