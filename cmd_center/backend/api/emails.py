"""Email API endpoints."""

from fastapi import APIRouter, Query
from typing import List

from ..models import EmailDraft
from ..services import get_email_service

router = APIRouter()


@router.post("/followups/generate", response_model=List[EmailDraft])
async def generate_followup_emails(owner_filter: str = Query(None)):
    """Generate follow-up emails for overdue/stuck deals."""
    service = get_email_service()
    drafts = await service.generate_followup_emails(owner_filter=owner_filter)
    return drafts


@router.post("/followups/send")
async def send_followup_emails(drafts: List[EmailDraft]):
    """Send follow-up emails."""
    service = get_email_service()
    results = await service.send_multiple_emails(drafts)
    
    return {
        "sent_count": sum(1 for success in results.values() if success),
        "failed_count": sum(1 for success in results.values() if not success),
        "results": results,
    }