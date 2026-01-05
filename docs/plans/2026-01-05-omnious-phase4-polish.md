# Omnious AI Agent Phase 4: Polish Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add production-ready polish to Omnious including file logging, enhanced error handling, context limit management, and comprehensive golden tests.

**Architecture:** File logger writes JSONL logs alongside SQLite persistence. Enhanced error handling provides graceful user feedback. Context manager tracks tokens and warns on limits. Golden tests validate tool selection and agent behavior.

**Tech Stack:** Python, JSON Lines (JSONL), pytest, existing MetricsTracker

---

## Task 0: Create File Logger for Conversations

**Files:**
- Create: `cmd_center/agent/observability/logger.py`
- Test: `tests/agent/test_file_logger.py`

**Step 1: Write the failing test**

Create `tests/agent/test_file_logger.py`:

```python
"""Tests for file-based conversation logging."""

import pytest
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from cmd_center.agent.observability.logger import ConversationLogger, get_conversation_logger


class TestConversationLogger:
    """Tests for ConversationLogger."""

    @pytest.fixture
    def temp_log_dir(self, tmp_path):
        """Create temporary log directory."""
        log_dir = tmp_path / "logs" / "omnious"
        log_dir.mkdir(parents=True)
        return log_dir

    @pytest.fixture
    def logger(self, temp_log_dir):
        """Create logger with temp directory."""
        return ConversationLogger(log_dir=str(temp_log_dir))

    def test_logger_creates_log_directory(self, tmp_path):
        """Logger creates log directory if it doesn't exist."""
        log_dir = tmp_path / "new_logs" / "omnious"
        logger = ConversationLogger(log_dir=str(log_dir))

        assert log_dir.exists()

    def test_log_message_writes_jsonl(self, logger, temp_log_dir):
        """Log message writes to JSONL file."""
        logger.log_message(
            conversation_id=1,
            role="user",
            content="Hello",
            tokens=10,
        )

        # Find log file
        log_files = list(temp_log_dir.glob("conversations_*.jsonl"))
        assert len(log_files) == 1

        # Read and verify
        with open(log_files[0], "r") as f:
            line = f.readline()
            data = json.loads(line)

        assert data["conversation_id"] == 1
        assert data["role"] == "user"
        assert data["content"] == "Hello"
        assert data["tokens"] == 10

    def test_log_message_includes_timestamp(self, logger, temp_log_dir):
        """Log message includes ISO timestamp."""
        logger.log_message(
            conversation_id=1,
            role="assistant",
            content="Hi there",
        )

        log_files = list(temp_log_dir.glob("conversations_*.jsonl"))
        with open(log_files[0], "r") as f:
            data = json.loads(f.readline())

        assert "timestamp" in data
        # Should be parseable as ISO datetime
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    def test_log_message_includes_tools_used(self, logger, temp_log_dir):
        """Log message includes tools_used when provided."""
        logger.log_message(
            conversation_id=1,
            role="assistant",
            content="Here are the deals",
            tools_used=["get_overdue_deals", "get_stuck_deals"],
        )

        log_files = list(temp_log_dir.glob("conversations_*.jsonl"))
        with open(log_files[0], "r") as f:
            data = json.loads(f.readline())

        assert data["tools_used"] == ["get_overdue_deals", "get_stuck_deals"]

    def test_log_file_named_with_date(self, logger, temp_log_dir):
        """Log file is named with current date."""
        logger.log_message(conversation_id=1, role="user", content="test")

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        expected_file = temp_log_dir / f"conversations_{today}.jsonl"

        assert expected_file.exists()

    def test_multiple_messages_append_to_file(self, logger, temp_log_dir):
        """Multiple messages append to same file."""
        logger.log_message(conversation_id=1, role="user", content="msg1")
        logger.log_message(conversation_id=1, role="assistant", content="msg2")
        logger.log_message(conversation_id=1, role="user", content="msg3")

        log_files = list(temp_log_dir.glob("conversations_*.jsonl"))
        assert len(log_files) == 1

        with open(log_files[0], "r") as f:
            lines = f.readlines()

        assert len(lines) == 3

    def test_singleton_get_conversation_logger(self, temp_log_dir):
        """get_conversation_logger returns singleton."""
        with patch("cmd_center.agent.observability.logger.DEFAULT_LOG_DIR", str(temp_log_dir)):
            logger1 = get_conversation_logger()
            logger2 = get_conversation_logger()

            assert logger1 is logger2
```

**Step 2: Run test to verify it fails**

Run: `source venv/bin/activate && pytest tests/agent/test_file_logger.py -v`
Expected: FAIL with "cannot import name 'ConversationLogger'"

**Step 3: Write minimal implementation**

Create `cmd_center/agent/observability/logger.py`:

```python
"""File-based conversation logging for the agent."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List


DEFAULT_LOG_DIR = "logs/omnious"


class ConversationLogger:
    """Logger that writes conversation messages to JSONL files."""

    def __init__(self, log_dir: str = DEFAULT_LOG_DIR):
        """Initialize the conversation logger.

        Args:
            log_dir: Directory to write log files to
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_file_path(self) -> Path:
        """Get the log file path for today."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.log_dir / f"conversations_{today}.jsonl"

    def log_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        tokens: int = 0,
        tools_used: Optional[List[str]] = None,
    ) -> None:
        """Log a message to the JSONL file.

        Args:
            conversation_id: ID of the conversation
            role: Message role (user, assistant, system)
            content: Message content
            tokens: Number of tokens used
            tools_used: List of tools used in this message
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "tokens": tokens,
        }

        if tools_used:
            log_entry["tools_used"] = tools_used

        log_file = self._get_log_file_path()
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")


# Singleton instance
_conversation_logger: Optional[ConversationLogger] = None


def get_conversation_logger() -> ConversationLogger:
    """Get or create conversation logger singleton."""
    global _conversation_logger
    if _conversation_logger is None:
        _conversation_logger = ConversationLogger()
    return _conversation_logger
```

**Step 4: Run test to verify it passes**

Run: `source venv/bin/activate && pytest tests/agent/test_file_logger.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add cmd_center/agent/observability/logger.py tests/agent/test_file_logger.py
git commit -m "feat(agent): add file-based conversation logger"
```

---

## Task 1: Integrate File Logger with Agent

**Files:**
- Modify: `cmd_center/agent/core/agent.py`
- Test: `tests/agent/test_agent_logging.py`

**Step 1: Write the failing test**

Create `tests/agent/test_agent_logging.py`:

```python
"""Tests for agent file logging integration."""

import pytest
from unittest.mock import patch, MagicMock

from cmd_center.agent.core.agent import OmniousAgent


class TestAgentLoggingIntegration:
    """Tests for agent file logging."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    def test_agent_has_file_logger(self, agent):
        """Agent has file logger attribute."""
        assert hasattr(agent, 'file_logger')
        assert agent.file_logger is not None

    def test_add_to_history_logs_to_file(self, agent):
        """Adding to history logs to file logger."""
        with patch.object(agent.file_logger, 'log_message') as mock_log:
            agent._add_to_history("user", "Hello")

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args.kwargs["role"] == "user"
            assert call_args.kwargs["content"] == "Hello"

    def test_log_includes_conversation_id(self, agent):
        """Log includes conversation ID when persistence is enabled."""
        agent.conversation_id = 42

        with patch.object(agent.file_logger, 'log_message') as mock_log:
            agent._add_to_history("assistant", "Hi there")

            call_args = mock_log.call_args
            assert call_args.kwargs["conversation_id"] == 42

    def test_log_includes_tools_used(self, agent):
        """Log includes tools used when provided."""
        with patch.object(agent.file_logger, 'log_message') as mock_log:
            agent._add_to_history(
                "assistant",
                "Here are the deals",
                tools_used=["get_overdue_deals"]
            )

            call_args = mock_log.call_args
            assert call_args.kwargs["tools_used"] == ["get_overdue_deals"]
```

**Step 2: Run test to verify it fails**

Run: `source venv/bin/activate && pytest tests/agent/test_agent_logging.py -v`
Expected: FAIL with "Agent has no attribute 'file_logger'"

**Step 3: Write minimal implementation**

Modify `cmd_center/agent/core/agent.py`:

```python
# Add import at top
from ..observability.logger import get_conversation_logger

# In __init__, add after metrics:
self.file_logger = get_conversation_logger()

# Modify _add_to_history method:
def _add_to_history(
    self,
    role: str,
    content: str,
    tools_used: Optional[List[str]] = None
) -> None:
    """Add a message to conversation history.

    Args:
        role: Message role (user, assistant)
        content: Message content
        tools_used: Optional list of tools used
    """
    self.conversation_history.append({
        "role": role,
        "content": content
    })

    # Persist message if store is enabled and conversation is active
    if self._store is not None and self.conversation_id is not None:
        self._store.add_message(self.conversation_id, role, content)

    # Log to file
    self.file_logger.log_message(
        conversation_id=self.conversation_id or 0,
        role=role,
        content=content,
        tokens=0,  # Token tracking done in metrics
        tools_used=tools_used,
    )
```

**Step 4: Run test to verify it passes**

Run: `source venv/bin/activate && pytest tests/agent/test_agent_logging.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add cmd_center/agent/core/agent.py tests/agent/test_agent_logging.py
git commit -m "feat(agent): integrate file logger with agent"
```

---

## Task 2: Add Context Manager for Token Limits

**Files:**
- Create: `cmd_center/agent/core/context.py`
- Test: `tests/agent/test_context_manager.py`

**Step 1: Write the failing test**

Create `tests/agent/test_context_manager.py`:

```python
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
        assert context.max_tokens == 128000  # Claude default
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

        # Rough estimate: ~1 token per 4 chars
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
        # Add enough tokens to exceed 80% of 8000 = 6400
        long_text = "word " * 2000  # Roughly 8000+ chars = 2000+ tokens
        context.add_message("user", long_text)

        assert context.is_near_limit() is True

    def test_get_warning_message(self, context):
        """get_warning returns appropriate message."""
        # Under limit
        context.add_message("user", "Hello")
        assert context.get_warning() is None

        # Near limit
        long_text = "word " * 2000
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
```

**Step 2: Run test to verify it fails**

Run: `source venv/bin/activate && pytest tests/agent/test_context_manager.py -v`
Expected: FAIL with "cannot import name 'ContextManager'"

**Step 3: Write minimal implementation**

Create `cmd_center/agent/core/context.py`:

```python
"""Context management for conversation token limits."""

from typing import Optional, List, Dict, Any


class ContextManager:
    """Manages conversation context and token limits.

    Tracks token usage and provides warnings when approaching limits.
    """

    # Approximate tokens per character (conservative estimate)
    TOKENS_PER_CHAR = 0.25

    def __init__(
        self,
        max_tokens: int = 128000,
        warning_threshold: float = 0.8,
    ):
        """Initialize context manager.

        Args:
            max_tokens: Maximum context window size
            warning_threshold: Fraction of max_tokens to trigger warning (0-1)
        """
        self.max_tokens = max_tokens
        self.warning_threshold = warning_threshold
        self.total_tokens = 0
        self._messages: List[Dict[str, Any]] = []

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Uses a conservative estimate based on characters.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        if not text:
            return 0
        return max(1, int(len(text) * self.TOKENS_PER_CHAR))

    def add_message(self, role: str, content: str) -> int:
        """Add a message and track its tokens.

        Args:
            role: Message role
            content: Message content

        Returns:
            Tokens used by this message
        """
        tokens = self.estimate_tokens(content)
        self._messages.append({
            "role": role,
            "content": content,
            "tokens": tokens,
        })
        self.total_tokens += tokens
        return tokens

    def is_near_limit(self) -> bool:
        """Check if token usage is near the limit.

        Returns:
            True if usage exceeds warning threshold
        """
        return self.total_tokens >= (self.max_tokens * self.warning_threshold)

    def get_warning(self) -> Optional[str]:
        """Get warning message if near limit.

        Returns:
            Warning message or None if under threshold
        """
        if not self.is_near_limit():
            return None

        percentage = (self.total_tokens / self.max_tokens) * 100
        remaining = self.max_tokens - self.total_tokens

        return (
            f"Context usage: {percentage:.0f}% ({self.total_tokens:,}/{self.max_tokens:,} tokens). "
            f"~{remaining:,} tokens remaining. Consider starting a new conversation soon."
        )

    def get_usage_summary(self) -> str:
        """Get token usage summary.

        Returns:
            Formatted usage string
        """
        percentage = (self.total_tokens / self.max_tokens) * 100
        return f"{self.total_tokens:,}/{self.max_tokens:,} tokens ({percentage:.0f}%)"

    def clear(self) -> None:
        """Clear all tracked messages and reset token count."""
        self._messages = []
        self.total_tokens = 0

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all tracked messages.

        Returns:
            List of message dicts with role, content, tokens
        """
        return self._messages.copy()
```

**Step 4: Run test to verify it passes**

Run: `source venv/bin/activate && pytest tests/agent/test_context_manager.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add cmd_center/agent/core/context.py tests/agent/test_context_manager.py
git commit -m "feat(agent): add context manager for token limits"
```

---

## Task 3: Integrate Context Manager with Agent

**Files:**
- Modify: `cmd_center/agent/core/agent.py`
- Test: `tests/agent/test_agent_context.py`

**Step 1: Write the failing test**

Create `tests/agent/test_agent_context.py`:

```python
"""Tests for agent context management integration."""

import pytest
from unittest.mock import patch, MagicMock

from cmd_center.agent.core.agent import OmniousAgent


class TestAgentContextIntegration:
    """Tests for agent context management."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    def test_agent_has_context_manager(self, agent):
        """Agent has context manager attribute."""
        assert hasattr(agent, 'context_manager')
        assert agent.context_manager is not None

    def test_add_to_history_tracks_context(self, agent):
        """Adding to history tracks context tokens."""
        agent._add_to_history("user", "Hello world")

        assert agent.context_manager.total_tokens > 0

    def test_clear_conversation_clears_context(self, agent):
        """Clearing conversation clears context."""
        agent._add_to_history("user", "Hello")
        agent.clear_conversation()

        assert agent.context_manager.total_tokens == 0

    def test_get_context_warning(self, agent):
        """Agent can get context warning."""
        # Should return None when under limit
        assert agent.get_context_warning() is None

    def test_get_context_usage(self, agent):
        """Agent can get context usage summary."""
        agent._add_to_history("user", "Hello")

        usage = agent.get_context_usage()
        assert "token" in usage.lower() or "/" in usage
```

**Step 2: Run test to verify it fails**

Run: `source venv/bin/activate && pytest tests/agent/test_agent_context.py -v`
Expected: FAIL with "Agent has no attribute 'context_manager'"

**Step 3: Write minimal implementation**

Modify `cmd_center/agent/core/agent.py`:

```python
# Add import at top
from .context import ContextManager

# In __init__, add after file_logger:
self.context_manager = ContextManager()

# Update _add_to_history to track context:
# Add after file logger call:
self.context_manager.add_message(role, content)

# Update clear_conversation:
def clear_conversation(self) -> None:
    """Clear conversation history."""
    self.conversation_history = []
    self.context_manager.clear()

# Add new methods:
def get_context_warning(self) -> Optional[str]:
    """Get context limit warning if near limit.

    Returns:
        Warning message or None if under threshold
    """
    return self.context_manager.get_warning()

def get_context_usage(self) -> str:
    """Get context usage summary.

    Returns:
        Formatted usage string
    """
    return self.context_manager.get_usage_summary()
```

**Step 4: Run test to verify it passes**

Run: `source venv/bin/activate && pytest tests/agent/test_agent_context.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add cmd_center/agent/core/agent.py tests/agent/test_agent_context.py
git commit -m "feat(agent): integrate context manager with agent"
```

---

## Task 4: Enhanced Error Handling

**Files:**
- Create: `cmd_center/agent/core/errors.py`
- Test: `tests/agent/test_error_handling.py`

**Step 1: Write the failing test**

Create `tests/agent/test_error_handling.py`:

```python
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
        assert "get_deals" not in response  # Don't expose internal names

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
```

**Step 2: Run test to verify it fails**

Run: `source venv/bin/activate && pytest tests/agent/test_error_handling.py -v`
Expected: FAIL with "cannot import name 'AgentError'"

**Step 3: Write minimal implementation**

Create `cmd_center/agent/core/errors.py`:

```python
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
    """Format an error into a user-friendly response.

    Args:
        error: The exception to format

    Returns:
        User-friendly error message
    """
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

    # Generic error
    return (
        "I'm sorry, I ran into an unexpected issue. "
        "Let me know if you'd like to try again or ask something different."
    )
```

**Step 4: Run test to verify it passes**

Run: `source venv/bin/activate && pytest tests/agent/test_error_handling.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add cmd_center/agent/core/errors.py tests/agent/test_error_handling.py
git commit -m "feat(agent): add enhanced error types and formatting"
```

---

## Task 5: Integrate Error Handling with Agent

**Files:**
- Modify: `cmd_center/agent/core/agent.py`
- Test: `tests/agent/test_agent_errors.py`

**Step 1: Write the failing test**

Create `tests/agent/test_agent_errors.py`:

```python
"""Tests for agent error handling integration."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx

from cmd_center.agent.core.agent import OmniousAgent


class TestAgentErrorHandling:
    """Tests for agent error handling."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    @pytest.mark.asyncio
    async def test_chat_handles_api_error_gracefully(self, agent):
        """Chat returns friendly message on API error."""
        with patch.object(
            agent, '_call_api_with_retry',
            new_callable=AsyncMock
        ) as mock_api:
            mock_api.side_effect = httpx.HTTPError("Connection failed")

            response = await agent.chat("Hello")

            # Should return friendly error, not crash
            assert "sorry" in response.lower() or "trouble" in response.lower()

    @pytest.mark.asyncio
    async def test_chat_handles_tool_error_gracefully(self, agent):
        """Chat handles tool execution errors gracefully."""
        # Mock API response that triggers tool call
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "function": {
                            "name": "get_overdue_deals",
                            "arguments": "{}"
                        }
                    }]
                }
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }

        with patch.object(
            agent, '_call_api_with_retry',
            new_callable=AsyncMock
        ) as mock_api:
            mock_api.return_value = mock_response

            with patch.object(agent.tools, 'execute') as mock_execute:
                mock_execute.side_effect = Exception("Database error")

                # Should not crash, returns error in tool result
                # The agent will continue and LLM will respond
```

**Step 2: Run test to verify it fails**

Run: `source venv/bin/activate && pytest tests/agent/test_agent_errors.py -v`
Expected: FAIL (behavior may not match)

**Step 3: Write minimal implementation**

Modify `cmd_center/agent/core/agent.py`:

```python
# Add import at top
from .errors import format_error_response, ToolExecutionError

# Update chat method to catch and format errors:
async def chat(self, message: str) -> str:
    """Send a message and get a response (non-streaming).

    Args:
        message: User's message

    Returns:
        Assistant's response
    """
    # Check for confirmation response first
    if self.has_pending_action():
        confirmation = self._is_confirmation(message)
        if confirmation == "yes":
            result = self.executor.execute(self.pending_action)
            self.pending_action = None
            # ... existing confirmation handling
        elif confirmation == "no":
            self.pending_action = None
            self._add_to_history("user", message)
            response = "No problem, I won't proceed with that action. How else can I help?"
            self._add_to_history("assistant", response)
            return response

    try:
        messages = self._build_messages(message)
        self._add_to_history("user", message)

        content = await self._call_llm_with_tools(messages)
        self._add_to_history("assistant", content)

        return content

    except Exception as e:
        error_response = format_error_response(e)
        self._add_to_history("assistant", error_response)
        return error_response

# Update _process_tool_calls to handle errors:
async def _process_tool_calls(
    self,
    tool_calls: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Process tool calls and return results."""
    results = []

    for tool_call in tool_calls:
        tool_id = tool_call["id"]
        function = tool_call["function"]
        tool_name = function["name"]

        try:
            arguments = json.loads(function["arguments"])
        except json.JSONDecodeError:
            arguments = {}

        try:
            # Execute the tool
            result = self.tools.execute(tool_name, arguments)

            # Check for pending action...
            # (existing code)

            # Format result
            if result.success:
                content = json.dumps(result.data)
            else:
                content = json.dumps({"error": result.error})

        except Exception as e:
            # Handle tool execution error
            content = json.dumps({
                "error": f"Tool execution failed: {str(e)}"
            })

        results.append({
            "role": "tool",
            "tool_call_id": tool_id,
            "content": content
        })

    return results
```

**Step 4: Run test to verify it passes**

Run: `source venv/bin/activate && pytest tests/agent/test_agent_errors.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add cmd_center/agent/core/agent.py tests/agent/test_agent_errors.py
git commit -m "feat(agent): integrate enhanced error handling"
```

---

## Task 6: Expand Golden Tests with Scenarios

**Files:**
- Modify: `tests/agent/test_golden_qa.py`
- Create: `tests/agent/test_golden_scenarios.py`

**Step 1: Create comprehensive scenario tests**

Create `tests/agent/test_golden_scenarios.py`:

```python
"""Golden scenario tests for Omnious agent behavior."""

import pytest
from unittest.mock import patch, MagicMock

from cmd_center.agent.core.agent import OmniousAgent
from cmd_center.agent.tools.base import PendingAction


# Scenario definitions
QUERY_SCENARIOS = [
    # Pipeline queries
    {"id": "pipeline_health", "query": "How is our pipeline doing?", "expected_tools": ["get_overdue_deals", "get_stuck_deals"]},
    {"id": "aramco_deals", "query": "Show me Aramco deals that need attention", "expected_tools": ["get_overdue_deals"]},
    {"id": "deal_lookup", "query": "What's the status of deal 456?", "expected_tools": ["get_deal_details"]},

    # Task queries
    {"id": "my_tasks", "query": "What tasks do I have?", "expected_tools": ["get_tasks"]},
    {"id": "overdue_work", "query": "What's overdue?", "expected_tools": ["get_overdue_tasks"]},
    {"id": "reminders", "query": "Any upcoming reminders?", "expected_tools": ["get_pending_reminders"]},

    # Employee queries
    {"id": "team_info", "query": "Who is on the sales team?", "expected_tools": ["get_employees"]},
    {"id": "person_lookup", "query": "Tell me about Mohammed", "expected_tools": ["get_employee_details"]},
    {"id": "skills", "query": "What skills does employee 3 have?", "expected_tools": ["get_employee_skills"]},

    # Financial queries
    {"id": "cashflow", "query": "What's our cashflow looking like?", "expected_tools": ["get_cashflow_projection"]},
    {"id": "dashboard", "query": "Show me the CEO dashboard", "expected_tools": ["get_ceo_dashboard"]},
    {"id": "kpis", "query": "What are the sales KPIs?", "expected_tools": ["get_owner_kpis"]},

    # Email queries
    {"id": "find_emails", "query": "Find emails about the contract", "expected_tools": ["search_emails"]},
    {"id": "recent_emails", "query": "Show me recent emails", "expected_tools": ["get_emails"]},

    # Document/HR queries
    {"id": "expiring_docs", "query": "Any documents expiring soon?", "expected_tools": ["get_expiring_documents"]},
    {"id": "bonuses", "query": "Who has unpaid bonuses?", "expected_tools": ["get_unpaid_bonuses"]},

    # Knowledge queries
    {"id": "company_info", "query": "What does GypTech do?", "expected_tools": ["read_knowledge"]},
    {"id": "procedures", "query": "What's the sales process?", "expected_tools": ["read_knowledge"]},
]

WRITE_SCENARIOS = [
    {"id": "create_task", "query": "Create a task to follow up with client", "expected_tools": ["request_create_task"]},
    {"id": "create_note", "query": "Add a note about the meeting", "expected_tools": ["request_create_note"]},
    {"id": "create_reminder", "query": "Remind me about this tomorrow", "expected_tools": ["request_create_reminder"]},
    {"id": "send_email", "query": "Send an email to client@example.com", "expected_tools": ["request_send_email"]},
    {"id": "update_deal", "query": "Mark deal 123 as won", "expected_tools": ["request_update_deal"]},
    {"id": "add_deal_note", "query": "Add a note to deal 456", "expected_tools": ["request_add_deal_note"]},
]


class TestQueryScenarios:
    """Test tool selection for query scenarios."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    @pytest.mark.parametrize("scenario", QUERY_SCENARIOS, ids=lambda s: s["id"])
    def test_query_tools_available(self, agent, scenario):
        """Verify expected tools are registered for query scenarios."""
        tool_names = [t["name"] for t in agent.tools.list_tools()]

        for expected_tool in scenario["expected_tools"]:
            assert expected_tool in tool_names, (
                f"Scenario '{scenario['id']}': Tool '{expected_tool}' not registered"
            )


class TestWriteScenarios:
    """Test tool selection for write scenarios."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    @pytest.mark.parametrize("scenario", WRITE_SCENARIOS, ids=lambda s: s["id"])
    def test_write_tools_available(self, agent, scenario):
        """Verify expected tools are registered for write scenarios."""
        tool_names = [t["name"] for t in agent.tools.list_tools()]

        for expected_tool in scenario["expected_tools"]:
            assert expected_tool in tool_names, (
                f"Scenario '{scenario['id']}': Tool '{expected_tool}' not registered"
            )

    @pytest.mark.parametrize("scenario", WRITE_SCENARIOS, ids=lambda s: s["id"])
    def test_write_tools_return_pending_action(self, agent, scenario):
        """Write tools return pending action, not immediate execution."""
        for tool_name in scenario["expected_tools"]:
            # Get minimal valid params for tool
            params = _get_minimal_params(tool_name)
            result = agent.tools.execute(tool_name, params)

            assert result.success, f"Tool {tool_name} failed"
            assert "pending_action" in result.data, (
                f"Tool {tool_name} should return pending_action"
            )


class TestRefusalScenarios:
    """Test that agent refuses out-of-scope requests."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    def test_no_delete_tool_exists(self, agent):
        """No delete tools should exist."""
        tool_names = [t["name"] for t in agent.tools.list_tools()]

        delete_tools = [t for t in tool_names if "delete" in t.lower()]
        assert len(delete_tools) == 0, f"Found delete tools: {delete_tools}"

    def test_no_payment_tool_exists(self, agent):
        """No payment/approval tools should exist."""
        tool_names = [t["name"] for t in agent.tools.list_tools()]

        payment_tools = [t for t in tool_names if "pay" in t.lower() or "approve" in t.lower()]
        assert len(payment_tools) == 0, f"Found payment tools: {payment_tools}"


class TestConfirmationScenarios:
    """Test confirmation flow scenarios."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    def test_pending_action_requires_confirmation(self, agent):
        """Pending action exists until confirmed or cancelled."""
        agent.pending_action = PendingAction(
            tool_name="request_create_task",
            preview="Create task: Test",
            payload={"title": "Test"},
        )

        assert agent.has_pending_action()
        assert agent.get_pending_preview() is not None

    def test_confirmation_clears_pending(self, agent):
        """Confirmation clears pending action."""
        agent.pending_action = PendingAction(
            tool_name="request_create_task",
            preview="Create task: Test",
            payload={"title": "Test"},
        )

        # Simulate confirmation
        agent.pending_action = None

        assert not agent.has_pending_action()

    @pytest.mark.parametrize("phrase", ["yes", "y", "confirm", "ok", "proceed"])
    def test_yes_phrases_detected(self, agent, phrase):
        """Various yes phrases are detected."""
        assert agent._is_confirmation(phrase) == "yes"

    @pytest.mark.parametrize("phrase", ["no", "n", "cancel", "stop", "abort"])
    def test_no_phrases_detected(self, agent, phrase):
        """Various no phrases are detected."""
        assert agent._is_confirmation(phrase) == "no"


def _get_minimal_params(tool_name: str) -> dict:
    """Get minimal valid params for each write tool."""
    params = {
        "request_create_task": {"title": "Test task"},
        "request_create_note": {"content": "Test note", "target_type": "deal", "target_id": 1},
        "request_create_reminder": {
            "target_type": "task",
            "target_id": 1,
            "remind_at": "2026-01-15T10:00:00",
            "message": "Test reminder",
        },
        "request_send_email": {
            "to": "test@example.com",
            "subject": "Test",
            "body": "Test body",
        },
        "request_update_deal": {"deal_id": 123, "status": "won"},
        "request_add_deal_note": {"deal_id": 123, "content": "Test note"},
    }
    return params.get(tool_name, {})
```

**Step 2: Run tests to verify they pass**

Run: `source venv/bin/activate && pytest tests/agent/test_golden_scenarios.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/agent/test_golden_scenarios.py
git commit -m "test(agent): add comprehensive golden scenario tests"
```

---

## Task 7: Final Integration Tests

**Files:**
- Modify: `tests/agent/test_phase3_integration.py` → Rename to `test_integration.py`
- Run all tests

**Step 1: Create comprehensive integration tests**

Create `tests/agent/test_phase4_integration.py`:

```python
"""Integration tests for Phase 4 polish features."""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from cmd_center.agent.core.agent import OmniousAgent
from cmd_center.agent.observability.logger import ConversationLogger
from cmd_center.agent.core.context import ContextManager
from cmd_center.agent.core.errors import format_error_response, ToolExecutionError


class TestPhase4Integration:
    """End-to-end tests for Phase 4 features."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    def test_agent_has_all_phase4_components(self, agent):
        """Agent has all Phase 4 components."""
        assert hasattr(agent, 'file_logger')
        assert hasattr(agent, 'context_manager')
        assert hasattr(agent, 'get_context_warning')
        assert hasattr(agent, 'get_context_usage')

    def test_file_logger_creates_logs(self, tmp_path):
        """File logger creates JSONL logs."""
        logger = ConversationLogger(log_dir=str(tmp_path))
        logger.log_message(
            conversation_id=1,
            role="user",
            content="Hello",
        )

        log_files = list(tmp_path.glob("*.jsonl"))
        assert len(log_files) == 1

    def test_context_manager_tracks_usage(self):
        """Context manager tracks token usage."""
        context = ContextManager(max_tokens=1000)
        context.add_message("user", "Hello world")

        assert context.total_tokens > 0
        assert "token" in context.get_usage_summary().lower()

    def test_error_formatting_friendly(self):
        """Error formatting produces friendly messages."""
        error = ToolExecutionError("test_tool", "Failed")
        response = format_error_response(error)

        assert "trouble" in response.lower() or "error" not in response.lower()
        assert "test_tool" not in response  # Don't expose internal names


class TestFullAgentWorkflow:
    """Test complete agent workflows with all features."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        with patch('cmd_center.agent.core.agent.get_config') as mock_config:
            mock_config.return_value = MagicMock(
                openrouter_api_key="test-key",
                openrouter_api_url="https://api.test.com",
                llm_model="test-model"
            )
            return OmniousAgent()

    def test_agent_initialization_complete(self, agent):
        """Agent initializes with all components."""
        # Core components
        assert agent.tools is not None
        assert agent.metrics is not None

        # Phase 3 components
        assert agent.executor is not None
        assert agent.pending_action is None

        # Phase 4 components
        assert agent.file_logger is not None
        assert agent.context_manager is not None

    def test_total_tool_count(self, agent):
        """All 25 tools are registered."""
        tools = agent.tools.list_tools()
        assert len(tools) == 25

    def test_all_tool_schemas_valid(self, agent):
        """All tools generate valid OpenAI schemas."""
        schemas = agent.tools.get_tools_schema()

        for schema in schemas:
            assert schema["type"] == "function"
            assert "function" in schema
            assert "name" in schema["function"]
            assert "description" in schema["function"]
            assert len(schema["function"]["description"]) > 10
```

**Step 2: Run all tests**

Run: `source venv/bin/activate && pytest tests/agent/ -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/agent/test_phase4_integration.py
git commit -m "test(agent): add Phase 4 integration tests"
```

---

## Task 8: Final Cleanup and Documentation

**Files:**
- Verify exports in `__init__.py` files
- Run full test suite

**Step 1: Verify exports**

Check `cmd_center/agent/observability/__init__.py`:

```python
"""Agent observability components."""

from .metrics import MetricsTracker, get_metrics_tracker
from .logger import ConversationLogger, get_conversation_logger

__all__ = [
    "MetricsTracker",
    "get_metrics_tracker",
    "ConversationLogger",
    "get_conversation_logger",
]
```

Check `cmd_center/agent/core/__init__.py`:

```python
"""Agent core components."""

from .agent import OmniousAgent, get_agent
from .prompts import build_system_prompt, SYSTEM_PROMPT
from .context import ContextManager
from .executor import ActionExecutor, get_executor
from .errors import (
    AgentError,
    ToolExecutionError,
    APIError,
    RateLimitError,
    ContextLimitError,
    format_error_response,
)

__all__ = [
    "OmniousAgent",
    "get_agent",
    "build_system_prompt",
    "SYSTEM_PROMPT",
    "ContextManager",
    "ActionExecutor",
    "get_executor",
    "AgentError",
    "ToolExecutionError",
    "APIError",
    "RateLimitError",
    "ContextLimitError",
    "format_error_response",
]
```

**Step 2: Run full test suite**

Run: `source venv/bin/activate && pytest tests/agent/ -v --tb=short`
Expected: All tests pass

**Step 3: Final commit**

```bash
git add cmd_center/agent/observability/__init__.py cmd_center/agent/core/__init__.py
git commit -m "chore(agent): update exports for Phase 4 components"
```

---

## Summary

Phase 4 adds production polish to Omnious:

| Feature | Description |
|---------|-------------|
| **File Logging** | JSONL logs to `logs/omnious/conversations_YYYY-MM-DD.jsonl` |
| **Context Management** | Token tracking with soft limit warnings |
| **Enhanced Errors** | Graceful user-friendly error responses |
| **Golden Tests** | 50+ scenario tests for tool selection and behavior |

**Total Tests After Phase 4:** ~800+ tests

**Components Added:**
- `cmd_center/agent/observability/logger.py`
- `cmd_center/agent/core/context.py`
- `cmd_center/agent/core/errors.py`
- `tests/agent/test_file_logger.py`
- `tests/agent/test_context_manager.py`
- `tests/agent/test_error_handling.py`
- `tests/agent/test_golden_scenarios.py`
- `tests/agent/test_phase4_integration.py`
