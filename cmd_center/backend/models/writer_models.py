"""Pydantic models for WriterService - content generation use cases."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ============================================================================
# INPUT CONTEXT MODELS
# ============================================================================

class EmailDraftContext(BaseModel):
    """Context for drafting an email."""
    recipients: list[str] = Field(..., description="Email recipients")
    subject_intent: str = Field(..., description="Intent/topic of email")
    deal_contexts: list[dict] = Field(..., description="Deal information with issues")
    language: str = Field(default="en", description="Email language (en, ar, etc.)")
    tone: str = Field(default="professional", description="Tone: professional, urgent, friendly")
    constraints: Optional[list[str]] = Field(None, description="Constraints like max_length, must_include_deadline")


class ReminderDraftContext(BaseModel):
    """Context for drafting a reminder message."""
    channel: str = Field(..., description="Channel: whatsapp, email, sms")
    urgency: str = Field(..., description="Urgency: low, medium, high, critical")
    recipient_role: str = Field(..., description="Recipient role: pm, sales, admin")
    deal_title: str = Field(..., description="Deal title")
    deal_stage: str = Field(..., description="Deal stage")
    context: str = Field(..., description="Additional context about why reminder is needed")
    due_date: Optional[datetime] = Field(None, description="Optional due date")
    language: str = Field(default="en", description="Message language")
    tone: str = Field(default="professional", description="Tone")


class DealSummaryContext(BaseModel):
    """Context for summarizing a deal."""
    deal_id: int = Field(..., description="Deal ID")
    deal_title: str = Field(..., description="Deal title")
    stage: str = Field(..., description="Current stage")
    owner_name: str = Field(..., description="Deal owner name")
    days_in_stage: int = Field(..., description="Days in current stage")
    notes: list[str] = Field(..., description="Recent notes")
    include_recommendations: bool = Field(default=True, description="Include recommendations")
    include_blockers: bool = Field(default=True, description="Include blockers analysis")
    max_notes: int = Field(default=10, description="Maximum notes to analyze")


class ComplianceContext(BaseModel):
    """Context for checking compliance documentation."""
    deal_id: int = Field(..., description="Deal ID")
    deal_title: str = Field(..., description="Deal title")
    stage: str = Field(..., description="Current stage")
    notes: list[str] = Field(..., description="Deal notes to analyze")
    check_survey: bool = Field(default=True, description="Check for survey checklist")
    check_quality_docs: bool = Field(default=True, description="Check for quality documents")
    check_custom_fields: Optional[list[str]] = Field(None, description="Custom fields to check")


class OrderReceivedContext(BaseModel):
    """Context for analyzing order received deals."""
    deal_id: int = Field(..., description="Deal ID")
    deal_title: str = Field(..., description="Deal title")
    notes: list[str] = Field(..., description="Deal notes to analyze")
    check_end_user: bool = Field(default=True, description="Check if end user identified")
    check_requests: bool = Field(default=True, description="Count end user requests")


class NoteSummaryContext(BaseModel):
    """Context for summarizing notes."""
    notes: list[str] = Field(..., description="Notes to summarize")
    format: str = Field(default="bullets", description="Output format: bullets, table, paragraph")
    max_length: int = Field(default=200, description="Max summary length")
    extract_action_items: bool = Field(default=True, description="Extract action items")


# ============================================================================
# OUTPUT RESULT MODELS
# ============================================================================

class DraftEmailResult(BaseModel):
    """Result from email drafting."""
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body (plain text)")
    body_html: Optional[str] = Field(None, description="Email body (HTML)")
    suggested_followups: Optional[list[str]] = Field(None, description="Suggested follow-up actions")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    warnings: list[str] = Field(default_factory=list, description="Warnings or notes")


class DraftReminderResult(BaseModel):
    """Result from reminder drafting."""
    message_text: str = Field(..., description="Main reminder message")
    short_version: Optional[str] = Field(None, description="Short version for SMS/WhatsApp")
    tags: list[str] = Field(default_factory=list, description="Tags like urgent, escalate, deadline_today")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")


class DealSummaryResult(BaseModel):
    """Result from deal summarization."""
    deal_id: int = Field(..., description="Deal ID")
    summary: str = Field(..., description="Deal summary")
    next_action: Optional[str] = Field(None, description="Suggested next action")
    blockers: list[str] = Field(default_factory=list, description="Identified blockers")
    missing_info: list[str] = Field(default_factory=list, description="Missing information")
    recommendations: Optional[list[str]] = Field(None, description="Recommendations")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")


class ComplianceResult(BaseModel):
    """Result from compliance check."""
    deal_id: int = Field(..., description="Deal ID")
    survey_checklist_present: Optional[bool] = Field(None, description="Survey checklist present")
    quality_docs_present: Optional[bool] = Field(None, description="Quality docs present")
    comment: str = Field(..., description="Summary comment")
    missing_items: list[str] = Field(default_factory=list, description="Missing compliance items")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")


class OrderReceivedResult(BaseModel):
    """Result from order received analysis."""
    deal_id: int = Field(..., description="Deal ID")
    end_user_identified: Optional[bool] = Field(None, description="End user identified")
    end_user_requests_count: int = Field(default=0, description="Count of end user requests")
    missing_items: list[str] = Field(default_factory=list, description="Missing items")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")


class NoteSummaryResult(BaseModel):
    """Result from note summarization."""
    summary: str = Field(..., description="Summary of notes")
    action_items: list[str] = Field(default_factory=list, description="Extracted action items")
    owners: list[str] = Field(default_factory=list, description="Detected owners/assignees")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
