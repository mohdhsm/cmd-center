"""Tests for context manager and token limits."""

import pytest

from cmd_center.agent.core.context import ContextManager


class TestContextManager:
    """Tests for ContextManager."""

    @pytest.fixture
    def context(self):
        """Create context manager instance."""
        return ContextManager(max_tokens=8000, warning_threshold=0.8)

    def test_default_limits(self):
        """Default token limits are set."""
        context = ContextManager()
        assert context.max_tokens == 128000
        assert context.warning_threshold == 0.8

    def test_custom_limits(self):
        """Custom token limits can be set."""
        context = ContextManager(max_tokens=4000, warning_threshold=0.9)
        assert context.max_tokens == 4000
        assert context.warning_threshold == 0.9

    def test_estimate_tokens(self, context):
        """Token estimation returns reasonable count."""
        text = "Hello, this is a test message."
        tokens = context.estimate_tokens(text)
        assert 5 <= tokens <= 15

    def test_add_message_tracks_tokens(self, context):
        """Adding message tracks token count."""
        context.add_message("user", "Hello")
        context.add_message("assistant", "Hi there, how can I help?")
        assert context.total_tokens > 0

    def test_is_near_limit_false_initially(self, context):
        """is_near_limit returns False when under threshold."""
        context.add_message("user", "Hello")
        assert context.is_near_limit() is False

    def test_is_near_limit_true_when_approaching(self, context):
        """is_near_limit returns True when near threshold."""
        # 6000 repetitions * 5 chars = 30000 chars * 0.25 = 7500 tokens
        # This exceeds 80% of 8000 = 6400 tokens threshold
        long_text = "word " * 6000
        context.add_message("user", long_text)
        assert context.is_near_limit() is True

    def test_get_warning_message(self, context):
        """get_warning returns appropriate message."""
        context.add_message("user", "Hello")
        assert context.get_warning() is None

        # Use enough text to exceed threshold (same as above test)
        long_text = "word " * 6000
        context.add_message("user", long_text)
        warning = context.get_warning()
        assert warning is not None
        assert "context" in warning.lower() or "token" in warning.lower()

    def test_clear_resets_tokens(self, context):
        """Clear resets token count."""
        context.add_message("user", "Hello")
        context.clear()
        assert context.total_tokens == 0

    def test_get_token_usage_summary(self, context):
        """get_usage_summary returns formatted string."""
        context.add_message("user", "Hello")
        summary = context.get_usage_summary()
        assert "token" in summary.lower() or "/" in summary
