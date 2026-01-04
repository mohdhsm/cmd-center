"""Tests for persistence models."""

import pytest
from datetime import datetime

from cmd_center.agent.persistence.models import AgentConversation, AgentMessage


class TestAgentConversation:
    def test_has_required_fields(self):
        conv = AgentConversation(title="Test Conversation")
        assert conv.title == "Test Conversation"
        assert conv.id is None
        assert conv.created_at is not None
        assert conv.updated_at is not None

    def test_has_messages_relationship(self):
        conv = AgentConversation(title="Test")
        assert hasattr(conv, "messages")

    def test_default_title(self):
        conv = AgentConversation()
        assert conv.title == "New Conversation"

    def test_timestamps_are_datetime(self):
        conv = AgentConversation(title="Test")
        assert isinstance(conv.created_at, datetime)
        assert isinstance(conv.updated_at, datetime)


class TestAgentMessage:
    def test_has_required_fields(self):
        msg = AgentMessage(conversation_id=1, role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.conversation_id == 1
        assert msg.created_at is not None

    def test_role_accepts_valid_values(self):
        for role in ["user", "assistant", "system"]:
            msg = AgentMessage(conversation_id=1, role=role, content="test")
            assert msg.role == role

    def test_has_optional_tool_fields(self):
        msg = AgentMessage(
            conversation_id=1,
            role="assistant",
            content=None,
        )
        # Set tool_calls via property setter after construction
        msg.tool_calls = [{"name": "get_deals", "args": {}}]
        assert msg.tool_calls is not None
        assert msg.tool_calls == [{"name": "get_deals", "args": {}}]

    def test_tool_calls_json_serialization(self):
        """Test that tool_calls property correctly serializes/deserializes JSON."""
        msg = AgentMessage(conversation_id=1, role="assistant", content=None)

        # Set tool_calls via property
        tool_calls_data = [{"name": "search", "args": {"query": "test"}}]
        msg.tool_calls = tool_calls_data

        # Verify it was stored as JSON
        assert msg.tool_calls_json is not None

        # Verify retrieval works
        assert msg.tool_calls == tool_calls_data

    def test_tool_calls_none_handling(self):
        """Test that tool_calls can be set to None."""
        msg = AgentMessage(conversation_id=1, role="assistant", content="Hello")
        msg.tool_calls = None
        assert msg.tool_calls is None
        assert msg.tool_calls_json is None

    def test_tool_results_json_serialization(self):
        """Test that tool_results property correctly serializes/deserializes JSON."""
        msg = AgentMessage(conversation_id=1, role="assistant", content=None)

        # Set tool_results via property
        tool_results_data = [{"id": "1", "output": "result"}]
        msg.tool_results = tool_results_data

        # Verify it was stored as JSON
        assert msg.tool_results_json is not None

        # Verify retrieval works
        assert msg.tool_results == tool_results_data

    def test_tool_results_none_handling(self):
        """Test that tool_results can be set to None."""
        msg = AgentMessage(conversation_id=1, role="assistant", content="Hello")
        msg.tool_results = None
        assert msg.tool_results is None
        assert msg.tool_results_json is None

    def test_content_can_be_none(self):
        """Test that content field can be None (for tool call messages)."""
        msg = AgentMessage(conversation_id=1, role="assistant", content=None)
        assert msg.content is None

    def test_id_defaults_to_none(self):
        """Test that id defaults to None before persistence."""
        msg = AgentMessage(conversation_id=1, role="user", content="test")
        assert msg.id is None

    def test_has_conversation_relationship(self):
        """Test that message has a relationship to conversation."""
        msg = AgentMessage(conversation_id=1, role="user", content="test")
        assert hasattr(msg, "conversation")
