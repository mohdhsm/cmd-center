"""WriterService - LLM-powered content generation service.

This service handles all content generation use cases:
- Email drafting
- Reminder drafting (multi-channel)
- Deal summarization
- Compliance checking
- Note summarization

It depends on:
- LLMClient (infrastructure/transport)
- PromptRegistry (templates)
- db_queries (data access)
- LLMObservabilityLogger (structured logging)
"""

import logging
from typing import Optional
from datetime import datetime

from ..models.writer_models import (
    EmailDraftContext,
    ReminderDraftContext,
    DealSummaryContext,
    ComplianceContext,
    OrderReceivedContext,
    NoteSummaryContext,
    DealHealthContext,
    DraftEmailResult,
    DraftReminderResult,
    DealSummaryResult,
    ComplianceResult,
    OrderReceivedResult,
    NoteSummaryResult,
    DealHealthResult,
)
from ..integrations.llm_client import get_llm_client, LLMClient, LLMValidationError, LLMError
from ..integrations.llm_observability import observe_llm_request, get_observability_logger
from .prompt_registry import get_prompt_registry, PromptRegistry

logger = logging.getLogger(__name__)


class WriterService:
    """Service for LLM-powered content generation.

    This service orchestrates all writing/analysis tasks by:
    1. Loading appropriate prompts from registry
    2. Calling LLM with structured output
    3. Handling errors and providing fallbacks
    4. Applying business rules/policies
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        prompt_registry: Optional[PromptRegistry] = None,
    ):
        self.llm = llm_client or get_llm_client()
        self.prompts = prompt_registry or get_prompt_registry()

    # ========================================================================
    # EMAIL DRAFTING
    # ========================================================================

    async def draft_email(self, context: EmailDraftContext) -> DraftEmailResult:
        """Draft a professional email based on context.

        Args:
            context: Email drafting context

        Returns:
            DraftEmailResult with subject, body, and metadata

        Raises:
            LLMError: On LLM failures (after retries)
        """
        # Get prompt config for observability
        config = self.prompts.get_prompt_config("email.followup.v1")

        with observe_llm_request(
            service="writer_service",
            operation="draft_email",
            model=config.get("model_tier", "balanced"),
            metadata={
                "num_recipients": len(context.recipients),
                "tone": context.tone,
                "language": context.language,
                "num_deal_contexts": len(context.deal_contexts),
            }
        ) as obs_ctx:
            try:
                # Get prompt
                system_prompt, user_prompt = self.prompts.render_prompt(
                    "email.followup.v1",
                    {
                        "recipients": context.recipients,
                        "subject_intent": context.subject_intent,
                        "language": context.language,
                        "tone": context.tone,
                        "deal_contexts": context.deal_contexts,
                        "constraints": context.constraints or [],
                    }
                )

                # Call LLM with structured output
                llm_response = await self.llm.generate_structured_completion(
                    schema=DraftEmailResult,
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    max_tokens=config["max_tokens"],
                    temperature=config["temperature"],
                    fallback_on_validation_error=True,
                )

                # Update observability context with LLM metrics
                # Note: Since generate_structured_completion returns the schema directly,
                # we don't have access to raw LLMResponse. This is a limitation.
                # For now, estimate based on result
                obs_ctx.metadata["confidence"] = llm_response.confidence
                obs_ctx.metadata["num_warnings"] = len(llm_response.warnings)

                # Apply communications policy
                llm_response.body = self._apply_comms_policy(llm_response.body, context)

                logger.info(
                    f"Successfully drafted email for {len(context.recipients)} recipients",
                    extra={"confidence": llm_response.confidence}
                )

                return llm_response

            except LLMValidationError as e:
                logger.error(f"Failed to parse email draft: {e}")
                obs_ctx.metadata["fallback"] = True
                return self._email_fallback(context, str(e))

            except LLMError as e:
                logger.error(f"LLM error during email drafting: {e}")
                raise

    # ========================================================================
    # REMINDER DRAFTING
    # ========================================================================

    async def draft_reminder(self, context: ReminderDraftContext) -> DraftReminderResult:
        """Draft a reminder message for specified channel.

        Args:
            context: Reminder drafting context

        Returns:
            DraftReminderResult with message and metadata

        Raises:
            LLMError: On LLM failures
        """
        try:
            # Select prompt based on channel
            prompt_id = f"reminder.{context.channel}.v1"
            if prompt_id not in [p.id for p in self.prompts._prompts.values()]:
                # Fallback to email template
                prompt_id = "reminder.email.v1"
                logger.warning(f"No prompt for channel '{context.channel}', using email template")

            # Render prompt
            system_prompt, user_prompt = self.prompts.render_prompt(
                prompt_id,
                {
                    "deal_title": context.deal_title,
                    "deal_stage": context.deal_stage,
                    "due_date": context.due_date.isoformat() if context.due_date else None,
                    "urgency": context.urgency,
                    "recipient_role": context.recipient_role,
                    "context": context.context,
                }
            )

            # Get config
            config = self.prompts.get_prompt_config(prompt_id)

            # Call LLM
            result = await self.llm.generate_structured_completion(
                schema=DraftReminderResult,
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=config["max_tokens"],
                temperature=config["temperature"],
                fallback_on_validation_error=True,
            )

            logger.info(
                f"Successfully drafted {context.channel} reminder",
                extra={"urgency": context.urgency, "confidence": result.confidence}
            )

            return result

        except LLMValidationError as e:
            logger.error(f"Failed to parse reminder: {e}")
            return self._reminder_fallback(context, str(e))

        except LLMError as e:
            logger.error(f"LLM error during reminder drafting: {e}")
            raise

    # ========================================================================
    # DEAL ANALYSIS
    # ========================================================================

    async def summarize_deal(self, context: DealSummaryContext) -> DealSummaryResult:
        """Generate a summary and analysis for a deal.

        Args:
            context: Deal summary context

        Returns:
            DealSummaryResult with summary and recommendations

        Raises:
            LLMError: On LLM failures
        """
        try:
            # Limit notes
            notes = context.notes[:context.max_notes]

            # Render prompt
            system_prompt, user_prompt = self.prompts.render_prompt(
                "deal.summarize.v1",
                {
                    "deal_title": context.deal_title,
                    "stage": context.stage,
                    "days_in_stage": context.days_in_stage,
                    "owner_name": context.owner_name,
                    "notes": notes,
                }
            )

            # Get config
            config = self.prompts.get_prompt_config("deal.summarize.v1")

            # Call LLM
            result = await self.llm.generate_structured_completion(
                schema=DealSummaryResult,
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=config["max_tokens"],
                temperature=config["temperature"],
                fallback_on_validation_error=True,
            )

            # Set deal_id
            result.deal_id = context.deal_id

            # Remove recommendations if not requested
            if not context.include_recommendations:
                result.recommendations = None

            # Remove blockers if not requested
            if not context.include_blockers:
                result.blockers = []

            logger.info(
                f"Successfully summarized deal {context.deal_id}",
                extra={"confidence": result.confidence}
            )

            return result

        except LLMValidationError as e:
            logger.error(f"Failed to parse deal summary for deal {context.deal_id}: {e}")
            return self._deal_summary_fallback(context, str(e))

        except LLMError as e:
            logger.error(f"LLM error during deal summarization: {e}")
            raise

    async def analyze_compliance(self, context: ComplianceContext) -> ComplianceResult:
        """Analyze deal compliance documentation.

        Args:
            context: Compliance check context

        Returns:
            ComplianceResult with compliance status

        Raises:
            LLMError: On LLM failures
        """
        try:
            # Render prompt
            system_prompt, user_prompt = self.prompts.render_prompt(
                "deal.compliance_check.v1",
                {
                    "deal_title": context.deal_title,
                    "stage": context.stage,
                    "notes": context.notes,
                }
            )

            # Get config
            config = self.prompts.get_prompt_config("deal.compliance_check.v1")

            # Call LLM
            result = await self.llm.generate_structured_completion(
                schema=ComplianceResult,
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=config["max_tokens"],
                temperature=config["temperature"],
                fallback_on_validation_error=True,
            )

            # Set deal_id
            result.deal_id = context.deal_id

            logger.info(
                f"Successfully analyzed compliance for deal {context.deal_id}",
                extra={"confidence": result.confidence}
            )

            return result

        except LLMValidationError as e:
            logger.error(f"Failed to parse compliance result for deal {context.deal_id}: {e}")
            return self._compliance_fallback(context, str(e))

        except LLMError as e:
            logger.error(f"LLM error during compliance analysis: {e}")
            raise

    async def analyze_order_received(self, context: OrderReceivedContext) -> OrderReceivedResult:
        """Analyze order received deal for end user identification.

        Args:
            context: Order received analysis context

        Returns:
            OrderReceivedResult with analysis

        Raises:
            LLMError: On LLM failures
        """
        try:
            # Render prompt
            system_prompt, user_prompt = self.prompts.render_prompt(
                "deal.order_received_analysis.v1",
                {
                    "deal_title": context.deal_title,
                    "notes": context.notes,
                }
            )

            # Get config
            config = self.prompts.get_prompt_config("deal.order_received_analysis.v1")

            # Call LLM
            result = await self.llm.generate_structured_completion(
                schema=OrderReceivedResult,
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=config["max_tokens"],
                temperature=config["temperature"],
                fallback_on_validation_error=True,
            )

            # Set deal_id
            result.deal_id = context.deal_id

            logger.info(
                f"Successfully analyzed order received for deal {context.deal_id}",
                extra={"confidence": result.confidence}
            )

            return result

        except LLMValidationError as e:
            logger.error(f"Failed to parse order received result for deal {context.deal_id}: {e}")
            return self._order_received_fallback(context, str(e))

        except LLMError as e:
            logger.error(f"LLM error during order received analysis: {e}")
            raise

    # ========================================================================
    # GENERIC SUMMARIZATION
    # ========================================================================

    async def summarize_notes(self, context: NoteSummaryContext) -> NoteSummaryResult:
        """Summarize notes/meeting text.

        Args:
            context: Note summary context

        Returns:
            NoteSummaryResult with summary and action items

        Raises:
            LLMError: On LLM failures
        """
        try:
            # Render prompt
            system_prompt, user_prompt = self.prompts.render_prompt(
                "notes.summarize.v1",
                {
                    "notes": context.notes,
                    "format": context.format,
                    "max_length": context.max_length,
                    "extract_action_items": context.extract_action_items,
                }
            )

            # Get config
            config = self.prompts.get_prompt_config("notes.summarize.v1")

            # Call LLM
            result = await self.llm.generate_structured_completion(
                schema=NoteSummaryResult,
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=config["max_tokens"],
                temperature=config["temperature"],
                fallback_on_validation_error=True,
            )

            logger.info(
                f"Successfully summarized {len(context.notes)} notes",
                extra={"confidence": result.confidence}
            )

            return result

        except LLMValidationError as e:
            logger.error(f"Failed to parse note summary: {e}")
            return self._note_summary_fallback(context, str(e))

        except LLMError as e:
            logger.error(f"LLM error during note summarization: {e}")
            raise

    # ========================================================================
    # DEAL HEALTH ANALYSIS
    # ========================================================================

    async def analyze_deal_health(self, context: DealHealthContext) -> DealHealthResult:
        """Analyze deal health and provide actionable insights.

        Args:
            context: Deal health analysis context

        Returns:
            DealHealthResult with status, blockers, and recommendations

        Raises:
            LLMError: On LLM failures
        """
        try:
            # Render prompt
            system_prompt, user_prompt = self.prompts.render_prompt(
                "deal.health_analysis.v1",
                {
                    "deal_id": context.deal_id,
                    "deal_title": context.deal_title,
                    "stage": context.stage,
                    "stage_code": context.stage_code,
                    "days_in_stage": context.days_in_stage,
                    "owner_name": context.owner_name,
                    "value_sar": context.value_sar,
                    "days_since_last_note": context.days_since_last_note,
                    "stage_history": context.stage_history,
                    "notes": context.notes,
                }
            )

            # Get config
            config = self.prompts.get_prompt_config("deal.health_analysis.v1")

            # Call LLM
            result = await self.llm.generate_structured_completion(
                schema=DealHealthResult,
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=config["max_tokens"],
                temperature=config["temperature"],
                fallback_on_validation_error=True,
            )

            # Set deal_id and days_in_stage from context
            result.deal_id = context.deal_id
            result.days_in_stage = context.days_in_stage

            logger.info(
                f"Successfully analyzed health for deal {context.deal_id}",
                extra={"health_status": result.health_status, "confidence": result.confidence}
            )

            return result

        except LLMValidationError as e:
            logger.error(f"Failed to parse health analysis for deal {context.deal_id}: {e}")
            return self._deal_health_fallback(context, str(e))

        except LLMError as e:
            logger.error(f"LLM error during deal health analysis: {e}")
            raise

    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================

    async def batch_summarize_deals(
        self,
        contexts: list[DealSummaryContext],
        max_concurrent: int = 5,
    ) -> list[DealSummaryResult]:
        """Summarize multiple deals concurrently.

        Args:
            contexts: List of deal summary contexts
            max_concurrent: Maximum concurrent LLM requests

        Returns:
            List of DealSummaryResult

        Note:
            This processes deals in batches to avoid rate limits
        """
        import asyncio

        results = []
        for i in range(0, len(contexts), max_concurrent):
            batch = contexts[i:i + max_concurrent]
            batch_results = await asyncio.gather(
                *[self.summarize_deal(ctx) for ctx in batch],
                return_exceptions=True,
            )

            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch summarization error: {result}")
                else:
                    results.append(result)

        logger.info(f"Batch summarized {len(results)}/{len(contexts)} deals")
        return results

    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================

    def _apply_comms_policy(self, text: str, context: EmailDraftContext) -> str:
        """Apply communication policy/guidelines to generated text.

        Args:
            text: Generated text
            context: Original context

        Returns:
            Modified text with policy applied
        """
        # Example: Ensure professional closing
        # Add more business rules as needed
        return text

    def _email_fallback(self, context: EmailDraftContext, error: str) -> DraftEmailResult:
        """Provide fallback email when LLM fails.

        Args:
            context: Original context
            error: Error message

        Returns:
            Basic DraftEmailResult
        """
        return DraftEmailResult(
            subject=f"Follow-up: {context.subject_intent}",
            body=f"Dear {', '.join(context.recipients)},\n\nThis is a follow-up regarding the deals mentioned.\n\nBest regards",
            confidence=0.0,
            warnings=[f"LLM error - using fallback: {error}"],
        )

    def _reminder_fallback(self, context: ReminderDraftContext, error: str) -> DraftReminderResult:
        """Provide fallback reminder when LLM fails."""
        return DraftReminderResult(
            message_text=f"Reminder: {context.deal_title} requires attention ({context.urgency} priority)",
            short_version=f"{context.deal_title} - {context.urgency}",
            tags=["fallback", context.urgency],
            confidence=0.0,
        )

    def _deal_summary_fallback(self, context: DealSummaryContext, error: str) -> DealSummaryResult:
        """Provide fallback deal summary when LLM fails."""
        return DealSummaryResult(
            deal_id=context.deal_id,
            summary=f"Deal in {context.stage} stage for {context.days_in_stage} days",
            next_action="Review deal status",
            confidence=0.0,
        )

    def _compliance_fallback(self, context: ComplianceContext, error: str) -> ComplianceResult:
        """Provide fallback compliance result when LLM fails."""
        return ComplianceResult(
            deal_id=context.deal_id,
            survey_checklist_present=None,
            quality_docs_present=None,
            comment="Unable to analyze compliance - LLM error",
            confidence=0.0,
        )

    def _order_received_fallback(self, context: OrderReceivedContext, error: str) -> OrderReceivedResult:
        """Provide fallback order received result when LLM fails."""
        return OrderReceivedResult(
            deal_id=context.deal_id,
            end_user_identified=None,
            end_user_requests_count=0,
            confidence=0.0,
        )

    def _note_summary_fallback(self, context: NoteSummaryContext, error: str) -> NoteSummaryResult:
        """Provide fallback note summary when LLM fails."""
        return NoteSummaryResult(
            summary=f"Summary of {len(context.notes)} notes unavailable due to error",
            confidence=0.0,
        )

    def _deal_health_fallback(self, context: DealHealthContext, error: str) -> DealHealthResult:
        """Provide fallback deal health result when LLM fails."""
        return DealHealthResult(
            deal_id=context.deal_id,
            health_status="unknown",
            summary=f"Unable to analyze deal health - LLM error: {error}",
            days_in_stage=context.days_in_stage,
            stage_threshold_warning=0,
            stage_threshold_critical=0,
            communication_assessment="Unknown",
            attribution="none",
            recommended_action="Manual review required",
            confidence=0.0,
        )


# Global service instance
_writer_service: Optional[WriterService] = None


def get_writer_service() -> WriterService:
    """Get or create writer service singleton."""
    global _writer_service
    if _writer_service is None:
        _writer_service = WriterService()
    return _writer_service
