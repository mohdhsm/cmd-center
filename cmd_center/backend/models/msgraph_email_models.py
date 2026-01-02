"""Pydantic models for Microsoft Graph Email Service.

This module provides high-level models for the email service interface,
distinct from the low-level DTOs in microsoft_client.py.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict


# ==================== Input Models ====================


class EmailRecipientInput(BaseModel):
    """Email recipient for composing emails."""

    email: str
    name: Optional[str] = None


class EmailAttachmentInput(BaseModel):
    """Attachment input for sending emails."""

    file_path: Path = Field(description="Local path to the file")
    name: Optional[str] = Field(default=None, description="Override filename")
    content_type: Optional[str] = Field(default=None, description="MIME type override")


class EmailComposeRequest(BaseModel):
    """Request to compose and send an email."""

    from_mailbox: str = Field(description="Mailbox to send from")
    to: List[str] = Field(description="List of recipient email addresses")
    subject: str
    body: str
    body_type: Literal["text", "html"] = "html"
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[EmailAttachmentInput]] = None
    save_to_sent: bool = True


class EmailSearchFilters(BaseModel):
    """Filters for searching emails."""

    subject: Optional[str] = Field(default=None, description="Search in subject")
    sender: Optional[str] = Field(default=None, description="Filter by sender email")
    from_date: Optional[datetime] = Field(default=None, description="Emails after this date")
    to_date: Optional[datetime] = Field(default=None, description="Emails before this date")
    folder: str = Field(default="inbox", description="Folder to search in")
    unread_only: bool = False
    has_attachments: Optional[bool] = None


# ==================== Response Models ====================


class EmailAddress(BaseModel):
    """Email address in responses."""

    model_config = ConfigDict(populate_by_name=True)

    address: str
    name: Optional[str] = None

    @classmethod
    def from_graph_recipient(cls, recipient: dict) -> "EmailAddress":
        """Create from Graph API recipient format."""
        email_addr = recipient.get("emailAddress", {})
        return cls(
            address=email_addr.get("address", ""),
            name=email_addr.get("name"),
        )


class EmailAttachment(BaseModel):
    """Email attachment metadata."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    content_type: str = "application/octet-stream"
    size: int = 0
    is_inline: bool = False


class EmailMessage(BaseModel):
    """Email message response model."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    subject: Optional[str] = None
    body_preview: str = ""
    body_content: Optional[str] = None
    body_type: Optional[str] = None
    sender: Optional[EmailAddress] = None
    to_recipients: List[EmailAddress] = Field(default_factory=list)
    cc_recipients: List[EmailAddress] = Field(default_factory=list)
    received_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    is_read: bool = False
    has_attachments: bool = False
    importance: str = "normal"
    folder_id: Optional[str] = None
    conversation_id: Optional[str] = None
    web_link: Optional[str] = None
    is_draft: bool = False
    attachments: Optional[List[EmailAttachment]] = None


class MailFolder(BaseModel):
    """Mail folder response model."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    parent_folder_id: Optional[str] = None
    child_folder_count: int = 0
    unread_count: int = 0
    total_count: int = 0


class EmailListResponse(BaseModel):
    """Paginated list of emails."""

    items: List[EmailMessage]
    total: Optional[int] = None
    has_more: bool = False


class FolderListResponse(BaseModel):
    """List of mail folders."""

    items: List[MailFolder]
    total: int = 0
