"""Unit tests for API adapter functionality.

Tests the HTTP client interactions, retry logic, and response handling
using mocked HTTP responses.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from cmd_center.agent.core.agent import OmniousAgent, StreamChunk


class TestAPIRetryLogic:
    """Tests for API call retry logic."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return OmniousAgent()

    @pytest.fixture
    def mock_messages(self):
        """Sample messages for testing."""
        return [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"}
        ]

    @pytest.mark.asyncio
    async def test_successful_call_no_retry(self, agent, mock_messages):
        """Successful call should not retry."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Hi!"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client.return_value
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value.post = AsyncMock(return_value=mock_response)

            response = await agent._call_api_with_retry(mock_messages)

            assert response.status_code == 200
            mock_client.return_value.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_on_429_rate_limit(self, agent, mock_messages):
        """Should retry on 429 rate limit error."""
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "Rate limited", request=MagicMock(), response=rate_limit_response
            )
        )

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Success"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }
        success_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client.return_value
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value.post = AsyncMock(
                side_effect=[rate_limit_response, success_response]
            )

            response = await agent._call_api_with_retry(mock_messages)

            assert response.status_code == 200
            assert mock_client.return_value.post.call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_exhausted(self, agent, mock_messages):
        """Should raise after max retries exhausted."""
        rate_limit_response = MagicMock()
        rate_limit_response.status_code = 429
        rate_limit_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "Rate limited", request=MagicMock(), response=rate_limit_response
            )
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client.return_value
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value.post = AsyncMock(return_value=rate_limit_response)

            with pytest.raises(httpx.HTTPStatusError):
                await agent._call_api_with_retry(mock_messages)

            assert mock_client.return_value.post.call_count == agent.MAX_RETRIES

    @pytest.mark.asyncio
    async def test_retry_on_http_error(self, agent, mock_messages):
        """Should retry on general HTTP errors."""
        error = httpx.ConnectError("Connection failed")

        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Success"}}],
            "usage": {}
        }
        success_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client.return_value
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value.post = AsyncMock(
                side_effect=[error, success_response]
            )

            response = await agent._call_api_with_retry(mock_messages)

            assert response.status_code == 200
            assert mock_client.return_value.post.call_count == 2


class TestAPIRequestFormat:
    """Tests for API request format."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return OmniousAgent()

    @pytest.mark.asyncio
    async def test_request_includes_authorization_header(self, agent):
        """Request must include Authorization header."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hi"}}],
            "usage": {}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client.return_value
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value.post = AsyncMock(return_value=mock_response)

            await agent._call_api_with_retry([{"role": "user", "content": "Hi"}])

            call_kwargs = mock_client.return_value.post.call_args
            headers = call_kwargs[1]["headers"]
            assert "Authorization" in headers
            assert headers["Authorization"].startswith("Bearer ")

    @pytest.mark.asyncio
    async def test_request_includes_model(self, agent):
        """Request must include model in payload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hi"}}],
            "usage": {}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client.return_value
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value.post = AsyncMock(return_value=mock_response)

            await agent._call_api_with_retry([{"role": "user", "content": "Hi"}])

            call_kwargs = mock_client.return_value.post.call_args
            payload = call_kwargs[1]["json"]
            assert "model" in payload

    @pytest.mark.asyncio
    async def test_request_includes_messages(self, agent):
        """Request must include messages array."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hi"}}],
            "usage": {}
        }
        mock_response.raise_for_status = MagicMock()

        messages = [{"role": "user", "content": "Hello"}]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client.return_value
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value.post = AsyncMock(return_value=mock_response)

            await agent._call_api_with_retry(messages)

            call_kwargs = mock_client.return_value.post.call_args
            payload = call_kwargs[1]["json"]
            assert "messages" in payload
            assert payload["messages"] == messages

    @pytest.mark.asyncio
    async def test_request_includes_tools_when_provided(self, agent):
        """Request must include tools when provided."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hi"}}],
            "usage": {}
        }
        mock_response.raise_for_status = MagicMock()

        tools = [{"type": "function", "function": {"name": "test"}}]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client.return_value
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value.post = AsyncMock(return_value=mock_response)

            await agent._call_api_with_retry(
                [{"role": "user", "content": "Hi"}],
                tools=tools
            )

            call_kwargs = mock_client.return_value.post.call_args
            payload = call_kwargs[1]["json"]
            assert "tools" in payload
            assert payload["tools"] == tools
            assert payload["tool_choice"] == "auto"


class TestToolCallProcessing:
    """Tests for processing tool calls from API responses."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return OmniousAgent()

    @pytest.mark.asyncio
    async def test_process_single_tool_call(self, agent):
        """Should process a single tool call correctly."""
        tool_calls = [
            {
                "id": "call_123",
                "function": {
                    "name": "get_overdue_deals",
                    "arguments": json.dumps({"days_threshold": 7})
                }
            }
        ]

        results = await agent._process_tool_calls(tool_calls)

        assert len(results) == 1
        assert results[0]["role"] == "tool"
        assert results[0]["tool_call_id"] == "call_123"
        assert "content" in results[0]

    @pytest.mark.asyncio
    async def test_process_multiple_tool_calls(self, agent):
        """Should process multiple tool calls."""
        tool_calls = [
            {
                "id": "call_1",
                "function": {
                    "name": "get_overdue_deals",
                    "arguments": "{}"
                }
            },
            {
                "id": "call_2",
                "function": {
                    "name": "get_employees",
                    "arguments": "{}"
                }
            }
        ]

        results = await agent._process_tool_calls(tool_calls)

        assert len(results) == 2
        assert results[0]["tool_call_id"] == "call_1"
        assert results[1]["tool_call_id"] == "call_2"

    @pytest.mark.asyncio
    async def test_process_tool_call_with_invalid_json(self, agent):
        """Should handle invalid JSON in arguments gracefully."""
        tool_calls = [
            {
                "id": "call_123",
                "function": {
                    "name": "get_overdue_deals",
                    "arguments": "invalid json {"
                }
            }
        ]

        # Should not raise, should use empty dict
        results = await agent._process_tool_calls(tool_calls)

        assert len(results) == 1
        assert results[0]["role"] == "tool"

    @pytest.mark.asyncio
    async def test_process_unknown_tool_returns_error(self, agent):
        """Should return error for unknown tool."""
        tool_calls = [
            {
                "id": "call_123",
                "function": {
                    "name": "nonexistent_tool",
                    "arguments": "{}"
                }
            }
        ]

        results = await agent._process_tool_calls(tool_calls)

        assert len(results) == 1
        content = json.loads(results[0]["content"])
        assert "error" in content


class TestMetricsTracking:
    """Tests for token/cost metrics tracking."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        agent = OmniousAgent()
        agent.metrics.reset()
        return agent

    @pytest.mark.asyncio
    async def test_tracks_tokens_from_response(self, agent):
        """Should track token usage from API response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Hi"}}],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client.return_value
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value.post = AsyncMock(return_value=mock_response)

            await agent._call_llm_with_tools([{"role": "user", "content": "Hi"}])

        stats = agent.metrics.get_stats()
        assert stats["input_tokens"] == 100
        assert stats["output_tokens"] == 50

    @pytest.mark.asyncio
    async def test_handles_missing_usage_gracefully(self, agent):
        """Should handle responses without usage field."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Hi"}}]
            # No usage field
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client.return_value
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value.post = AsyncMock(return_value=mock_response)

            # Should not raise
            await agent._call_llm_with_tools([{"role": "user", "content": "Hi"}])


class TestChatMethod:
    """Tests for the main chat method."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return OmniousAgent()

    @pytest.mark.asyncio
    async def test_chat_returns_string(self, agent):
        """chat() should return a string response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Hello!"}}],
            "usage": {}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client.return_value
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value.post = AsyncMock(return_value=mock_response)

            result = await agent.chat("Hi")

            assert isinstance(result, str)
            assert result == "Hello!"

    @pytest.mark.asyncio
    async def test_chat_adds_to_history(self, agent):
        """chat() should add messages to conversation history."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Hello!"}}],
            "usage": {}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client.return_value
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value.post = AsyncMock(return_value=mock_response)

            await agent.chat("Hi")

            assert len(agent.conversation_history) == 2
            assert agent.conversation_history[0]["role"] == "user"
            assert agent.conversation_history[0]["content"] == "Hi"
            assert agent.conversation_history[1]["role"] == "assistant"
            assert agent.conversation_history[1]["content"] == "Hello!"

    @pytest.mark.asyncio
    async def test_chat_handles_tool_calls(self, agent):
        """chat() should handle tool calls in response."""
        # First response with tool call
        tool_response = MagicMock()
        tool_response.status_code = 200
        tool_response.json.return_value = {
            "choices": [{
                "message": {
                    "role": "assistant",
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
            "usage": {}
        }
        tool_response.raise_for_status = MagicMock()

        # Second response with final answer
        final_response = MagicMock()
        final_response.status_code = 200
        final_response.json.return_value = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "There are 5 overdue deals."
                }
            }],
            "usage": {}
        }
        final_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client.return_value
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value.post = AsyncMock(
                side_effect=[tool_response, final_response]
            )

            result = await agent.chat("Show me overdue deals")

            assert result == "There are 5 overdue deals."
            assert mock_client.return_value.post.call_count == 2


class TestReActLoop:
    """Tests for ReAct loop behavior."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return OmniousAgent()

    @pytest.mark.asyncio
    async def test_react_loop_continues_on_tool_calls(self, agent):
        """ReAct loop should continue making calls when tools are invoked."""
        responses = []

        # Multiple tool calls then final response
        for i in range(3):
            r = MagicMock()
            r.status_code = 200
            r.json.return_value = {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": f"call_{i}",
                            "function": {
                                "name": "get_overdue_deals",
                                "arguments": "{}"
                            }
                        }]
                    }
                }],
                "usage": {}
            }
            r.raise_for_status = MagicMock()
            responses.append(r)

        final = MagicMock()
        final.status_code = 200
        final.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Done"}}],
            "usage": {}
        }
        final.raise_for_status = MagicMock()
        responses.append(final)

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client.return_value
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value.post = AsyncMock(side_effect=responses)

            result = await agent.chat("Query")

            assert result == "Done"
            assert mock_client.return_value.post.call_count == 4

    @pytest.mark.asyncio
    async def test_react_loop_has_max_iterations(self, agent):
        """ReAct loop should stop after max iterations."""
        # Create infinite tool call responses
        def create_tool_response():
            r = MagicMock()
            r.status_code = 200
            r.json.return_value = {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": "call_x",
                            "function": {
                                "name": "get_overdue_deals",
                                "arguments": "{}"
                            }
                        }]
                    }
                }],
                "usage": {}
            }
            r.raise_for_status = MagicMock()
            return r

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client.return_value
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value.post = AsyncMock(
                side_effect=[create_tool_response() for _ in range(15)]
            )

            # Should not hang, should stop after max iterations (10 by default)
            result = await agent._call_llm_with_tools(
                [{"role": "user", "content": "Query"}],
                max_iterations=10
            )

            # Should have made 11 calls (initial + 10 iterations)
            assert mock_client.return_value.post.call_count == 11
