"""Tests for chat method confirmation handling."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

from cmd_center.agent.core.agent import OmniousAgent
from cmd_center.agent.tools.base import PendingAction, ToolResult


class TestChatHandlesPendingActionFromTool:
    """Tests for pending_action being set when write tool is called."""

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
    async def test_pending_action_set_from_write_tool_result(self, agent):
        """Pending action is set when write tool returns pending_action."""
        # Simulate a tool call response with pending_action
        tool_calls = [
            {
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "request_create_task",
                    "arguments": json.dumps({"title": "Follow up with client"})
                }
            }
        ]

        # Process tool calls - write tool should return pending_action
        results = await agent._process_tool_calls(tool_calls)

        # Verify pending_action is set
        assert agent.has_pending_action() is True
        assert agent.pending_action.tool_name == "request_create_task"
        assert "Follow up with client" in agent.pending_action.preview
        assert agent.pending_action.payload["title"] == "Follow up with client"

    @pytest.mark.asyncio
    async def test_pending_action_not_set_from_read_tool(self, agent):
        """Pending action is NOT set when read-only tool is called."""
        tool_calls = [
            {
                "id": "call_456",
                "type": "function",
                "function": {
                    "name": "get_overdue_deals",
                    "arguments": json.dumps({})
                }
            }
        ]

        # Mock the read tool to return non-pending data
        with patch.object(agent.tools, "execute") as mock_execute:
            mock_execute.return_value = ToolResult(success=True, data={"deals": []})
            await agent._process_tool_calls(tool_calls)

        # Verify pending_action is NOT set
        assert agent.has_pending_action() is False


class TestChatExecutesOnYes:
    """Tests for executing confirmed actions on 'yes'."""

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
    async def test_chat_executes_action_on_yes(self, agent):
        """Chat executes pending action when user confirms with 'yes'."""
        # Set up a pending action
        agent.pending_action = PendingAction(
            tool_name="request_create_task",
            preview="CREATE TASK\n  Title: Follow up",
            payload={"title": "Follow up"},
        )

        # Mock the executor
        agent.executor.execute = MagicMock(return_value={
            "success": True,
            "action": "Task created",
            "id": 123,
        })

        # User confirms
        response = await agent.chat("yes")

        # Verify executor was called with the pending action
        agent.executor.execute.assert_called_once()
        called_action = agent.executor.execute.call_args[0][0]
        assert called_action.tool_name == "request_create_task"

        # Verify pending action is cleared
        assert agent.pending_action is None

        # Verify response indicates success
        assert "Done" in response
        assert "123" in response

    @pytest.mark.asyncio
    async def test_chat_handles_execution_error(self, agent):
        """Chat returns error message if execution fails."""
        # Set up a pending action
        agent.pending_action = PendingAction(
            tool_name="request_create_task",
            preview="CREATE TASK\n  Title: Test",
            payload={"title": "Test"},
        )

        # Mock executor to return error
        agent.executor.execute = MagicMock(return_value={
            "success": False,
            "error": "Database connection failed",
        })

        # User confirms
        response = await agent.chat("yes")

        # Verify pending action is cleared even on error
        assert agent.pending_action is None

        # Verify response indicates error
        assert "error" in response.lower()
        assert "Database connection failed" in response

    @pytest.mark.asyncio
    async def test_chat_accepts_various_yes_phrases(self, agent):
        """Chat accepts various confirmation phrases."""
        yes_phrases = ["yes", "y", "confirm", "ok", "proceed", "go ahead"]

        for phrase in yes_phrases:
            # Reset pending action for each test
            agent.pending_action = PendingAction(
                tool_name="request_create_task",
                preview="CREATE TASK",
                payload={"title": "Test"},
            )

            # Mock the executor
            agent.executor.execute = MagicMock(return_value={
                "success": True,
                "action": "Task created",
                "id": 1,
            })

            response = await agent.chat(phrase)

            # Verify executor was called
            agent.executor.execute.assert_called()
            assert "Done" in response, f"Failed for phrase: {phrase}"


class TestChatCancelsOnNo:
    """Tests for canceling pending actions on 'no'."""

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
    async def test_chat_cancels_action_on_no(self, agent):
        """Chat cancels pending action when user says 'no'."""
        # Set up a pending action
        agent.pending_action = PendingAction(
            tool_name="request_create_task",
            preview="CREATE TASK\n  Title: Test",
            payload={"title": "Test"},
        )

        # Mock the executor
        agent.executor.execute = MagicMock()

        # User cancels
        response = await agent.chat("no")

        # Verify executor was NOT called
        agent.executor.execute.assert_not_called()

        # Verify pending action is cleared
        assert agent.pending_action is None

        # Verify response indicates cancellation
        assert "won't proceed" in response.lower() or "no problem" in response.lower()

    @pytest.mark.asyncio
    async def test_chat_accepts_various_no_phrases(self, agent):
        """Chat accepts various cancellation phrases."""
        no_phrases = ["no", "n", "cancel", "stop", "abort", "never mind"]

        for phrase in no_phrases:
            # Reset pending action for each test
            agent.pending_action = PendingAction(
                tool_name="request_create_task",
                preview="CREATE TASK",
                payload={"title": "Test"},
            )

            # Mock the executor
            agent.executor.execute = MagicMock()

            response = await agent.chat(phrase)

            # Verify executor was NOT called
            agent.executor.execute.assert_not_called()
            assert agent.pending_action is None, f"Failed for phrase: {phrase}"


class TestChatContinuesNormallyWithoutPending:
    """Tests that chat continues normally when no pending action."""

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
    async def test_chat_proceeds_normally_without_pending(self, agent):
        """Chat processes message normally when no pending action."""
        # Mock the LLM call
        with patch.object(agent, '_call_llm_with_tools', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Here are your deals..."

            response = await agent.chat("What deals need attention?")

            # Verify LLM was called
            mock_llm.assert_called_once()
            assert response == "Here are your deals..."

    @pytest.mark.asyncio
    async def test_chat_ignores_yes_without_pending(self, agent):
        """Chat treats 'yes' as normal message when no pending action."""
        # No pending action set
        assert agent.pending_action is None

        # Mock the LLM call
        with patch.object(agent, '_call_llm_with_tools', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "I'm not sure what you're confirming."

            response = await agent.chat("yes")

            # Verify LLM was called (not treated as confirmation)
            mock_llm.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_ignores_ambiguous_with_pending(self, agent):
        """Chat passes ambiguous message to LLM even with pending action."""
        # Set up a pending action
        agent.pending_action = PendingAction(
            tool_name="request_create_task",
            preview="CREATE TASK",
            payload={"title": "Test"},
        )

        # Mock the LLM call
        with patch.object(agent, '_call_llm_with_tools', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Let me help you with that."

            # User sends an ambiguous message (not yes/no)
            response = await agent.chat("What else can you do?")

            # Verify LLM was called
            mock_llm.assert_called_once()

            # Pending action should still be there (not cleared by non-confirmation)
            assert agent.pending_action is not None
