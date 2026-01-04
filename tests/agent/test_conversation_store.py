"""Tests for ConversationStore."""

import pytest
from unittest.mock import MagicMock, patch

from cmd_center.agent.persistence.conversation_store import ConversationStore
from cmd_center.agent.persistence.models import AgentConversation, AgentMessage


class TestConversationStore:
    """Tests for ConversationStore CRUD operations."""

    def test_create_conversation(self):
        """Test creating a new conversation."""
        with patch("cmd_center.agent.persistence.conversation_store.Session") as MockSession:
            mock_session = MagicMock()
            MockSession.return_value.__enter__ = MagicMock(return_value=mock_session)
            MockSession.return_value.__exit__ = MagicMock(return_value=False)

            store = ConversationStore()
            conv = store.create_conversation("Test Chat")

            assert conv.title == "Test Chat"
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()

    def test_create_conversation_default_title(self):
        """Test creating conversation with default title."""
        with patch("cmd_center.agent.persistence.conversation_store.Session") as MockSession:
            mock_session = MagicMock()
            MockSession.return_value.__enter__ = MagicMock(return_value=mock_session)
            MockSession.return_value.__exit__ = MagicMock(return_value=False)

            store = ConversationStore()
            conv = store.create_conversation()

            assert conv.title == "New Conversation"

    def test_get_conversation(self):
        """Test retrieving a conversation by ID."""
        with patch("cmd_center.agent.persistence.conversation_store.Session") as MockSession:
            mock_session = MagicMock()
            mock_conv = AgentConversation(id=1, title="Retrieved Chat")
            mock_session.get.return_value = mock_conv
            MockSession.return_value.__enter__ = MagicMock(return_value=mock_session)
            MockSession.return_value.__exit__ = MagicMock(return_value=False)

            store = ConversationStore()
            conv = store.get_conversation(conversation_id=1)

            assert conv is not None
            assert conv.title == "Retrieved Chat"
            mock_session.get.assert_called_once_with(AgentConversation, 1)

    def test_get_conversation_not_found(self):
        """Test retrieving a non-existent conversation returns None."""
        with patch("cmd_center.agent.persistence.conversation_store.Session") as MockSession:
            mock_session = MagicMock()
            mock_session.get.return_value = None
            MockSession.return_value.__enter__ = MagicMock(return_value=mock_session)
            MockSession.return_value.__exit__ = MagicMock(return_value=False)

            store = ConversationStore()
            conv = store.get_conversation(conversation_id=999)

            assert conv is None

    def test_add_message(self):
        """Test adding a message to a conversation."""
        with patch("cmd_center.agent.persistence.conversation_store.Session") as MockSession:
            mock_session = MagicMock()
            mock_conv = AgentConversation(id=1, title="Test")
            mock_session.get.return_value = mock_conv
            MockSession.return_value.__enter__ = MagicMock(return_value=mock_session)
            MockSession.return_value.__exit__ = MagicMock(return_value=False)

            store = ConversationStore()
            msg = store.add_message(conversation_id=1, role="user", content="Hello")

            assert msg.role == "user"
            assert msg.content == "Hello"
            assert msg.conversation_id == 1
            mock_session.add.assert_called()

    def test_add_message_with_tool_calls(self):
        """Test adding a message with tool calls."""
        with patch("cmd_center.agent.persistence.conversation_store.Session") as MockSession:
            mock_session = MagicMock()
            mock_conv = AgentConversation(id=1, title="Test")
            mock_session.get.return_value = mock_conv
            MockSession.return_value.__enter__ = MagicMock(return_value=mock_session)
            MockSession.return_value.__exit__ = MagicMock(return_value=False)

            store = ConversationStore()
            tool_calls = [{"name": "get_deals", "args": {}}]
            msg = store.add_message(
                conversation_id=1,
                role="assistant",
                content=None,
                tool_calls=tool_calls
            )

            assert msg.role == "assistant"
            assert msg.tool_calls == tool_calls

    def test_add_message_with_tool_results(self):
        """Test adding a message with tool results."""
        with patch("cmd_center.agent.persistence.conversation_store.Session") as MockSession:
            mock_session = MagicMock()
            mock_conv = AgentConversation(id=1, title="Test")
            mock_session.get.return_value = mock_conv
            MockSession.return_value.__enter__ = MagicMock(return_value=mock_session)
            MockSession.return_value.__exit__ = MagicMock(return_value=False)

            store = ConversationStore()
            tool_results = [{"id": "1", "output": "result"}]
            msg = store.add_message(
                conversation_id=1,
                role="user",
                tool_results=tool_results
            )

            assert msg.tool_results == tool_results

    def test_add_message_updates_conversation_timestamp(self):
        """Test that adding a message updates the conversation's updated_at."""
        with patch("cmd_center.agent.persistence.conversation_store.Session") as MockSession:
            mock_session = MagicMock()
            mock_conv = MagicMock(spec=AgentConversation)
            mock_conv.id = 1
            mock_session.get.return_value = mock_conv
            MockSession.return_value.__enter__ = MagicMock(return_value=mock_session)
            MockSession.return_value.__exit__ = MagicMock(return_value=False)

            store = ConversationStore()
            store.add_message(conversation_id=1, role="user", content="Hello")

            # Verify updated_at was set
            assert mock_conv.updated_at is not None

    def test_get_messages(self):
        """Test retrieving messages for a conversation."""
        with patch("cmd_center.agent.persistence.conversation_store.Session") as MockSession:
            mock_session = MagicMock()
            mock_messages = [
                AgentMessage(id=1, conversation_id=1, role="user", content="Hi"),
                AgentMessage(id=2, conversation_id=1, role="assistant", content="Hello!")
            ]
            mock_session.exec.return_value.all.return_value = mock_messages
            MockSession.return_value.__enter__ = MagicMock(return_value=mock_session)
            MockSession.return_value.__exit__ = MagicMock(return_value=False)

            store = ConversationStore()
            messages = store.get_messages(conversation_id=1)

            assert len(messages) == 2
            assert messages[0].role == "user"
            assert messages[1].role == "assistant"

    def test_get_messages_empty(self):
        """Test retrieving messages when none exist."""
        with patch("cmd_center.agent.persistence.conversation_store.Session") as MockSession:
            mock_session = MagicMock()
            mock_session.exec.return_value.all.return_value = []
            MockSession.return_value.__enter__ = MagicMock(return_value=mock_session)
            MockSession.return_value.__exit__ = MagicMock(return_value=False)

            store = ConversationStore()
            messages = store.get_messages(conversation_id=1)

            assert len(messages) == 0

    def test_list_conversations(self):
        """Test listing all conversations."""
        with patch("cmd_center.agent.persistence.conversation_store.Session") as MockSession:
            mock_session = MagicMock()
            mock_convs = [
                AgentConversation(id=1, title="Chat 1"),
                AgentConversation(id=2, title="Chat 2")
            ]
            mock_session.exec.return_value.all.return_value = mock_convs
            MockSession.return_value.__enter__ = MagicMock(return_value=mock_session)
            MockSession.return_value.__exit__ = MagicMock(return_value=False)

            store = ConversationStore()
            convs = store.list_conversations()

            assert len(convs) == 2
            assert convs[0].title == "Chat 1"

    def test_list_conversations_with_limit(self):
        """Test listing conversations with a custom limit."""
        with patch("cmd_center.agent.persistence.conversation_store.Session") as MockSession:
            mock_session = MagicMock()
            mock_session.exec.return_value.all.return_value = [
                AgentConversation(id=1, title="Chat 1")
            ]
            MockSession.return_value.__enter__ = MagicMock(return_value=mock_session)
            MockSession.return_value.__exit__ = MagicMock(return_value=False)

            store = ConversationStore()
            convs = store.list_conversations(limit=10)

            assert len(convs) == 1
            # Verify exec was called (limit is applied in the query)
            mock_session.exec.assert_called_once()

    def test_delete_conversation(self):
        """Test deleting a conversation and its messages."""
        with patch("cmd_center.agent.persistence.conversation_store.Session") as MockSession:
            mock_session = MagicMock()
            mock_conv = AgentConversation(id=1, title="To Delete")
            mock_messages = [
                AgentMessage(id=1, conversation_id=1, role="user", content="Hi")
            ]
            mock_session.get.return_value = mock_conv
            mock_session.exec.return_value.all.return_value = mock_messages
            MockSession.return_value.__enter__ = MagicMock(return_value=mock_session)
            MockSession.return_value.__exit__ = MagicMock(return_value=False)

            store = ConversationStore()
            result = store.delete_conversation(conversation_id=1)

            assert result is True
            # Should delete messages and conversation
            assert mock_session.delete.call_count >= 2
            mock_session.commit.assert_called_once()

    def test_delete_conversation_not_found(self):
        """Test deleting a non-existent conversation returns False."""
        with patch("cmd_center.agent.persistence.conversation_store.Session") as MockSession:
            mock_session = MagicMock()
            mock_session.get.return_value = None
            MockSession.return_value.__enter__ = MagicMock(return_value=mock_session)
            MockSession.return_value.__exit__ = MagicMock(return_value=False)

            store = ConversationStore()
            result = store.delete_conversation(conversation_id=999)

            assert result is False
            mock_session.delete.assert_not_called()
