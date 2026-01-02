"""Sync Microsoft Graph emails to local SQLite cache."""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlmodel import Session, select

from .. import db
from ..db import CachedEmail, CachedEmailAttachment, CachedMailFolder, SyncMetadata
from ..models.msgraph_email_models import EmailMessage, MailFolder
from .msgraph_email_service import get_msgraph_email_service

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
    with Session(db.engine) as session:
        meta = session.exec(
            select(SyncMetadata).where(SyncMetadata.entity_type == entity_type)
        ).first()
        if meta and meta.status == "success":
            dt = meta.last_sync_time
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        return None


def is_sync_in_progress(mailbox: str) -> bool:
    """Check if a sync is currently in progress for a mailbox."""
    entity_type = f"emails_{mailbox}"
    with Session(db.engine) as session:
        meta = session.exec(
            select(SyncMetadata).where(SyncMetadata.entity_type == entity_type)
        ).first()
        return meta is not None and meta.status == "in_progress"


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
    with Session(db.engine) as session:
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
    """Sync mail folders for a mailbox.

    Note: DB operations (Session/commit) are synchronous inside this async function.
    This is acceptable because:
    1. This runs as a background sync task, not in the request/response cycle
    2. SQLite operations are fast (typically <10ms)
    3. The async context allows concurrent folder fetches across mailboxes
    """
    start_time = datetime.now()

    try:
        service = get_msgraph_email_service()
        folders = await service.get_folders(mailbox=mailbox)

        with Session(db.engine) as session:
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
    """Sync emails for a mailbox.

    Note: DB operations (Session/commit) are synchronous inside this async function.
    This is acceptable because:
    1. This runs as a background sync task, not in the request/response cycle
    2. SQLite operations are fast (typically <10ms)
    3. The async context allows concurrent email fetches from MSGraph API
    """
    start_time = datetime.now()
    emails_synced = 0
    attachments_synced = 0

    try:
        service = get_msgraph_email_service()
        await sync_folders_for_mailbox(mailbox)

        emails = await service.get_emails(
            mailbox=mailbox,
            folder=folder,
            include_attachments=True,
            limit=limit_per_folder,
        )

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        filtered_emails = [
            e for e in emails
            if e.received_at is None or e.received_at >= cutoff_date
        ]

        with Session(db.engine) as session:
            for email in filtered_emails:
                cached = _email_to_cached(email, mailbox)

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
    """Sync emails for all configured mailboxes."""
    semaphore = asyncio.Semaphore(concurrency)
    results = []

    async def sync_one(mailbox: str):
        async with semaphore:
            # Check if sync is already in progress to prevent duplicate concurrent syncs
            if is_sync_in_progress(mailbox):
                return {
                    "mailbox": mailbox,
                    "skipped": True,
                    "reason": "Sync already in progress",
                }

            last_sync = get_last_email_sync_time(mailbox)
            if last_sync:
                age_minutes = (datetime.now(timezone.utc) - last_sync).total_seconds() / 60
                if age_minutes < ttl_minutes:
                    return {
                        "mailbox": mailbox,
                        "skipped": True,
                        "reason": f"Synced {age_minutes:.1f} minutes ago",
                    }

            # Set status to in_progress before starting sync
            update_email_sync_metadata(mailbox, "in_progress")

            effective_days = days_back
            if effective_days is None:
                effective_days = INCREMENTAL_DAYS_BACK if last_sync else DEFAULT_DAYS_BACK

            try:
                result = await sync_emails_for_mailbox(
                    mailbox=mailbox,
                    days_back=effective_days,
                    folder="inbox",
                )
                # sync_emails_for_mailbox already sets success/failed status
                return result
            except Exception as e:
                # Ensure status is set to failed on unexpected errors
                update_email_sync_metadata(mailbox, "failed", error_message=str(e))
                return {
                    "mailbox": mailbox,
                    "folder": "inbox",
                    "emails_synced": 0,
                    "error": str(e),
                    "ok": False,
                }

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
    "is_sync_in_progress",
    "update_email_sync_metadata",
    "sync_folders_for_mailbox",
    "sync_emails_for_mailbox",
    "sync_all_mailboxes",
]
