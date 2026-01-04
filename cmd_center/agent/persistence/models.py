"""SQLModel models for agent conversation persistence."""

from datetime import datetime, timezone
from typing import Optional, List, Any
from sqlmodel import SQLModel, Field, Relationship
import json


class AgentConversation(SQLModel, table=True):
    """Stores agent conversation sessions."""

    __tablename__ = "agent_conversations"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(default="New Conversation")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    messages: List["AgentMessage"] = Relationship(back_populates="conversation")


class AgentMessage(SQLModel, table=True):
    """Stores individual messages within an agent conversation."""

    __tablename__ = "agent_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="agent_conversations.id", index=True)
    role: str = Field(description="user, assistant, or system")
    content: Optional[str] = Field(default=None)
    tool_calls_json: Optional[str] = Field(default=None)
    tool_results_json: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    conversation: Optional[AgentConversation] = Relationship(back_populates="messages")

    @property
    def tool_calls(self) -> Optional[List[Any]]:
        """Deserialize tool_calls from JSON storage."""
        if self.tool_calls_json:
            return json.loads(self.tool_calls_json)
        return None

    @tool_calls.setter
    def tool_calls(self, value: Optional[List[Any]]) -> None:
        """Serialize tool_calls to JSON for storage."""
        if value is not None:
            self.tool_calls_json = json.dumps(value)
        else:
            self.tool_calls_json = None

    @property
    def tool_results(self) -> Optional[List[Any]]:
        """Deserialize tool_results from JSON storage."""
        if self.tool_results_json:
            return json.loads(self.tool_results_json)
        return None

    @tool_results.setter
    def tool_results(self, value: Optional[List[Any]]) -> None:
        """Serialize tool_results to JSON for storage."""
        if value is not None:
            self.tool_results_json = json.dumps(value)
        else:
            self.tool_results_json = None
