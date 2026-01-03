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

    def test_parse_and_execute_success(self):
        """parse_and_execute parses arguments and executes."""
        tool = SampleTool()
        result = tool.parse_and_execute({"name": "test", "count": 5})
        assert result.success is True
        assert result.data["name"] == "test"

    def test_parse_and_execute_with_defaults(self):
        """parse_and_execute uses default values."""
        tool = SampleTool()
        result = tool.parse_and_execute({"name": "test"})
        assert result.success is True
        assert result.data["count"] == 10  # default value

    def test_parse_and_execute_validation_error(self):
        """parse_and_execute returns error on invalid params."""
        tool = SampleTool()
        result = tool.parse_and_execute({"count": 5})  # missing required 'name'
        assert result.success is False
        assert result.error is not None


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
