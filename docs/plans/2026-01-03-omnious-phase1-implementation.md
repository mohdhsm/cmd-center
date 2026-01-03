# Omnious AI Agent - Phase 1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the core foundation of Omnious - a chat interface with streaming responses that can query deals, tasks, and employees using OpenRouter tool calling.

**Architecture:** ReAct loop with native OpenRouter/OpenAI function calling. Agent imports existing services, streams responses, and tracks token usage.

**Tech Stack:** Python, Textual (TUI), OpenRouter API (OpenAI-compatible tools format), Pydantic

---

## Prerequisites

Before starting, ensure:
- OpenRouter API key is configured in `.env`
- Existing services work: `deal_health_service`, `task_service`, `employee_service`
- Tests pass: `pytest tests/`

---

## Task 1: Create Agent Module Structure

**Files:**
- Create: `cmd_center/agent/__init__.py`
- Create: `cmd_center/agent/core/__init__.py`
- Create: `cmd_center/agent/tools/__init__.py`
- Create: `cmd_center/agent/observability/__init__.py`

**Step 1: Create directory structure**

```bash
mkdir -p cmd_center/agent/core
mkdir -p cmd_center/agent/tools
mkdir -p cmd_center/agent/observability
```

**Step 2: Create `cmd_center/agent/__init__.py`**

```python
"""Omnious AI Agent module."""

from .core.agent import OmniousAgent, get_agent

__all__ = ["OmniousAgent", "get_agent"]
```

**Step 3: Create `cmd_center/agent/core/__init__.py`**

```python
"""Agent core components."""

from .agent import OmniousAgent, get_agent
from .prompts import SYSTEM_PROMPT

__all__ = ["OmniousAgent", "get_agent", "SYSTEM_PROMPT"]
```

**Step 4: Create `cmd_center/agent/tools/__init__.py`**

```python
"""Agent tools for querying data."""

from .registry import ToolRegistry, get_tool_registry
from .base import BaseTool, ToolResult

__all__ = ["ToolRegistry", "get_tool_registry", "BaseTool", "ToolResult"]
```

**Step 5: Create `cmd_center/agent/observability/__init__.py`**

```python
"""Agent observability components."""

from .metrics import MetricsTracker, get_metrics_tracker

__all__ = ["MetricsTracker", "get_metrics_tracker"]
```

**Step 6: Commit**

```bash
git add cmd_center/agent/
git commit -m "feat(agent): create Omnious agent module structure"
```

---

## Task 2: Implement Metrics Tracker

**Files:**
- Create: `cmd_center/agent/observability/metrics.py`
- Create: `tests/agent/__init__.py`
- Create: `tests/agent/test_metrics.py`

**Step 1: Write the failing test**

Create `tests/agent/__init__.py`:
```python
"""Tests for Omnious agent module."""
```

Create `tests/agent/test_metrics.py`:
```python
"""Tests for MetricsTracker."""

import pytest
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_metrics.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'cmd_center.agent.observability.metrics'"

**Step 3: Write minimal implementation**

Create `cmd_center/agent/observability/metrics.py`:
```python
"""Token and cost tracking for agent sessions."""

from typing import Optional


class MetricsTracker:
    """Track token usage and costs for agent sessions."""

    # Claude Sonnet 4 via OpenRouter pricing (per 1M tokens)
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/agent/test_metrics.py -v`
Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add cmd_center/agent/observability/metrics.py tests/agent/
git commit -m "feat(agent): add MetricsTracker for token and cost tracking"
```

---

## Task 3: Implement Omnious System Prompt

**Files:**
- Create: `cmd_center/agent/core/prompts.py`
- Create: `tests/agent/test_prompts.py`

**Step 1: Write the failing test**

Create `tests/agent/test_prompts.py`:
```python
"""Tests for Omnious prompts."""

import pytest
from cmd_center.agent.core.prompts import SYSTEM_PROMPT, build_system_prompt


class TestSystemPrompt:
    """Test system prompt configuration."""

    def test_system_prompt_contains_identity(self):
        """System prompt establishes Omnious identity."""
        assert "Omnious" in SYSTEM_PROMPT
        assert "all-knowing" in SYSTEM_PROMPT.lower()

    def test_system_prompt_contains_personality(self):
        """System prompt includes personality traits."""
        prompt_lower = SYSTEM_PROMPT.lower()
        assert "friendly" in prompt_lower or "witty" in prompt_lower

    def test_system_prompt_contains_boundaries(self):
        """System prompt includes scope boundaries."""
        prompt_lower = SYSTEM_PROMPT.lower()
        assert "delete" in prompt_lower  # Mentions no deletion
        assert "confirm" in prompt_lower  # Mentions confirmation

    def test_build_system_prompt_basic(self):
        """Build system prompt returns valid string."""
        prompt = build_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_build_system_prompt_with_context(self):
        """Build system prompt can include additional context."""
        prompt = build_system_prompt(additional_context="Today is Monday.")
        assert "Monday" in prompt
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_prompts.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `cmd_center/agent/core/prompts.py`:
```python
"""Omnious agent prompts and persona definition."""

from typing import Optional

SYSTEM_PROMPT = """You are Omnious, the all-knowing AI assistant for GypTech's Command Center.

## Identity
- Name: Omnious (you may playfully refer to yourself as "the all-knowing AI")
- Tone: Friendly, witty, and professional
- Style: Concise but thorough, with light humor when appropriate
- Language: English only

## Your Capabilities
You can help users by:
1. Querying company data (deals, tasks, employees, etc.)
2. Analyzing pipeline health and identifying issues
3. Answering questions about deals, tasks, and team members
4. Providing insights based on the data you can access

## Tools Available
You have access to tools that query the company database. Use them to answer questions accurately.
Always base your answers on data from tools - never make up information.

## Scope Boundaries
You MUST REFUSE to:
1. Delete anything - You cannot delete data
2. Make financial commitments - You cannot approve payments or bonuses
3. Send emails without confirmation - Always require explicit approval
4. Modify data without confirmation - Always show a preview first
5. Make up information - If you don't know, say so and offer to look it up

When refusing a request outside your scope, be friendly about it:
Example: "I appreciate the spring cleaning energy, but I'm not authorized to delete anything.
I can help you review the items and mark them as complete one by one if you'd like."

## Response Style
- Be concise but complete
- Use data from tools to support your answers
- If you need to call multiple tools, do so efficiently
- Format lists and data clearly
- End responses with a helpful offer when appropriate

Example greeting:
"Greetings! The all-knowing Omnious is at your service. What would you like to know about today?"
"""


def build_system_prompt(additional_context: Optional[str] = None) -> str:
    """Build the complete system prompt.

    Args:
        additional_context: Optional additional context to include

    Returns:
        Complete system prompt string
    """
    prompt = SYSTEM_PROMPT

    if additional_context:
        prompt += f"\n\n## Additional Context\n{additional_context}"

    return prompt
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/agent/test_prompts.py -v`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add cmd_center/agent/core/prompts.py tests/agent/test_prompts.py
git commit -m "feat(agent): add Omnious system prompt and persona"
```

---

## Task 4: Implement Tool Base Classes

**Files:**
- Create: `cmd_center/agent/tools/base.py`
- Create: `tests/agent/test_tools_base.py`

**Step 1: Write the failing test**

Create `tests/agent/test_tools_base.py`:
```python
"""Tests for tool base classes."""

import pytest
from pydantic import BaseModel
from cmd_center.agent.tools.base import BaseTool, ToolResult, pydantic_to_openai_schema


class SampleParams(BaseModel):
    """Sample parameters for testing."""
    name: str
    count: int = 10


class SampleTool(BaseTool):
    """Sample tool for testing."""

    name = "sample_tool"
    description = "A sample tool for testing"
    parameters_model = SampleParams

    def execute(self, params: SampleParams) -> ToolResult:
        return ToolResult(success=True, data={"name": params.name, "count": params.count})


class TestToolResult:
    """Test ToolResult dataclass."""

    def test_success_result(self):
        """Successful result has data."""
        result = ToolResult(success=True, data={"key": "value"})
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None

    def test_error_result(self):
        """Error result has error message."""
        result = ToolResult(success=False, error="Something went wrong")
        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.data is None


class TestBaseTool:
    """Test BaseTool class."""

    def test_tool_has_name(self):
        """Tool has a name."""
        tool = SampleTool()
        assert tool.name == "sample_tool"

    def test_tool_has_description(self):
        """Tool has a description."""
        tool = SampleTool()
        assert tool.description == "A sample tool for testing"

    def test_tool_generates_openai_schema(self):
        """Tool generates OpenAI-compatible schema."""
        tool = SampleTool()
        schema = tool.get_openai_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "sample_tool"
        assert schema["function"]["description"] == "A sample tool for testing"
        assert "parameters" in schema["function"]
        assert schema["function"]["parameters"]["type"] == "object"

    def test_tool_schema_includes_properties(self):
        """Tool schema includes parameter properties."""
        tool = SampleTool()
        schema = tool.get_openai_schema()

        props = schema["function"]["parameters"]["properties"]
        assert "name" in props
        assert "count" in props

    def test_tool_schema_includes_required(self):
        """Tool schema includes required fields."""
        tool = SampleTool()
        schema = tool.get_openai_schema()

        required = schema["function"]["parameters"].get("required", [])
        assert "name" in required
        # count has default, so not required

    def test_tool_execute(self):
        """Tool can be executed with params."""
        tool = SampleTool()
        params = SampleParams(name="test", count=5)
        result = tool.execute(params)

        assert result.success is True
        assert result.data["name"] == "test"
        assert result.data["count"] == 5


class TestPydanticToOpenAISchema:
    """Test pydantic_to_openai_schema function."""

    def test_converts_model(self):
        """Converts Pydantic model to OpenAI schema."""
        schema = pydantic_to_openai_schema(SampleParams)

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "name" in schema["properties"]

    def test_includes_required(self):
        """Includes required fields."""
        schema = pydantic_to_openai_schema(SampleParams)

        assert "required" in schema
        assert "name" in schema["required"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_tools_base.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `cmd_center/agent/tools/base.py`:
```python
"""Base classes for agent tools."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional, Type

from pydantic import BaseModel


@dataclass
class ToolResult:
    """Result from executing a tool."""

    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


def pydantic_to_openai_schema(model: Type[BaseModel]) -> dict:
    """Convert Pydantic model to OpenAI function parameters schema.

    Args:
        model: Pydantic model class

    Returns:
        OpenAI-compatible parameters schema
    """
    json_schema = model.model_json_schema()

    # Remove $defs if present (not needed for OpenAI)
    schema = {
        "type": "object",
        "properties": json_schema.get("properties", {}),
    }

    # Add required fields if present
    if "required" in json_schema:
        schema["required"] = json_schema["required"]

    return schema


class BaseTool(ABC):
    """Base class for all agent tools."""

    name: str = ""
    description: str = ""
    parameters_model: Type[BaseModel] = BaseModel

    def get_openai_schema(self) -> dict:
        """Get OpenAI-compatible tool schema.

        Returns:
            Tool schema in OpenAI function format
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": pydantic_to_openai_schema(self.parameters_model),
            }
        }

    @abstractmethod
    def execute(self, params: BaseModel) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            params: Validated parameters

        Returns:
            ToolResult with data or error
        """
        pass

    def parse_and_execute(self, arguments: dict) -> ToolResult:
        """Parse arguments and execute the tool.

        Args:
            arguments: Raw arguments dict from LLM

        Returns:
            ToolResult with data or error
        """
        try:
            params = self.parameters_model.model_validate(arguments)
            return self.execute(params)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/agent/test_tools_base.py -v`
Expected: PASS (10 tests)

**Step 5: Commit**

```bash
git add cmd_center/agent/tools/base.py tests/agent/test_tools_base.py
git commit -m "feat(agent): add BaseTool class with OpenAI schema generation"
```

---

## Task 5: Implement Tool Registry

**Files:**
- Create: `cmd_center/agent/tools/registry.py`
- Create: `tests/agent/test_registry.py`

**Step 1: Write the failing test**

Create `tests/agent/test_registry.py`:
```python
"""Tests for tool registry."""

import pytest
from pydantic import BaseModel
from cmd_center.agent.tools.base import BaseTool, ToolResult
from cmd_center.agent.tools.registry import ToolRegistry


class MockParams(BaseModel):
    """Mock parameters."""
    value: str


class MockTool(BaseTool):
    """Mock tool for testing."""

    name = "mock_tool"
    description = "A mock tool"
    parameters_model = MockParams

    def execute(self, params: MockParams) -> ToolResult:
        return ToolResult(success=True, data={"value": params.value})


class AnotherMockTool(BaseTool):
    """Another mock tool."""

    name = "another_tool"
    description = "Another mock tool"
    parameters_model = MockParams

    def execute(self, params: MockParams) -> ToolResult:
        return ToolResult(success=True, data={"result": "ok"})


class TestToolRegistry:
    """Test ToolRegistry class."""

    def test_register_tool(self):
        """Can register a tool."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)

        assert "mock_tool" in registry.tools

    def test_register_multiple_tools(self):
        """Can register multiple tools."""
        registry = ToolRegistry()
        registry.register(MockTool())
        registry.register(AnotherMockTool())

        assert len(registry.tools) == 2

    def test_get_tool(self):
        """Can get tool by name."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)

        retrieved = registry.get("mock_tool")
        assert retrieved is tool

    def test_get_nonexistent_tool(self):
        """Returns None for nonexistent tool."""
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    def test_get_tools_schema(self):
        """Get OpenAI schema for all tools."""
        registry = ToolRegistry()
        registry.register(MockTool())
        registry.register(AnotherMockTool())

        schemas = registry.get_tools_schema()

        assert len(schemas) == 2
        assert all(s["type"] == "function" for s in schemas)
        names = [s["function"]["name"] for s in schemas]
        assert "mock_tool" in names
        assert "another_tool" in names

    def test_execute_tool(self):
        """Execute tool by name with arguments."""
        registry = ToolRegistry()
        registry.register(MockTool())

        result = registry.execute("mock_tool", {"value": "test"})

        assert result.success is True
        assert result.data["value"] == "test"

    def test_execute_nonexistent_tool(self):
        """Executing nonexistent tool returns error."""
        registry = ToolRegistry()

        result = registry.execute("nonexistent", {})

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_list_tools(self):
        """List all registered tools."""
        registry = ToolRegistry()
        registry.register(MockTool())
        registry.register(AnotherMockTool())

        tools = registry.list_tools()

        assert len(tools) == 2
        assert any(t["name"] == "mock_tool" for t in tools)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_registry.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `cmd_center/agent/tools/registry.py`:
```python
"""Tool registry for managing agent tools."""

from typing import Dict, List, Optional

from .base import BaseTool, ToolResult


class ToolRegistry:
    """Registry for agent tools."""

    def __init__(self):
        """Initialize empty registry."""
        self.tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool.

        Args:
            tool: Tool instance to register
        """
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool if found, None otherwise
        """
        return self.tools.get(name)

    def get_tools_schema(self) -> List[dict]:
        """Get OpenAI-compatible schema for all tools.

        Returns:
            List of tool schemas in OpenAI format
        """
        return [tool.get_openai_schema() for tool in self.tools.values()]

    def execute(self, name: str, arguments: dict) -> ToolResult:
        """Execute a tool by name.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            ToolResult with data or error
        """
        tool = self.get(name)
        if tool is None:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found"
            )

        return tool.parse_and_execute(arguments)

    def list_tools(self) -> List[dict]:
        """List all registered tools with metadata.

        Returns:
            List of tool info dicts
        """
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self.tools.values()
        ]


# Singleton instance
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create tool registry singleton."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/agent/test_registry.py -v`
Expected: PASS (8 tests)

**Step 5: Commit**

```bash
git add cmd_center/agent/tools/registry.py tests/agent/test_registry.py
git commit -m "feat(agent): add ToolRegistry for tool management"
```

---

## Task 6: Implement Pipeline Tools (Read-Only)

**Files:**
- Create: `cmd_center/agent/tools/pipeline_tools.py`
- Create: `tests/agent/test_pipeline_tools.py`

**Step 1: Write the failing test**

Create `tests/agent/test_pipeline_tools.py`:
```python
"""Tests for pipeline tools."""

import pytest
from unittest.mock import Mock, patch
from cmd_center.agent.tools.pipeline_tools import (
    GetOverdueDeals,
    GetStuckDeals,
    GetDealDetails,
    GetDealNotes,
)


class TestGetOverdueDeals:
    """Test GetOverdueDeals tool."""

    def test_tool_name(self):
        """Tool has correct name."""
        tool = GetOverdueDeals()
        assert tool.name == "get_overdue_deals"

    def test_tool_description(self):
        """Tool has description."""
        tool = GetOverdueDeals()
        assert "overdue" in tool.description.lower()

    def test_schema_has_pipeline_param(self):
        """Schema includes pipeline parameter."""
        tool = GetOverdueDeals()
        schema = tool.get_openai_schema()
        props = schema["function"]["parameters"]["properties"]
        assert "pipeline" in props

    @patch("cmd_center.agent.tools.pipeline_tools.get_deal_health_service")
    def test_execute_returns_deals(self, mock_get_service):
        """Execute returns deals from service."""
        # Setup mock
        mock_service = Mock()
        mock_service.get_overdue_deals.return_value = [
            Mock(id=1, title="Deal 1", owner="Alice", overdue_days=10, value=1000),
            Mock(id=2, title="Deal 2", owner="Bob", overdue_days=5, value=2000),
        ]
        mock_get_service.return_value = mock_service

        tool = GetOverdueDeals()
        result = tool.parse_and_execute({"pipeline": "aramco"})

        assert result.success is True
        assert len(result.data["deals"]) == 2


class TestGetStuckDeals:
    """Test GetStuckDeals tool."""

    def test_tool_name(self):
        """Tool has correct name."""
        tool = GetStuckDeals()
        assert tool.name == "get_stuck_deals"

    @patch("cmd_center.agent.tools.pipeline_tools.get_deal_health_service")
    def test_execute_returns_stuck_deals(self, mock_get_service):
        """Execute returns stuck deals."""
        mock_service = Mock()
        mock_service.get_stuck_deals.return_value = []
        mock_get_service.return_value = mock_service

        tool = GetStuckDeals()
        result = tool.parse_and_execute({"min_days": 30})

        assert result.success is True


class TestGetDealDetails:
    """Test GetDealDetails tool."""

    def test_tool_name(self):
        """Tool has correct name."""
        tool = GetDealDetails()
        assert tool.name == "get_deal_details"

    def test_schema_requires_deal_id(self):
        """Schema requires deal_id parameter."""
        tool = GetDealDetails()
        schema = tool.get_openai_schema()
        required = schema["function"]["parameters"].get("required", [])
        assert "deal_id" in required

    @patch("cmd_center.agent.tools.pipeline_tools.get_deal_health_service")
    def test_execute_with_valid_deal(self, mock_get_service):
        """Execute returns deal details."""
        mock_service = Mock()
        mock_service.get_deal_detail.return_value = Mock(
            id=123,
            title="Test Deal",
            stage="Under Progress",
            owner="Alice",
            value_sar=50000,
        )
        mock_get_service.return_value = mock_service

        tool = GetDealDetails()
        result = tool.parse_and_execute({"deal_id": 123})

        assert result.success is True
        assert result.data["deal"]["id"] == 123


class TestGetDealNotes:
    """Test GetDealNotes tool."""

    def test_tool_name(self):
        """Tool has correct name."""
        tool = GetDealNotes()
        assert tool.name == "get_deal_notes"

    @patch("cmd_center.agent.tools.pipeline_tools.get_deal_health_service")
    def test_execute_returns_notes(self, mock_get_service):
        """Execute returns deal notes."""
        mock_service = Mock()
        mock_service.get_deal_notes.return_value = [
            Mock(content="Note 1", author="Alice"),
            Mock(content="Note 2", author="Bob"),
        ]
        mock_get_service.return_value = mock_service

        tool = GetDealNotes()
        result = tool.parse_and_execute({"deal_id": 123, "limit": 5})

        assert result.success is True
        assert len(result.data["notes"]) == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_pipeline_tools.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `cmd_center/agent/tools/pipeline_tools.py`:
```python
"""Pipeline and deal-related tools for the agent."""

from typing import Optional, List
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult
from ...backend.services.deal_health_service import get_deal_health_service


class GetOverdueDealsParams(BaseModel):
    """Parameters for get_overdue_deals tool."""
    pipeline: str = Field(
        default="aramco",
        description="Pipeline to query: 'aramco' or 'commercial'"
    )
    min_days: int = Field(
        default=7,
        description="Minimum days without activity to be considered overdue"
    )


class GetOverdueDeals(BaseTool):
    """Get deals with no recent activity (overdue)."""

    name = "get_overdue_deals"
    description = "Get deals that have had no activity for a specified number of days. Use this to find deals that need attention."
    parameters_model = GetOverdueDealsParams

    def execute(self, params: GetOverdueDealsParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_deal_health_service()
            pipeline_name = "Aramco Projects" if params.pipeline == "aramco" else "Commercial"
            deals = service.get_overdue_deals(pipeline_name, params.min_days)

            # Convert to serializable format
            deals_data = [
                {
                    "id": d.id,
                    "title": d.title,
                    "owner": d.owner,
                    "stage": d.stage,
                    "overdue_days": d.overdue_days,
                    "value_sar": d.value,
                }
                for d in deals
            ]

            return ToolResult(
                success=True,
                data={
                    "deals": deals_data,
                    "count": len(deals_data),
                    "pipeline": params.pipeline,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetStuckDealsParams(BaseModel):
    """Parameters for get_stuck_deals tool."""
    pipeline: str = Field(
        default="aramco",
        description="Pipeline to query: 'aramco' or 'commercial'"
    )
    min_days: int = Field(
        default=30,
        description="Minimum days in current stage to be considered stuck"
    )


class GetStuckDeals(BaseTool):
    """Get deals stuck in their current stage."""

    name = "get_stuck_deals"
    description = "Get deals that have been in their current stage for too long. Use this to identify bottlenecks."
    parameters_model = GetStuckDealsParams

    def execute(self, params: GetStuckDealsParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_deal_health_service()
            pipeline_name = "Aramco Projects" if params.pipeline == "aramco" else "Commercial"
            deals = service.get_stuck_deals(pipeline_name, params.min_days)

            deals_data = [
                {
                    "id": d.id,
                    "title": d.title,
                    "owner": d.owner,
                    "stage": d.stage,
                    "days_in_stage": d.days_in_stage,
                    "value_sar": d.value,
                }
                for d in deals
            ]

            return ToolResult(
                success=True,
                data={
                    "deals": deals_data,
                    "count": len(deals_data),
                    "pipeline": params.pipeline,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetDealDetailsParams(BaseModel):
    """Parameters for get_deal_details tool."""
    deal_id: int = Field(description="The ID of the deal to get details for")


class GetDealDetails(BaseTool):
    """Get detailed information about a specific deal."""

    name = "get_deal_details"
    description = "Get full details about a specific deal including stage, owner, value, and activity counts."
    parameters_model = GetDealDetailsParams

    def execute(self, params: GetDealDetailsParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_deal_health_service()
            deal = service.get_deal_detail(params.deal_id)

            if deal is None:
                return ToolResult(
                    success=False,
                    error=f"Deal {params.deal_id} not found"
                )

            return ToolResult(
                success=True,
                data={
                    "deal": {
                        "id": deal.id,
                        "title": deal.title,
                        "pipeline": deal.pipeline,
                        "stage": deal.stage,
                        "owner": deal.owner,
                        "org_name": deal.org_name,
                        "value_sar": deal.value_sar,
                        "notes_count": deal.notes_count,
                        "activities_count": deal.activities_count,
                        "email_messages_count": deal.email_messages_count,
                    }
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetDealNotesParams(BaseModel):
    """Parameters for get_deal_notes tool."""
    deal_id: int = Field(description="The ID of the deal to get notes for")
    limit: int = Field(default=10, description="Maximum number of notes to return")


class GetDealNotes(BaseTool):
    """Get notes for a specific deal."""

    name = "get_deal_notes"
    description = "Get the most recent notes for a deal. Use this to understand deal history and context."
    parameters_model = GetDealNotesParams

    def execute(self, params: GetDealNotesParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_deal_health_service()
            notes = service.get_deal_notes(params.deal_id, params.limit)

            notes_data = [
                {
                    "content": n.content,
                    "author": n.author,
                    "date": n.date.isoformat() if n.date else None,
                }
                for n in notes
            ]

            return ToolResult(
                success=True,
                data={
                    "notes": notes_data,
                    "count": len(notes_data),
                    "deal_id": params.deal_id,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/agent/test_pipeline_tools.py -v`
Expected: PASS (9 tests)

**Step 5: Commit**

```bash
git add cmd_center/agent/tools/pipeline_tools.py tests/agent/test_pipeline_tools.py
git commit -m "feat(agent): add pipeline tools (overdue, stuck, details, notes)"
```

---

## Task 7: Implement Task and Employee Tools

**Files:**
- Create: `cmd_center/agent/tools/task_tools.py`
- Create: `cmd_center/agent/tools/employee_tools.py`
- Create: `tests/agent/test_task_employee_tools.py`

**Step 1: Write the failing test**

Create `tests/agent/test_task_employee_tools.py`:
```python
"""Tests for task and employee tools."""

import pytest
from unittest.mock import Mock, patch
from cmd_center.agent.tools.task_tools import GetTasks, GetOverdueTasks
from cmd_center.agent.tools.employee_tools import GetEmployees, GetEmployeeDetails


class TestGetTasks:
    """Test GetTasks tool."""

    def test_tool_name(self):
        """Tool has correct name."""
        tool = GetTasks()
        assert tool.name == "get_tasks"

    @patch("cmd_center.agent.tools.task_tools.get_task_service")
    def test_execute_returns_tasks(self, mock_get_service):
        """Execute returns tasks from service."""
        mock_service = Mock()
        mock_service.get_tasks.return_value = Mock(
            items=[
                Mock(id=1, title="Task 1", status="open"),
                Mock(id=2, title="Task 2", status="done"),
            ],
            total=2,
        )
        mock_get_service.return_value = mock_service

        tool = GetTasks()
        result = tool.parse_and_execute({})

        assert result.success is True
        assert len(result.data["tasks"]) == 2


class TestGetOverdueTasks:
    """Test GetOverdueTasks tool."""

    def test_tool_name(self):
        """Tool has correct name."""
        tool = GetOverdueTasks()
        assert tool.name == "get_overdue_tasks"

    @patch("cmd_center.agent.tools.task_tools.get_task_service")
    def test_execute_returns_overdue_tasks(self, mock_get_service):
        """Execute returns overdue tasks."""
        mock_service = Mock()
        mock_service.get_overdue_tasks.return_value = [
            Mock(id=1, title="Overdue Task"),
        ]
        mock_get_service.return_value = mock_service

        tool = GetOverdueTasks()
        result = tool.parse_and_execute({})

        assert result.success is True


class TestGetEmployees:
    """Test GetEmployees tool."""

    def test_tool_name(self):
        """Tool has correct name."""
        tool = GetEmployees()
        assert tool.name == "get_employees"

    @patch("cmd_center.agent.tools.employee_tools.get_employee_service")
    def test_execute_returns_employees(self, mock_get_service):
        """Execute returns employees."""
        mock_service = Mock()
        mock_service.get_employees.return_value = Mock(
            items=[
                Mock(id=1, full_name="Alice", department="sales"),
                Mock(id=2, full_name="Bob", department="operations"),
            ],
            total=2,
        )
        mock_get_service.return_value = mock_service

        tool = GetEmployees()
        result = tool.parse_and_execute({})

        assert result.success is True
        assert len(result.data["employees"]) == 2


class TestGetEmployeeDetails:
    """Test GetEmployeeDetails tool."""

    def test_tool_name(self):
        """Tool has correct name."""
        tool = GetEmployeeDetails()
        assert tool.name == "get_employee_details"

    @patch("cmd_center.agent.tools.employee_tools.get_employee_service")
    def test_execute_returns_employee(self, mock_get_service):
        """Execute returns employee details."""
        mock_service = Mock()
        mock_service.get_employee_by_id.return_value = Mock(
            id=1,
            full_name="Alice",
            role_title="Sales Manager",
            department="sales",
            email="alice@example.com",
        )
        mock_get_service.return_value = mock_service

        tool = GetEmployeeDetails()
        result = tool.parse_and_execute({"employee_id": 1})

        assert result.success is True
        assert result.data["employee"]["full_name"] == "Alice"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_task_employee_tools.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write implementations**

Create `cmd_center/agent/tools/task_tools.py`:
```python
"""Task-related tools for the agent."""

from typing import Optional
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult
from ...backend.services.task_service import get_task_service
from ...backend.models.task_models import TaskFilters


class GetTasksParams(BaseModel):
    """Parameters for get_tasks tool."""
    status: Optional[str] = Field(
        default=None,
        description="Filter by status: 'open', 'in_progress', 'done', 'cancelled'"
    )
    assignee_id: Optional[int] = Field(
        default=None,
        description="Filter by assignee employee ID"
    )
    is_critical: Optional[bool] = Field(
        default=None,
        description="Filter for critical tasks only"
    )
    limit: int = Field(
        default=20,
        description="Maximum number of tasks to return"
    )


class GetTasks(BaseTool):
    """Get tasks with optional filters."""

    name = "get_tasks"
    description = "Get tasks with optional filtering by status, assignee, or priority. Use this to find specific tasks or get an overview."
    parameters_model = GetTasksParams

    def execute(self, params: GetTasksParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_task_service()
            filters = TaskFilters(
                status=params.status,
                assignee_employee_id=params.assignee_id,
                is_critical=params.is_critical,
                page_size=params.limit,
            )
            result = service.get_tasks(filters)

            tasks_data = [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "is_critical": t.is_critical,
                    "due_at": t.due_at.isoformat() if t.due_at else None,
                    "assignee_employee_id": t.assignee_employee_id,
                }
                for t in result.items
            ]

            return ToolResult(
                success=True,
                data={
                    "tasks": tasks_data,
                    "count": len(tasks_data),
                    "total": result.total,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetOverdueTasksParams(BaseModel):
    """Parameters for get_overdue_tasks tool."""
    limit: int = Field(
        default=20,
        description="Maximum number of tasks to return"
    )


class GetOverdueTasks(BaseTool):
    """Get tasks that are past their due date."""

    name = "get_overdue_tasks"
    description = "Get tasks that are past their due date and not completed. Use this to identify urgent tasks."
    parameters_model = GetOverdueTasksParams

    def execute(self, params: GetOverdueTasksParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_task_service()
            tasks = service.get_overdue_tasks(params.limit)

            tasks_data = [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "is_critical": t.is_critical,
                    "due_at": t.due_at.isoformat() if t.due_at else None,
                    "assignee_employee_id": t.assignee_employee_id,
                }
                for t in tasks
            ]

            return ToolResult(
                success=True,
                data={
                    "tasks": tasks_data,
                    "count": len(tasks_data),
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

Create `cmd_center/agent/tools/employee_tools.py`:
```python
"""Employee-related tools for the agent."""

from typing import Optional
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult
from ...backend.services.employee_service import get_employee_service
from ...backend.models.employee_models import EmployeeFilters


class GetEmployeesParams(BaseModel):
    """Parameters for get_employees tool."""
    department: Optional[str] = Field(
        default=None,
        description="Filter by department: 'sales', 'operations', 'finance', etc."
    )
    is_active: Optional[bool] = Field(
        default=True,
        description="Filter by active status"
    )
    search: Optional[str] = Field(
        default=None,
        description="Search by name"
    )


class GetEmployees(BaseTool):
    """Get list of employees."""

    name = "get_employees"
    description = "Get employees with optional filtering by department or search term. Use this to find team members."
    parameters_model = GetEmployeesParams

    def execute(self, params: GetEmployeesParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_employee_service()
            filters = EmployeeFilters(
                department=params.department,
                is_active=params.is_active,
                search=params.search,
            )
            result = service.get_employees(filters)

            employees_data = [
                {
                    "id": e.id,
                    "full_name": e.full_name,
                    "role_title": e.role_title,
                    "department": e.department,
                    "email": e.email,
                }
                for e in result.items
            ]

            return ToolResult(
                success=True,
                data={
                    "employees": employees_data,
                    "count": len(employees_data),
                    "total": result.total,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetEmployeeDetailsParams(BaseModel):
    """Parameters for get_employee_details tool."""
    employee_id: int = Field(description="The ID of the employee")


class GetEmployeeDetails(BaseTool):
    """Get detailed information about a specific employee."""

    name = "get_employee_details"
    description = "Get full details about a specific employee including role, department, and contact info."
    parameters_model = GetEmployeeDetailsParams

    def execute(self, params: GetEmployeeDetailsParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_employee_service()
            employee = service.get_employee_by_id(params.employee_id)

            if employee is None:
                return ToolResult(
                    success=False,
                    error=f"Employee {params.employee_id} not found"
                )

            return ToolResult(
                success=True,
                data={
                    "employee": {
                        "id": employee.id,
                        "full_name": employee.full_name,
                        "role_title": employee.role_title,
                        "department": employee.department,
                        "email": employee.email,
                        "phone": employee.phone,
                        "is_active": employee.is_active,
                    }
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/agent/test_task_employee_tools.py -v`
Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add cmd_center/agent/tools/task_tools.py cmd_center/agent/tools/employee_tools.py tests/agent/test_task_employee_tools.py
git commit -m "feat(agent): add task and employee tools"
```

---

## Task 8: Implement OmniousAgent Core

**Files:**
- Create: `cmd_center/agent/core/agent.py`
- Create: `tests/agent/test_agent_core.py`

**Step 1: Write the failing test**

Create `tests/agent/test_agent_core.py`:
```python
"""Tests for OmniousAgent core."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import json

from cmd_center.agent.core.agent import OmniousAgent, StreamChunk


class TestStreamChunk:
    """Test StreamChunk dataclass."""

    def test_text_chunk(self):
        """Text chunk has type and content."""
        chunk = StreamChunk(type="text", content="Hello")
        assert chunk.type == "text"
        assert chunk.content == "Hello"

    def test_tool_call_chunk(self):
        """Tool call chunk has tool info."""
        chunk = StreamChunk(type="tool_call", tool_name="get_deals")
        assert chunk.type == "tool_call"
        assert chunk.tool_name == "get_deals"


class TestOmniousAgent:
    """Test OmniousAgent class."""

    def test_init(self):
        """Agent initializes with required components."""
        agent = OmniousAgent()
        assert agent.tools is not None
        assert agent.metrics is not None

    def test_has_tools_registered(self):
        """Agent has tools registered."""
        agent = OmniousAgent()
        tools = agent.tools.list_tools()
        assert len(tools) > 0
        # Check for expected tools
        tool_names = [t["name"] for t in tools]
        assert "get_overdue_deals" in tool_names
        assert "get_tasks" in tool_names
        assert "get_employees" in tool_names

    def test_build_messages(self):
        """Build messages includes system prompt and user message."""
        agent = OmniousAgent()
        messages = agent._build_messages("What deals need attention?")

        assert len(messages) >= 2
        assert messages[0]["role"] == "system"
        assert "Omnious" in messages[0]["content"]
        assert messages[-1]["role"] == "user"
        assert "deals" in messages[-1]["content"]

    def test_conversation_history(self):
        """Agent maintains conversation history."""
        agent = OmniousAgent()
        agent._add_to_history("user", "Hello")
        agent._add_to_history("assistant", "Hi there!")

        assert len(agent.conversation_history) == 2
        assert agent.conversation_history[0]["role"] == "user"
        assert agent.conversation_history[1]["role"] == "assistant"

    def test_clear_conversation(self):
        """Clear conversation resets history."""
        agent = OmniousAgent()
        agent._add_to_history("user", "Hello")
        agent.clear_conversation()

        assert len(agent.conversation_history) == 0


class TestOmniousAgentToolCalling:
    """Test tool calling in OmniousAgent."""

    @pytest.mark.asyncio
    async def test_process_tool_calls(self):
        """Process tool calls executes tools and returns results."""
        agent = OmniousAgent()

        tool_calls = [
            {
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "get_overdue_deals",
                    "arguments": json.dumps({"pipeline": "aramco"})
                }
            }
        ]

        with patch.object(agent.tools, "execute") as mock_execute:
            mock_execute.return_value = Mock(success=True, data={"deals": []})

            results = await agent._process_tool_calls(tool_calls)

            assert len(results) == 1
            assert results[0]["role"] == "tool"
            assert results[0]["tool_call_id"] == "call_123"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/agent/test_agent_core.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `cmd_center/agent/core/agent.py`:
```python
"""Omnious Agent core - main orchestration and ReAct loop."""

import json
import logging
from dataclasses import dataclass
from typing import AsyncIterator, List, Optional

from ..tools.registry import ToolRegistry
from ..tools.pipeline_tools import (
    GetOverdueDeals,
    GetStuckDeals,
    GetDealDetails,
    GetDealNotes,
)
from ..tools.task_tools import GetTasks, GetOverdueTasks
from ..tools.employee_tools import GetEmployees, GetEmployeeDetails
from ..observability.metrics import MetricsTracker
from .prompts import build_system_prompt
from ...backend.integrations.llm_client import get_llm_client

logger = logging.getLogger(__name__)


@dataclass
class StreamChunk:
    """Chunk of streamed response."""
    type: str  # "text", "tool_call", "tool_result", "done"
    content: Optional[str] = None
    tool_name: Optional[str] = None
    tool_result: Optional[dict] = None


class OmniousAgent:
    """The all-knowing Omnious agent for Command Center."""

    def __init__(self):
        """Initialize the agent."""
        self.llm = get_llm_client()
        self.tools = ToolRegistry()
        self.metrics = MetricsTracker()
        self.conversation_history: List[dict] = []

        # Register all tools
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all available tools."""
        # Pipeline tools
        self.tools.register(GetOverdueDeals())
        self.tools.register(GetStuckDeals())
        self.tools.register(GetDealDetails())
        self.tools.register(GetDealNotes())

        # Task tools
        self.tools.register(GetTasks())
        self.tools.register(GetOverdueTasks())

        # Employee tools
        self.tools.register(GetEmployees())
        self.tools.register(GetEmployeeDetails())

    def _build_messages(self, user_input: str) -> List[dict]:
        """Build messages array for LLM.

        Args:
            user_input: User's message

        Returns:
            Messages array for OpenRouter API
        """
        messages = [
            {"role": "system", "content": build_system_prompt()}
        ]

        # Add conversation history
        messages.extend(self.conversation_history)

        # Add current user message
        messages.append({"role": "user", "content": user_input})

        return messages

    def _add_to_history(self, role: str, content: str) -> None:
        """Add message to conversation history.

        Args:
            role: Message role (user, assistant, tool)
            content: Message content
        """
        self.conversation_history.append({"role": role, "content": content})

    def clear_conversation(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []

    async def _process_tool_calls(self, tool_calls: List[dict]) -> List[dict]:
        """Process tool calls and return results.

        Args:
            tool_calls: List of tool call objects from LLM

        Returns:
            List of tool result messages
        """
        results = []

        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])

            logger.info(f"Executing tool: {tool_name} with args: {arguments}")

            # Execute the tool
            result = self.tools.execute(tool_name, arguments)

            # Format result for LLM
            if result.success:
                content = json.dumps(result.data)
            else:
                content = json.dumps({"error": result.error})

            results.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": content,
            })

        return results

    async def chat(self, user_input: str) -> str:
        """Send a message and get a response.

        Args:
            user_input: User's message

        Returns:
            Agent's response
        """
        # Build messages
        messages = self._build_messages(user_input)

        # Add user message to history
        self._add_to_history("user", user_input)

        # Make API call with tools
        response = await self._call_llm_with_tools(messages)

        # Add assistant response to history
        self._add_to_history("assistant", response)

        return response

    async def _call_llm_with_tools(self, messages: List[dict], max_iterations: int = 10) -> str:
        """Call LLM with tools, handling tool calls in a loop.

        Args:
            messages: Messages for the LLM
            max_iterations: Maximum tool calling iterations

        Returns:
            Final text response
        """
        import httpx

        for iteration in range(max_iterations):
            # Call OpenRouter API
            headers = {
                "Authorization": f"Bearer {self.llm.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.llm.model,
                "messages": messages,
                "tools": self.tools.get_tools_schema(),
                "tool_choice": "auto",
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.llm.api_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            # Track tokens
            if "usage" in data:
                self.metrics.track(
                    data["usage"].get("prompt_tokens", 0),
                    data["usage"].get("completion_tokens", 0),
                )

            # Get the assistant message
            assistant_message = data["choices"][0]["message"]

            # Check for tool calls
            if "tool_calls" in assistant_message and assistant_message["tool_calls"]:
                # Add assistant message with tool calls to messages
                messages.append(assistant_message)

                # Process tool calls
                tool_results = await self._process_tool_calls(assistant_message["tool_calls"])

                # Add tool results to messages
                messages.extend(tool_results)

                # Continue loop to get final response
                continue

            # No tool calls - return the text response
            return assistant_message.get("content", "")

        return "I apologize, but I wasn't able to complete the request after several attempts."

    async def chat_stream(self, user_input: str) -> AsyncIterator[StreamChunk]:
        """Send a message and stream the response.

        Args:
            user_input: User's message

        Yields:
            StreamChunk objects as response is generated
        """
        # Build messages
        messages = self._build_messages(user_input)

        # Add user message to history
        self._add_to_history("user", user_input)

        accumulated_text = ""

        # Stream with tool handling
        async for chunk in self._stream_with_tools(messages):
            yield chunk
            if chunk.type == "text" and chunk.content:
                accumulated_text += chunk.content

        # Add complete response to history
        if accumulated_text:
            self._add_to_history("assistant", accumulated_text)

        yield StreamChunk(type="done")

    async def _stream_with_tools(self, messages: List[dict], max_iterations: int = 10) -> AsyncIterator[StreamChunk]:
        """Stream response with tool handling.

        Args:
            messages: Messages for the LLM
            max_iterations: Maximum tool calling iterations

        Yields:
            StreamChunk objects
        """
        import httpx

        for iteration in range(max_iterations):
            headers = {
                "Authorization": f"Bearer {self.llm.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.llm.model,
                "messages": messages,
                "tools": self.tools.get_tools_schema(),
                "tool_choice": "auto",
                "stream": True,
            }

            accumulated_content = ""
            accumulated_tool_calls = []
            current_tool_call = None

            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.llm.api_url}/chat/completions",
                    headers=headers,
                    json=payload,
                ) as response:
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue

                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        if "choices" not in data or not data["choices"]:
                            continue

                        delta = data["choices"][0].get("delta", {})

                        # Handle text content
                        if "content" in delta and delta["content"]:
                            yield StreamChunk(type="text", content=delta["content"])
                            accumulated_content += delta["content"]

                        # Handle tool calls
                        if "tool_calls" in delta:
                            for tc in delta["tool_calls"]:
                                idx = tc.get("index", 0)

                                # Ensure we have enough slots
                                while len(accumulated_tool_calls) <= idx:
                                    accumulated_tool_calls.append({
                                        "id": "",
                                        "type": "function",
                                        "function": {"name": "", "arguments": ""}
                                    })

                                if "id" in tc:
                                    accumulated_tool_calls[idx]["id"] = tc["id"]
                                if "function" in tc:
                                    if "name" in tc["function"]:
                                        accumulated_tool_calls[idx]["function"]["name"] = tc["function"]["name"]
                                        yield StreamChunk(type="tool_call", tool_name=tc["function"]["name"])
                                    if "arguments" in tc["function"]:
                                        accumulated_tool_calls[idx]["function"]["arguments"] += tc["function"]["arguments"]

            # If we have tool calls, process them
            if accumulated_tool_calls:
                # Add assistant message with tool calls
                assistant_msg = {
                    "role": "assistant",
                    "content": accumulated_content or None,
                    "tool_calls": accumulated_tool_calls,
                }
                messages.append(assistant_msg)

                # Process and yield tool results
                for tool_call in accumulated_tool_calls:
                    tool_name = tool_call["function"]["name"]
                    arguments = json.loads(tool_call["function"]["arguments"])

                    result = self.tools.execute(tool_name, arguments)

                    if result.success:
                        content = json.dumps(result.data)
                    else:
                        content = json.dumps({"error": result.error})

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": content,
                    })

                    yield StreamChunk(
                        type="tool_result",
                        tool_name=tool_name,
                        tool_result=result.data if result.success else {"error": result.error}
                    )

                # Continue loop for next response
                continue

            # No tool calls - we're done
            break


# Singleton instance
_agent: Optional[OmniousAgent] = None


def get_agent() -> OmniousAgent:
    """Get or create agent singleton."""
    global _agent
    if _agent is None:
        _agent = OmniousAgent()
    return _agent
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/agent/test_agent_core.py -v`
Expected: PASS (8 tests)

**Step 5: Commit**

```bash
git add cmd_center/agent/core/agent.py tests/agent/test_agent_core.py
git commit -m "feat(agent): implement OmniousAgent core with tool calling"
```

---

## Task 9: Implement Agent TUI Screen

**Files:**
- Create: `cmd_center/screens/agent_screen.py`

**Step 1: Create the agent screen**

Create `cmd_center/screens/agent_screen.py`:
```python
"""Agent chat screen for Omnious."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Static, Input, Footer
from textual import log

from ..agent import get_agent


class MessageWidget(Static):
    """Widget for displaying a chat message."""

    DEFAULT_CSS = """
    MessageWidget {
        padding: 1;
        margin: 0 1;
    }

    MessageWidget.user {
        background: $primary-darken-2;
        border: solid $primary;
    }

    MessageWidget.assistant {
        background: $surface;
        border: solid $secondary;
    }
    """

    def __init__(self, role: str, content: str = ""):
        super().__init__(content)
        self.role = role
        self.add_class(role)


class AgentScreen(Screen):
    """Chat screen for Omnious agent."""

    CSS = """
    AgentScreen {
        layout: vertical;
    }

    #header {
        height: 3;
        background: $primary;
        color: $text;
        text-align: center;
        padding: 1;
    }

    #metrics {
        dock: right;
        width: auto;
        padding: 0 2;
    }

    #chat-container {
        height: 1fr;
        border: solid $primary;
    }

    #status-bar {
        height: 1;
        background: $surface-darken-1;
        color: $text-muted;
        padding: 0 1;
    }

    #input-container {
        height: 3;
        padding: 0 1;
    }

    #chat-input {
        width: 100%;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("ctrl+l", "clear_chat", "Clear"),
    ]

    def __init__(self):
        super().__init__()
        self.agent = get_agent()
        self._current_message: MessageWidget | None = None

    def compose(self) -> ComposeResult:
        yield Static("Omnious - The All-Knowing AI", id="header")
        yield Static(self.agent.metrics.format_display(), id="metrics")

        with VerticalScroll(id="chat-container"):
            # Welcome message
            yield MessageWidget(
                "assistant",
                "Greetings! The all-knowing Omnious is at your service. "
                "What would you like to know about today?"
            )

        yield Static("Ready", id="status-bar")

        with Vertical(id="input-container"):
            yield Input(placeholder="Ask Omnious anything...", id="chat-input")

        yield Footer()

    def on_mount(self) -> None:
        """Focus input on mount."""
        self.query_one("#chat-input", Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission."""
        user_input = event.value.strip()
        if not user_input:
            return

        # Clear input
        event.input.value = ""

        # Add user message
        chat = self.query_one("#chat-container", VerticalScroll)
        chat.mount(MessageWidget("user", user_input))

        # Create assistant message placeholder
        self._current_message = MessageWidget("assistant", "")
        chat.mount(self._current_message)

        # Update status
        self._set_status("Thinking...")

        # Stream response
        try:
            async for chunk in self.agent.chat_stream(user_input):
                if chunk.type == "text" and chunk.content:
                    self._append_to_current(chunk.content)
                elif chunk.type == "tool_call":
                    self._set_status(f"Using {chunk.tool_name}...")
                elif chunk.type == "done":
                    self._set_status("Ready")
                    self._update_metrics()
        except Exception as e:
            log(f"Error in chat: {e}")
            self._append_to_current(f"\n\nError: {str(e)[:100]}")
            self._set_status("Error")

        # Scroll to bottom
        chat.scroll_end()

    def _append_to_current(self, text: str) -> None:
        """Append text to current message."""
        if self._current_message:
            current = str(self._current_message.renderable)
            self._current_message.update(current + text)

    def _set_status(self, status: str) -> None:
        """Update status bar."""
        self.query_one("#status-bar", Static).update(status)

    def _update_metrics(self) -> None:
        """Update metrics display."""
        self.query_one("#metrics", Static).update(
            self.agent.metrics.format_display()
        )

    def action_go_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()

    def action_clear_chat(self) -> None:
        """Clear chat history."""
        self.agent.clear_conversation()
        chat = self.query_one("#chat-container", VerticalScroll)

        # Remove all messages except welcome
        for widget in list(chat.query(MessageWidget)):
            widget.remove()

        # Add fresh welcome
        chat.mount(MessageWidget(
            "assistant",
            "Chat cleared! The all-knowing Omnious awaits your questions."
        ))

        self.agent.metrics.reset()
        self._update_metrics()
```

**Step 2: Test manually**

Run the app and navigate to the agent screen to test:
```bash
python -m cmd_center.main
# Press 'i' to open agent (if binding added) or navigate manually
```

**Step 3: Commit**

```bash
git add cmd_center/screens/agent_screen.py
git commit -m "feat(agent): add TUI chat screen for Omnious"
```

---

## Task 10: Wire Up Agent Screen to App

**Files:**
- Modify: `cmd_center/app.py` (or main app file)

**Step 1: Add import and binding**

Add to the main app file:
```python
from .screens.agent_screen import AgentScreen

# In BINDINGS:
("i", "open_agent", "Omnious"),

# Add action:
def action_open_agent(self) -> None:
    """Open Omnious agent screen."""
    self.push_screen(AgentScreen())
```

**Step 2: Test the integration**

Run: `python -m cmd_center.main`
Press: `i` to open Omnious
Test: Ask "What deals need attention?"

**Step 3: Commit**

```bash
git add cmd_center/app.py
git commit -m "feat(agent): wire up Omnious screen with 'i' keybinding"
```

---

## Task 11: Run Full Test Suite

**Step 1: Run all agent tests**

```bash
pytest tests/agent/ -v
```

Expected: All tests pass

**Step 2: Run full test suite**

```bash
pytest tests/ -v
```

Expected: All tests pass (including existing tests)

**Step 3: Final commit if needed**

```bash
git add -A
git commit -m "feat(agent): complete Phase 1 of Omnious agent"
```

---

## Summary

Phase 1 delivers:
- **Agent Core**: ReAct loop with OpenRouter tool calling
- **System Prompt**: Omnious persona with boundaries
- **Tool System**: Base classes + registry with OpenAI schema
- **6 Read Tools**: overdue/stuck deals, deal details/notes, tasks, employees
- **TUI Screen**: Chat interface with streaming
- **Metrics**: Token/cost tracking in header

Total new files: ~15
Total new tests: ~40
Estimated effort: 8-10 focused tasks

---

## Next Phase Preview

Phase 2 will add:
- More read tools (cashflow, emails, knowledge base)
- Conversation persistence (SQLModel tables)
- Knowledge base markdown files
