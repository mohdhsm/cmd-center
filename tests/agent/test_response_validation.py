"""Response validation contract tests.

These tests validate:
1. API response parsing and validation
2. Error response handling
3. Streaming response format compliance
4. Tool call response validation
5. Edge cases in response handling
"""

import pytest
import json
from dataclasses import asdict

from cmd_center.agent.core.agent import StreamChunk, OmniousAgent
from cmd_center.agent.tools.base import ToolResult


class TestResponseParsingContract:
    """Contract tests for API response parsing."""

    def test_parse_valid_text_response(self):
        """Valid text response can be parsed."""
        response_data = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "anthropic/claude-sonnet-4",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello, how can I help you?"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 10,
                "total_tokens": 60
            }
        }

        # Validate structure
        assert "choices" in response_data
        assert len(response_data["choices"]) == 1
        assert response_data["choices"][0]["message"]["role"] == "assistant"
        assert response_data["choices"][0]["message"]["content"] is not None
        assert response_data["choices"][0]["finish_reason"] == "stop"

    def test_parse_tool_call_response(self):
        """Tool call response can be parsed correctly."""
        response_data = {
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_abc123",
                                "type": "function",
                                "function": {
                                    "name": "get_overdue_deals",
                                    "arguments": '{"pipeline": "aramco", "min_days": 7}'
                                }
                            }
                        ]
                    },
                    "finish_reason": "tool_calls"
                }
            ]
        }

        message = response_data["choices"][0]["message"]
        assert message["content"] is None
        assert "tool_calls" in message
        assert len(message["tool_calls"]) == 1

        tool_call = message["tool_calls"][0]
        assert tool_call["id"] == "call_abc123"
        assert tool_call["type"] == "function"
        assert tool_call["function"]["name"] == "get_overdue_deals"

        # Validate arguments can be parsed as JSON
        args = json.loads(tool_call["function"]["arguments"])
        assert args["pipeline"] == "aramco"
        assert args["min_days"] == 7

    def test_parse_multiple_tool_calls(self):
        """Multiple tool calls in single response can be parsed."""
        response_data = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "get_overdue_deals",
                                    "arguments": "{}"
                                }
                            },
                            {
                                "id": "call_2",
                                "type": "function",
                                "function": {
                                    "name": "get_stuck_deals",
                                    "arguments": "{}"
                                }
                            }
                        ]
                    }
                }
            ]
        }

        tool_calls = response_data["choices"][0]["message"]["tool_calls"]
        assert len(tool_calls) == 2
        assert tool_calls[0]["function"]["name"] == "get_overdue_deals"
        assert tool_calls[1]["function"]["name"] == "get_stuck_deals"

    def test_parse_response_with_usage_metrics(self):
        """Usage metrics in response can be extracted."""
        response_data = {
            "choices": [{"message": {"content": "Hello"}}],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }

        usage = response_data["usage"]
        assert usage["prompt_tokens"] == 100
        assert usage["completion_tokens"] == 50
        assert usage["total_tokens"] == 150

    def test_parse_response_without_usage(self):
        """Response without usage metrics is valid."""
        response_data = {
            "choices": [{"message": {"content": "Hello"}}]
        }

        # No usage key - should be handled gracefully
        assert "usage" not in response_data
        usage = response_data.get("usage", {})
        assert usage.get("prompt_tokens", 0) == 0


class TestErrorResponseContract:
    """Contract tests for error response handling."""

    def test_rate_limit_error_structure(self):
        """Rate limit error (429) has expected structure."""
        error_response = {
            "error": {
                "message": "Rate limit exceeded",
                "type": "rate_limit_error",
                "code": 429
            }
        }

        assert "error" in error_response
        assert error_response["error"]["code"] == 429
        assert "rate" in error_response["error"]["type"].lower()

    def test_authentication_error_structure(self):
        """Authentication error (401) has expected structure."""
        error_response = {
            "error": {
                "message": "Invalid API key",
                "type": "authentication_error",
                "code": 401
            }
        }

        assert error_response["error"]["code"] == 401
        assert "authentication" in error_response["error"]["type"].lower()

    def test_model_not_found_error_structure(self):
        """Model not found error has expected structure."""
        error_response = {
            "error": {
                "message": "Model 'unknown-model' not found",
                "type": "invalid_request_error",
                "code": 404
            }
        }

        assert error_response["error"]["code"] == 404

    def test_context_length_exceeded_structure(self):
        """Context length exceeded error has expected structure."""
        error_response = {
            "error": {
                "message": "Context length exceeded. Maximum is 128000 tokens.",
                "type": "invalid_request_error",
                "code": 400
            }
        }

        assert "context" in error_response["error"]["message"].lower()


class TestStreamingChunkContract:
    """Contract tests for streaming chunk format."""

    def test_text_delta_chunk_format(self):
        """Text delta chunk has correct format."""
        chunk_data = {
            "id": "chatcmpl-123",
            "object": "chat.completion.chunk",
            "created": 1234567890,
            "model": "anthropic/claude-sonnet-4",
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

        assert chunk_data["object"] == "chat.completion.chunk"
        delta = chunk_data["choices"][0]["delta"]
        assert "content" in delta
        assert delta["content"] == "Hello"

    def test_role_delta_chunk_format(self):
        """First chunk with role has correct format."""
        chunk_data = {
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "role": "assistant"
                    },
                    "finish_reason": None
                }
            ]
        }

        delta = chunk_data["choices"][0]["delta"]
        assert delta["role"] == "assistant"
        assert "content" not in delta

    def test_tool_call_delta_chunk_format(self):
        """Tool call delta chunk has correct format."""
        chunk_data = {
            "choices": [
                {
                    "index": 0,
                    "delta": {
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "call_abc",
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

        delta = chunk_data["choices"][0]["delta"]
        assert "tool_calls" in delta
        tc = delta["tool_calls"][0]
        assert tc["index"] == 0
        assert tc["function"]["name"] == "get_deals"

    def test_tool_call_arguments_streaming(self):
        """Tool call arguments are streamed incrementally."""
        chunks = [
            {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": '{"pip'}}]}}]},
            {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": 'eline":'}}]}}]},
            {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": '"aramco"}'}}]}}]},
        ]

        # Simulate accumulating arguments
        accumulated_args = ""
        for chunk in chunks:
            args_delta = chunk["choices"][0]["delta"]["tool_calls"][0]["function"]["arguments"]
            accumulated_args += args_delta

        assert accumulated_args == '{"pipeline":"aramco"}'
        parsed = json.loads(accumulated_args)
        assert parsed["pipeline"] == "aramco"

    def test_finish_reason_stop_chunk(self):
        """Final chunk with finish_reason=stop."""
        chunk_data = {
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }
            ]
        }

        assert chunk_data["choices"][0]["finish_reason"] == "stop"
        assert chunk_data["choices"][0]["delta"] == {}

    def test_finish_reason_tool_calls_chunk(self):
        """Final chunk with finish_reason=tool_calls."""
        chunk_data = {
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "tool_calls"
                }
            ]
        }

        assert chunk_data["choices"][0]["finish_reason"] == "tool_calls"


class TestToolMessageContract:
    """Contract tests for tool message format."""

    def test_tool_result_message_format(self):
        """Tool result message has correct format."""
        tool_result_message = {
            "role": "tool",
            "tool_call_id": "call_abc123",
            "content": '{"deals": [{"id": 1, "title": "Test Deal"}]}'
        }

        assert tool_result_message["role"] == "tool"
        assert tool_result_message["tool_call_id"] == "call_abc123"

        # Content should be valid JSON
        content = json.loads(tool_result_message["content"])
        assert "deals" in content

    def test_tool_error_result_format(self):
        """Tool error result has correct format."""
        tool_result_message = {
            "role": "tool",
            "tool_call_id": "call_abc123",
            "content": '{"error": "Deal not found"}'
        }

        content = json.loads(tool_result_message["content"])
        assert "error" in content
        assert content["error"] == "Deal not found"

    def test_assistant_with_tool_calls_format(self):
        """Assistant message with tool_calls has correct format."""
        assistant_message = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_abc",
                    "type": "function",
                    "function": {
                        "name": "get_deal_details",
                        "arguments": '{"deal_id": 123}'
                    }
                }
            ]
        }

        assert assistant_message["role"] == "assistant"
        assert assistant_message["content"] is None
        assert len(assistant_message["tool_calls"]) == 1


class TestStreamChunkDataclass:
    """Contract tests for StreamChunk dataclass serialization."""

    def test_stream_chunk_to_dict(self):
        """StreamChunk can be converted to dict."""
        chunk = StreamChunk(type="text", content="Hello")
        chunk_dict = asdict(chunk)

        assert chunk_dict["type"] == "text"
        assert chunk_dict["content"] == "Hello"
        assert chunk_dict["tool_name"] is None

    def test_stream_chunk_default_values(self):
        """StreamChunk has correct default values."""
        chunk = StreamChunk(type="done")

        assert chunk.content is None
        assert chunk.tool_name is None
        assert chunk.tool_args is None
        assert chunk.tool_result is None
        assert chunk.error is None

    def test_stream_chunk_equality(self):
        """StreamChunk equality works correctly."""
        chunk1 = StreamChunk(type="text", content="Hello")
        chunk2 = StreamChunk(type="text", content="Hello")
        chunk3 = StreamChunk(type="text", content="World")

        assert chunk1 == chunk2
        assert chunk1 != chunk3

    def test_all_chunk_types_serializable(self):
        """All StreamChunk types can be serialized."""
        chunks = [
            StreamChunk(type="text", content="Hello"),
            StreamChunk(type="tool_call", tool_name="get_deals", tool_args={"limit": 10}),
            StreamChunk(type="tool_result", tool_name="get_deals", tool_result={"deals": []}),
            StreamChunk(type="error", error="Something went wrong"),
            StreamChunk(type="done"),
        ]

        for chunk in chunks:
            chunk_dict = asdict(chunk)
            assert isinstance(chunk_dict, dict)
            assert chunk_dict["type"] == chunk.type


class TestToolResultValidation:
    """Contract tests for ToolResult validation."""

    def test_tool_result_success_format(self):
        """Successful ToolResult has correct format."""
        result = ToolResult(success=True, data={"deals": [], "count": 0})

        assert result.success is True
        assert isinstance(result.data, dict)
        assert result.error is None

    def test_tool_result_error_format(self):
        """Error ToolResult has correct format."""
        result = ToolResult(success=False, error="Service unavailable")

        assert result.success is False
        assert result.error == "Service unavailable"
        assert result.data is None

    def test_tool_result_data_is_json_serializable(self):
        """ToolResult data must be JSON serializable."""
        result = ToolResult(
            success=True,
            data={
                "deals": [
                    {"id": 1, "title": "Deal 1", "value": 50000.0},
                    {"id": 2, "title": "Deal 2", "value": 75000.0}
                ],
                "count": 2,
                "pipeline": "aramco"
            }
        )

        # Should not raise
        json_str = json.dumps(result.data)
        parsed = json.loads(json_str)
        assert parsed["count"] == 2

    def test_tool_result_with_nested_data(self):
        """ToolResult with nested data structures."""
        result = ToolResult(
            success=True,
            data={
                "employee": {
                    "id": 1,
                    "name": "John Doe",
                    "skills": [
                        {"name": "Python", "rating": 4},
                        {"name": "SQL", "rating": 3}
                    ]
                }
            }
        )

        assert result.data["employee"]["skills"][0]["name"] == "Python"


class TestMessageArrayContract:
    """Contract tests for message array format sent to API."""

    def test_message_array_structure(self):
        """Message array has correct structure."""
        agent = OmniousAgent()
        messages = agent._build_messages("Hello")

        # Must be a list
        assert isinstance(messages, list)

        # First must be system
        assert messages[0]["role"] == "system"

        # Last must be user
        assert messages[-1]["role"] == "user"

    def test_all_messages_have_required_fields(self):
        """All messages have role and content fields."""
        agent = OmniousAgent()
        agent._add_to_history("user", "Previous message")
        agent._add_to_history("assistant", "Previous response")
        messages = agent._build_messages("New message")

        for msg in messages:
            assert "role" in msg
            assert "content" in msg
            assert msg["role"] in ["system", "user", "assistant"]

    def test_message_roles_alternate_correctly(self):
        """User and assistant messages alternate after system."""
        agent = OmniousAgent()
        agent._add_to_history("user", "Q1")
        agent._add_to_history("assistant", "A1")
        agent._add_to_history("user", "Q2")
        agent._add_to_history("assistant", "A2")
        messages = agent._build_messages("Q3")

        # After system, should alternate
        roles = [m["role"] for m in messages[1:]]
        assert roles == ["user", "assistant", "user", "assistant", "user"]

    def test_system_message_substantial(self):
        """System message contains substantial prompt."""
        agent = OmniousAgent()
        messages = agent._build_messages("Hello")

        system_content = messages[0]["content"]
        assert len(system_content) > 100
        assert "Omnious" in system_content or "agent" in system_content.lower()
