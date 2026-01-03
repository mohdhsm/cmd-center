"""Token and cost tracking for agent sessions."""

from typing import Optional


class MetricsTracker:
    """Track token usage and costs for agent sessions."""

    # Claude Sonnet 3.5 via OpenRouter pricing (per 1M tokens)
    PRICING = {
        "input": 3.00,   # $3 per 1M input tokens
        "output": 15.00,  # $15 per 1M output tokens
    }

    def __init__(self):
        """Initialize metrics tracker."""
        self.session_tokens: int = 0
        self.session_cost: float = 0.0
        self.request_count: int = 0
        self._input_tokens: int = 0
        self._output_tokens: int = 0

    def track(self, input_tokens: int, output_tokens: int) -> None:
        """Track token usage from a request.

        Args:
            input_tokens: Number of input/prompt tokens
            output_tokens: Number of output/completion tokens
        """
        self._input_tokens += input_tokens
        self._output_tokens += output_tokens
        self.session_tokens += input_tokens + output_tokens
        self.request_count += 1

        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * self.PRICING["input"]
        output_cost = (output_tokens / 1_000_000) * self.PRICING["output"]
        self.session_cost += input_cost + output_cost

    def reset(self) -> None:
        """Reset all counters."""
        self.session_tokens = 0
        self.session_cost = 0.0
        self.request_count = 0
        self._input_tokens = 0
        self._output_tokens = 0

    def format_display(self) -> str:
        """Format metrics for display in UI header.

        Returns:
            Formatted string like "Tokens: 12,450 | $0.23"
        """
        return f"Tokens: {self.session_tokens:,} | ${self.session_cost:.2f}"

    def get_stats(self) -> dict:
        """Get detailed statistics.

        Returns:
            Dict with all metrics
        """
        return {
            "session_tokens": self.session_tokens,
            "input_tokens": self._input_tokens,
            "output_tokens": self._output_tokens,
            "session_cost": self.session_cost,
            "request_count": self.request_count,
        }


# Singleton instance
_metrics_tracker: Optional[MetricsTracker] = None


def get_metrics_tracker() -> MetricsTracker:
    """Get or create metrics tracker singleton."""
    global _metrics_tracker
    if _metrics_tracker is None:
        _metrics_tracker = MetricsTracker()
    return _metrics_tracker
