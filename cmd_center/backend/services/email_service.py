"""Email service for generating and sending follow-up emails.

MIGRATION NOTE: This service has been refactored to use WriterService
instead of direct LLM calls. See docs/LLM_Architecture_Implementation.md
for migration details.
"""

import logging
from typing import List, Optional

from ..models import EmailDraft, DealIssue, OverdueDeal, ComplianceStatus
from ..models import EmailDraftContext, DraftEmailResult
from ..integrations import get_email_client
from .deal_health_service import get_deal_health_service
from .writer_service import get_writer_service
from .llm_analysis_service import get_llm_analysis_service

logger = logging.getLogger(__name__)


class EmailService:
    """Service for generating and sending follow-up emails.

    Uses WriterService for LLM-powered email generation with confidence scoring.
    """

    def __init__(self):
        self.writer = get_writer_service()
        self.email_client = get_email_client()
        self.deal_health = get_deal_health_service()
        self.llm_analysis = get_llm_analysis_service()

        # Confidence thresholds for auto-send
        self.MIN_CONFIDENCE_AUTO_SEND = 0.7
        self.MIN_CONFIDENCE_REVIEW = 0.5
    
    async def generate_followup_emails(
        self,
        owner_filter: Optional[str] = None,
        min_confidence: float = 0.5,
    ) -> List[EmailDraft]:
        """Generate follow-up emails for overdue/stuck deals.

        Args:
            owner_filter: Filter by owner name (optional)
            min_confidence: Minimum confidence threshold for email generation

        Returns:
            List of EmailDraft objects with confidence scores

        Note:
            Uses WriterService for LLM-powered email generation with:
            - Professional tone based on issue severity
            - Confidence scoring for auto-send decisions
            - Suggested follow-ups and warnings
        """
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

        # Generate email drafts using WriterService
        drafts = []
        for owner, issues in owner_deals.items():
            if not issues:
                continue

            # Build deal contexts for WriterService
            deal_contexts = []
            urgency_level = "medium"
            for issue in issues:
                context_dict = {
                    "title": issue.title,
                    "pipeline": issue.pipeline,
                    "stage": issue.stage,
                    "issue": issue.issue_summary,
                    "next_action": issue.next_action,
                }
                deal_contexts.append(context_dict)

                # Determine urgency
                if "Overdue" in issue.issue_summary:
                    days = int(issue.issue_summary.split()[1])
                    if days > 14:
                        urgency_level = "urgent"

            # Determine tone based on urgency
            tone = "professional"
            if urgency_level == "urgent":
                tone = "urgent"

            # Generate email with WriterService
            try:
                email_result = await self.writer.draft_email(EmailDraftContext(
                    recipients=[f"{owner.lower().replace(' ', '.')}@example.com"],  # Placeholder
                    subject_intent=f"Follow-up needed on {len(issues)} deals",
                    deal_contexts=deal_contexts,
                    tone=tone,
                    language="en",
                    constraints=[
                        "max_length:500",
                        "include_action_items",
                        "courteous_but_clear"
                    ]
                ))

                # Check confidence threshold
                if email_result.confidence < min_confidence:
                    logger.warning(
                        f"Low confidence ({email_result.confidence:.2f}) for email to {owner}. "
                        f"Flagging for manual review."
                    )

                # Create EmailDraft from result
                draft = EmailDraft(
                    salesperson=owner,
                    to_email=f"{owner.lower().replace(' ', '.')}@example.com",
                    subject=email_result.subject,
                    body=email_result.body,
                    deals=issues,
                )

                # Add metadata for decision-making
                draft.confidence = email_result.confidence  # type: ignore
                draft.suggested_followups = email_result.suggested_followups  # type: ignore
                draft.warnings = email_result.warnings  # type: ignore

                drafts.append(draft)

            except Exception as e:
                logger.error(f"Failed to generate email for {owner}: {e}")
                # Fallback to simple email without LLM
                draft = EmailDraft(
                    salesperson=owner,
                    to_email=f"{owner.lower().replace(' ', '.')}@example.com",
                    subject=f"Follow-up needed on {len(issues)} deals",
                    body=self._generate_fallback_email(owner, issues),
                    deals=issues,
                )
                draft.confidence = 0.0  # type: ignore
                draft.warnings = [f"LLM generation failed: {str(e)}"]  # type: ignore
                drafts.append(draft)

        return drafts

    def _generate_fallback_email(self, owner: str, issues: List[DealIssue]) -> str:
        """Generate simple fallback email when LLM fails.

        Args:
            owner: Owner name
            issues: List of deal issues

        Returns:
            Simple text-based email body
        """
        body = f"Hi {owner},\n\n"
        body += "The following deals need your attention:\n\n"
        for issue in issues:
            body += f"- {issue.title} ({issue.stage}): {issue.issue_summary}\n"
            body += f"  Next Action: {issue.next_action}\n\n"
        body += "Please review and update these deals at your earliest convenience.\n\n"
        body += "Best regards,\nCommand Center"
        return body
    
    async def send_email(self, draft: EmailDraft, force: bool = False) -> bool:
        """Send a single email draft.

        Args:
            draft: Email draft to send
            force: Force send even if confidence is low

        Returns:
            True if sent successfully, False otherwise
        """
        # Check confidence before sending
        confidence = getattr(draft, 'confidence', 1.0)
        if not force and confidence < self.MIN_CONFIDENCE_AUTO_SEND:
            logger.warning(
                f"Email to {draft.salesperson} has confidence {confidence:.2f} "
                f"(below auto-send threshold {self.MIN_CONFIDENCE_AUTO_SEND}). "
                f"Skipping auto-send. Use force=True to override."
            )
            return False

        success = await self.email_client.send_email(
            to_email=draft.to_email,
            subject=draft.subject,
            body=draft.body,
        )
        return success

    async def send_multiple_emails(
        self,
        drafts: List[EmailDraft],
        auto_send_threshold: Optional[float] = None,
    ) -> dict[str, dict]:
        """Send multiple email drafts with confidence-based filtering.

        Args:
            drafts: List of email drafts
            auto_send_threshold: Override default auto-send threshold

        Returns:
            Dict mapping salesperson to result dict with:
                - sent: bool (whether email was sent)
                - confidence: float (email generation confidence)
                - reason: str (reason if not sent)
        """
        threshold = auto_send_threshold or self.MIN_CONFIDENCE_AUTO_SEND
        results = {}

        for draft in drafts:
            confidence = getattr(draft, 'confidence', 1.0)
            warnings = getattr(draft, 'warnings', [])

            if confidence < threshold:
                results[draft.salesperson] = {
                    "sent": False,
                    "confidence": confidence,
                    "reason": f"Low confidence ({confidence:.2f}), requires manual review",
                    "warnings": warnings,
                }
                logger.info(f"Skipping email to {draft.salesperson}: low confidence")
                continue

            try:
                success = await self.send_email(draft, force=True)
                results[draft.salesperson] = {
                    "sent": success,
                    "confidence": confidence,
                    "reason": "Sent successfully" if success else "Send failed",
                    "warnings": warnings,
                }
            except Exception as e:
                logger.error(f"Failed to send email to {draft.salesperson}: {e}")
                results[draft.salesperson] = {
                    "sent": False,
                    "confidence": confidence,
                    "reason": f"Error: {str(e)}",
                    "warnings": warnings,
                }

        return results

    def get_emails_for_review(self, drafts: List[EmailDraft]) -> List[EmailDraft]:
        """Filter emails that need manual review based on confidence.

        Args:
            drafts: List of email drafts

        Returns:
            List of drafts requiring manual review
        """
        return [
            draft for draft in drafts
            if getattr(draft, 'confidence', 1.0) < self.MIN_CONFIDENCE_AUTO_SEND
        ]

    def get_emails_ready_to_send(self, drafts: List[EmailDraft]) -> List[EmailDraft]:
        """Filter emails ready for auto-send based on confidence.

        Args:
            drafts: List of email drafts

        Returns:
            List of drafts ready for auto-send
        """
        return [
            draft for draft in drafts
            if getattr(draft, 'confidence', 1.0) >= self.MIN_CONFIDENCE_AUTO_SEND
        ]


# Global service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service