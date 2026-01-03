"""Tests for MetricsTracker."""

import pytest

# Import directly from the metrics module to avoid parent __init__.py import chain
from cmd_center.agent.observability.metrics import MetricsTracker


class TestMetricsTracker:
    """Test MetricsTracker token and cost tracking."""

    def test_initial_state(self):
        """Tracker starts with zero values."""
        tracker = MetricsTracker()
        assert tracker.session_tokens == 0
        assert tracker.session_cost == 0.0
        assert tracker.request_count == 0

    def test_track_usage(self):
        """Track updates counters correctly."""
        tracker = MetricsTracker()
        tracker.track(input_tokens=100, output_tokens=50)

        assert tracker.session_tokens == 150
        assert tracker.request_count == 1
        assert tracker.session_cost > 0

    def test_track_multiple_requests(self):
        """Multiple tracks accumulate correctly."""
        tracker = MetricsTracker()
        tracker.track(input_tokens=100, output_tokens=50)
        tracker.track(input_tokens=200, output_tokens=100)

        assert tracker.session_tokens == 450
        assert tracker.request_count == 2

    def test_reset(self):
        """Reset clears all counters."""
        tracker = MetricsTracker()
        tracker.track(input_tokens=100, output_tokens=50)
        tracker.reset()

        assert tracker.session_tokens == 0
        assert tracker.session_cost == 0.0
        assert tracker.request_count == 0

    def test_cost_calculation(self):
        """Cost is calculated based on Claude Sonnet pricing."""
        tracker = MetricsTracker()
        # 1M input tokens = $3, 1M output tokens = $15
        tracker.track(input_tokens=1_000_000, output_tokens=1_000_000)

        # $3 + $15 = $18
        assert tracker.session_cost == pytest.approx(18.0, rel=0.01)

    def test_format_display(self):
        """Format display returns user-friendly string."""
        tracker = MetricsTracker()
        tracker.track(input_tokens=5000, output_tokens=1000)

        display = tracker.format_display()
        assert "6,000" in display or "6000" in display  # Total tokens
        assert "$" in display  # Cost indicator
