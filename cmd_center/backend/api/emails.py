"""Email API endpoints."""

import json
from datetime import date, datetime
from typing import List

from fastapi import APIRouter, HTTPException, Query

from ..models import EmailDraft
from ..models.email_models import FollowupEmailRequest, FollowupEmailResponse
from ..services import get_email_service
from ..services.db_queries import get_deal_by_id

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


@router.post("/followup/generate", response_model=FollowupEmailResponse)
async def generate_followup_email(request: FollowupEmailRequest):
    """Generate a follow-up email template for a specific deal based on mode."""
    # Fetch deal from database
    deal = get_deal_by_id(request.deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail=f"Deal {request.deal_id} not found")

    deal_title = deal.title
    owner_name = deal.owner_name or "Team Member"

    # Determine deadline from raw_json if available
    deadline_str = "N/A"
    is_overdue = False
    if deal.raw_json:
        raw = json.loads(deal.raw_json)
        deadline_str = raw.get("expected_close_date") or raw.get("close_time") or "N/A"
        if deadline_str and deadline_str != "N/A":
            try:
                deadline_date = datetime.fromisoformat(deadline_str.replace("Z", "+00:00")).date()
                is_overdue = deadline_date < date.today()
            except Exception:
                pass

    last_update_str = str(deal.update_time)[:10] if deal.update_time else "Unknown"

    # Generate subject and body based on mode
    if request.mode == "overdue":
        if is_overdue:
            subject = f"CRITICAL {deal_title} is overdue, reach end user to change SDD"
            body = f"""Dear {owner_name},

The deadline for this deal is {deadline_str}, currently is overdue please contact the end user to change its SDD (Statistical Delivery Date) ASAP.

Once the date is updated, please update it in Pipedrive.
"""
        else:
            subject = f"{deal_title} is near overdue, contact end user to change SDD"
            body = f"""Dear {owner_name},

The deadline for this deal is near overdue, please contact the end user to extend the SDD (Statistical Delivery Date).

Once the date is updated, please update it in Pipedrive.
"""
    elif request.mode == "stuck":
        subject = f"Deal hasn't been updated in a while, please update it"
        body = f"""Dear {owner_name},

The following deal is stuck and hasn't been updated since {last_update_str}, please do the necessary and get more information and update it with the latest.

Log your activities and notes in Pipedrive.

Thanks,
"""
    elif request.mode == "order":
        subject = f"Activate {deal_title} ASAP"
        body = f"""Dear {owner_name},

It's important for us to complete the projects and push the projects from start to finish.

It's your responsibility to contact the end user. The deal {deal_title} has been stuck for a while, contact the end user, get information from them, move the deal through.

Log your activities and emails in Pipedrive.
"""
    else:
        subject = f"Follow-up needed: {deal_title}"
        body = f"""Dear {owner_name},

Please review and update the deal {deal_title} in Pipedrive.

Thanks,
"""

    return FollowupEmailResponse(
        deal_id=request.deal_id,
        deal_title=deal_title,
        owner_name=owner_name,
        subject=subject,
        body=body,
        recipient_email=request.recipient_email,
    )