"""Tests for PendingAction dataclass."""

import pytest
from datetime import datetime, timezone

from cmd_center.agent.tools.base import PendingAction


class TestPendingAction:
    """Tests for PendingAction dataclass."""

    def test_pending_action_creation(self):
        """PendingAction can be created with required fields."""
        action = PendingAction(
            tool_name="request_create_task",
            preview="Create task: Follow up with client",
            payload={"title": "Follow up with client", "priority": "high"},
        )

        assert action.tool_name == "request_create_task"
        assert action.preview == "Create task: Follow up with client"
        assert action.payload["title"] == "Follow up with client"
        assert action.created_at is not None

    def test_pending_action_has_timestamp(self):
        """PendingAction automatically sets created_at timestamp."""
        before = datetime.now(timezone.utc)
        action = PendingAction(
            tool_name="test",
            preview="test",
            payload={},
        )
        after = datetime.now(timezone.utc)

        assert before <= action.created_at <= after

    def test_pending_action_equality(self):
        """Two PendingActions with same data are equal."""
        ts = datetime.now(timezone.utc)
        action1 = PendingAction(
            tool_name="test",
            preview="test",
            payload={"a": 1},
            created_at=ts,
        )
        action2 = PendingAction(
            tool_name="test",
            preview="test",
            payload={"a": 1},
            created_at=ts,
        )

        assert action1 == action2
