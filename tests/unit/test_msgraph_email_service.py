"""Unit tests for MSGraph Email Service.

Tests cover:
- Service initialization
- Email response model conversion
- Filter building
- Attachment handling
- Cached email reads from local database
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from sqlmodel import Session

from cmd_center.backend.services.msgraph_email_service import (
    MSGraphEmailService,
    get_msgraph_email_service,
)
from cmd_center.backend.models.msgraph_email_models import (
    EmailMessage,
    EmailAddress,
    EmailAttachment,
    MailFolder,
    EmailAttachmentInput,
)
from cmd_center.backend.integrations.microsoft_client import (
    EmailMessageDTO,
    EmailRecipient,
    EmailAddress as ClientEmailAddress,
    EmailBody,
    MailFolderDTO,
    EmailAttachmentDTO,
)
from cmd_center.backend.db import CachedEmail, CachedMailFolder


class TestMSGraphEmailServiceInit:
    """Test service initialization."""

    def test_default_mailbox(self):
        """Service uses default mailbox."""
        service = MSGraphEmailService()
        assert service.default_mailbox == "mohammed@gyptech.com.sa"

    def test_custom_mailbox(self):
        """Service accepts custom default mailbox."""
        service = MSGraphEmailService(default_mailbox="test@example.com")
        assert service.default_mailbox == "test@example.com"

    def test_default_attachments_dir(self):
        """Service uses default attachments directory."""
        service = MSGraphEmailService()
        assert service.attachments_dir == Path("attachments")

    def test_custom_attachments_dir(self):
        """Service accepts custom attachments directory."""
        service = MSGraphEmailService(attachments_dir=Path("/tmp/attachments"))
        assert service.attachments_dir == Path("/tmp/attachments")

    def test_resolve_mailbox_uses_default(self):
        """Resolve mailbox returns default when None provided."""
        service = MSGraphEmailService(default_mailbox="default@example.com")
        assert service._resolve_mailbox(None) == "default@example.com"

    def test_resolve_mailbox_uses_provided(self):
        """Resolve mailbox returns provided value."""
        service = MSGraphEmailService(default_mailbox="default@example.com")
        assert service._resolve_mailbox("other@example.com") == "other@example.com"


class TestMessageConversion:
    """Test EmailMessageDTO to EmailMessage conversion."""

    def test_convert_simple_message(self):
        """Convert message with minimal fields."""
        service = MSGraphEmailService()

        dto = EmailMessageDTO(
            id="msg-123",
            subject="Test Subject",
            body_preview="This is a preview...",
            is_read=False,
            has_attachments=False,
            importance="normal",
        )

        result = service._convert_message(dto)

        assert result.id == "msg-123"
        assert result.subject == "Test Subject"
        assert result.body_preview == "This is a preview..."
        assert result.is_read is False
        assert result.has_attachments is False

    def test_convert_message_with_sender(self):
        """Convert message with sender."""
        service = MSGraphEmailService()

        dto = EmailMessageDTO(
            id="msg-123",
            subject="Test",
            from_recipient=EmailRecipient(
                email_address=ClientEmailAddress(
                    address="sender@example.com",
                    name="Sender Name",
                )
            ),
        )

        result = service._convert_message(dto)

        assert result.sender is not None
        assert result.sender.address == "sender@example.com"
        assert result.sender.name == "Sender Name"

    def test_convert_message_with_recipients(self):
        """Convert message with to/cc recipients."""
        service = MSGraphEmailService()

        dto = EmailMessageDTO(
            id="msg-123",
            subject="Test",
            to_recipients=[
                EmailRecipient(
                    email_address=ClientEmailAddress(address="to1@example.com")
                ),
                EmailRecipient(
                    email_address=ClientEmailAddress(address="to2@example.com", name="To 2")
                ),
            ],
            cc_recipients=[
                EmailRecipient(
                    email_address=ClientEmailAddress(address="cc@example.com")
                ),
            ],
        )

        result = service._convert_message(dto)

        assert len(result.to_recipients) == 2
        assert result.to_recipients[0].address == "to1@example.com"
        assert result.to_recipients[1].name == "To 2"
        assert len(result.cc_recipients) == 1

    def test_convert_message_with_body(self):
        """Convert message with body content."""
        service = MSGraphEmailService()

        dto = EmailMessageDTO(
            id="msg-123",
            subject="Test",
            body=EmailBody(
                content_type="html",
                content="<p>Hello World</p>",
            ),
        )

        result = service._convert_message(dto)

        assert result.body_content == "<p>Hello World</p>"
        assert result.body_type == "html"

    def test_convert_message_with_dates(self):
        """Convert message with datetime fields."""
        service = MSGraphEmailService()

        dto = EmailMessageDTO(
            id="msg-123",
            subject="Test",
            received_datetime="2024-01-15T10:30:00Z",
            sent_datetime="2024-01-15T10:29:00Z",
        )

        result = service._convert_message(dto)

        assert result.received_at is not None
        assert result.received_at.year == 2024
        assert result.received_at.month == 1
        assert result.received_at.day == 15


class TestAttachmentConversion:
    """Test EmailAttachmentDTO to EmailAttachment conversion."""

    def test_convert_attachment(self):
        """Convert attachment metadata."""
        service = MSGraphEmailService()

        dto = EmailAttachmentDTO(
            id="att-123",
            name="document.pdf",
            content_type="application/pdf",
            size=1024,
            is_inline=False,
        )

        result = service._convert_attachment(dto)

        assert result.id == "att-123"
        assert result.name == "document.pdf"
        assert result.content_type == "application/pdf"
        assert result.size == 1024
        assert result.is_inline is False


class TestFolderConversion:
    """Test MailFolderDTO to MailFolder conversion."""

    def test_convert_folder(self):
        """Convert folder metadata."""
        service = MSGraphEmailService()

        dto = MailFolderDTO(
            id="folder-123",
            display_name="Inbox",
            parent_folder_id=None,
            child_folder_count=2,
            unread_item_count=5,
            total_item_count=100,
        )

        result = service._convert_folder(dto)

        assert result.id == "folder-123"
        assert result.name == "Inbox"
        assert result.unread_count == 5
        assert result.total_count == 100


class TestFolderResolution:
    """Test folder name to ID resolution."""

    @pytest.mark.asyncio
    async def test_resolve_well_known_folder(self):
        """Well-known folder names are passed through."""
        service = MSGraphEmailService()

        # Mock the client
        service._client = MagicMock()

        result = await service._resolve_folder_id("test@example.com", "inbox")
        assert result == "inbox"

        result = await service._resolve_folder_id("test@example.com", "sentitems")
        assert result == "sentitems"

    @pytest.mark.asyncio
    async def test_resolve_folder_by_id(self):
        """Long strings are treated as folder IDs."""
        service = MSGraphEmailService()
        service._client = MagicMock()

        # Long ID-like string (>50 chars)
        long_id = "AAMkAGVmMDEzMTM4LTZmYWUtNDdkNC1hMDZiLTU1OGY5OTZhYmY4OAAuAAAAAAAiQ8W967B7TKBjg"
        result = await service._resolve_folder_id("test@example.com", long_id)
        assert result == long_id

    @pytest.mark.asyncio
    async def test_resolve_folder_by_name(self):
        """Custom folder names are looked up."""
        service = MSGraphEmailService()
        service._client = MagicMock()
        service._client.get_mail_folder_by_name = AsyncMock(
            return_value=MailFolderDTO(
                id="custom-folder-id",
                display_name="Custom Folder",
            )
        )

        result = await service._resolve_folder_id("test@example.com", "Custom Folder")
        assert result == "custom-folder-id"


class TestAttachmentPreparation:
    """Test attachment preparation for sending."""

    @pytest.mark.asyncio
    async def test_prepare_attachment_missing_file(self, tmp_path):
        """Missing file returns None."""
        service = MSGraphEmailService()

        att = EmailAttachmentInput(file_path=tmp_path / "nonexistent.pdf")
        result = await service._prepare_attachment(att)

        assert result is None

    @pytest.mark.asyncio
    async def test_prepare_attachment_success(self, tmp_path):
        """Valid file is prepared correctly."""
        service = MSGraphEmailService()

        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World")

        att = EmailAttachmentInput(file_path=test_file)
        result = await service._prepare_attachment(att)

        assert result is not None
        assert result["name"] == "test.txt"
        assert result["@odata.type"] == "#microsoft.graph.fileAttachment"
        assert "contentBytes" in result

    @pytest.mark.asyncio
    async def test_prepare_attachment_with_custom_name(self, tmp_path):
        """Custom filename is used when provided."""
        service = MSGraphEmailService()

        test_file = tmp_path / "original.txt"
        test_file.write_text("Content")

        att = EmailAttachmentInput(file_path=test_file, name="renamed.txt")
        result = await service._prepare_attachment(att)

        assert result["name"] == "renamed.txt"


class TestEmailRetrieval:
    """Test email retrieval methods."""

    @pytest.mark.asyncio
    async def test_get_emails(self):
        """Get emails from mailbox."""
        service = MSGraphEmailService()
        service._client = MagicMock()
        service._client.get_messages = AsyncMock(
            return_value=[
                EmailMessageDTO(id="msg-1", subject="Email 1"),
                EmailMessageDTO(id="msg-2", subject="Email 2"),
            ]
        )

        result = await service.get_emails(mailbox="test@example.com", folder="inbox")

        assert len(result) == 2
        assert result[0].id == "msg-1"
        assert result[1].id == "msg-2"

    @pytest.mark.asyncio
    async def test_get_emails_unread_only(self):
        """Get emails with unread filter."""
        service = MSGraphEmailService()
        service._client = MagicMock()
        service._client.get_messages = AsyncMock(return_value=[])

        await service.get_emails(mailbox="test@example.com", unread_only=True)

        # Verify filter was passed
        call_args = service._client.get_messages.call_args
        assert call_args.kwargs["filter_query"] == "isRead eq false"

    @pytest.mark.asyncio
    async def test_get_email_by_id(self):
        """Get single email by ID."""
        service = MSGraphEmailService()
        service._client = MagicMock()
        service._client.get_message_by_id = AsyncMock(
            return_value=EmailMessageDTO(
                id="msg-123",
                subject="Test Email",
                has_attachments=False,
            )
        )

        result = await service.get_email_by_id("msg-123", mailbox="test@example.com")

        assert result is not None
        assert result.id == "msg-123"
        assert result.subject == "Test Email"


class TestEmailActions:
    """Test email action methods."""

    @pytest.mark.asyncio
    async def test_mark_as_read(self):
        """Mark email as read."""
        service = MSGraphEmailService()
        service._client = MagicMock()
        service._client.update_message = AsyncMock(return_value=True)

        result = await service.mark_as_read("msg-123", mailbox="test@example.com")

        assert result is True
        service._client.update_message.assert_called_once_with(
            mailbox="test@example.com",
            message_id="msg-123",
            is_read=True,
        )

    @pytest.mark.asyncio
    async def test_reply(self):
        """Reply to email."""
        service = MSGraphEmailService()
        service._client = MagicMock()
        service._client.reply_to_message = AsyncMock(return_value=True)

        result = await service.reply(
            "msg-123",
            mailbox="test@example.com",
            comment="Thanks for the email!",
        )

        assert result is True
        service._client.reply_to_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_forward(self):
        """Forward email."""
        service = MSGraphEmailService()
        service._client = MagicMock()
        service._client.forward_message = AsyncMock(return_value=True)

        result = await service.forward(
            "msg-123",
            to=["forward@example.com"],
            mailbox="test@example.com",
            comment="FYI",
        )

        assert result is True


class TestSendEmail:
    """Test email sending."""

    @pytest.mark.asyncio
    async def test_send_simple_email(self):
        """Send email without attachments."""
        service = MSGraphEmailService()
        service._client = MagicMock()
        service._client.send_mail = AsyncMock(return_value=True)

        result = await service.send_email(
            from_mailbox="sender@example.com",
            to=["recipient@example.com"],
            subject="Test Subject",
            body="<p>Hello World</p>",
        )

        assert result is True
        service._client.send_mail.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_with_cc_bcc(self):
        """Send email with CC and BCC."""
        service = MSGraphEmailService()
        service._client = MagicMock()
        service._client.send_mail = AsyncMock(return_value=True)

        await service.send_email(
            from_mailbox="sender@example.com",
            to=["to@example.com"],
            subject="Test",
            body="Body",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
        )

        call_args = service._client.send_mail.call_args
        assert call_args.kwargs["cc_recipients"] == ["cc@example.com"]
        assert call_args.kwargs["bcc_recipients"] == ["bcc@example.com"]


class TestFolderManagement:
    """Test folder management methods."""

    @pytest.mark.asyncio
    async def test_get_folders(self):
        """Get mail folders."""
        service = MSGraphEmailService()
        service._client = MagicMock()
        service._client.get_mail_folders = AsyncMock(
            return_value=[
                MailFolderDTO(id="f1", display_name="Inbox"),
                MailFolderDTO(id="f2", display_name="Sent Items"),
            ]
        )

        result = await service.get_folders(mailbox="test@example.com")

        assert len(result) == 2
        assert result[0].name == "Inbox"
        assert result[1].name == "Sent Items"

    @pytest.mark.asyncio
    async def test_create_folder(self):
        """Create mail folder."""
        service = MSGraphEmailService()
        service._client = MagicMock()
        service._client.create_mail_folder = AsyncMock(
            return_value=MailFolderDTO(id="new-folder", display_name="New Folder")
        )

        result = await service.create_folder(
            folder_name="New Folder",
            mailbox="test@example.com",
        )

        assert result.id == "new-folder"
        assert result.name == "New Folder"


class TestServiceSingleton:
    """Test singleton pattern."""

    def test_get_service_creates_instance(self):
        """get_msgraph_email_service creates instance."""
        # Reset global state
        import cmd_center.backend.services.msgraph_email_service as module
        module._msgraph_email_service = None

        service = get_msgraph_email_service()
        assert service is not None
        assert isinstance(service, MSGraphEmailService)

    def test_get_service_returns_same_instance(self):
        """get_msgraph_email_service returns same instance."""
        import cmd_center.backend.services.msgraph_email_service as module
        module._msgraph_email_service = None

        service1 = get_msgraph_email_service()
        service2 = get_msgraph_email_service()
        assert service1 is service2


class TestCachedEmailReads:
    """Test reading emails from local cache."""

    def test_get_cached_emails(self, override_db, test_engine):
        """Get emails from local cache."""
        # Insert test data
        with Session(test_engine) as session:
            email = CachedEmail(
                graph_id="cached-msg-123",
                mailbox="test@example.com",
                subject="Cached Subject",
                body_preview="Preview...",
                sender_address="sender@example.com",
                received_at=datetime.now(timezone.utc),
                is_read=False,
                has_attachments=False,
            )
            session.add(email)
            session.commit()

        service = MSGraphEmailService(default_mailbox="test@example.com")
        result = service.get_cached_emails(mailbox="test@example.com", limit=10)

        assert len(result) >= 1
        assert any(e.subject == "Cached Subject" for e in result)

    def test_get_cached_emails_unread_only(self, override_db, test_engine):
        """Get only unread emails from cache."""
        with Session(test_engine) as session:
            # Add read email
            read_email = CachedEmail(
                graph_id="cached-read-1",
                mailbox="test@example.com",
                subject="Read Email",
                is_read=True,
                has_attachments=False,
            )
            # Add unread email
            unread_email = CachedEmail(
                graph_id="cached-unread-1",
                mailbox="test@example.com",
                subject="Unread Email",
                is_read=False,
                has_attachments=False,
            )
            session.add(read_email)
            session.add(unread_email)
            session.commit()

        service = MSGraphEmailService(default_mailbox="test@example.com")
        result = service.get_cached_emails(mailbox="test@example.com", unread_only=True)

        assert len(result) >= 1
        assert all(e.is_read is False for e in result)
        assert any(e.subject == "Unread Email" for e in result)

    def test_get_cached_emails_by_folder(self, override_db, test_engine):
        """Get emails filtered by folder_id."""
        with Session(test_engine) as session:
            email1 = CachedEmail(
                graph_id="cached-inbox-1",
                mailbox="test@example.com",
                folder_id="inbox",
                subject="Inbox Email",
                is_read=False,
                has_attachments=False,
            )
            email2 = CachedEmail(
                graph_id="cached-sent-1",
                mailbox="test@example.com",
                folder_id="sentitems",
                subject="Sent Email",
                is_read=True,
                has_attachments=False,
            )
            session.add(email1)
            session.add(email2)
            session.commit()

        service = MSGraphEmailService(default_mailbox="test@example.com")
        result = service.get_cached_emails(
            mailbox="test@example.com", folder_id="inbox"
        )

        assert len(result) >= 1
        assert all(e.folder_id == "inbox" for e in result)

    def test_get_cached_email_by_id(self, override_db, test_engine):
        """Get single email from cache by Graph ID."""
        with Session(test_engine) as session:
            email = CachedEmail(
                graph_id="cached-single-123",
                mailbox="test@example.com",
                subject="Single Email",
                is_read=True,
                has_attachments=False,
            )
            session.add(email)
            session.commit()

        service = MSGraphEmailService(default_mailbox="test@example.com")
        result = service.get_cached_email_by_id(
            "cached-single-123", mailbox="test@example.com"
        )

        assert result is not None
        assert result.subject == "Single Email"
        assert result.is_read is True

    def test_get_cached_email_by_id_not_found(self, override_db, test_engine):
        """Return None when email not found in cache."""
        service = MSGraphEmailService(default_mailbox="test@example.com")
        result = service.get_cached_email_by_id(
            "nonexistent-id", mailbox="test@example.com"
        )

        assert result is None

    def test_get_cached_email_with_recipients(self, override_db, test_engine):
        """Get email with to/cc recipients from cache."""
        import json

        with Session(test_engine) as session:
            email = CachedEmail(
                graph_id="cached-recipients-1",
                mailbox="test@example.com",
                subject="Email with Recipients",
                sender_address="sender@example.com",
                sender_name="Sender Name",
                to_recipients_json=json.dumps([
                    {"address": "to1@example.com", "name": "To One"},
                    {"address": "to2@example.com"},
                ]),
                cc_recipients_json=json.dumps([
                    {"address": "cc@example.com", "name": "CC User"},
                ]),
                is_read=False,
                has_attachments=False,
            )
            session.add(email)
            session.commit()

        service = MSGraphEmailService(default_mailbox="test@example.com")
        result = service.get_cached_email_by_id(
            "cached-recipients-1", mailbox="test@example.com"
        )

        assert result is not None
        assert result.sender.address == "sender@example.com"
        assert result.sender.name == "Sender Name"
        assert len(result.to_recipients) == 2
        assert result.to_recipients[0].address == "to1@example.com"
        assert result.to_recipients[0].name == "To One"
        assert len(result.cc_recipients) == 1
        assert result.cc_recipients[0].address == "cc@example.com"

    def test_get_cached_folders(self, override_db, test_engine):
        """Get mail folders from cache."""
        with Session(test_engine) as session:
            folder1 = CachedMailFolder(
                graph_id="folder-inbox-id",
                mailbox="test@example.com",
                display_name="Inbox",
                unread_count=5,
                total_count=100,
            )
            folder2 = CachedMailFolder(
                graph_id="folder-sent-id",
                mailbox="test@example.com",
                display_name="Sent Items",
                unread_count=0,
                total_count=50,
            )
            session.add(folder1)
            session.add(folder2)
            session.commit()

        service = MSGraphEmailService(default_mailbox="test@example.com")
        result = service.get_cached_folders(mailbox="test@example.com")

        assert len(result) >= 2
        folder_names = [f.name for f in result]
        assert "Inbox" in folder_names
        assert "Sent Items" in folder_names

        # Verify folder attributes
        inbox = next(f for f in result if f.name == "Inbox")
        assert inbox.id == "folder-inbox-id"
        assert inbox.unread_count == 5
        assert inbox.total_count == 100

    def test_get_cached_emails_pagination(self, override_db, test_engine):
        """Test pagination with offset and limit."""
        with Session(test_engine) as session:
            for i in range(5):
                email = CachedEmail(
                    graph_id=f"cached-page-{i}",
                    mailbox="test@example.com",
                    subject=f"Email {i}",
                    received_at=datetime(2024, 1, 1 + i, tzinfo=timezone.utc),
                    is_read=False,
                    has_attachments=False,
                )
                session.add(email)
            session.commit()

        service = MSGraphEmailService(default_mailbox="test@example.com")

        # Get first 2 emails
        result1 = service.get_cached_emails(
            mailbox="test@example.com", limit=2, offset=0
        )
        assert len(result1) == 2

        # Get next 2 emails
        result2 = service.get_cached_emails(
            mailbox="test@example.com", limit=2, offset=2
        )
        assert len(result2) == 2

        # Verify different emails returned
        ids1 = {e.id for e in result1}
        ids2 = {e.id for e in result2}
        assert ids1.isdisjoint(ids2)
