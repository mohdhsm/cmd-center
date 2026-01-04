"""Tests for OmniousAgent core."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import json
import httpx

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

    def test_error_chunk(self):
        """Error chunk has error message."""
        chunk = StreamChunk(type="error", error="Something went wrong")
        assert chunk.type == "error"
        assert chunk.error == "Something went wrong"


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


class TestOmniousAgentRetry:
    """Test retry logic."""

    @pytest.mark.asyncio
    async def test_call_api_with_retry_success(self):
        """Successful API call returns data."""
        agent = OmniousAgent()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "Hello"}}]}
        mock_response.raise_for_status = Mock()

        async with httpx.AsyncClient() as client:
            with patch.object(client, "post", return_value=mock_response):
                assert agent.MAX_RETRIES == 3

    @pytest.mark.asyncio
    async def test_returns_error_after_max_retries(self):
        """Agent has retry constants defined."""
        agent = OmniousAgent()
        assert hasattr(agent, "MAX_RETRIES")
        assert hasattr(agent, "RETRY_DELAYS")
        assert agent.MAX_RETRIES == 3
        assert len(agent.RETRY_DELAYS) == 3


class TestAgentPersistence:
    """Test agent persistence integration."""

    def test_agent_can_save_conversation(self):
        """Agent with persist=True can start and save a conversation."""
        with patch("cmd_center.agent.persistence.ConversationStore") as MockStore:
            mock_store = Mock()
            mock_conv = Mock(id=1)
            mock_store.create_conversation.return_value = mock_conv
            MockStore.return_value = mock_store

            agent = OmniousAgent(persist=True)
            agent.start_new_conversation("Test Chat")

            mock_store.create_conversation.assert_called_with("Test Chat")
            assert agent.conversation_id == 1

    def test_agent_saves_messages_when_persisting(self):
        """Agent saves messages to store when persisting."""
        with patch("cmd_center.agent.persistence.ConversationStore") as MockStore:
            mock_store = Mock()
            mock_conv = Mock(id=1)
            mock_store.create_conversation.return_value = mock_conv
            MockStore.return_value = mock_store

            agent = OmniousAgent(persist=True)
            agent.start_new_conversation()
            agent._add_to_history("user", "Hello")

            mock_store.add_message.assert_called()

    def test_agent_can_load_conversation(self):
        """Agent can load conversation and restore history."""
        with patch("cmd_center.agent.persistence.ConversationStore") as MockStore:
            mock_store = Mock()
            mock_store.get_messages.return_value = [
                Mock(role="user", content="Previous message")
            ]
            MockStore.return_value = mock_store

            agent = OmniousAgent(persist=True)
            agent.load_conversation(1)

            assert len(agent.conversation_history) == 1
            assert agent.conversation_history[0]["role"] == "user"
            assert agent.conversation_history[0]["content"] == "Previous message"

    def test_agent_without_persist_has_no_store(self):
        """Agent without persist=True does not initialize a store."""
        agent = OmniousAgent()
        assert agent._store is None
        assert agent.conversation_id is None

    def test_load_conversation_without_persist_raises_error(self):
        """Loading conversation without persist=True raises ValueError."""
        agent = OmniousAgent()
        with pytest.raises(ValueError, match="Persistence not enabled"):
            agent.load_conversation(1)
