"""Email service for generating and sending follow-up emails."""

from typing import List, Optional

from ..models import EmailDraft, DealIssue, OverdueDeal, ComplianceStatus
from ..integrations import get_llm_client, get_email_client
from .deal_health_service import get_deal_health_service
from .llm_analysis_service import get_llm_analysis_service


class EmailService:
    """Service for generating and sending follow-up emails."""
    
    def __init__(self):
        self.llm = get_llm_client()
        self.email_client = get_email_client()
        self.deal_health = get_deal_health_service()
        self.llm_analysis = get_llm_analysis_service()
    
    async def generate_followup_emails(
        self,
        owner_filter: Optional[str] = None,
    ) -> List[EmailDraft]:
        """Generate follow-up emails for overdue/stuck deals."""
        # Get overdue deals
        aramco_overdue = self.deal_health.get_overdue_deals("Aramco Projects", min_days=7)
        commercial_overdue = self.deal_health.get_overdue_deals("pipeline", min_days=7)
        
        # Get compliance issues
        compliance_issues = await self.llm_analysis.analyze_compliance("Aramco Projects")
        
        # Group by owner
        owner_deals = {}
        
        for deal in aramco_overdue + commercial_overdue:
            if owner_filter and deal.owner != owner_filter:
                continue
            
            if deal.owner not in owner_deals:
                owner_deals[deal.owner] = []
            
            issue = DealIssue(
                deal_id=deal.id,
                title=deal.title,
                pipeline=deal.pipeline,
                stage=deal.stage,
                issue_summary=f"Overdue {deal.overdue_days} days",
                next_action="Update deal status and add activity",
            )
            owner_deals[deal.owner].append(issue)
        
        # Add compliance issues
        for comp in compliance_issues:
            if owner_filter and comp.owner != owner_filter:
                continue
            
            if comp.owner not in owner_deals:
                owner_deals[comp.owner] = []
            
            issues = []
            if not comp.survey_checklist_present:
                issues.append("missing survey checklist")
            if not comp.quality_docs_present:
                issues.append("missing quality docs")
            
            if issues:
                issue = DealIssue(
                    deal_id=comp.id,
                    title=comp.title,
                    pipeline=comp.pipeline,
                    stage=comp.stage,
                    issue_summary=f"Compliance: {', '.join(issues)}",
                    next_action="Upload required documentation",
                )
                owner_deals[comp.owner].append(issue)
        
        # Generate email drafts
        drafts = []
        for owner, issues in owner_deals.items():
            if not issues:
                continue
            
            # Generate email body with LLM
            prompt = f"""Generate a professional follow-up email for {owner} about the following deals:

{chr(10).join(f"- {issue.title}: {issue.issue_summary}" for issue in issues)}

Be courteous but clear about the actions needed."""
            
            body = await self.llm.generate_completion(
                prompt,
                system_prompt="You are a helpful sales manager writing follow-up emails.",
                max_tokens=500,
            )
            
            draft = EmailDraft(
                salesperson=owner,
                to_email=f"{owner.lower().replace(' ', '.')}@example.com",  # Placeholder
                subject=f"Follow-up needed on {len(issues)} deals",
                body=body,
                deals=issues,
            )
            drafts.append(draft)
        
        return drafts
    
    async def send_email(self, draft: EmailDraft) -> bool:
        """Send a single email draft."""
        success = await self.email_client.send_email(
            to_email=draft.to_email,
            subject=draft.subject,
            body=draft.body,
        )
        return success
    
    async def send_multiple_emails(self, drafts: List[EmailDraft]) -> dict[str, bool]:
        """Send multiple email drafts."""
        results = {}
        for draft in drafts:
            success = await self.send_email(draft)
            results[draft.salesperson] = success
        return results


# Global service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service