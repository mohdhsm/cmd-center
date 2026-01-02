"""Email-related Pydantic models."""

from pydantic import BaseModel
from typing import Optional
from .deal_models import PipelineName, StageName, OwnerName


class DealIssue(BaseModel):
    """Single deal issue summary for email body."""
    
    deal_id: int
    title: str
    pipeline: PipelineName
    stage: StageName
    issue_summary: str  # e.g. "Overdue 10 days and missing survey checklist"
    next_action: Optional[str] = None


class EmailDraft(BaseModel):
    """Email draft to a salesperson about multiple deals."""

    salesperson: OwnerName
    to_email: str
    subject: str
    body: str
    deals: list[DealIssue]


class FollowupEmailRequest(BaseModel):
    """Request to generate a follow-up email for a deal."""
    deal_id: int
    mode: str  # "overdue", "stuck", "order"
    recipient_email: str = "mohd@gyptech.com.sa"  # Default for testing


class FollowupEmailResponse(BaseModel):
    """Pre-filled email template response."""
    deal_id: int
    deal_title: str
    owner_name: str
    subject: str
    body: str
    recipient_email: str


class SendFollowupRequest(BaseModel):
    """Request to send a follow-up email."""
    deal_id: int
    recipient_email: str
    subject: str
    body: str