"""Test email sync scheduler integration."""

import pytest
from unittest.mock import AsyncMock, patch

from cmd_center.backend.services.sync_scheduler import (
    run_email_sync,
    email_loop,
)


class TestEmailScheduler:
    """Test email scheduler functions."""

    @pytest.mark.asyncio
    async def test_run_email_sync_calls_sync_all(self):
        """run_email_sync calls sync_all_mailboxes."""
        with patch("cmd_center.backend.services.sync_scheduler.sync_all_mailboxes") as mock_sync:
            mock_sync.return_value = {
                "synced": 2,
                "skipped": 0,
                "failed": 0,
            }
            await run_email_sync()
            mock_sync.assert_called_once()

    def test_email_loop_exists(self):
        """email_loop function is defined."""
        assert callable(email_loop)
