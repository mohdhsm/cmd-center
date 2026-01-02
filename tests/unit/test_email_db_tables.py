"""Test email cache database tables."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from cmd_center.backend.db import (
    CachedEmail,
    CachedEmailAttachment,
    CachedMailFolder,
)


class TestCachedEmailTable:
    """Test CachedEmail table operations."""

    def test_create_cached_email(self, test_engine):
        """Can create a cached email record."""
        unique_id = f"test-email-{uuid.uuid4()}"

        with Session(test_engine) as session:
            email = CachedEmail(
                graph_id=unique_id,
                mailbox="mohammed@gyptech.com.sa",
                folder_id="inbox",
                subject="Test Email",
                body_preview="This is a preview...",
                body_content="<p>Full body</p>",
                body_type="html",
                sender_address="sender@example.com",
                sender_name="Sender Name",
                received_at=datetime.now(timezone.utc),
                is_read=False,
                has_attachments=False,
                importance="normal",
            )
            session.add(email)
            session.commit()

            # Query back
            result = session.exec(
                select(CachedEmail).where(CachedEmail.graph_id == unique_id)
            ).first()

            assert result is not None
            assert result.subject == "Test Email"
            assert result.mailbox == "mohammed@gyptech.com.sa"

    def test_cached_email_unique_constraint(self, test_engine):
        """Graph ID + mailbox must be unique."""
        unique_id = f"unique-test-{uuid.uuid4()}"

        with Session(test_engine) as session:
            email1 = CachedEmail(
                graph_id=unique_id,
                mailbox="test@gyptech.com.sa",
                subject="Email 1",
            )
            session.add(email1)
            session.commit()

        # Same graph_id + mailbox should fail
        with Session(test_engine) as session:
            email2 = CachedEmail(
                graph_id=unique_id,
                mailbox="test@gyptech.com.sa",
                subject="Email 2",
            )
            session.add(email2)
            with pytest.raises(IntegrityError):
                session.commit()


class TestCachedEmailAttachmentTable:
    """Test CachedEmailAttachment table operations."""

    def test_create_cached_attachment(self, test_engine):
        """Can create attachment metadata."""
        unique_id = f"att-{uuid.uuid4()}"

        with Session(test_engine) as session:
            attachment = CachedEmailAttachment(
                graph_id=unique_id,
                email_graph_id=f"email-{uuid.uuid4()}",
                mailbox="mohammed@gyptech.com.sa",
                name="document.pdf",
                content_type="application/pdf",
                size=1024,
                is_inline=False,
            )
            session.add(attachment)
            session.commit()

            result = session.exec(
                select(CachedEmailAttachment).where(CachedEmailAttachment.graph_id == unique_id)
            ).first()

            assert result is not None
            assert result.name == "document.pdf"

    def test_cached_attachment_unique_constraint(self, test_engine):
        """Graph ID + mailbox must be unique."""
        unique_id = f"att-unique-{uuid.uuid4()}"

        with Session(test_engine) as session:
            attachment1 = CachedEmailAttachment(
                graph_id=unique_id,
                email_graph_id=f"email-{uuid.uuid4()}",
                mailbox="test@gyptech.com.sa",
                name="doc1.pdf",
            )
            session.add(attachment1)
            session.commit()

        # Same graph_id + mailbox should fail
        with Session(test_engine) as session:
            attachment2 = CachedEmailAttachment(
                graph_id=unique_id,
                email_graph_id=f"email-{uuid.uuid4()}",
                mailbox="test@gyptech.com.sa",
                name="doc2.pdf",
            )
            session.add(attachment2)
            with pytest.raises(IntegrityError):
                session.commit()


class TestCachedMailFolderTable:
    """Test CachedMailFolder table operations."""

    def test_create_cached_folder(self, test_engine):
        """Can create folder metadata."""
        unique_id = f"folder-{uuid.uuid4()}"

        with Session(test_engine) as session:
            folder = CachedMailFolder(
                graph_id=unique_id,
                mailbox="mohammed@gyptech.com.sa",
                display_name="Inbox",
                unread_count=5,
                total_count=100,
            )
            session.add(folder)
            session.commit()

            result = session.exec(
                select(CachedMailFolder).where(CachedMailFolder.graph_id == unique_id)
            ).first()

            assert result is not None
            assert result.display_name == "Inbox"
            assert result.unread_count == 5

    def test_cached_folder_unique_constraint(self, test_engine):
        """Graph ID + mailbox must be unique."""
        unique_id = f"folder-unique-{uuid.uuid4()}"

        with Session(test_engine) as session:
            folder1 = CachedMailFolder(
                graph_id=unique_id,
                mailbox="test@gyptech.com.sa",
                display_name="Inbox",
            )
            session.add(folder1)
            session.commit()

        # Same graph_id + mailbox should fail
        with Session(test_engine) as session:
            folder2 = CachedMailFolder(
                graph_id=unique_id,
                mailbox="test@gyptech.com.sa",
                display_name="Inbox Copy",
            )
            session.add(folder2)
            with pytest.raises(IntegrityError):
                session.commit()
