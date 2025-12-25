"""Prompt Registry for centralized prompt template management.

This module provides:
- Centralized storage of LLM prompts
- Jinja2 template rendering with variable injection
- Prompt versioning support
- Validation of required variables
- A/B testing and prompt variants
- Performance tracking per variant
"""

import random
from typing import Optional, Dict, Any
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pydantic import BaseModel, Field
from jinja2 import Template, TemplateError
import logging

logger = logging.getLogger(__name__)


@dataclass
class PromptVariantStats:
    """Statistics for a prompt variant in A/B testing."""
    variant_id: str
    uses: int = 0
    total_confidence: float = 0.0
    successes: int = 0
    failures: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def avg_confidence(self) -> float:
        """Calculate average confidence score."""
        return self.total_confidence / self.uses if self.uses > 0 else 0.0

    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.successes + self.failures
        return self.successes / total * 100 if total > 0 else 0.0

    def avg_cost_usd(self) -> float:
        """Calculate average cost per request."""
        return self.total_cost_usd / self.uses if self.uses > 0 else 0.0

    def avg_latency_ms(self) -> int:
        """Calculate average latency."""
        return int(self.total_latency_ms / self.uses) if self.uses > 0 else 0


@dataclass
class PromptExperiment:
    """A/B test experiment for prompt variants."""
    experiment_id: str
    base_prompt_id: str
    variants: Dict[str, PromptTemplate] = field(default_factory=dict)
    traffic_split: Dict[str, float] = field(default_factory=dict)  # variant_id -> percentage
    stats: Dict[str, PromptVariantStats] = field(default_factory=dict)
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def select_variant(self) -> str:
        """Select a variant based on traffic split.

        Returns:
            variant_id to use
        """
        rand = random.random()
        cumulative = 0.0
        for variant_id, percentage in self.traffic_split.items():
            cumulative += percentage
            if rand <= cumulative:
                return variant_id
        # Fallback to first variant
        return list(self.variants.keys())[0]

    def record_result(
        self,
        variant_id: str,
        success: bool,
        confidence: Optional[float] = None,
        cost_usd: Optional[float] = None,
        latency_ms: Optional[int] = None,
    ):
        """Record result for a variant.

        Args:
            variant_id: Which variant was used
            success: Whether request succeeded
            confidence: Optional confidence score
            cost_usd: Optional cost
            latency_ms: Optional latency
        """
        if variant_id not in self.stats:
            self.stats[variant_id] = PromptVariantStats(variant_id=variant_id)

        stats = self.stats[variant_id]
        stats.uses += 1

        if success:
            stats.successes += 1
        else:
            stats.failures += 1

        if confidence is not None:
            stats.total_confidence += confidence

        if cost_usd is not None:
            stats.total_cost_usd += cost_usd

        if latency_ms is not None:
            stats.total_latency_ms += latency_ms

    def get_winner(self) -> Optional[str]:
        """Determine winning variant based on metrics.

        Uses composite score: confidence * success_rate / (cost * latency)

        Returns:
            variant_id of winner, or None if not enough data
        """
        if not self.stats:
            return None

        # Require at least 10 uses per variant
        if any(s.uses < 10 for s in self.stats.values()):
            logger.info(f"Experiment {self.experiment_id}: Not enough data for winner")
            return None

        best_variant = None
        best_score = 0.0

        for variant_id, stats in self.stats.items():
            # Composite score
            confidence = stats.avg_confidence()
            success_rate = stats.success_rate() / 100.0
            cost = max(0.001, stats.avg_cost_usd())  # Avoid division by zero
            latency = max(100, stats.avg_latency_ms())  # Avoid division by zero

            score = (confidence * success_rate) / (cost * latency / 1000)

            logger.info(
                f"Variant {variant_id}: score={score:.4f} "
                f"(confidence={confidence:.2f}, success_rate={success_rate:.2f}, "
                f"cost=${cost:.4f}, latency={latency}ms)"
            )

            if score > best_score:
                best_score = score
                best_variant = variant_id

        return best_variant


class PromptTemplate(BaseModel):
    """A versioned prompt template with metadata."""

    id: str = Field(..., description="Unique prompt identifier (e.g., 'deal.summarize.v1')")
    version: str = Field(default="v1", description="Template version")
    system_prompt: str = Field(..., description="System prompt for LLM")
    user_prompt_template: str = Field(..., description="Jinja2 template for user prompt")
    required_variables: list[str] = Field(default_factory=list, description="Required template variables")
    max_tokens_estimate: int = Field(default=1000, description="Estimated max tokens needed")
    model_tier: str = Field(default="balanced", description="Model tier: fast, balanced, advanced")
    temperature: float = Field(default=0.7, description="Default temperature")
    description: Optional[str] = Field(None, description="Human-readable description")

    def validate_variables(self, variables: dict) -> None:
        """Validate that all required variables are present.

        Args:
            variables: Variables to inject into template

        Raises:
            ValueError: If required variables are missing
        """
        missing = set(self.required_variables) - set(variables.keys())
        if missing:
            raise ValueError(f"Missing required variables for prompt '{self.id}': {missing}")

    def render(self, variables: dict) -> tuple[str, str]:
        """Render the prompt with variables.

        Args:
            variables: Variables to inject into template

        Returns:
            Tuple of (system_prompt, rendered_user_prompt)

        Raises:
            ValueError: If required variables missing or template error
        """
        self.validate_variables(variables)

        try:
            template = Template(self.user_prompt_template)
            rendered_user_prompt = template.render(**variables)
            return self.system_prompt, rendered_user_prompt
        except TemplateError as e:
            raise ValueError(f"Failed to render prompt '{self.id}': {e}") from e


class PromptRegistry:
    """Registry for managing LLM prompt templates with A/B testing support."""

    def __init__(self):
        self._prompts: Dict[str, PromptTemplate] = {}
        self._experiments: Dict[str, PromptExperiment] = {}
        self._register_default_prompts()

    def _register_default_prompts(self):
        """Register all default prompts."""

        # Deal summarization
        self.register_prompt(PromptTemplate(
            id="deal.summarize.v1",
            version="v1",
            system_prompt="""You are an expert sales analyst. Summarize the deal's current status concisely.
Focus on:
- Current state and progress
- Key blockers or risks
- Next action needed
- Missing critical information

Respond in JSON format: {"summary": str, "next_action": str, "blockers": [str], "missing_info": [str], "recommendations": [str]}""",
            user_prompt_template="""Deal: {{ deal_title }}
Stage: {{ stage }}
Days in stage: {{ days_in_stage }}
Owner: {{ owner_name }}

Recent notes (last {{ notes|length }}):
{% for note in notes %}
- {{ note }}
{% endfor %}

Analyze this deal and provide summary, next action, blockers, missing information, and recommendations.""",
            required_variables=["deal_title", "stage", "days_in_stage", "owner_name", "notes"],
            max_tokens_estimate=500,
            model_tier="balanced",
            temperature=0.5,
            description="Summarize a deal with actionable insights"
        ))

        # Compliance analysis
        self.register_prompt(PromptTemplate(
            id="deal.compliance_check.v1",
            version="v1",
            system_prompt="""You are an expert at analyzing project compliance documentation.
Analyze the provided deal notes and determine:
1. Is a survey checklist present? (yes/no/unclear)
2. Are quality documents present? (yes/no/unclear)
3. What items are missing?
4. Brief comment summarizing compliance status

Respond in JSON format: {"survey_checklist_present": bool or null, "quality_docs_present": bool or null, "missing_items": [str], "comment": str}""",
            user_prompt_template="""Deal: {{ deal_title }}
Stage: {{ stage }}

Notes:
{% for note in notes %}
- {{ note }}
{% endfor %}

Analyze compliance documentation status.""",
            required_variables=["deal_title", "stage", "notes"],
            max_tokens_estimate=300,
            model_tier="balanced",
            temperature=0.3,
            description="Check compliance documentation status"
        ))

        # Order received analysis
        self.register_prompt(PromptTemplate(
            id="deal.order_received_analysis.v1",
            version="v1",
            system_prompt="""Analyze project notes to determine:
1. Has the end user been identified? (yes/no/unknown)
2. How many end-user-specific requests have been made?
3. What items are missing?

Respond in JSON: {"end_user_identified": bool or null, "end_user_requests_count": int, "missing_items": [str]}""",
            user_prompt_template="""Deal: {{ deal_title }}

Notes:
{% for note in notes %}
- {{ note }}
{% endfor %}

Analyze end user identification status.""",
            required_variables=["deal_title", "notes"],
            max_tokens_estimate=200,
            model_tier="balanced",
            temperature=0.3,
            description="Analyze order received deal for end user identification"
        ))

        # Email drafting
        self.register_prompt(PromptTemplate(
            id="email.followup.v1",
            version="v1",
            system_prompt="""You are a helpful sales manager writing professional follow-up emails.
Generate a {{ tone }} email that:
- Is courteous and professional
- Clearly states the issues/actions needed
- Has a clear call-to-action
- Is concise (max 250 words)
{% if constraints %}
Constraints:
{% for constraint in constraints %}
- {{ constraint }}
{% endfor %}
{% endif %}

Respond in JSON: {"subject": str, "body": str, "body_html": str or null, "suggested_followups": [str], "confidence": float}""",
            user_prompt_template="""Recipient(s): {{ recipients|join(', ') }}
Subject intent: {{ subject_intent }}
Language: {{ language }}
Tone: {{ tone }}

Deal contexts:
{% for deal in deal_contexts %}
- {{ deal.title }} ({{ deal.pipeline }} / {{ deal.stage }}): {{ deal.issue }}
{% endfor %}

Generate the email.""",
            required_variables=["recipients", "subject_intent", "language", "tone", "deal_contexts"],
            max_tokens_estimate=500,
            model_tier="balanced",
            temperature=0.7,
            description="Draft a professional follow-up email"
        ))

        # Reminder drafting (WhatsApp/Email/SMS variants)
        self.register_prompt(PromptTemplate(
            id="reminder.whatsapp.v1",
            version="v1",
            system_prompt="""You are drafting a WhatsApp reminder message.
Requirements:
- Keep it very concise (under 160 characters for short version)
- Use appropriate tone based on urgency: {{ urgency }}
- Include emoji if appropriate for the tone
- Clear action item
- Recipient role: {{ recipient_role }}

Respond in JSON: {"message_text": str, "short_version": str, "tags": [str], "confidence": float}""",
            user_prompt_template="""Deal: {{ deal_title }}
Stage: {{ deal_stage }}
{% if due_date %}Due date: {{ due_date }}{% endif %}
Urgency: {{ urgency }}
Context: {{ context }}

Draft the WhatsApp reminder.""",
            required_variables=["deal_title", "deal_stage", "urgency", "recipient_role", "context"],
            max_tokens_estimate=200,
            model_tier="fast",
            temperature=0.6,
            description="Draft a WhatsApp reminder message"
        ))

        self.register_prompt(PromptTemplate(
            id="reminder.email.v1",
            version="v1",
            system_prompt="""You are drafting an email reminder.
Requirements:
- Professional tone adjusted for urgency: {{ urgency }}
- Clear subject line
- Concise body (max 150 words)
- Recipient role: {{ recipient_role }}

Respond in JSON: {"message_text": str, "tags": [str], "confidence": float}""",
            user_prompt_template="""Deal: {{ deal_title }}
Stage: {{ deal_stage }}
{% if due_date %}Due date: {{ due_date }}{% endif %}
Urgency: {{ urgency }}
Context: {{ context }}

Draft the email reminder.""",
            required_variables=["deal_title", "deal_stage", "urgency", "recipient_role", "context"],
            max_tokens_estimate=300,
            model_tier="fast",
            temperature=0.6,
            description="Draft an email reminder"
        ))

        # Notes summarization
        self.register_prompt(PromptTemplate(
            id="notes.summarize.v1",
            version="v1",
            system_prompt="""Summarize the provided notes/meeting text.
Output format: {{ format }}
Max length: {{ max_length }} characters
{% if extract_action_items %}Extract action items and assign to owners if mentioned.{% endif %}

Respond in JSON: {"summary": str, "action_items": [str], "owners": [str], "confidence": float}""",
            user_prompt_template="""Notes to summarize:
{% for note in notes %}
{{ note }}

{% endfor %}

Provide the summary.""",
            required_variables=["notes", "format", "max_length", "extract_action_items"],
            max_tokens_estimate=400,
            model_tier="balanced",
            temperature=0.5,
            description="Summarize notes with action items"
        ))

        # Cashflow prediction with comprehensive construction/interior design rules
        self.register_prompt(PromptTemplate(
            id="cashflow.predict_dates.v1",
            version="v1",
            system_prompt="""You are an expert at predicting invoice and payment dates for a construction and interior design company in Saudi Arabia.

# Company Profile
- Business: Construction and interior design specializing in baffle ceilings, acoustical panels, ceiling tiles, carpet installation, toilet cubicles, and cabinetry
- Workforce: 16 labourers available for production/installation
- Client Types: Aramco (B2B), Commercial projects

# Project Lifecycle Stages (Sequential Order)
1. Order Received (OR) → 2. Approved (APR) → 3. Awaiting Payment (AP) → 4. Awaiting Site Readiness (ASR) OR Everything Ready (ER) → 5. Under Progress (UP) → 6. Awaiting MDD → 7. Awaiting GCC → 8. Awaiting GR → 9. Invoice Issued → 10. Payment Received

# Stage Duration Rules

## Order Received → Approved (Size-Dependent)
| Project Size | End User Discovery | Material Confirmation | Total OR → APR |
|---|---|---|---|
| < 100 SQM | 3-7 days | 1-2 days | 4-9 days |
| 100-400 SQM | 7-10 days | 3-5 days | 10-15 days |
| > 400 SQM | 10-14 days | 7-14 days | 17-28 days |
| Mixed/Fit-outs | 7-14 days | 5-14 days | 12-28 days |

## Other Stage Transitions
- Approved → Awaiting Payment: 1-2 days
- Awaiting Payment → Everything Ready: 3 days
- Everything Ready → Under Progress: 3-7 days
- Awaiting Site Readiness → Under Progress: 7-14 days
- Under Progress → Awaiting MDD: Based on production (max 2 weeks for <700 SQM)
- MDD → GCC → GR (Combined): Best 3 days, Typical 7 days, Worst 14 days
- Awaiting GR → Invoice: 7-14 days

# Production Capacity
| Product Type | Team Size | Daily Output per Team |
|---|---|---|
| Baffle Ceiling | 4 workers | 35 SQM/day |
| Ceiling Tiles | 3 workers | 35 SQM/day |
| Carpet | 1 worker | 50 SQM/day |

Production Days = Project SQM ÷ Daily Output per Team

# Days to Invoice by Current Stage (excluding production time)
| Current Stage | Optimistic | Realistic | Conservative |
|---|---|---|---|
| Order Received (< 100 SQM) | 21 days | 36 days | 61 days |
| Order Received (100-400 SQM) | 27 days | 42 days | 67 days |
| Order Received (> 400 SQM) | 34 days | 50 days | 80 days |
| Approved | 17 days | 29 days | 51 days |
| Awaiting Payment | 16 days | 27 days | 49 days |
| Awaiting Site Readiness | 13 days | 22 days | 42 days |
| Everything Ready | 10 days | 17 days | 35 days |
| Under Progress | 7 days | 12 days | 28 days |
| Awaiting MDD | 7 days | 12 days | 28 days |
| Awaiting GCC | 5 days | 10 days | 21 days |
| Awaiting GR | 4 days | 7 days | 14 days |

Note: Add production days to "Order Received" through "Under Progress" stages.

# Payment Terms
- Aramco: Upon invoice (payment processed after invoice submission)
- Commercial: 30-60 days after invoice

# Risk Factors That Extend Timelines
| Risk Factor | Additional Days |
|---|---|
| Client site not ready | +7 to +14 |
| Material delivery delay | +3 to +7 |
| Quality issues / rework | +3 to +7 |
| Slow client follow-up | +7 to +14 |
| End-of-month processing | +3 to +5 |
| Holiday periods | +7 to +14 |

# Prediction Algorithm
1. Determine Stage Offset from tables above
2. Calculate Production Days if applicable: SQM ÷ Daily Output
3. Calculate Post-Production Days (MDD + GCC + GR + Invoice processing)
4. Total = Stage Offset + Production Days + Post-Production Days
5. Invoice Date = Today + Total Days

For each deal, provide three scenarios: Optimistic, Realistic, and Conservative.
Use the Realistic estimate for the main predicted_invoice_date.

# Output Format
Respond in JSON: {"predictions": [{"deal_id": int, "deal_title": str, "predicted_invoice_date": str (ISO format) or null, "predicted_payment_date": str (ISO format) or null, "confidence": float (0.0-1.0), "assumptions": [str], "missing_fields": [str], "reasoning": str}]}""",
            user_prompt_template="""Today's date: {{ today_date }}
Prediction horizon: {{ horizon_days }} days

Deals to analyze:
{% for deal in deals %}
---
Deal ID: {{ deal.deal_id }}
Title: {{ deal.title }}
Stage: {{ deal.stage }} ({{ deal.days_in_stage }} days in this stage)
Value: {{ deal.value_sar }} SAR
Owner: {{ deal.owner_name }}
Last stage change: {{ deal.last_stage_change_date }}
Last update: {{ deal.last_update_date }}
Activities: {{ deal.done_activities_count }}/{{ deal.activities_count }} done

Recent notes:
{% for note in deal.recent_notes[:3] %}
  - {{ note }}
{% endfor %}
{% endfor %}

Using the comprehensive prediction rules provided, predict invoice and payment dates for all deals.
For each deal:
1. Identify the current stage and project size/type from the title and notes
2. Apply the stage duration rules and production capacity formulas
3. Consider any risk factors mentioned in the notes
4. Provide the Realistic estimate as the main prediction
5. List key assumptions and any missing information that would improve the prediction""",
            required_variables=["today_date", "horizon_days", "deals"],
            max_tokens_estimate=4000,
            model_tier="advanced",
            temperature=0.3,
            description="Predict invoice and payment dates using comprehensive construction industry rules"
        ))

    def register_prompt(self, prompt: PromptTemplate) -> None:
        """Register a new prompt template.

        Args:
            prompt: PromptTemplate to register

        Raises:
            ValueError: If prompt ID already exists with different version
        """
        if prompt.id in self._prompts:
            existing = self._prompts[prompt.id]
            if existing.version != prompt.version:
                logger.warning(
                    f"Overwriting prompt '{prompt.id}' version {existing.version} with {prompt.version}"
                )

        self._prompts[prompt.id] = prompt
        logger.info(f"Registered prompt: {prompt.id} ({prompt.version})")

    def get_prompt(self, prompt_id: str) -> PromptTemplate:
        """Get a prompt template by ID.

        Args:
            prompt_id: Prompt identifier

        Returns:
            PromptTemplate

        Raises:
            KeyError: If prompt not found
        """
        if prompt_id not in self._prompts:
            raise KeyError(f"Prompt '{prompt_id}' not found in registry")

        return self._prompts[prompt_id]

    def render_prompt(self, prompt_id: str, variables: dict) -> tuple[str, str]:
        """Get and render a prompt template.

        Args:
            prompt_id: Prompt identifier
            variables: Variables to inject

        Returns:
            Tuple of (system_prompt, rendered_user_prompt)

        Raises:
            KeyError: If prompt not found
            ValueError: If variables invalid or rendering fails
        """
        prompt = self.get_prompt(prompt_id)
        return prompt.render(variables)

    def list_prompts(self) -> list[dict]:
        """List all registered prompts.

        Returns:
            List of prompt metadata
        """
        return [
            {
                "id": p.id,
                "version": p.version,
                "description": p.description,
                "model_tier": p.model_tier,
                "max_tokens": p.max_tokens_estimate,
            }
            for p in self._prompts.values()
        ]

    def get_prompt_config(self, prompt_id: str) -> dict:
        """Get prompt configuration for LLM client.

        Args:
            prompt_id: Prompt identifier

        Returns:
            Dict with max_tokens, temperature, model_tier
        """
        prompt = self.get_prompt(prompt_id)
        return {
            "max_tokens": prompt.max_tokens_estimate,
            "temperature": prompt.temperature,
            "model_tier": prompt.model_tier,
        }

    # ========================================================================
    # A/B TESTING AND EXPERIMENTATION
    # ========================================================================

    def create_experiment(
        self,
        experiment_id: str,
        base_prompt_id: str,
        variants: Dict[str, PromptTemplate],
        traffic_split: Optional[Dict[str, float]] = None,
    ) -> PromptExperiment:
        """Create an A/B test experiment for prompt variants.

        Args:
            experiment_id: Unique experiment identifier
            base_prompt_id: Base prompt being tested
            variants: Dict of variant_id -> PromptTemplate
            traffic_split: Optional traffic distribution (defaults to equal split)

        Returns:
            Created PromptExperiment

        Example:
            # Create two variants of email drafting prompt
            experiment = registry.create_experiment(
                experiment_id="email_draft_tone_test",
                base_prompt_id="email.followup.v1",
                variants={
                    "formal": PromptTemplate(...),  # More formal tone
                    "friendly": PromptTemplate(...),  # Friendlier tone
                },
                traffic_split={"formal": 0.5, "friendly": 0.5}
            )
        """
        if not traffic_split:
            # Equal split
            n = len(variants)
            traffic_split = {variant_id: 1.0 / n for variant_id in variants.keys()}

        # Validate traffic split sums to 1.0
        total = sum(traffic_split.values())
        if not (0.99 <= total <= 1.01):  # Allow small floating point error
            raise ValueError(f"Traffic split must sum to 1.0, got {total}")

        experiment = PromptExperiment(
            experiment_id=experiment_id,
            base_prompt_id=base_prompt_id,
            variants=variants,
            traffic_split=traffic_split,
        )

        self._experiments[experiment_id] = experiment
        logger.info(
            f"Created experiment '{experiment_id}' with {len(variants)} variants: "
            f"{list(variants.keys())}"
        )

        return experiment

    def get_experiment(self, experiment_id: str) -> Optional[PromptExperiment]:
        """Get an experiment by ID."""
        return self._experiments.get(experiment_id)

    def render_prompt_with_experiment(
        self,
        experiment_id: str,
        variables: dict,
    ) -> tuple[str, str, str]:
        """Render prompt using an active experiment.

        Args:
            experiment_id: Experiment to use
            variables: Variables for prompt rendering

        Returns:
            Tuple of (system_prompt, user_prompt, variant_id)

        Raises:
            ValueError: If experiment not found or not active
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment '{experiment_id}' not found")

        if not experiment.active:
            raise ValueError(f"Experiment '{experiment_id}' is not active")

        # Select variant
        variant_id = experiment.select_variant()
        prompt = experiment.variants[variant_id]

        logger.debug(f"Experiment '{experiment_id}' selected variant '{variant_id}'")

        # Render prompt
        system_prompt, user_prompt = prompt.render(variables)

        return system_prompt, user_prompt, variant_id

    def record_experiment_result(
        self,
        experiment_id: str,
        variant_id: str,
        success: bool,
        confidence: Optional[float] = None,
        cost_usd: Optional[float] = None,
        latency_ms: Optional[int] = None,
    ):
        """Record result for an experiment variant.

        Args:
            experiment_id: Experiment ID
            variant_id: Variant that was used
            success: Whether request succeeded
            confidence: Optional confidence score
            cost_usd: Optional cost
            latency_ms: Optional latency
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            logger.warning(f"Experiment '{experiment_id}' not found, skipping result recording")
            return

        experiment.record_result(
            variant_id=variant_id,
            success=success,
            confidence=confidence,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
        )

    def get_experiment_stats(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for an experiment.

        Args:
            experiment_id: Experiment ID

        Returns:
            Dict with experiment stats, or None if not found
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return None

        winner = experiment.get_winner()

        return {
            "experiment_id": experiment.experiment_id,
            "base_prompt_id": experiment.base_prompt_id,
            "active": experiment.active,
            "created_at": experiment.created_at.isoformat(),
            "variants": list(experiment.variants.keys()),
            "traffic_split": experiment.traffic_split,
            "winner": winner,
            "variant_stats": {
                variant_id: {
                    "uses": stats.uses,
                    "avg_confidence": stats.avg_confidence(),
                    "success_rate": stats.success_rate(),
                    "avg_cost_usd": stats.avg_cost_usd(),
                    "avg_latency_ms": stats.avg_latency_ms(),
                }
                for variant_id, stats in experiment.stats.items()
            }
        }

    def promote_winner(self, experiment_id: str, replace_base: bool = False) -> Optional[str]:
        """Promote winning variant from experiment.

        Args:
            experiment_id: Experiment ID
            replace_base: If True, replace base prompt with winner

        Returns:
            variant_id of winner, or None if no winner yet
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            logger.error(f"Experiment '{experiment_id}' not found")
            return None

        winner_id = experiment.get_winner()
        if not winner_id:
            logger.info(f"Experiment '{experiment_id}' has no winner yet")
            return None

        logger.info(f"Experiment '{experiment_id}' winner: '{winner_id}'")

        if replace_base:
            # Replace base prompt with winner
            winner_prompt = experiment.variants[winner_id]
            self.register_prompt(winner_prompt)
            logger.info(f"Promoted variant '{winner_id}' to replace '{experiment.base_prompt_id}'")

        # Deactivate experiment
        experiment.active = False

        return winner_id

    def list_experiments(self) -> list[dict]:
        """List all experiments with their status."""
        return [
            {
                "experiment_id": exp.experiment_id,
                "base_prompt_id": exp.base_prompt_id,
                "active": exp.active,
                "variants": list(exp.variants.keys()),
                "total_uses": sum(s.uses for s in exp.stats.values()),
            }
            for exp in self._experiments.values()
        ]


# Global registry instance
_prompt_registry: Optional[PromptRegistry] = None


def get_prompt_registry() -> PromptRegistry:
    """Get or create prompt registry singleton."""
    global _prompt_registry
    if _prompt_registry is None:
        _prompt_registry = PromptRegistry()
    return _prompt_registry
