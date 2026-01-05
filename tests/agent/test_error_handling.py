"""Tests for enhanced error handling."""

import pytest

from cmd_center.agent.core.errors import (
    AgentError,
    ToolExecutionError,
    APIError,
    RateLimitError,
    ContextLimitError,
    format_error_response,
)


class TestAgentErrors:
    """Tests for agent error types."""

    def test_agent_error_base_class(self):
        """AgentError is base class for all agent errors."""
        error = AgentError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert isinstance(error, Exception)

    def test_tool_execution_error(self):
        """ToolExecutionError captures tool name."""
        error = ToolExecutionError("get_deals", "Database connection failed")
        assert "get_deals" in str(error)
        assert "Database connection failed" in str(error)
        assert error.tool_name == "get_deals"

    def test_api_error(self):
        """APIError captures status code."""
        error = APIError(503, "Service unavailable")
        assert error.status_code == 503
        assert "503" in str(error)
        assert "Service unavailable" in str(error)

    def test_rate_limit_error(self):
        """RateLimitError includes retry info."""
        error = RateLimitError(retry_after=30)
        assert error.retry_after == 30
        assert "30" in str(error) or "retry" in str(error).lower()

    def test_context_limit_error(self):
        """ContextLimitError includes token info."""
        error = ContextLimitError(current=150000, limit=128000)
        assert error.current == 150000
        assert error.limit == 128000


class TestErrorFormatting:
    """Tests for error response formatting."""

    def test_format_tool_error(self):
        """Tool errors format user-friendly."""
        error = ToolExecutionError("get_deals", "Connection timeout")
        response = format_error_response(error)
        assert "trouble" in response.lower() or "error" in response.lower()
        assert "get_deals" not in response

    def test_format_api_error(self):
        """API errors format user-friendly."""
        error = APIError(500, "Internal server error")
        response = format_error_response(error)
        assert "try again" in response.lower() or "moment" in response.lower()

    def test_format_rate_limit_error(self):
        """Rate limit errors suggest waiting."""
        error = RateLimitError(retry_after=60)
        response = format_error_response(error)
        assert "moment" in response.lower() or "wait" in response.lower()

    def test_format_context_limit_error(self):
        """Context limit errors suggest new conversation."""
        error = ContextLimitError(current=150000, limit=128000)
        response = format_error_response(error)
        assert "conversation" in response.lower() or "long" in response.lower()

    def test_format_generic_error(self):
        """Generic errors get friendly message."""
        error = Exception("Unknown error")
        response = format_error_response(error)
        assert "sorry" in response.lower() or "trouble" in response.lower()
