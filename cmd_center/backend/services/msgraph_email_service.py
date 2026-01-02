"""Microsoft Graph Email Service for managing emails via Graph API.

This service provides a high-level interface for email operations including:
- Reading and searching emails
- Sending emails with attachments
- Reply, forward, and move operations
- Folder management
- Attachment downloads
"""

import base64
import json
import logging
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from sqlmodel import Session, select
from .. import db
from ..db import CachedEmail, CachedEmailAttachment, CachedMailFolder
from ..integrations.microsoft_client import (
    get_microsoft_client,
    MicrosoftClient,
    EmailMessageDTO,
    MailFolderDTO,
    EmailAttachmentDTO,
)
from ..models.msgraph_email_models import (
    EmailMessage,
    EmailAddress,
    EmailAttachment,
    MailFolder,
    EmailSearchFilters,
    EmailAttachmentInput,
)

logger = logging.getLogger(__name__)

# Default attachments directory
DEFAULT_ATTACHMENTS_DIR = Path("attachments")


class MSGraphEmailService:
    """High-level service for Microsoft Graph email operations."""

    def __init__(
        self,
        default_mailbox: str = "mohammed@gyptech.com.sa",
        attachments_dir: Optional[Path] = None,
    ):
        """
        Initialize the email service.

        Args:
            default_mailbox: Default mailbox to use when not specified
            attachments_dir: Directory for saving attachments (default: ./attachments)
        """
        self.default_mailbox = default_mailbox
        self.attachments_dir = attachments_dir or DEFAULT_ATTACHMENTS_DIR
        self._client: Optional[MicrosoftClient] = None

    @property
    def client(self) -> MicrosoftClient:
        """Get the Microsoft Graph client (lazy initialization)."""
        if self._client is None:
            self._client = get_microsoft_client()
        return self._client

    def _resolve_mailbox(self, mailbox: Optional[str]) -> str:
        """Resolve mailbox to use, defaulting if not specified."""
        return mailbox or self.default_mailbox

    # ==================== Reading Emails ====================

    async def get_emails(
        self,
        mailbox: Optional[str] = None,
        folder: str = "inbox",
        unread_only: bool = False,
        include_attachments: bool = False,
        limit: int = 50,
        skip: int = 0,
    ) -> List[EmailMessage]:
        """
        Get emails from a mailbox folder.

        Args:
            mailbox: Email address of the mailbox (uses default if None)
            folder: Folder name or ID (default: inbox)
            unread_only: Only return unread emails
            include_attachments: Include attachment metadata
            limit: Maximum number of emails to return
            skip: Number of emails to skip (for pagination)

        Returns:
            List of email messages
        """
        mailbox = self._resolve_mailbox(mailbox)

        # Build filter query
        filter_query = None
        if unread_only:
            filter_query = "isRead eq false"

        # Get folder ID if name provided
        folder_id = await self._resolve_folder_id(mailbox, folder)

        messages = await self.client.get_messages(
            mailbox=mailbox,
            folder_id=folder_id,
            top=limit,
            skip=skip,
            filter_query=filter_query,
        )

        result = []
        for msg in messages:
            email = self._convert_message(msg)
            if include_attachments and msg.has_attachments:
                attachments = await self.client.get_message_attachments(mailbox, msg.id)
                email.attachments = [self._convert_attachment(a) for a in attachments]
            result.append(email)

        return result

    async def get_email_by_id(
        self,
        message_id: str,
        mailbox: Optional[str] = None,
        include_attachments: bool = True,
    ) -> Optional[EmailMessage]:
        """
        Get a single email by ID.

        Args:
            message_id: ID of the email message
            mailbox: Email address of the mailbox
            include_attachments: Include attachment metadata

        Returns:
            Email message or None if not found
        """
        mailbox = self._resolve_mailbox(mailbox)

        msg = await self.client.get_message_by_id(mailbox, message_id)
        if not msg:
            return None

        email = self._convert_message(msg)

        if include_attachments and msg.has_attachments:
            attachments = await self.client.get_message_attachments(mailbox, message_id)
            email.attachments = [self._convert_attachment(a) for a in attachments]

        return email

    # ==================== Searching Emails ====================

    async def search_emails(
        self,
        mailbox: Optional[str] = None,
        subject: Optional[str] = None,
        sender: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        folder: str = "inbox",
        unread_only: bool = False,
        has_attachments: Optional[bool] = None,
        limit: int = 50,
    ) -> List[EmailMessage]:
        """
        Search emails with various filters.

        Args:
            mailbox: Email address of the mailbox
            subject: Search in subject
            sender: Filter by sender email address
            from_date: Emails received after this date
            to_date: Emails received before this date
            folder: Folder to search in
            unread_only: Only return unread emails
            has_attachments: Filter by attachment presence
            limit: Maximum number of results

        Returns:
            List of matching email messages
        """
        mailbox = self._resolve_mailbox(mailbox)
        folder_id = await self._resolve_folder_id(mailbox, folder)

        # Build filter conditions
        filters = []

        if unread_only:
            filters.append("isRead eq false")

        if has_attachments is not None:
            filters.append(f"hasAttachments eq {str(has_attachments).lower()}")

        if sender:
            filters.append(f"from/emailAddress/address eq '{sender}'")

        if from_date:
            filters.append(f"receivedDateTime ge {from_date.isoformat()}Z")

        if to_date:
            filters.append(f"receivedDateTime le {to_date.isoformat()}Z")

        filter_query = " and ".join(filters) if filters else None

        # Use search for subject (OData $search)
        search_query = subject if subject else None

        messages = await self.client.get_messages(
            mailbox=mailbox,
            folder_id=folder_id,
            top=limit,
            filter_query=filter_query,
            search_query=search_query,
        )

        return [self._convert_message(msg) for msg in messages]

    # ==================== Sending Emails ====================

    async def send_email(
        self,
        from_mailbox: str,
        to: List[str],
        subject: str,
        body: str,
        body_type: str = "html",
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[EmailAttachmentInput]] = None,
        save_to_sent: bool = True,
    ) -> bool:
        """
        Send an email.

        Args:
            from_mailbox: Mailbox to send from (required for app-only auth)
            to: List of recipient email addresses
            subject: Email subject
            body: Email body content
            body_type: "text" or "html"
            cc: List of CC recipients
            bcc: List of BCC recipients
            attachments: List of file attachments
            save_to_sent: Whether to save to Sent Items folder

        Returns:
            True if sent successfully
        """
        # Process attachments
        graph_attachments = None
        if attachments:
            graph_attachments = []
            for att in attachments:
                graph_att = await self._prepare_attachment(att)
                if graph_att:
                    graph_attachments.append(graph_att)

        return await self.client.send_mail(
            mailbox=from_mailbox,
            subject=subject,
            body=body,
            to_recipients=to,
            cc_recipients=cc,
            bcc_recipients=bcc,
            body_type=body_type,
            save_to_sent=save_to_sent,
            attachments=graph_attachments,
        )

    # ==================== Email Actions ====================

    async def reply(
        self,
        message_id: str,
        mailbox: Optional[str] = None,
        comment: str = "",
        reply_all: bool = False,
    ) -> bool:
        """
        Reply to an email.

        Args:
            message_id: ID of the message to reply to
            mailbox: Mailbox containing the message
            comment: Reply text
            reply_all: Whether to reply to all recipients

        Returns:
            True if successful
        """
        mailbox = self._resolve_mailbox(mailbox)
        return await self.client.reply_to_message(
            mailbox=mailbox,
            message_id=message_id,
            comment=comment,
            reply_all=reply_all,
        )

    async def forward(
        self,
        message_id: str,
        to: List[str],
        mailbox: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> bool:
        """
        Forward an email.

        Args:
            message_id: ID of the message to forward
            to: List of recipient email addresses
            mailbox: Mailbox containing the message
            comment: Optional comment to add

        Returns:
            True if successful
        """
        mailbox = self._resolve_mailbox(mailbox)
        return await self.client.forward_message(
            mailbox=mailbox,
            message_id=message_id,
            to_recipients=to,
            comment=comment,
        )

    async def move_to_folder(
        self,
        message_id: str,
        destination_folder: str,
        mailbox: Optional[str] = None,
    ) -> bool:
        """
        Move an email to a different folder.

        Args:
            message_id: ID of the message to move
            destination_folder: Folder name or ID
            mailbox: Mailbox containing the message

        Returns:
            True if successful
        """
        mailbox = self._resolve_mailbox(mailbox)

        # Resolve folder name to ID
        folder_id = await self._resolve_folder_id(mailbox, destination_folder)

        result = await self.client.move_message(
            mailbox=mailbox,
            message_id=message_id,
            destination_folder_id=folder_id,
        )
        return result is not None

    async def mark_as_read(
        self,
        message_id: str,
        mailbox: Optional[str] = None,
        read: bool = True,
    ) -> bool:
        """
        Mark an email as read or unread.

        Args:
            message_id: ID of the message
            mailbox: Mailbox containing the message
            read: True to mark as read, False for unread

        Returns:
            True if successful
        """
        mailbox = self._resolve_mailbox(mailbox)
        return await self.client.update_message(
            mailbox=mailbox,
            message_id=message_id,
            is_read=read,
        )

    async def delete_email(
        self,
        message_id: str,
        mailbox: Optional[str] = None,
    ) -> bool:
        """
        Delete an email (moves to Deleted Items).

        Args:
            message_id: ID of the message to delete
            mailbox: Mailbox containing the message

        Returns:
            True if successful
        """
        mailbox = self._resolve_mailbox(mailbox)
        return await self.client.delete_message(mailbox, message_id)

    # ==================== Attachments ====================

    async def get_attachments(
        self,
        message_id: str,
        mailbox: Optional[str] = None,
    ) -> List[EmailAttachment]:
        """
        Get attachment metadata for an email.

        Args:
            message_id: ID of the message
            mailbox: Mailbox containing the message

        Returns:
            List of attachment metadata
        """
        mailbox = self._resolve_mailbox(mailbox)
        attachments = await self.client.get_message_attachments(mailbox, message_id)
        return [self._convert_attachment(a) for a in attachments]

    async def download_attachment(
        self,
        message_id: str,
        attachment_id: str,
        mailbox: Optional[str] = None,
        save_path: Optional[Path] = None,
        filename: Optional[str] = None,
    ) -> Path:
        """
        Download an attachment to disk.

        Args:
            message_id: ID of the message
            attachment_id: ID of the attachment
            mailbox: Mailbox containing the message
            save_path: Full path to save file (overrides default)
            filename: Filename to use (fetched from metadata if not provided)

        Returns:
            Path to the downloaded file
        """
        mailbox = self._resolve_mailbox(mailbox)

        # Get filename from attachment metadata if not provided
        if not filename:
            attachments = await self.client.get_message_attachments(mailbox, message_id)
            for att in attachments:
                if att.id == attachment_id:
                    filename = att.name
                    break

        if not filename:
            filename = f"attachment_{attachment_id}"

        # Determine save path
        if save_path:
            file_path = save_path
        else:
            self.attachments_dir.mkdir(parents=True, exist_ok=True)
            file_path = self.attachments_dir / filename

        # Download content
        content = await self.client.download_attachment(
            mailbox=mailbox,
            message_id=message_id,
            attachment_id=attachment_id,
        )

        # Write to file
        file_path.write_bytes(content)
        logger.info(f"Downloaded attachment to {file_path}")

        return file_path

    async def download_all_attachments(
        self,
        message_id: str,
        mailbox: Optional[str] = None,
        save_dir: Optional[Path] = None,
    ) -> List[Path]:
        """
        Download all attachments from an email.

        Args:
            message_id: ID of the message
            mailbox: Mailbox containing the message
            save_dir: Directory to save files (uses default if not provided)

        Returns:
            List of paths to downloaded files
        """
        mailbox = self._resolve_mailbox(mailbox)
        save_dir = save_dir or self.attachments_dir
        save_dir.mkdir(parents=True, exist_ok=True)

        attachments = await self.client.get_message_attachments(mailbox, message_id)
        downloaded = []

        for att in attachments:
            if att.is_inline:
                continue  # Skip inline images

            file_path = save_dir / att.name
            content = await self.client.download_attachment(
                mailbox=mailbox,
                message_id=message_id,
                attachment_id=att.id,
            )
            file_path.write_bytes(content)
            downloaded.append(file_path)
            logger.info(f"Downloaded attachment: {att.name}")

        return downloaded

    # ==================== Folder Management ====================

    async def get_folders(
        self,
        mailbox: Optional[str] = None,
    ) -> List[MailFolder]:
        """
        Get all mail folders in a mailbox.

        Args:
            mailbox: Email address of the mailbox

        Returns:
            List of mail folders
        """
        mailbox = self._resolve_mailbox(mailbox)
        folders = await self.client.get_mail_folders(mailbox)
        return [self._convert_folder(f) for f in folders]

    async def create_folder(
        self,
        folder_name: str,
        parent_folder_id: Optional[str] = None,
        mailbox: Optional[str] = None,
    ) -> MailFolder:
        """
        Create a new mail folder.

        Args:
            folder_name: Display name for the folder
            parent_folder_id: Optional parent folder ID (creates subfolder)
            mailbox: Email address of the mailbox

        Returns:
            Created mail folder
        """
        mailbox = self._resolve_mailbox(mailbox)
        folder = await self.client.create_mail_folder(
            mailbox=mailbox,
            display_name=folder_name,
            parent_folder_id=parent_folder_id,
        )
        return self._convert_folder(folder)

    async def get_folder_by_name(
        self,
        folder_name: str,
        mailbox: Optional[str] = None,
    ) -> Optional[MailFolder]:
        """
        Get a folder by name.

        Args:
            folder_name: Display name of the folder
            mailbox: Email address of the mailbox

        Returns:
            Mail folder or None if not found
        """
        mailbox = self._resolve_mailbox(mailbox)
        folder = await self.client.get_mail_folder_by_name(mailbox, folder_name)
        if folder:
            return self._convert_folder(folder)
        return None

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
        """
        mailbox = self._resolve_mailbox(mailbox)

        with Session(db.engine) as session:
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
        """
        mailbox = self._resolve_mailbox(mailbox)

        with Session(db.engine) as session:
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
        """
        mailbox = self._resolve_mailbox(mailbox)

        with Session(db.engine) as session:
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

    # ==================== Helper Methods ====================

    async def _resolve_folder_id(self, mailbox: str, folder: str) -> str:
        """Resolve folder name to folder ID."""
        # Well-known folder names can be used directly
        well_known = {"inbox", "drafts", "sentitems", "deleteditems", "junkemail", "archive"}
        if folder.lower() in well_known:
            return folder.lower()

        # Check if it's already an ID (Graph IDs are long base64-like strings)
        if len(folder) > 50:
            return folder

        # Look up by name
        folder_obj = await self.client.get_mail_folder_by_name(mailbox, folder)
        if folder_obj:
            return folder_obj.id

        # Fall back to using it as-is
        return folder

    async def _prepare_attachment(self, att: EmailAttachmentInput) -> Optional[dict]:
        """Prepare attachment for Graph API."""
        file_path = Path(att.file_path)

        if not file_path.exists():
            logger.warning(f"Attachment file not found: {file_path}")
            return None

        # Read file content
        content = file_path.read_bytes()

        # Determine MIME type
        content_type = att.content_type
        if not content_type:
            content_type, _ = mimetypes.guess_type(str(file_path))
            content_type = content_type or "application/octet-stream"

        # Determine filename
        name = att.name or file_path.name

        return {
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": name,
            "contentType": content_type,
            "contentBytes": base64.b64encode(content).decode("utf-8"),
        }

    def _convert_message(self, msg: EmailMessageDTO) -> EmailMessage:
        """Convert client DTO to service model."""
        # Extract sender
        sender = None
        if msg.from_recipient:
            sender = EmailAddress(
                address=msg.from_recipient.email_address.address,
                name=msg.from_recipient.email_address.name,
            )

        # Extract recipients
        to_recipients = [
            EmailAddress(
                address=r.email_address.address,
                name=r.email_address.name,
            )
            for r in msg.to_recipients
        ]

        cc_recipients = [
            EmailAddress(
                address=r.email_address.address,
                name=r.email_address.name,
            )
            for r in msg.cc_recipients
        ]

        # Parse dates
        received_at = None
        if msg.received_datetime:
            try:
                received_at = datetime.fromisoformat(msg.received_datetime.replace("Z", "+00:00"))
            except ValueError:
                pass

        sent_at = None
        if msg.sent_datetime:
            try:
                sent_at = datetime.fromisoformat(msg.sent_datetime.replace("Z", "+00:00"))
            except ValueError:
                pass

        # Extract body
        body_content = None
        body_type = None
        if msg.body:
            body_content = msg.body.content
            body_type = msg.body.content_type

        return EmailMessage(
            id=msg.id,
            subject=msg.subject,
            body_preview=msg.body_preview,
            body_content=body_content,
            body_type=body_type,
            sender=sender,
            to_recipients=to_recipients,
            cc_recipients=cc_recipients,
            received_at=received_at,
            sent_at=sent_at,
            is_read=msg.is_read,
            has_attachments=msg.has_attachments,
            importance=msg.importance,
            folder_id=msg.parent_folder_id,
            conversation_id=msg.conversation_id,
            web_link=msg.web_link,
            is_draft=msg.is_draft,
        )

    def _convert_attachment(self, att: EmailAttachmentDTO) -> EmailAttachment:
        """Convert client DTO to service model."""
        return EmailAttachment(
            id=att.id,
            name=att.name,
            content_type=att.content_type,
            size=att.size,
            is_inline=att.is_inline,
        )

    def _convert_folder(self, folder: MailFolderDTO) -> MailFolder:
        """Convert client DTO to service model."""
        return MailFolder(
            id=folder.id,
            name=folder.display_name,
            parent_folder_id=folder.parent_folder_id,
            child_folder_count=folder.child_folder_count,
            unread_count=folder.unread_item_count,
            total_count=folder.total_item_count,
        )


# Global service instance
_msgraph_email_service: Optional[MSGraphEmailService] = None


def get_msgraph_email_service(
    default_mailbox: str = "mohammed@gyptech.com.sa",
) -> MSGraphEmailService:
    """Get or create MSGraph Email service singleton."""
    global _msgraph_email_service
    if _msgraph_email_service is None:
        _msgraph_email_service = MSGraphEmailService(default_mailbox=default_mailbox)
    return _msgraph_email_service
