# Email Sync to Database Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Sync Microsoft Graph emails to SQLite database for fast local viewing, eliminating API latency on reads.

**Architecture:** Create new `CachedEmail`, `CachedEmailAttachment`, and `CachedMailFolder` database tables. Add email sync functions to `email_sync.py` that fetch from Graph API and upsert to SQLite. Integrate with existing scheduler. The `MSGraphEmailService` gains optional methods to read from cache.

**Tech Stack:** SQLModel (database), httpx (async HTTP), Microsoft Graph API, asyncio (concurrency)

---

## Overview

### Database Tables (3 new)
1. `CachedEmail` - Email messages with all metadata
2. `CachedEmailAttachment` - Attachment metadata (not content)
3. `CachedMailFolder` - Folder structure and counts

### Sync Strategy
- **Initial Bootstrap:** Sync last 90 days of emails per mailbox
- **Incremental Sync:** Fetch only emails modified since last sync (Graph supports `deltaLink`)
- **Schedule:** Every 15 minutes for active mailboxes
- **TTL:** Skip mailbox if synced within last 15 minutes

### Mailboxes to Sync
- `mohammed@gyptech.com.sa` (default)
- `info@gyptech.com.sa`

---

## Task 1: Create Database Tables in db.py

**Files:**
- Modify: `cmd_center/backend/db.py`
- Test: `tests/unit/test_email_db_tables.py`

**Step 1: Write the failing test**

Create `tests/unit/test_email_db_tables.py`:

```python
"""Test email cache database tables."""

from datetime import datetime, timezone
from sqlmodel import Session, select

from cmd_center.backend.db import (
    engine,
    init_db,
    CachedEmail,
    CachedEmailAttachment,
    CachedMailFolder,
)


class TestCachedEmailTable:
    """Test CachedEmail table operations."""

    def test_create_cached_email(self):
        """Can create a cached email record."""
        init_db()

        with Session(engine) as session:
            email = CachedEmail(
                graph_id="AAMkAGVmMDEzMTM4LTZmYWUtNDdkNC1hMDZi",
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
                select(CachedEmail).where(CachedEmail.graph_id == "AAMkAGVmMDEzMTM4LTZmYWUtNDdkNC1hMDZi")
            ).first()

            assert result is not None
            assert result.subject == "Test Email"
            assert result.mailbox == "mohammed@gyptech.com.sa"

    def test_cached_email_unique_constraint(self):
        """Graph ID + mailbox must be unique."""
        init_db()

        with Session(engine) as session:
            email1 = CachedEmail(
                graph_id="unique-test-id",
                mailbox="test@gyptech.com.sa",
                subject="Email 1",
            )
            session.add(email1)
            session.commit()

        # Same graph_id + mailbox should fail
        with Session(engine) as session:
            email2 = CachedEmail(
                graph_id="unique-test-id",
                mailbox="test@gyptech.com.sa",
                subject="Email 2",
            )
            session.add(email2)
            try:
                session.commit()
                assert False, "Should have raised IntegrityError"
            except Exception:
                session.rollback()


class TestCachedEmailAttachmentTable:
    """Test CachedEmailAttachment table operations."""

    def test_create_cached_attachment(self):
        """Can create attachment metadata."""
        init_db()

        with Session(engine) as session:
            attachment = CachedEmailAttachment(
                graph_id="att-123",
                email_graph_id="AAMkAGVmMDEzMTM4LTZmYWUtNDdkNC1hMDZi",
                mailbox="mohammed@gyptech.com.sa",
                name="document.pdf",
                content_type="application/pdf",
                size=1024,
                is_inline=False,
            )
            session.add(attachment)
            session.commit()

            result = session.exec(
                select(CachedEmailAttachment).where(CachedEmailAttachment.graph_id == "att-123")
            ).first()

            assert result is not None
            assert result.name == "document.pdf"


class TestCachedMailFolderTable:
    """Test CachedMailFolder table operations."""

    def test_create_cached_folder(self):
        """Can create folder metadata."""
        init_db()

        with Session(engine) as session:
            folder = CachedMailFolder(
                graph_id="folder-123",
                mailbox="mohammed@gyptech.com.sa",
                display_name="Inbox",
                unread_count=5,
                total_count=100,
            )
            session.add(folder)
            session.commit()

            result = session.exec(
                select(CachedMailFolder).where(CachedMailFolder.graph_id == "folder-123")
            ).first()

            assert result is not None
            assert result.display_name == "Inbox"
            assert result.unread_count == 5
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_email_db_tables.py -v`
Expected: FAIL with "cannot import name 'CachedEmail' from 'cmd_center.backend.db'"

**Step 3: Write minimal implementation**

Add to `cmd_center/backend/db.py` before `init_db()`:

```python
# ============================================================================
# Email Cache Tables (Microsoft Graph)
# ============================================================================

class CachedEmail(SQLModel, table=True):
    """Cached email from Microsoft Graph for fast local reads."""
    __tablename__ = "cached_email"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Graph identification
    graph_id: str = Field(index=True)  # MS Graph message ID
    mailbox: str = Field(index=True)  # Which mailbox this belongs to

    # Folder
    folder_id: Optional[str] = Field(default=None, index=True)

    # Content
    subject: Optional[str] = Field(default=None, index=True)
    body_preview: str = ""
    body_content: Optional[str] = None
    body_type: Optional[str] = None  # "text" or "html"

    # Sender
    sender_address: Optional[str] = Field(default=None, index=True)
    sender_name: Optional[str] = None

    # Recipients (JSON arrays)
    to_recipients_json: Optional[str] = None
    cc_recipients_json: Optional[str] = None

    # Timestamps
    received_at: Optional[datetime] = Field(default=None, index=True)
    sent_at: Optional[datetime] = None

    # Flags
    is_read: bool = Field(default=False, index=True)
    has_attachments: bool = Field(default=False, index=True)
    importance: str = Field(default="normal")
    is_draft: bool = Field(default=False)

    # Graph metadata
    conversation_id: Optional[str] = Field(default=None, index=True)
    web_link: Optional[str] = None

    # Sync tracking
    synced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    graph_modified_at: Optional[datetime] = None  # From Graph API

    # Composite unique constraint via __table_args__
    __table_args__ = (
        Index("ix_cached_email_graph_mailbox", "graph_id", "mailbox", unique=True),
    )


class CachedEmailAttachment(SQLModel, table=True):
    """Cached email attachment metadata (not content)."""
    __tablename__ = "cached_email_attachment"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Graph identification
    graph_id: str = Field(index=True)  # MS Graph attachment ID
    email_graph_id: str = Field(index=True)  # Parent email's Graph ID
    mailbox: str = Field(index=True)

    # Metadata
    name: str
    content_type: str = "application/octet-stream"
    size: int = 0
    is_inline: bool = False

    # Sync tracking
    synced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CachedMailFolder(SQLModel, table=True):
    """Cached mail folder metadata."""
    __tablename__ = "cached_mail_folder"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Graph identification
    graph_id: str = Field(index=True)
    mailbox: str = Field(index=True)

    # Folder info
    display_name: str = Field(index=True)
    parent_folder_id: Optional[str] = None
    child_folder_count: int = 0

    # Counts
    unread_count: int = 0
    total_count: int = 0

    # Sync tracking
    synced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_cached_mail_folder_graph_mailbox", "graph_id", "mailbox", unique=True),
    )
```

**Step 4: Update `__all__` in db.py**

Add to the `__all__` list:

```python
    # Email Cache tables
    "CachedEmail",
    "CachedEmailAttachment",
    "CachedMailFolder",
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/unit/test_email_db_tables.py -v`
Expected: PASS (3 tests)

**Step 6: Commit**

```bash
git add cmd_center/backend/db.py tests/unit/test_email_db_tables.py
git commit -m "$(cat <<'EOF'
feat: add email cache database tables

Add CachedEmail, CachedEmailAttachment, and CachedMailFolder tables
for storing Microsoft Graph emails locally for fast reads.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Create Email Sync Module

**Files:**
- Create: `cmd_center/backend/services/email_sync.py`
- Test: `tests/unit/test_email_sync.py`

**Step 1: Write the failing test**

Create `tests/unit/test_email_sync.py`:

```python
"""Test email sync module."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from sqlmodel import Session, select

from cmd_center.backend.db import engine, init_db, CachedEmail, CachedMailFolder
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

    def test_get_last_sync_time_returns_none_initially(self):
        """Returns None when no sync has occurred."""
        init_db()
        result = get_last_email_sync_time("test@example.com")
        assert result is None

    def test_update_and_get_sync_time(self):
        """Can update and retrieve sync time."""
        init_db()
        update_email_sync_metadata("test@example.com", "success", records_synced=10)
        result = get_last_email_sync_time("test@example.com")
        assert result is not None


class TestSyncFolders:
    """Test folder sync."""

    @pytest.mark.asyncio
    async def test_sync_folders_creates_records(self):
        """sync_folders_for_mailbox creates CachedMailFolder records."""
        init_db()

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
        with Session(engine) as session:
            folder = session.exec(
                select(CachedMailFolder).where(CachedMailFolder.graph_id == "folder-123")
            ).first()
            assert folder is not None
            assert folder.display_name == "Inbox"
            assert folder.unread_count == 5


class TestSyncEmails:
    """Test email sync."""

    @pytest.mark.asyncio
    async def test_sync_emails_creates_records(self):
        """sync_emails_for_mailbox creates CachedEmail records."""
        init_db()

        # Mock email
        mock_email = MagicMock()
        mock_email.id = "msg-123"
        mock_email.subject = "Test Subject"
        mock_email.body_preview = "Preview..."
        mock_email.body_content = "<p>Body</p>"
        mock_email.body_type = "html"
        mock_email.sender = MagicMock(address="sender@example.com", name="Sender")
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
        with Session(engine) as session:
            email = session.exec(
                select(CachedEmail).where(CachedEmail.graph_id == "msg-123")
            ).first()
            assert email is not None
            assert email.subject == "Test Subject"
            assert email.sender_address == "sender@example.com"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_email_sync.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'cmd_center.backend.services.email_sync'"

**Step 3: Write minimal implementation**

Create `cmd_center/backend/services/email_sync.py`:

```python
"""Sync Microsoft Graph emails to local SQLite cache."""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlmodel import Session, select

from ..db import engine, CachedEmail, CachedEmailAttachment, CachedMailFolder, SyncMetadata
from ..models.msgraph_email_models import EmailMessage, MailFolder

logger = logging.getLogger(__name__)

# Mailboxes to sync
SYNC_MAILBOXES = [
    "mohammed@gyptech.com.sa",
    "info@gyptech.com.sa",
]

# Default sync settings
DEFAULT_DAYS_BACK = 90  # Initial sync: 90 days
INCREMENTAL_DAYS_BACK = 7  # Incremental: last 7 days


def get_last_email_sync_time(mailbox: str) -> Optional[datetime]:
    """Get the last successful sync time for a mailbox."""
    entity_type = f"emails_{mailbox}"
    with Session(engine) as session:
        meta = session.exec(
            select(SyncMetadata).where(SyncMetadata.entity_type == entity_type)
        ).first()
        if meta and meta.status == "success":
            dt = meta.last_sync_time
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        return None


def update_email_sync_metadata(
    mailbox: str,
    status: str,
    records_synced: int = 0,
    records_total: int = 0,
    duration_ms: int = 0,
    error_message: Optional[str] = None,
):
    """Update sync metadata for a mailbox."""
    entity_type = f"emails_{mailbox}"
    with Session(engine) as session:
        meta = session.exec(
            select(SyncMetadata).where(SyncMetadata.entity_type == entity_type)
        ).first()

        if meta:
            meta.last_sync_time = datetime.now(timezone.utc)
            meta.status = status
            meta.records_synced = records_synced
            meta.records_total = records_total
            meta.last_sync_duration_ms = duration_ms
            meta.error_message = error_message
        else:
            meta = SyncMetadata(
                entity_type=entity_type,
                last_sync_time=datetime.now(timezone.utc),
                status=status,
                records_synced=records_synced,
                records_total=records_total,
                last_sync_duration_ms=duration_ms,
                error_message=error_message,
            )
            session.add(meta)

        session.commit()


async def sync_folders_for_mailbox(mailbox: str) -> Dict[str, Any]:
    """
    Sync mail folders for a mailbox.

    Args:
        mailbox: Email address of the mailbox

    Returns:
        Dict with sync results
    """
    from .msgraph_email_service import get_msgraph_email_service

    start_time = datetime.now()
    entity_type = f"folders_{mailbox}"

    try:
        service = get_msgraph_email_service()
        folders = await service.get_folders(mailbox=mailbox)

        with Session(engine) as session:
            for folder in folders:
                cached = CachedMailFolder(
                    graph_id=folder.id,
                    mailbox=mailbox,
                    display_name=folder.name,
                    parent_folder_id=folder.parent_folder_id,
                    child_folder_count=folder.child_folder_count,
                    unread_count=folder.unread_count,
                    total_count=folder.total_count,
                    synced_at=datetime.now(timezone.utc),
                )
                # Upsert
                existing = session.exec(
                    select(CachedMailFolder).where(
                        CachedMailFolder.graph_id == folder.id,
                        CachedMailFolder.mailbox == mailbox,
                    )
                ).first()
                if existing:
                    existing.display_name = cached.display_name
                    existing.parent_folder_id = cached.parent_folder_id
                    existing.child_folder_count = cached.child_folder_count
                    existing.unread_count = cached.unread_count
                    existing.total_count = cached.total_count
                    existing.synced_at = cached.synced_at
                else:
                    session.add(cached)
            session.commit()

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return {
            "mailbox": mailbox,
            "folders_synced": len(folders),
            "duration_ms": duration_ms,
            "ok": True,
        }

    except Exception as e:
        logger.error(f"Failed to sync folders for {mailbox}: {e}")
        return {
            "mailbox": mailbox,
            "folders_synced": 0,
            "error": str(e),
            "ok": False,
        }


async def sync_emails_for_mailbox(
    mailbox: str,
    days_back: int = DEFAULT_DAYS_BACK,
    folder: str = "inbox",
    limit_per_folder: int = 500,
) -> Dict[str, Any]:
    """
    Sync emails for a mailbox.

    Args:
        mailbox: Email address of the mailbox
        days_back: Number of days to look back
        folder: Folder to sync (default: inbox)
        limit_per_folder: Max emails per folder

    Returns:
        Dict with sync results
    """
    from .msgraph_email_service import get_msgraph_email_service

    start_time = datetime.now()
    emails_synced = 0
    attachments_synced = 0

    try:
        service = get_msgraph_email_service()

        # First sync folders
        await sync_folders_for_mailbox(mailbox)

        # Get emails from specified folder
        emails = await service.get_emails(
            mailbox=mailbox,
            folder=folder,
            include_attachments=True,
            limit=limit_per_folder,
        )

        # Filter by date if needed
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        filtered_emails = [
            e for e in emails
            if e.received_at is None or e.received_at >= cutoff_date
        ]

        with Session(engine) as session:
            for email in filtered_emails:
                cached = _email_to_cached(email, mailbox)

                # Upsert email
                existing = session.exec(
                    select(CachedEmail).where(
                        CachedEmail.graph_id == email.id,
                        CachedEmail.mailbox == mailbox,
                    )
                ).first()

                if existing:
                    _update_cached_email(existing, cached)
                else:
                    session.add(cached)
                    emails_synced += 1

                # Sync attachments
                if email.attachments:
                    for att in email.attachments:
                        cached_att = CachedEmailAttachment(
                            graph_id=att.id,
                            email_graph_id=email.id,
                            mailbox=mailbox,
                            name=att.name,
                            content_type=att.content_type,
                            size=att.size,
                            is_inline=att.is_inline,
                            synced_at=datetime.now(timezone.utc),
                        )
                        existing_att = session.exec(
                            select(CachedEmailAttachment).where(
                                CachedEmailAttachment.graph_id == att.id,
                                CachedEmailAttachment.mailbox == mailbox,
                            )
                        ).first()
                        if not existing_att:
                            session.add(cached_att)
                            attachments_synced += 1

            session.commit()

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        update_email_sync_metadata(
            mailbox, "success",
            records_synced=emails_synced,
            records_total=len(filtered_emails),
            duration_ms=duration_ms,
        )

        return {
            "mailbox": mailbox,
            "folder": folder,
            "emails_synced": emails_synced,
            "emails_total": len(filtered_emails),
            "attachments_synced": attachments_synced,
            "duration_ms": duration_ms,
            "ok": True,
        }

    except Exception as e:
        logger.error(f"Failed to sync emails for {mailbox}: {e}")
        update_email_sync_metadata(mailbox, "failed", error_message=str(e))
        return {
            "mailbox": mailbox,
            "folder": folder,
            "emails_synced": 0,
            "error": str(e),
            "ok": False,
        }


async def sync_all_mailboxes(
    days_back: Optional[int] = None,
    ttl_minutes: int = 15,
    concurrency: int = 2,
) -> Dict[str, Any]:
    """
    Sync emails for all configured mailboxes.

    Args:
        days_back: Override days to look back (None = auto)
        ttl_minutes: Skip mailbox if synced within this time
        concurrency: Max concurrent mailbox syncs

    Returns:
        Dict with sync results
    """
    semaphore = asyncio.Semaphore(concurrency)
    results = []

    async def sync_one(mailbox: str):
        async with semaphore:
            # Check TTL
            last_sync = get_last_email_sync_time(mailbox)
            if last_sync:
                age_minutes = (datetime.now(timezone.utc) - last_sync).total_seconds() / 60
                if age_minutes < ttl_minutes:
                    return {
                        "mailbox": mailbox,
                        "skipped": True,
                        "reason": f"Synced {age_minutes:.1f} minutes ago",
                    }

            # Determine days_back
            effective_days = days_back
            if effective_days is None:
                effective_days = INCREMENTAL_DAYS_BACK if last_sync else DEFAULT_DAYS_BACK

            # Sync inbox
            return await sync_emails_for_mailbox(
                mailbox=mailbox,
                days_back=effective_days,
                folder="inbox",
            )

    results = await asyncio.gather(*[sync_one(m) for m in SYNC_MAILBOXES])

    return {
        "mailboxes": SYNC_MAILBOXES,
        "results": results,
        "synced": sum(1 for r in results if r.get("ok")),
        "skipped": sum(1 for r in results if r.get("skipped")),
        "failed": sum(1 for r in results if not r.get("ok") and not r.get("skipped")),
    }


def _email_to_cached(email: EmailMessage, mailbox: str) -> CachedEmail:
    """Convert EmailMessage to CachedEmail."""
    to_recipients = [{"address": r.address, "name": r.name} for r in email.to_recipients]
    cc_recipients = [{"address": r.address, "name": r.name} for r in email.cc_recipients]

    return CachedEmail(
        graph_id=email.id,
        mailbox=mailbox,
        folder_id=email.folder_id,
        subject=email.subject,
        body_preview=email.body_preview,
        body_content=email.body_content,
        body_type=email.body_type,
        sender_address=email.sender.address if email.sender else None,
        sender_name=email.sender.name if email.sender else None,
        to_recipients_json=json.dumps(to_recipients) if to_recipients else None,
        cc_recipients_json=json.dumps(cc_recipients) if cc_recipients else None,
        received_at=email.received_at,
        sent_at=email.sent_at,
        is_read=email.is_read,
        has_attachments=email.has_attachments,
        importance=email.importance,
        is_draft=email.is_draft,
        conversation_id=email.conversation_id,
        web_link=email.web_link,
        synced_at=datetime.now(timezone.utc),
    )


def _update_cached_email(existing: CachedEmail, new: CachedEmail):
    """Update existing cached email with new data."""
    existing.folder_id = new.folder_id
    existing.subject = new.subject
    existing.body_preview = new.body_preview
    existing.body_content = new.body_content
    existing.body_type = new.body_type
    existing.sender_address = new.sender_address
    existing.sender_name = new.sender_name
    existing.to_recipients_json = new.to_recipients_json
    existing.cc_recipients_json = new.cc_recipients_json
    existing.received_at = new.received_at
    existing.sent_at = new.sent_at
    existing.is_read = new.is_read
    existing.has_attachments = new.has_attachments
    existing.importance = new.importance
    existing.is_draft = new.is_draft
    existing.conversation_id = new.conversation_id
    existing.web_link = new.web_link
    existing.synced_at = datetime.now(timezone.utc)


__all__ = [
    "SYNC_MAILBOXES",
    "get_last_email_sync_time",
    "update_email_sync_metadata",
    "sync_folders_for_mailbox",
    "sync_emails_for_mailbox",
    "sync_all_mailboxes",
]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_email_sync.py -v`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add cmd_center/backend/services/email_sync.py tests/unit/test_email_sync.py
git commit -m "$(cat <<'EOF'
feat: add email sync module for Graph API emails

Create email_sync.py with functions to sync emails and folders from
Microsoft Graph to local SQLite cache. Supports incremental sync
with TTL-based skipping.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Add Email Sync to Scheduler

**Files:**
- Modify: `cmd_center/backend/services/sync_scheduler.py`
- Test: `tests/unit/test_email_scheduler.py`

**Step 1: Write the failing test**

Create `tests/unit/test_email_scheduler.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_email_scheduler.py -v`
Expected: FAIL with "cannot import name 'run_email_sync'"

**Step 3: Write minimal implementation**

Add to `cmd_center/backend/services/sync_scheduler.py`:

After the existing imports, add:

```python
from .email_sync import sync_all_mailboxes
```

Add a new lock after the existing locks:

```python
email_lock = asyncio.Lock()
```

Add a new task variable:

```python
email_task: Optional[asyncio.Task] = None
```

Add the sync function after `run_stage_history_sync`:

```python
async def run_email_sync():
    """Run email sync for all mailboxes."""
    async with email_lock:
        logger.info("Starting email sync...")
        start_time = asyncio.get_event_loop().time()
        try:
            result = await sync_all_mailboxes(ttl_minutes=15)
            duration = asyncio.get_event_loop().time() - start_time
            logger.info(
                f"Email sync completed in {duration:.2f}s: "
                f"{result['synced']} synced, {result['skipped']} skipped, {result['failed']} failed"
            )
        except asyncio.CancelledError:
            raise
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            logger.error(f"Email sync failed after {duration:.2f}s: {e}")
```

Add the loop function after `stage_history_loop`:

```python
async def email_loop():
    """Periodic email sync loop (every 15 minutes)."""
    while True:
        await asyncio.sleep(15 * 60)  # 15 minutes
        await run_email_sync()
```

Update `start_scheduler` to add:

```python
    global deals_task, notes_task, stage_history_task, email_task

    # ... existing code ...

    if email_task is None or email_task.done():
        email_task = asyncio.create_task(email_loop())
        logger.info("Started email sync loop")
```

Update `stop_scheduler` to add:

```python
    global deals_task, notes_task, stage_history_task, email_task

    # ... existing code ...

    if email_task and not email_task.done():
        email_task.cancel()
        try:
            await email_task
        except asyncio.CancelledError:
            pass
        logger.info("Stopped email sync loop")
```

Update `lifespan_manager` after `await run_stage_history_sync()` to add:

```python
    await run_email_sync()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_email_scheduler.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add cmd_center/backend/services/sync_scheduler.py tests/unit/test_email_scheduler.py
git commit -m "$(cat <<'EOF'
feat: integrate email sync into scheduler

Add email_loop and run_email_sync to sync_scheduler.py.
Emails sync every 15 minutes with TTL-based skipping.
Initial sync runs on application startup.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Add Cached Email Read Methods to Service

**Files:**
- Modify: `cmd_center/backend/services/msgraph_email_service.py`
- Test: `tests/unit/test_msgraph_email_service.py` (extend existing)

**Step 1: Write the failing test**

Add to `tests/unit/test_msgraph_email_service.py`:

```python
class TestCachedEmailReads:
    """Test reading emails from local cache."""

    def test_get_cached_emails(self):
        """Get emails from local cache."""
        from cmd_center.backend.db import init_db, engine, CachedEmail
        from sqlmodel import Session
        from datetime import datetime, timezone

        init_db()

        # Insert test data
        with Session(engine) as session:
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

        service = MSGraphEmailService()
        result = service.get_cached_emails(mailbox="test@example.com", limit=10)

        assert len(result) >= 1
        assert any(e.subject == "Cached Subject" for e in result)

    def test_get_cached_email_by_id(self):
        """Get single email from cache by Graph ID."""
        from cmd_center.backend.db import init_db, engine, CachedEmail
        from sqlmodel import Session
        from datetime import datetime, timezone

        init_db()

        with Session(engine) as session:
            email = CachedEmail(
                graph_id="cached-single-123",
                mailbox="test@example.com",
                subject="Single Email",
                is_read=True,
            )
            session.add(email)
            session.commit()

        service = MSGraphEmailService()
        result = service.get_cached_email_by_id("cached-single-123", mailbox="test@example.com")

        assert result is not None
        assert result.subject == "Single Email"
        assert result.is_read is True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_msgraph_email_service.py::TestCachedEmailReads -v`
Expected: FAIL with "has no attribute 'get_cached_emails'"

**Step 3: Write minimal implementation**

Add to `cmd_center/backend/services/msgraph_email_service.py`:

Add import at top:

```python
from sqlmodel import Session, select
from ..db import engine, CachedEmail, CachedEmailAttachment, CachedMailFolder
```

Add methods to `MSGraphEmailService` class after `get_folder_by_name`:

```python
    # ==================== Cached Reads (Local Database) ====================

    def get_cached_emails(
        self,
        mailbox: Optional[str] = None,
        folder_id: Optional[str] = None,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[EmailMessage]:
        """
        Get emails from local cache (fast, no API call).

        Args:
            mailbox: Email address of the mailbox
            folder_id: Filter by folder ID
            unread_only: Only return unread emails
            limit: Maximum number of emails
            offset: Offset for pagination

        Returns:
            List of cached email messages
        """
        mailbox = self._resolve_mailbox(mailbox)

        with Session(engine) as session:
            query = select(CachedEmail).where(CachedEmail.mailbox == mailbox)

            if folder_id:
                query = query.where(CachedEmail.folder_id == folder_id)

            if unread_only:
                query = query.where(CachedEmail.is_read == False)

            query = query.order_by(CachedEmail.received_at.desc())
            query = query.offset(offset).limit(limit)

            cached_emails = session.exec(query).all()

        return [self._cached_to_email_message(e) for e in cached_emails]

    def get_cached_email_by_id(
        self,
        graph_id: str,
        mailbox: Optional[str] = None,
    ) -> Optional[EmailMessage]:
        """
        Get a single email from cache by Graph ID.

        Args:
            graph_id: Microsoft Graph message ID
            mailbox: Email address of the mailbox

        Returns:
            Email message or None if not found
        """
        mailbox = self._resolve_mailbox(mailbox)

        with Session(engine) as session:
            cached = session.exec(
                select(CachedEmail).where(
                    CachedEmail.graph_id == graph_id,
                    CachedEmail.mailbox == mailbox,
                )
            ).first()

            if not cached:
                return None

            return self._cached_to_email_message(cached)

    def get_cached_folders(
        self,
        mailbox: Optional[str] = None,
    ) -> List[MailFolder]:
        """
        Get mail folders from local cache.

        Args:
            mailbox: Email address of the mailbox

        Returns:
            List of cached mail folders
        """
        mailbox = self._resolve_mailbox(mailbox)

        with Session(engine) as session:
            cached_folders = session.exec(
                select(CachedMailFolder).where(CachedMailFolder.mailbox == mailbox)
            ).all()

        return [
            MailFolder(
                id=f.graph_id,
                name=f.display_name,
                parent_folder_id=f.parent_folder_id,
                child_folder_count=f.child_folder_count,
                unread_count=f.unread_count,
                total_count=f.total_count,
            )
            for f in cached_folders
        ]

    def _cached_to_email_message(self, cached: CachedEmail) -> EmailMessage:
        """Convert CachedEmail to EmailMessage."""
        import json

        sender = None
        if cached.sender_address:
            sender = EmailAddress(
                address=cached.sender_address,
                name=cached.sender_name,
            )

        to_recipients = []
        if cached.to_recipients_json:
            try:
                to_list = json.loads(cached.to_recipients_json)
                to_recipients = [
                    EmailAddress(address=r["address"], name=r.get("name"))
                    for r in to_list
                ]
            except (json.JSONDecodeError, KeyError):
                pass

        cc_recipients = []
        if cached.cc_recipients_json:
            try:
                cc_list = json.loads(cached.cc_recipients_json)
                cc_recipients = [
                    EmailAddress(address=r["address"], name=r.get("name"))
                    for r in cc_list
                ]
            except (json.JSONDecodeError, KeyError):
                pass

        return EmailMessage(
            id=cached.graph_id,
            subject=cached.subject,
            body_preview=cached.body_preview,
            body_content=cached.body_content,
            body_type=cached.body_type,
            sender=sender,
            to_recipients=to_recipients,
            cc_recipients=cc_recipients,
            received_at=cached.received_at,
            sent_at=cached.sent_at,
            is_read=cached.is_read,
            has_attachments=cached.has_attachments,
            importance=cached.importance,
            folder_id=cached.folder_id,
            conversation_id=cached.conversation_id,
            web_link=cached.web_link,
            is_draft=cached.is_draft,
        )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_msgraph_email_service.py::TestCachedEmailReads -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add cmd_center/backend/services/msgraph_email_service.py tests/unit/test_msgraph_email_service.py
git commit -m "$(cat <<'EOF'
feat: add cached email read methods to MSGraphEmailService

Add get_cached_emails, get_cached_email_by_id, and get_cached_folders
methods that read from local SQLite cache for fast email access
without API calls.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Export New Functions and Update Architecture

**Files:**
- Modify: `cmd_center/backend/services/__init__.py`
- Modify: `docs/Architecture.md`

**Step 1: Update services/__init__.py**

Add after the existing imports:

```python
# Email Sync
from .email_sync import (
    SYNC_MAILBOXES,
    sync_emails_for_mailbox,
    sync_folders_for_mailbox,
    sync_all_mailboxes,
    get_last_email_sync_time,
    update_email_sync_metadata,
)
```

Add to `__all__`:

```python
    # Email Sync
    "SYNC_MAILBOXES",
    "sync_emails_for_mailbox",
    "sync_folders_for_mailbox",
    "sync_all_mailboxes",
    "get_last_email_sync_time",
    "update_email_sync_metadata",
```

**Step 2: Update Architecture.md**

Add to Section 4.1 (Core Tables):

```markdown
### 4.8 Email Cache Tables (Microsoft Graph)

| Table | Purpose | Sync Frequency |
|-------|---------|----------------|
| `cached_email` | Cached email messages | Every 15 minutes |
| `cached_email_attachment` | Attachment metadata | With emails |
| `cached_mail_folder` | Folder structure | With emails |
```

Add to Section 7.1 (Service → Query Mapping):

```markdown
| **Email Sync** | |
| `email_sync` | Uses `msgraph_email_service`, writes to `CachedEmail`, `CachedMailFolder` |
```

Add to Section 8.2 (Sync Strategy):

```markdown
| Emails (inbox) | Last 90 days | Incremental (7 days) | 15 minutes |
| Folders | All | Full | With emails |
```

Update Section 11.3 to add:

```markdown
✅ **Email Caching** - Local SQLite cache for fast email reads
```

**Step 3: Commit**

```bash
git add cmd_center/backend/services/__init__.py docs/Architecture.md
git commit -m "$(cat <<'EOF'
docs: update exports and architecture for email sync

Export email sync functions from services/__init__.py.
Update Architecture.md with email cache tables and sync strategy.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Run Full Test Suite

**Step 1: Run all tests**

```bash
pytest tests/ -v --tb=short
```

Expected: All tests pass (including new email sync tests)

**Step 2: Verify email tables created**

```bash
python -c "from cmd_center.backend.db import init_db; init_db(); print('Tables created successfully')"
```

**Step 3: Final commit if needed**

```bash
git status
# If any uncommitted changes:
git add -A
git commit -m "$(cat <<'EOF'
chore: final cleanup for email sync feature

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Summary

| Task | Files | Tests |
|------|-------|-------|
| 1. Database Tables | `db.py` | 3 tests |
| 2. Email Sync Module | `email_sync.py` | 5 tests |
| 3. Scheduler Integration | `sync_scheduler.py` | 2 tests |
| 4. Cached Read Methods | `msgraph_email_service.py` | 2 tests |
| 5. Exports & Docs | `__init__.py`, `Architecture.md` | - |
| 6. Full Test Suite | - | All pass |

**Total new tests:** ~12 tests
**Total new files:** 1 (`email_sync.py`)
**Modified files:** 4 (`db.py`, `sync_scheduler.py`, `msgraph_email_service.py`, `services/__init__.py`)
