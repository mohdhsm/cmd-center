"""Test email sync module."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from sqlmodel import Session, select

from cmd_center.backend.db import CachedEmail, CachedMailFolder
from cmd_center.backend.services.email_sync import (
    sync_emails_for_mailbox,
    sync_folders_for_mailbox,
    get_last_email_sync_time,
    update_email_sync_metadata,
    SYNC_MAILBOXES,
)


class TestEmailSyncMetadata:
    """Test sync metadata helpers."""

    def test_sync_mailboxes_defined(self):
        """SYNC_MAILBOXES contains expected mailboxes."""
        assert "mohammed@gyptech.com.sa" in SYNC_MAILBOXES
        assert "info@gyptech.com.sa" in SYNC_MAILBOXES

    def test_get_last_sync_time_returns_none_initially(self, override_db):
        """Returns None when no sync has occurred."""
        result = get_last_email_sync_time("test@example.com")
        assert result is None

    def test_update_and_get_sync_time(self, override_db):
        """Can update and retrieve sync time."""
        update_email_sync_metadata("test@example.com", "success", records_synced=10)
        result = get_last_email_sync_time("test@example.com")
        assert result is not None


class TestSyncFolders:
    """Test folder sync."""

    @pytest.mark.asyncio
    async def test_sync_folders_creates_records(self, override_db, test_engine):
        """sync_folders_for_mailbox creates CachedMailFolder records."""
        # Mock the MSGraph service
        mock_folder = MagicMock()
        mock_folder.id = "folder-123"
        mock_folder.name = "Inbox"
        mock_folder.parent_folder_id = None
        mock_folder.child_folder_count = 0
        mock_folder.unread_count = 5
        mock_folder.total_count = 100

        with patch("cmd_center.backend.services.email_sync.get_msgraph_email_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_folders = AsyncMock(return_value=[mock_folder])
            mock_get_service.return_value = mock_service

            result = await sync_folders_for_mailbox("test@example.com")

        assert result["folders_synced"] == 1

        # Verify database record
        with Session(test_engine) as session:
            folder = session.exec(
                select(CachedMailFolder).where(CachedMailFolder.graph_id == "folder-123")
            ).first()
            assert folder is not None
            assert folder.display_name == "Inbox"
            assert folder.unread_count == 5


class TestSyncEmails:
    """Test email sync."""

    @pytest.mark.asyncio
    async def test_sync_emails_creates_records(self, override_db, test_engine):
        """sync_emails_for_mailbox creates CachedEmail records."""
        # Mock email
        mock_email = MagicMock()
        mock_email.id = "msg-123"
        mock_email.subject = "Test Subject"
        mock_email.body_preview = "Preview..."
        mock_email.body_content = "<p>Body</p>"
        mock_email.body_type = "html"
        mock_sender = MagicMock()
        mock_sender.address = "sender@example.com"
        mock_sender.name = "Sender"
        mock_email.sender = mock_sender
        mock_email.to_recipients = []
        mock_email.cc_recipients = []
        mock_email.received_at = datetime.now(timezone.utc)
        mock_email.sent_at = None
        mock_email.is_read = False
        mock_email.has_attachments = False
        mock_email.importance = "normal"
        mock_email.folder_id = "inbox"
        mock_email.conversation_id = "conv-123"
        mock_email.web_link = None
        mock_email.is_draft = False
        mock_email.attachments = None

        with patch("cmd_center.backend.services.email_sync.get_msgraph_email_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_emails = AsyncMock(return_value=[mock_email])
            mock_service.get_folders = AsyncMock(return_value=[])
            mock_get_service.return_value = mock_service

            result = await sync_emails_for_mailbox("test@example.com", days_back=7)

        assert result["emails_synced"] >= 1

        # Verify database record
        with Session(test_engine) as session:
            email = session.exec(
                select(CachedEmail).where(CachedEmail.graph_id == "msg-123")
            ).first()
            assert email is not None
            assert email.subject == "Test Subject"
            assert email.sender_address == "sender@example.com"

    @pytest.mark.asyncio
    async def test_sync_emails_handles_msgraph_exception(self, override_db, test_engine):
        """sync_emails_for_mailbox handles MSGraph service exceptions gracefully."""
        with patch("cmd_center.backend.services.email_sync.get_msgraph_email_service") as mock_get_service:
            mock_service = MagicMock()
            # Folder sync succeeds, but email fetch throws an exception
            mock_service.get_folders = AsyncMock(return_value=[])
            mock_service.get_emails = AsyncMock(side_effect=Exception("MSGraph API connection failed"))
            mock_get_service.return_value = mock_service

            result = await sync_emails_for_mailbox("test@example.com", days_back=7)

        # Verify error handling returns proper result structure
        assert result["ok"] is False
        assert result["emails_synced"] == 0
        assert "error" in result
        assert "MSGraph API connection failed" in result["error"]
