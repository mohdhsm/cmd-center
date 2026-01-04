"""Conversation storage for the agent."""

from typing import List, Optional
from datetime import datetime, timezone
from sqlmodel import Session, select

from .models import AgentConversation, AgentMessage
from ...backend.db import engine


class ConversationStore:
    """Store for managing agent conversations and messages."""

    def create_conversation(self, title: str = "New Conversation") -> AgentConversation:
        """Create a new conversation.

        Args:
            title: The title for the conversation. Defaults to "New Conversation".

        Returns:
            The created AgentConversation instance.
        """
        with Session(engine) as session:
            conv = AgentConversation(title=title)
            session.add(conv)
            session.commit()
            session.refresh(conv)
            return conv

    def get_conversation(self, conversation_id: int) -> Optional[AgentConversation]:
        """Get a conversation by ID.

        Args:
            conversation_id: The ID of the conversation to retrieve.

        Returns:
            The AgentConversation if found, None otherwise.
        """
        with Session(engine) as session:
            return session.get(AgentConversation, conversation_id)

    def list_conversations(self, limit: int = 50) -> List[AgentConversation]:
        """List conversations ordered by most recently updated.

        Args:
            limit: Maximum number of conversations to return. Defaults to 50.

        Returns:
            List of AgentConversation instances.
        """
        with Session(engine) as session:
            statement = select(AgentConversation).order_by(
                AgentConversation.updated_at.desc()
            ).limit(limit)
            return session.exec(statement).all()

    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: Optional[str] = None,
        tool_calls: Optional[list] = None,
        tool_results: Optional[list] = None,
    ) -> AgentMessage:
        """Add a message to a conversation.

        Args:
            conversation_id: The ID of the conversation.
            role: The role of the message sender (user, assistant, or system).
            content: The text content of the message.
            tool_calls: Optional list of tool calls made by the assistant.
            tool_results: Optional list of tool results.

        Returns:
            The created AgentMessage instance.
        """
        with Session(engine) as session:
            msg = AgentMessage(
                conversation_id=conversation_id,
                role=role,
                content=content
            )
            if tool_calls:
                msg.tool_calls = tool_calls
            if tool_results:
                msg.tool_results = tool_results
            session.add(msg)

            # Update the conversation's updated_at timestamp
            conv = session.get(AgentConversation, conversation_id)
            if conv:
                conv.updated_at = datetime.now(timezone.utc)

            session.commit()
            session.refresh(msg)
            return msg

    def get_messages(self, conversation_id: int) -> List[AgentMessage]:
        """Get all messages for a conversation ordered by creation time.

        Args:
            conversation_id: The ID of the conversation.

        Returns:
            List of AgentMessage instances ordered by created_at.
        """
        with Session(engine) as session:
            statement = select(AgentMessage).where(
                AgentMessage.conversation_id == conversation_id
            ).order_by(AgentMessage.created_at)
            return session.exec(statement).all()

    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation and all its messages.

        Args:
            conversation_id: The ID of the conversation to delete.

        Returns:
            True if the conversation was deleted, False if not found.
        """
        with Session(engine) as session:
            conv = session.get(AgentConversation, conversation_id)
            if not conv:
                return False

            # Delete all messages first
            statement = select(AgentMessage).where(
                AgentMessage.conversation_id == conversation_id
            )
            for msg in session.exec(statement).all():
                session.delete(msg)

            # Delete the conversation
            session.delete(conv)
            session.commit()
            return True
