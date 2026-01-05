"""Tests for file-based conversation logging."""

import pytest
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from cmd_center.agent.observability.logger import ConversationLogger, get_conversation_logger


class TestConversationLogger:
    """Tests for ConversationLogger."""

    @pytest.fixture
    def temp_log_dir(self, tmp_path):
        """Create temporary log directory."""
        log_dir = tmp_path / "logs" / "omnious"
        log_dir.mkdir(parents=True)
        return log_dir

    @pytest.fixture
    def logger(self, temp_log_dir):
        """Create logger with temp directory."""
        return ConversationLogger(log_dir=str(temp_log_dir))

    def test_logger_creates_log_directory(self, tmp_path):
        """Logger creates log directory if it doesn't exist."""
        log_dir = tmp_path / "new_logs" / "omnious"
        logger = ConversationLogger(log_dir=str(log_dir))

        assert log_dir.exists()

    def test_log_message_writes_jsonl(self, logger, temp_log_dir):
        """Log message writes to JSONL file."""
        logger.log_message(
            conversation_id=1,
            role="user",
            content="Hello",
            tokens=10,
        )

        log_files = list(temp_log_dir.glob("conversations_*.jsonl"))
        assert len(log_files) == 1

        with open(log_files[0], "r") as f:
            line = f.readline()
            data = json.loads(line)

        assert data["conversation_id"] == 1
        assert data["role"] == "user"
        assert data["content"] == "Hello"
        assert data["tokens"] == 10

    def test_log_message_includes_timestamp(self, logger, temp_log_dir):
        """Log message includes ISO timestamp."""
        logger.log_message(
            conversation_id=1,
            role="assistant",
            content="Hi there",
        )

        log_files = list(temp_log_dir.glob("conversations_*.jsonl"))
        with open(log_files[0], "r") as f:
            data = json.loads(f.readline())

        assert "timestamp" in data
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    def test_log_message_includes_tools_used(self, logger, temp_log_dir):
        """Log message includes tools_used when provided."""
        logger.log_message(
            conversation_id=1,
            role="assistant",
            content="Here are the deals",
            tools_used=["get_overdue_deals", "get_stuck_deals"],
        )

        log_files = list(temp_log_dir.glob("conversations_*.jsonl"))
        with open(log_files[0], "r") as f:
            data = json.loads(f.readline())

        assert data["tools_used"] == ["get_overdue_deals", "get_stuck_deals"]

    def test_log_file_named_with_date(self, logger, temp_log_dir):
        """Log file is named with current date."""
        logger.log_message(conversation_id=1, role="user", content="test")

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        expected_file = temp_log_dir / f"conversations_{today}.jsonl"

        assert expected_file.exists()

    def test_multiple_messages_append_to_file(self, logger, temp_log_dir):
        """Multiple messages append to same file."""
        logger.log_message(conversation_id=1, role="user", content="msg1")
        logger.log_message(conversation_id=1, role="assistant", content="msg2")
        logger.log_message(conversation_id=1, role="user", content="msg3")

        log_files = list(temp_log_dir.glob("conversations_*.jsonl"))
        assert len(log_files) == 1

        with open(log_files[0], "r") as f:
            lines = f.readlines()

        assert len(lines) == 3

    def test_singleton_get_conversation_logger(self, temp_log_dir):
        """get_conversation_logger returns singleton."""
        with patch("cmd_center.agent.observability.logger.DEFAULT_LOG_DIR", str(temp_log_dir)):
            logger1 = get_conversation_logger()
            logger2 = get_conversation_logger()

            assert logger1 is logger2
