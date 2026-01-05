"""Context management for conversation token limits."""

from typing import Optional, List, Dict, Any


class ContextManager:
    """Manages conversation context and token limits."""

    TOKENS_PER_CHAR = 0.25

    def __init__(
        self,
        max_tokens: int = 128000,
        warning_threshold: float = 0.8,
    ):
        self.max_tokens = max_tokens
        self.warning_threshold = warning_threshold
        self.total_tokens = 0
        self._messages: List[Dict[str, Any]] = []

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text.

        Uses a rough estimate of ~0.25 tokens per character.

        Args:
            text: The text to estimate tokens for.

        Returns:
            Estimated token count (minimum 1 for non-empty text).
        """
        if not text:
            return 0
        return max(1, int(len(text) * self.TOKENS_PER_CHAR))

    def add_message(self, role: str, content: str) -> int:
        """Add a message and track its tokens.

        Args:
            role: The message role (user, assistant, system).
            content: The message content.

        Returns:
            Number of tokens added.
        """
        tokens = self.estimate_tokens(content)
        self._messages.append({
            "role": role,
            "content": content,
            "tokens": tokens,
        })
        self.total_tokens += tokens
        return tokens

    def is_near_limit(self) -> bool:
        """Check if token usage is near the limit.

        Returns:
            True if usage is at or above warning threshold.
        """
        return self.total_tokens >= (self.max_tokens * self.warning_threshold)

    def get_warning(self) -> Optional[str]:
        """Get warning message if near limit.

        Returns:
            Warning message string, or None if not near limit.
        """
        if not self.is_near_limit():
            return None
        percentage = (self.total_tokens / self.max_tokens) * 100
        remaining = self.max_tokens - self.total_tokens
        return (
            f"Context usage: {percentage:.0f}% ({self.total_tokens:,}/{self.max_tokens:,} tokens). "
            f"~{remaining:,} tokens remaining. Consider starting a new conversation soon."
        )

    def get_usage_summary(self) -> str:
        """Get formatted token usage summary.

        Returns:
            Formatted string showing current usage.
        """
        percentage = (self.total_tokens / self.max_tokens) * 100
        return f"{self.total_tokens:,}/{self.max_tokens:,} tokens ({percentage:.0f}%)"

    def clear(self) -> None:
        """Reset token count and clear messages."""
        self._messages = []
        self.total_tokens = 0

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get a copy of all tracked messages.

        Returns:
            List of message dictionaries.
        """
        return self._messages.copy()
