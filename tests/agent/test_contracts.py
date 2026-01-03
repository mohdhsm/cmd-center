"""Contract tests for agent response validation.

These tests validate:
1. StreamChunk dataclass structure and valid types
2. OpenAI-compatible API response format expectations
3. Tool call/result format compliance
4. Message format contracts
"""

import pytest
from dataclasses import fields

from cmd_center.agent.core.agent import StreamChunk, OmniousAgent


class TestStreamChunkContract:
    """Contract tests for StreamChunk dataclass."""

    VALID_TYPES = {"text", "tool_call", "tool_result", "error", "done"}

    def test_has_required_type_field(self):
        """StreamChunk must have a type field."""
        field_names = [f.name for f in fields(StreamChunk)]
        assert "type" in field_names

    def test_has_content_field(self):
        """StreamChunk must have content field for text."""
        field_names = [f.name for f in fields(StreamChunk)]
        assert "content" in field_names

    def test_has_tool_name_field(self):
        """StreamChunk must have tool_name field for tool calls."""
        field_names = [f.name for f in fields(StreamChunk)]
        assert "tool_name" in field_names

    def test_has_tool_args_field(self):
        """StreamChunk must have tool_args field for tool calls."""
        field_names = [f.name for f in fields(StreamChunk)]
        assert "tool_args" in field_names

    def test_has_tool_result_field(self):
        """StreamChunk must have tool_result field for tool results."""
        field_names = [f.name for f in fields(StreamChunk)]
        assert "tool_result" in field_names

    def test_has_error_field(self):
        """StreamChunk must have error field for errors."""
        field_names = [f.name for f in fields(StreamChunk)]
        assert "error" in field_names

    @pytest.mark.parametrize("chunk_type", ["text", "tool_call", "tool_result", "error", "done"])
    def test_valid_type_values(self, chunk_type):
        """StreamChunk accepts all valid type values."""
        chunk = StreamChunk(type=chunk_type)
        assert chunk.type == chunk_type

    def test_text_chunk_contract(self):
        """Text chunk must have type='text' and content."""
        chunk = StreamChunk(type="text", content="Hello world")
        assert chunk.type == "text"
        assert chunk.content == "Hello world"
        assert chunk.tool_name is None
        assert chunk.error is None

    def test_tool_call_chunk_contract(self):
        """Tool call chunk must have type='tool_call' and tool_name."""
        chunk = StreamChunk(type="tool_call", tool_name="get_deals", tool_args={"limit": 10})
        assert chunk.type == "tool_call"
        assert chunk.tool_name == "get_deals"
        assert chunk.tool_args == {"limit": 10}

    def test_tool_result_chunk_contract(self):
        """Tool result chunk must have type='tool_result' and tool_result."""
        chunk = StreamChunk(
            type="tool_result",
            tool_name="get_deals",
            tool_result={"deals": [{"id": 1}]}
        )
        assert chunk.type == "tool_result"
        assert chunk.tool_name == "get_deals"
        assert chunk.tool_result == {"deals": [{"id": 1}]}

    def test_error_chunk_contract(self):
        """Error chunk must have type='error' and error message."""
        chunk = StreamChunk(type="error", error="API timeout")
        assert chunk.type == "error"
        assert chunk.error == "API timeout"
        assert chunk.content is None

    def test_done_chunk_contract(self):
        """Done chunk signals stream completion."""
        chunk = StreamChunk(type="done")
        assert chunk.type == "done"
        assert chunk.content is None


class TestMessageFormatContract:
    """Contract tests for message format sent to API."""

    def test_build_messages_returns_list(self):
        """_build_messages must return a list."""
        agent = OmniousAgent()
        messages = agent._build_messages("Hello")
        assert isinstance(messages, list)

    def test_messages_have_role_field(self):
        """All messages must have a role field."""
        agent = OmniousAgent()
        messages = agent._build_messages("Hello")
        for msg in messages:
            assert "role" in msg

    def test_messages_have_content_field(self):
        """All messages must have a content field."""
        agent = OmniousAgent()
        messages = agent._build_messages("Hello")
        for msg in messages:
            assert "content" in msg

    def test_first_message_is_system(self):
        """First message must be system prompt."""
        agent = OmniousAgent()
        messages = agent._build_messages("Hello")
        assert messages[0]["role"] == "system"
        assert len(messages[0]["content"]) > 100  # System prompt should be substantial

    def test_last_message_is_user(self):
        """Last message must be user message."""
        agent = OmniousAgent()
        messages = agent._build_messages("Hello")
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "Hello"

    def test_conversation_history_included(self):
        """Conversation history must be included in messages."""
        agent = OmniousAgent()
        agent._add_to_history("user", "Previous question")
        agent._add_to_history("assistant", "Previous answer")

        messages = agent._build_messages("New question")

        # Should have: system, prev_user, prev_assistant, new_user
        assert len(messages) == 4
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Previous question"
        assert messages[2]["role"] == "assistant"
        assert messages[2]["content"] == "Previous answer"


class TestToolSchemaContract:
    """Contract tests for OpenAI tool schema format."""

    def test_tools_schema_is_list(self):
        """Tools schema must be a list."""
        agent = OmniousAgent()
        schemas = agent.tools.get_tools_schema()
        assert isinstance(schemas, list)

    def test_each_tool_has_type_function(self):
        """Each tool schema must have type='function'."""
        agent = OmniousAgent()
        schemas = agent.tools.get_tools_schema()
        for schema in schemas:
            assert schema["type"] == "function"

    def test_each_tool_has_function_object(self):
        """Each tool schema must have a function object."""
        agent = OmniousAgent()
        schemas = agent.tools.get_tools_schema()
        for schema in schemas:
            assert "function" in schema
            assert isinstance(schema["function"], dict)

    def test_function_has_name(self):
        """Each function must have a name."""
        agent = OmniousAgent()
        schemas = agent.tools.get_tools_schema()
        for schema in schemas:
            assert "name" in schema["function"]
            assert isinstance(schema["function"]["name"], str)
            assert len(schema["function"]["name"]) > 0

    def test_function_has_description(self):
        """Each function must have a description."""
        agent = OmniousAgent()
        schemas = agent.tools.get_tools_schema()
        for schema in schemas:
            assert "description" in schema["function"]
            assert isinstance(schema["function"]["description"], str)
            assert len(schema["function"]["description"]) > 10

    def test_function_has_parameters(self):
        """Each function must have parameters object."""
        agent = OmniousAgent()
        schemas = agent.tools.get_tools_schema()
        for schema in schemas:
            assert "parameters" in schema["function"]
            params = schema["function"]["parameters"]
            assert params["type"] == "object"
            assert "properties" in params

    def test_parameters_required_field_if_present_is_list(self):
        """If required field exists, it must be a list."""
        agent = OmniousAgent()
        schemas = agent.tools.get_tools_schema()
        for schema in schemas:
            params = schema["function"]["parameters"]
            # required field is optional in OpenAI format (omitted when all params have defaults)
            if "required" in params:
                assert isinstance(params["required"], list)


class TestToolResultContract:
    """Contract tests for tool execution results."""

    def test_tool_result_has_success_field(self):
        """ToolResult must have success field."""
        from cmd_center.agent.tools.base import ToolResult
        result = ToolResult(success=True, data={"test": 1})
        assert hasattr(result, "success")

    def test_tool_result_has_data_field(self):
        """ToolResult must have data field."""
        from cmd_center.agent.tools.base import ToolResult
        result = ToolResult(success=True, data={"test": 1})
        assert hasattr(result, "data")

    def test_tool_result_has_error_field(self):
        """ToolResult must have error field."""
        from cmd_center.agent.tools.base import ToolResult
        result = ToolResult(success=False, error="Failed")
        assert hasattr(result, "error")

    def test_success_result_has_data(self):
        """Successful result must have data."""
        from cmd_center.agent.tools.base import ToolResult
        result = ToolResult(success=True, data={"deals": []})
        assert result.success is True
        assert result.data is not None
        assert result.error is None

    def test_error_result_has_error_message(self):
        """Error result must have error message."""
        from cmd_center.agent.tools.base import ToolResult
        result = ToolResult(success=False, error="Not found")
        assert result.success is False
        assert result.error == "Not found"

    def test_execute_returns_tool_result(self):
        """Tool execute must return ToolResult."""
        from cmd_center.agent.tools.base import ToolResult
        agent = OmniousAgent()
        result = agent.tools.execute("get_overdue_deals", {})
        assert isinstance(result, ToolResult)

    def test_execute_unknown_tool_returns_error(self):
        """Executing unknown tool returns error result."""
        from cmd_center.agent.tools.base import ToolResult
        agent = OmniousAgent()
        result = agent.tools.execute("nonexistent_tool", {})
        assert isinstance(result, ToolResult)
        assert result.success is False
        assert "not found" in result.error.lower()


class TestOpenAIResponseContract:
    """Contract tests for expected OpenAI API response format.

    These tests validate the structure we expect from OpenRouter/OpenAI responses.
    """

    def test_expected_response_structure(self):
        """Document expected response structure."""
        # This is a documentation test showing expected format
        expected_response = {
            "id": "chatcmpl-xxx",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "anthropic/claude-3.5-sonnet",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello!",
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }

        # Validate structure
        assert "choices" in expected_response
        assert len(expected_response["choices"]) > 0
        assert "message" in expected_response["choices"][0]
        assert "usage" in expected_response

    def test_expected_tool_call_response_structure(self):
        """Document expected tool call response structure."""
        expected_response = {
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_xxx",
                                "type": "function",
                                "function": {
                                    "name": "get_deals",
                                    "arguments": '{"limit": 10}'
                                }
                            }
                        ]
                    },
                    "finish_reason": "tool_calls"
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
            }
        }

        # Validate tool call structure
        message = expected_response["choices"][0]["message"]
        assert "tool_calls" in message
        tool_call = message["tool_calls"][0]
        assert "id" in tool_call
        assert "function" in tool_call
        assert "name" in tool_call["function"]
        assert "arguments" in tool_call["function"]

    def test_expected_streaming_chunk_structure(self):
        """Document expected streaming chunk structure."""
        # Text delta chunk
        text_chunk = {
            "id": "chatcmpl-xxx",
            "object": "chat.completion.chunk",
            "created": 1234567890,
            "model": "anthropic/claude-3.5-sonnet",
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "content": "Hello"
                    },
                    "finish_reason": None
                }
            ]
        }

        assert "choices" in text_chunk
        assert "delta" in text_chunk["choices"][0]
        assert "content" in text_chunk["choices"][0]["delta"]

    def test_expected_streaming_tool_call_chunk(self):
        """Document expected streaming tool call chunk."""
        tool_chunk = {
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "call_xxx",
                                "type": "function",
                                "function": {
                                    "name": "get_deals",
                                    "arguments": ""
                                }
                            }
                        ]
                    },
                    "finish_reason": None
                }
            ]
        }

        delta = tool_chunk["choices"][0]["delta"]
        assert "tool_calls" in delta
        tc = delta["tool_calls"][0]
        assert "function" in tc
