"""File-based conversation logging for the agent."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List


DEFAULT_LOG_DIR = "logs/omnious"


class ConversationLogger:
    """Logger that writes conversation messages to JSONL files."""

    def __init__(self, log_dir: str = DEFAULT_LOG_DIR):
        """Initialize the conversation logger.

        Args:
            log_dir: Directory to write log files to
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_file_path(self) -> Path:
        """Get the log file path for today."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.log_dir / f"conversations_{today}.jsonl"

    def log_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        tokens: int = 0,
        tools_used: Optional[List[str]] = None,
    ) -> None:
        """Log a message to the JSONL file.

        Args:
            conversation_id: ID of the conversation
            role: Message role (user, assistant, system)
            content: Message content
            tokens: Number of tokens used
            tools_used: List of tools used in this message
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "tokens": tokens,
        }

        if tools_used:
            log_entry["tools_used"] = tools_used

        log_file = self._get_log_file_path()
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")


# Singleton instance
_conversation_logger: Optional[ConversationLogger] = None


def get_conversation_logger() -> ConversationLogger:
    """Get or create conversation logger singleton."""
    global _conversation_logger
    if _conversation_logger is None:
        _conversation_logger = ConversationLogger()
    return _conversation_logger
