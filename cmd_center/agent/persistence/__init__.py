"""Persistence package for agent conversations."""

from .models import AgentConversation, AgentMessage

# Lazy import to avoid circular dependency with backend.db
_ConversationStore = None


def __getattr__(name):
    """Lazy loading of ConversationStore to avoid circular imports."""
    if name == "ConversationStore":
        global _ConversationStore
        if _ConversationStore is None:
            from .conversation_store import ConversationStore as _CS
            _ConversationStore = _CS
        return _ConversationStore
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["AgentConversation", "AgentMessage", "ConversationStore"]
