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
