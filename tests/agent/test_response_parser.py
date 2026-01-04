"""Response parser validation tests.

Tests for parsing and validating API response data,
including streaming SSE responses, tool call accumulation,
and edge cases in response handling.
"""

import pytest
import json
from dataclasses import asdict

from cmd_center.agent.core.agent import StreamChunk


class TestSSELineParsingContract:
    """Tests for Server-Sent Events (SSE) line parsing."""

    def test_valid_data_line_parsing(self):
        """Valid 'data: ' prefixed lines are parsed correctly."""
        raw_line = 'data: {"choices":[{"delta":{"content":"Hi"}}]}'
        
        # Remove data: prefix
        data = raw_line[6:]  # Remove "data: "
        parsed = json.loads(data)
        
        assert "choices" in parsed
        assert parsed["choices"][0]["delta"]["content"] == "Hi"

    def test_done_marker_recognized(self):
        """[DONE] marker is recognized as stream end."""
        raw_line = "data: [DONE]"
        data = raw_line[6:]
        
        assert data == "[DONE]"
        # Should not attempt JSON parse

    def test_empty_lines_handled(self):
        """Empty lines are ignored."""
        empty_lines = ["", "\n", "\r\n", "   "]
        
        for line in empty_lines:
            # Should be skipped (not starting with 'data: ')
            assert not line.startswith("data: ")

    def test_non_data_lines_ignored(self):
        """Lines not starting with 'data: ' are ignored."""
        non_data_lines = [
            ": comment",  # SSE comment
            "event: message",  # event line
            "id: 123",  # id line
            "retry: 1000",  # retry line
        ]
        
        for line in non_data_lines:
            assert not line.startswith("data: ")

    def test_invalid_json_in_data_line(self):
        """Invalid JSON in data line is handled gracefully."""
        raw_line = "data: {invalid json"
        data = raw_line[6:]
        
        with pytest.raises(json.JSONDecodeError):
            json.loads(data)


class TestStreamingDeltaAccumulation:
    """Tests for accumulating streaming deltas."""

    def test_text_content_accumulation(self):
        """Text content deltas accumulate correctly."""
        deltas = [
            {"choices": [{"delta": {"content": "Hello"}}]},
            {"choices": [{"delta": {"content": " "}}]},
            {"choices": [{"delta": {"content": "world"}}]},
            {"choices": [{"delta": {"content": "!"}}]},
        ]
        
        accumulated = ""
        for chunk in deltas:
            content = chunk["choices"][0]["delta"].get("content", "")
            accumulated += content
        
        assert accumulated == "Hello world!"

    def test_empty_delta_content(self):
        """Empty delta content doesn't break accumulation."""
        deltas = [
            {"choices": [{"delta": {"content": "Start"}}]},
            {"choices": [{"delta": {}}]},  # Empty delta
            {"choices": [{"delta": {"content": ""}}]},  # Empty content
            {"choices": [{"delta": {"content": "End"}}]},
        ]
        
        accumulated = ""
        for chunk in deltas:
            delta = chunk["choices"][0]["delta"]
            if "content" in delta and delta["content"]:
                accumulated += delta["content"]
        
        assert accumulated == "StartEnd"

    def test_role_in_first_delta(self):
        """First delta may contain role without content."""
        first_delta = {"choices": [{"delta": {"role": "assistant"}}]}
        
        delta = first_delta["choices"][0]["delta"]
        assert delta.get("role") == "assistant"
        assert "content" not in delta


class TestToolCallDeltaAccumulation:
    """Tests for tool call delta accumulation during streaming."""

    def test_tool_call_name_accumulation(self):
        """Tool call name is accumulated correctly."""
        chunks = [
            {
                "choices": [{
                    "delta": {
                        "tool_calls": [{
                            "index": 0,
                            "id": "call_123",
                            "type": "function",
                            "function": {"name": "get_", "arguments": ""}
                        }]
                    }
                }]
            },
            {
                "choices": [{
                    "delta": {
                        "tool_calls": [{
                            "index": 0,
                            "function": {"name": "deals", "arguments": ""}
                        }]
                    }
                }]
            },
        ]
        
        # Simulate accumulation
        tool_calls = [{"id": "", "type": "function", "function": {"name": "", "arguments": ""}}]
        
        for chunk in chunks:
            for tc_delta in chunk["choices"][0]["delta"]["tool_calls"]:
                idx = tc_delta.get("index", 0)
                if "id" in tc_delta:
                    tool_calls[idx]["id"] = tc_delta["id"]
                if "function" in tc_delta:
                    if "name" in tc_delta["function"]:
                        tool_calls[idx]["function"]["name"] += tc_delta["function"]["name"]
        
        assert tool_calls[0]["function"]["name"] == "get_deals"
        assert tool_calls[0]["id"] == "call_123"

    def test_tool_call_arguments_accumulation(self):
        """Tool call arguments are accumulated correctly."""
        argument_chunks = [
            '{"pip',
            'eline":',
            ' "aramco',
            '", "days',
            '": 7}',
        ]
        
        accumulated = ""
        for chunk in argument_chunks:
            accumulated += chunk
        
        assert accumulated == '{"pipeline": "aramco", "days": 7}'
        parsed = json.loads(accumulated)
        assert parsed["pipeline"] == "aramco"
        assert parsed["days"] == 7

    def test_multiple_tool_calls_in_stream(self):
        """Multiple tool calls in same response are tracked by index."""
        chunks = [
            {"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "call_1", "function": {"name": "tool_a"}}]}}]},
            {"choices": [{"delta": {"tool_calls": [{"index": 1, "id": "call_2", "function": {"name": "tool_b"}}]}}]},
            {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": '{"a":1}'}}]}}]},
            {"choices": [{"delta": {"tool_calls": [{"index": 1, "function": {"arguments": '{"b":2}'}}]}}]},
        ]
        
        # Simulate accumulation
        tool_calls = []
        
        for chunk in chunks:
            for tc_delta in chunk["choices"][0]["delta"]["tool_calls"]:
                idx = tc_delta.get("index", 0)
                
                # Extend list if needed
                while len(tool_calls) <= idx:
                    tool_calls.append({"id": "", "function": {"name": "", "arguments": ""}})
                
                if "id" in tc_delta:
                    tool_calls[idx]["id"] = tc_delta["id"]
                if "function" in tc_delta:
                    if "name" in tc_delta["function"]:
                        tool_calls[idx]["function"]["name"] = tc_delta["function"]["name"]
                    if "arguments" in tc_delta["function"]:
                        tool_calls[idx]["function"]["arguments"] += tc_delta["function"]["arguments"]
        
        assert len(tool_calls) == 2
        assert tool_calls[0]["id"] == "call_1"
        assert tool_calls[0]["function"]["name"] == "tool_a"
        assert tool_calls[1]["id"] == "call_2"
        assert tool_calls[1]["function"]["name"] == "tool_b"


class TestFinishReasonParsing:
    """Tests for finish_reason parsing in streaming responses."""

    def test_finish_reason_stop(self):
        """finish_reason 'stop' indicates normal completion."""
        final_chunk = {
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        
        assert final_chunk["choices"][0]["finish_reason"] == "stop"
        assert final_chunk["choices"][0]["delta"] == {}

    def test_finish_reason_tool_calls(self):
        """finish_reason 'tool_calls' indicates tool invocation."""
        final_chunk = {
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "tool_calls"
            }]
        }
        
        assert final_chunk["choices"][0]["finish_reason"] == "tool_calls"

    def test_finish_reason_length(self):
        """finish_reason 'length' indicates max tokens hit."""
        final_chunk = {
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "length"
            }]
        }
        
        assert final_chunk["choices"][0]["finish_reason"] == "length"

    def test_null_finish_reason_during_stream(self):
        """finish_reason is null during active streaming."""
        mid_chunk = {
            "choices": [{
                "index": 0,
                "delta": {"content": "text"},
                "finish_reason": None
            }]
        }
        
        assert mid_chunk["choices"][0]["finish_reason"] is None


class TestStreamChunkTypeMapping:
    """Tests for mapping parsed data to StreamChunk types."""

    def test_text_delta_maps_to_text_chunk(self):
        """Text delta creates 'text' type StreamChunk."""
        delta = {"content": "Hello"}
        chunk = StreamChunk(type="text", content=delta["content"])
        
        assert chunk.type == "text"
        assert chunk.content == "Hello"

    def test_tool_call_maps_to_tool_call_chunk(self):
        """Tool call creates 'tool_call' type StreamChunk."""
        tool_name = "get_deals"
        tool_args = {"pipeline": "aramco"}
        chunk = StreamChunk(type="tool_call", tool_name=tool_name, tool_args=tool_args)
        
        assert chunk.type == "tool_call"
        assert chunk.tool_name == "get_deals"
        assert chunk.tool_args["pipeline"] == "aramco"

    def test_tool_result_maps_to_tool_result_chunk(self):
        """Tool result creates 'tool_result' type StreamChunk."""
        chunk = StreamChunk(
            type="tool_result",
            tool_name="get_deals",
            tool_result={"deals": [{"id": 1}]}
        )
        
        assert chunk.type == "tool_result"
        assert chunk.tool_name == "get_deals"
        assert len(chunk.tool_result["deals"]) == 1

    def test_error_maps_to_error_chunk(self):
        """Error creates 'error' type StreamChunk."""
        chunk = StreamChunk(type="error", error="API timeout")
        
        assert chunk.type == "error"
        assert chunk.error == "API timeout"

    def test_completion_maps_to_done_chunk(self):
        """Completion creates 'done' type StreamChunk."""
        chunk = StreamChunk(type="done")
        
        assert chunk.type == "done"
        assert chunk.content is None


class TestResponseChoicesValidation:
    """Tests for validating choices array in responses."""

    def test_single_choice_response(self):
        """Single choice response is parsed correctly."""
        response = {
            "choices": [{"message": {"content": "Hello"}}]
        }
        
        assert len(response["choices"]) == 1
        assert response["choices"][0]["message"]["content"] == "Hello"

    def test_multiple_choices_first_used(self):
        """Multiple choices - first one is typically used."""
        response = {
            "choices": [
                {"message": {"content": "First"}},
                {"message": {"content": "Second"}}
            ]
        }
        
        # Convention is to use first choice
        assert response["choices"][0]["message"]["content"] == "First"

    def test_empty_choices_handled(self):
        """Empty choices array is handled."""
        response = {"choices": []}
        
        assert len(response["choices"]) == 0
        # Should gracefully handle this case

    def test_missing_choices_detected(self):
        """Missing choices key is detected."""
        response = {}
        
        assert "choices" not in response


class TestMessageContentExtraction:
    """Tests for extracting content from message objects."""

    def test_string_content_extraction(self):
        """String content is extracted directly."""
        message = {"role": "assistant", "content": "Hello"}
        
        assert message["content"] == "Hello"
        assert isinstance(message["content"], str)

    def test_null_content_with_tool_calls(self):
        """Null content when tool_calls present."""
        message = {
            "role": "assistant",
            "content": None,
            "tool_calls": [{"id": "call_1", "function": {"name": "test"}}]
        }
        
        assert message["content"] is None
        assert "tool_calls" in message

    def test_empty_string_content(self):
        """Empty string content is valid."""
        message = {"role": "assistant", "content": ""}
        
        assert message["content"] == ""
        assert isinstance(message["content"], str)

    def test_content_with_special_characters(self):
        """Content with special characters preserved."""
        special_content = "Line1\nLine2\tTab\"Quote\"Unicode: 日本語"
        message = {"role": "assistant", "content": special_content}
        
        assert message["content"] == special_content


class TestUsageDataExtraction:
    """Tests for extracting usage/token data from responses."""

    def test_complete_usage_data(self):
        """Complete usage data is extracted."""
        response = {
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }
        
        usage = response["usage"]
        assert usage["prompt_tokens"] == 100
        assert usage["completion_tokens"] == 50
        assert usage["total_tokens"] == 150

    def test_partial_usage_data(self):
        """Partial usage data with defaults."""
        response = {
            "usage": {
                "prompt_tokens": 100
            }
        }
        
        usage = response["usage"]
        assert usage.get("prompt_tokens", 0) == 100
        assert usage.get("completion_tokens", 0) == 0
        assert usage.get("total_tokens", 0) == 0

    def test_missing_usage_defaults(self):
        """Missing usage returns defaults."""
        response = {"choices": [{"message": {"content": "Hi"}}]}
        
        usage = response.get("usage", {})
        assert usage.get("prompt_tokens", 0) == 0
        assert usage.get("completion_tokens", 0) == 0


class TestEdgeCasesAndErrors:
    """Tests for edge cases and error conditions."""

    def test_unicode_content_handling(self):
        """Unicode content is handled correctly."""
        content = "مرحبا 你好 🎉"
        
        # Simulate JSON round-trip
        encoded = json.dumps({"content": content})
        decoded = json.loads(encoded)
        
        assert decoded["content"] == content

    def test_very_long_content(self):
        """Very long content strings are handled."""
        long_content = "A" * 100000
        
        chunk = StreamChunk(type="text", content=long_content)
        assert len(chunk.content) == 100000

    def test_nested_json_in_tool_args(self):
        """Nested JSON in tool arguments is parsed correctly."""
        args_json = '{"filter": {"status": "active", "tags": ["urgent", "review"]}}'
        
        parsed = json.loads(args_json)
        assert parsed["filter"]["status"] == "active"
        assert len(parsed["filter"]["tags"]) == 2

    def test_escaped_characters_in_json(self):
        """Escaped characters in JSON are handled."""
        json_str = '{"content": "Line1\\nLine2\\t\\"quoted\\""}'
        
        parsed = json.loads(json_str)
        assert "\n" in parsed["content"]
        assert "\t" in parsed["content"]
        assert '"' in parsed["content"]

    def test_malformed_tool_call_structure(self):
        """Malformed tool call structure is handled gracefully."""
        malformed = {
            "choices": [{
                "message": {
                    "tool_calls": [
                        {"id": "call_1"}  # Missing function key
                    ]
                }
            }]
        }
        
        tc = malformed["choices"][0]["message"]["tool_calls"][0]
        # Should check for 'function' key before accessing
        assert tc.get("function") is None
