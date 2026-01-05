"""Integration tests for Phase 4 polish features."""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from cmd_center.agent.core.agent import OmniousAgent
from cmd_center.agent.observability.logger import ConversationLogger
from cmd_center.agent.core.context import ContextManager
from cmd_center.agent.core.errors import format_error_response, ToolExecutionError


class TestPhase4Integration:
    """End-to-end tests for Phase 4 features."""

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

    def test_agent_has_all_phase4_components(self, agent):
        """Agent has all Phase 4 components."""
        assert hasattr(agent, 'file_logger')
        assert hasattr(agent, 'context_manager')
        assert hasattr(agent, 'get_context_warning')
        assert hasattr(agent, 'get_context_usage')

    def test_file_logger_creates_logs(self, tmp_path):
        """File logger creates JSONL logs."""
        logger = ConversationLogger(log_dir=str(tmp_path))
        logger.log_message(
            conversation_id=1,
            role="user",
            content="Hello",
        )

        log_files = list(tmp_path.glob("*.jsonl"))
        assert len(log_files) == 1

    def test_context_manager_tracks_usage(self):
        """Context manager tracks token usage."""
        context = ContextManager(max_tokens=1000)
        context.add_message("user", "Hello world")

        assert context.total_tokens > 0
        assert "token" in context.get_usage_summary().lower()

    def test_error_formatting_friendly(self):
        """Error formatting produces friendly messages."""
        error = ToolExecutionError("test_tool", "Failed")
        response = format_error_response(error)

        assert "trouble" in response.lower() or "error" not in response.lower()
        assert "test_tool" not in response


class TestFullAgentWorkflow:
    """Test complete agent workflows with all features."""

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

    def test_agent_initialization_complete(self, agent):
        """Agent initializes with all components."""
        # Core components
        assert agent.tools is not None
        assert agent.metrics is not None

        # Phase 3 components
        assert agent.executor is not None
        assert agent.pending_action is None

        # Phase 4 components
        assert agent.file_logger is not None
        assert agent.context_manager is not None

    def test_total_tool_count(self, agent):
        """All 25 tools are registered."""
        tools = agent.tools.list_tools()
        assert len(tools) == 25

    def test_all_tool_schemas_valid(self, agent):
        """All tools generate valid OpenAI schemas."""
        schemas = agent.tools.get_tools_schema()

        for schema in schemas:
            assert schema["type"] == "function"
            assert "function" in schema
            assert "name" in schema["function"]
            assert "description" in schema["function"]
            assert len(schema["function"]["description"]) > 10
