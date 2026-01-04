"""Email tools for the agent."""

from typing import Optional
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult, run_async
from ...backend.services.msgraph_email_service import get_msgraph_email_service


class SearchEmailsParams(BaseModel):
    """Parameters for search_emails tool."""

    subject: Optional[str] = Field(
        default=None,
        description="Search term to find in email subjects"
    )
    sender: Optional[str] = Field(
        default=None,
        description="Filter by sender email address"
    )
    folder: str = Field(
        default="inbox",
        description="Email folder to search in (e.g., inbox, sentitems)"
    )
    limit: int = Field(
        default=10,
        description="Maximum number of results to return"
    )


class SearchEmails(BaseTool):
    """Search emails by subject or sender."""

    name = "search_emails"
    description = "Search through emails using subject keywords or sender address. Returns matching emails with subject, sender, date, and preview."
    parameters_model = SearchEmailsParams

    def execute(self, params: SearchEmailsParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_msgraph_email_service()

            # Call the async search_emails method
            emails = run_async(
                service.search_emails(
                    subject=params.subject,
                    sender=params.sender,
                    folder=params.folder,
                    limit=params.limit,
                )
            )

            # Transform EmailMessage objects to dict format for JSON serialization
            emails_data = []
            for email in emails:
                email_dict = {
                    "id": email.id,
                    "subject": email.subject,
                    "body_preview": email.body_preview,
                    "sender_address": email.sender.address if email.sender else None,
                    "sender_name": email.sender.name if email.sender else None,
                    "received_at": email.received_at.isoformat() if email.received_at else None,
                    "is_read": email.is_read,
                    "has_attachments": email.has_attachments,
                }
                emails_data.append(email_dict)

            return ToolResult(
                success=True,
                data={
                    "emails": emails_data,
                    "count": len(emails_data),
                    "subject_filter": params.subject,
                    "sender_filter": params.sender,
                    "folder": params.folder,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetEmailsParams(BaseModel):
    """Parameters for get_emails tool."""

    limit: int = Field(
        default=20,
        description="Maximum number of emails to return"
    )
    folder: str = Field(
        default="inbox",
        description="Email folder to read from (e.g., inbox, sentitems, drafts)"
    )
    unread_only: bool = Field(
        default=False,
        description="Only return unread emails"
    )


class GetEmails(BaseTool):
    """Get recent emails from inbox or specified folder."""

    name = "get_emails"
    description = "Get recent emails from inbox or specified folder. Use this to check the latest emails or look for specific messages."
    parameters_model = GetEmailsParams

    def execute(self, params: GetEmailsParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_msgraph_email_service()

            # Call the async get_emails method
            emails = run_async(
                service.get_emails(
                    folder=params.folder,
                    unread_only=params.unread_only,
                    limit=params.limit,
                )
            )

            # Transform EmailMessage objects to dict format for JSON serialization
            emails_data = []
            for email in emails:
                email_dict = {
                    "id": email.id,
                    "subject": email.subject,
                    "body_preview": email.body_preview,
                    "sender_address": email.sender.address if email.sender else None,
                    "sender_name": email.sender.name if email.sender else None,
                    "received_at": email.received_at.isoformat() if email.received_at else None,
                    "is_read": email.is_read,
                    "has_attachments": email.has_attachments,
                }
                emails_data.append(email_dict)

            return ToolResult(
                success=True,
                data={
                    "emails": emails_data,
                    "count": len(emails_data),
                    "folder": params.folder,
                    "unread_only": params.unread_only,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
