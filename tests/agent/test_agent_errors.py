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

                # Should not crash - tool error is captured and returned to LLM
                # The test verifies the error handling path is taken
                # We need to set up a second API call that returns a final response
                final_response = MagicMock()
                final_response.json.return_value = {
                    "choices": [{
                        "message": {
                            "content": "I encountered an error with the tool."
                        }
                    }],
                    "usage": {"prompt_tokens": 20, "completion_tokens": 10}
                }
                mock_api.side_effect = [mock_response, final_response]

                response = await agent.chat("Get overdue deals")

                # Verify tool.execute was called and error was caught
                mock_execute.assert_called_once()
                # The response should be the LLM's response after seeing the error
                assert response is not None
