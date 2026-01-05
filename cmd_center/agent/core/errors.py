"""Error types and handling for the agent."""

from typing import Optional


class AgentError(Exception):
    """Base exception for all agent errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ToolExecutionError(AgentError):
    """Error during tool execution."""

    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' failed: {message}")


class APIError(AgentError):
    """Error from LLM API call."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"API error {status_code}: {message}")


class RateLimitError(AgentError):
    """Rate limit exceeded error."""

    def __init__(self, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        message = "Rate limit exceeded"
        if retry_after:
            message += f", retry after {retry_after} seconds"
        super().__init__(message)


class ContextLimitError(AgentError):
    """Context window limit exceeded."""

    def __init__(self, current: int, limit: int):
        self.current = current
        self.limit = limit
        super().__init__(
            f"Context limit exceeded: {current:,} tokens (limit: {limit:,})"
        )


def format_error_response(error: Exception) -> str:
    """Format an error into a user-friendly response."""
    if isinstance(error, ToolExecutionError):
        return (
            "I'm having a bit of trouble retrieving that information right now. "
            "Let me try a different approach, or you can ask me again in a moment."
        )

    if isinstance(error, RateLimitError):
        return (
            "I need to take a brief pause - I've been quite busy! "
            "Please wait a moment and try again."
        )

    if isinstance(error, APIError):
        if error.status_code >= 500:
            return (
                "I'm experiencing some technical difficulties at the moment. "
                "Please try again in a few moments."
            )
        return (
            "I encountered an issue processing your request. "
            "Could you try rephrasing or ask something else?"
        )

    if isinstance(error, ContextLimitError):
        return (
            "Our conversation has gotten quite long! "
            "To keep things running smoothly, you might want to start a new conversation. "
            "I'll still have access to all the same tools and knowledge."
        )

    return (
        "I'm sorry, I ran into an unexpected issue. "
        "Let me know if you'd like to try again or ask something different."
    )
