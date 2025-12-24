# LLM Services Quick Reference

## Service Overview

| Service | Purpose | Use When |
|---------|---------|----------|
| **WriterService** | Content generation (emails, summaries, analysis) | Drafting emails, summarizing deals, analyzing compliance |
| **CashflowPredictionService** | Intelligent cashflow forecasting | Predicting invoice/payment dates |
| **LLMClient** | Low-level LLM infrastructure | Custom use cases not covered by services |
| **PromptRegistry** | Centralized prompt management | Accessing/modifying prompts |

---

## WriterService

### Import

```python
from cmd_center.backend.services.writer_service import get_writer_service
from cmd_center.backend.models import (
    EmailDraftContext, DealSummaryContext, ComplianceContext,
    ReminderDraftContext, OrderReceivedContext, NoteSummaryContext
)

writer = get_writer_service()
```

### Draft Email

```python
result = await writer.draft_email(EmailDraftContext(
    recipients=["user@example.com"],
    subject_intent="Follow-up on overdue deals",
    deal_contexts=[{"title": "Deal X", "pipeline": "Aramco", "stage": "Order Received", "issue": "Overdue 14 days"}],
    tone="professional",  # professional | urgent | friendly
    language="en",
    constraints=["max_length:250", "must_include_deadline"]
))

print(result.subject)           # str
print(result.body)              # str
print(result.body_html)         # Optional[str]
print(result.confidence)        # float (0.0-1.0)
print(result.suggested_followups)  # Optional[list[str]]
```

### Summarize Deal

```python
result = await writer.summarize_deal(DealSummaryContext(
    deal_id=12345,
    deal_title="Project Alpha",
    stage="Order Received",
    owner_name="John Doe",
    days_in_stage=14,
    notes=["Note 1", "Note 2", "Note 3"],
    include_recommendations=True,
    include_blockers=True,
    max_notes=10
))

print(result.summary)           # str
print(result.next_action)       # Optional[str]
print(result.blockers)          # list[str]
print(result.missing_info)      # list[str]
print(result.recommendations)   # Optional[list[str]]
print(result.confidence)        # float (0.0-1.0)
```

### Check Compliance

```python
result = await writer.analyze_compliance(ComplianceContext(
    deal_id=12345,
    deal_title="Project Alpha",
    stage="Order Received",
    notes=["Survey checklist uploaded", "Quality docs pending"],
    check_survey=True,
    check_quality_docs=True
))

print(result.survey_checklist_present)  # Optional[bool]
print(result.quality_docs_present)      # Optional[bool]
print(result.comment)                   # str
print(result.missing_items)             # list[str]
print(result.confidence)                # float (0.0-1.0)
```

### Draft Reminder

```python
result = await writer.draft_reminder(ReminderDraftContext(
    channel="whatsapp",  # whatsapp | email | sms
    urgency="high",      # low | medium | high | critical
    recipient_role="pm", # pm | sales | admin
    deal_title="Project Alpha",
    deal_stage="Order Received",
    context="Deal stuck for 30 days",
    due_date=datetime(2025, 1, 15),
    language="en"
))

print(result.message_text)      # str
print(result.short_version)     # Optional[str] (for SMS/WhatsApp)
print(result.tags)              # list[str] (e.g., ["urgent", "deadline_today"])
print(result.confidence)        # float (0.0-1.0)
```

### Analyze Order Received

```python
result = await writer.analyze_order_received(OrderReceivedContext(
    deal_id=12345,
    deal_title="Project Alpha",
    notes=["Customer confirmed", "Waiting for end user details"],
    check_end_user=True,
    check_requests=True
))

print(result.end_user_identified)       # Optional[bool]
print(result.end_user_requests_count)   # int
print(result.missing_items)             # list[str]
print(result.confidence)                # float (0.0-1.0)
```

### Summarize Notes

```python
result = await writer.summarize_notes(NoteSummaryContext(
    notes=["Meeting with client", "Agreed on specs", "Follow up next week"],
    format="bullets",  # bullets | table | paragraph
    max_length=200,
    extract_action_items=True
))

print(result.summary)           # str
print(result.action_items)      # list[str]
print(result.owners)            # list[str]
print(result.confidence)        # float (0.0-1.0)
```

### Batch Operations

```python
contexts = [
    DealSummaryContext(deal_id=1, deal_title="Deal 1", ...),
    DealSummaryContext(deal_id=2, deal_title="Deal 2", ...),
    DealSummaryContext(deal_id=3, deal_title="Deal 3", ...),
]

results = await writer.batch_summarize_deals(contexts, max_concurrent=5)
# Returns list[DealSummaryResult]
```

---

## CashflowPredictionService

### Import

```python
from cmd_center.backend.services.cashflow_prediction_service import get_cashflow_prediction_service
from cmd_center.backend.models import (
    CashflowPredictionInput, PredictionOptions,
    ForecastOptions, DealForPrediction
)

service = get_cashflow_prediction_service()
```

### Predict Cashflow (Main)

```python
result = await service.predict_cashflow(CashflowPredictionInput(
    pipeline_name="Aramco Projects",
    horizon_days=90,
    granularity="week",  # week | month
    today_date=datetime.now(),  # Optional, defaults to now
    assumptions_flags={}  # Optional overrides
))

# Metadata
print(result.metadata.generated_at)             # datetime
print(result.metadata.deals_analyzed)           # int
print(result.metadata.deals_with_predictions)   # int
print(result.metadata.avg_confidence)           # float

# Per-deal predictions
for pred in result.per_deal_predictions:
    print(pred.deal_id)                 # int
    print(pred.deal_title)              # str
    print(pred.predicted_invoice_date)  # Optional[datetime]
    print(pred.predicted_payment_date)  # Optional[datetime]
    print(pred.confidence)              # float (0.0-1.0)
    print(pred.assumptions)             # list[str]
    print(pred.missing_fields)          # list[str]
    print(pred.reasoning)               # Optional[str]

# Aggregated forecast
for bucket in result.aggregated_forecast:
    print(bucket.period)                        # str (e.g., "2025-W01")
    print(bucket.expected_invoice_value_sar)    # float
    print(bucket.deal_count)                    # int
    print(bucket.comment)                       # Optional[str]

# Warnings and assumptions
print(result.warnings)          # list[str]
print(result.assumptions_used)  # list[str]
```

### Predict Deal Dates Only

```python
deals = [
    DealForPrediction(
        deal_id=1,
        title="Project A",
        stage="Order Received",
        stage_id=27,
        value_sar=100000,
        owner_name="John",
        days_in_stage=14,
        recent_notes=["Note 1", "Note 2"]
    ),
    # ... more deals
]

options = PredictionOptions(
    horizon_days=90,
    confidence_threshold=0.7,
    use_deterministic_overrides=True
)

predictions = await service.predict_deal_dates(deals, options, datetime.now())
# Returns list[DealPrediction]
```

### Generate Forecast Table

```python
# From predictions
forecast = service.generate_forecast_table(
    predictions,
    ForecastOptions(
        group_by="week",  # week | month | owner | stage
        include_confidence_bands=True,
        currency="SAR"
    )
)

# Periods
for period in forecast.periods:
    print(period.period)                # str (e.g., "2025-W01")
    print(period.invoice_value_sar)     # float
    print(period.payment_value_sar)     # float
    print(period.deal_count)            # int
    print(period.avg_confidence)        # float

# Totals
print(forecast.totals.total_invoice_value_sar)  # float
print(forecast.totals.total_payment_value_sar)  # float
print(forecast.totals.total_deals)              # int
```

### Explain Assumptions

```python
report = service.explain_assumptions(predictions)

print(report.global_assumptions)        # list[str] - Common assumptions
print(report.per_deal_assumptions)      # dict[int, list[str]] - Per deal
print(report.confidence_distribution)   # dict[str, int] - {"high": 10, "medium": 5, "low": 2}
```

---

## LLMClient (Direct Usage)

### Import

```python
from cmd_center.backend.integrations.llm_client import get_llm_client

client = get_llm_client()
```

### Basic Completion

```python
response = await client.generate_completion(
    prompt="Summarize this text: ...",
    system_prompt="You are a helpful assistant",
    max_tokens=500,
    temperature=0.7,
    model=None  # Optional model override
)

print(response.content)         # str
print(response.usage.prompt_tokens)     # int
print(response.usage.completion_tokens) # int
print(response.usage.total_tokens)      # int
print(response.usage.estimated_cost_usd)  # float
print(response.response_time_ms)        # int
print(response.model)                   # str
```

### Structured Completion

```python
from pydantic import BaseModel

class EmailResponse(BaseModel):
    subject: str
    body: str
    confidence: float

result = await client.generate_structured_completion(
    schema=EmailResponse,
    prompt="Draft an email about...",
    system_prompt="You are a professional writer",
    max_tokens=500,
    temperature=0.7,
    fallback_on_validation_error=True
)

# result is an instance of EmailResponse
print(result.subject)
print(result.body)
print(result.confidence)
```

### Streaming

```python
async for token in client.stream_completion(
    prompt="Write a story...",
    system_prompt="You are a creative writer",
    max_tokens=1000,
    temperature=0.9
):
    print(token, end='', flush=True)
```

### Metrics

```python
metrics = client.get_metrics()
print(metrics["request_count"])   # int
print(metrics["total_tokens"])    # int
print(metrics["total_cost_usd"])  # float

# Reset
client.reset_metrics()
```

---

## PromptRegistry

### Import

```python
from cmd_center.backend.services.prompt_registry import get_prompt_registry

registry = get_prompt_registry()
```

### List Prompts

```python
prompts = registry.list_prompts()
for p in prompts:
    print(p["id"])              # str (e.g., "deal.summarize.v1")
    print(p["version"])         # str
    print(p["description"])     # Optional[str]
    print(p["model_tier"])      # str (fast | balanced | advanced)
    print(p["max_tokens"])      # int
```

### Render Prompt

```python
system_prompt, user_prompt = registry.render_prompt(
    "deal.summarize.v1",
    {
        "deal_title": "Project Alpha",
        "stage": "Order Received",
        "days_in_stage": 14,
        "owner_name": "John Doe",
        "notes": ["Note 1", "Note 2"]
    }
)
```

### Get Prompt Config

```python
config = registry.get_prompt_config("deal.summarize.v1")
print(config["max_tokens"])    # int
print(config["temperature"])   # float
print(config["model_tier"])    # str
```

### Register Custom Prompt

```python
from cmd_center.backend.services.prompt_registry import PromptTemplate

registry.register_prompt(PromptTemplate(
    id="custom.analysis.v1",
    version="v1",
    system_prompt="You are an expert analyst...",
    user_prompt_template="Analyze: {{ text }}",
    required_variables=["text"],
    max_tokens_estimate=500,
    model_tier="balanced",
    temperature=0.5,
    description="Custom analysis prompt"
))
```

---

## Error Handling

### LLM Errors

```python
from cmd_center.backend.integrations.llm_client import LLMError, LLMRateLimitError, LLMValidationError

try:
    result = await writer.summarize_deal(context)
except LLMRateLimitError:
    # Rate limit exceeded - wait and retry
    await asyncio.sleep(60)
    result = await writer.summarize_deal(context)
except LLMValidationError as e:
    # LLM response didn't match expected schema
    print(f"Validation error: {e}")
    # Service already returned fallback with confidence=0.0
except LLMError as e:
    # General LLM error (network, timeout, etc.)
    print(f"LLM error: {e}")
    raise
```

### Confidence Thresholds

```python
result = await writer.summarize_deal(context)

if result.confidence < 0.5:
    print("WARNING: Low confidence result, manual review recommended")
elif result.confidence < 0.7:
    print("CAUTION: Medium confidence result")
else:
    print("OK: High confidence result")
```

---

## Best Practices

### 1. Always Check Confidence

```python
result = await writer.draft_email(context)
if result.confidence >= 0.7:
    # Auto-send or approve
    pass
else:
    # Flag for manual review
    pass
```

### 2. Use Batch Operations for Multiple Items

```python
# ❌ Bad (sequential)
for deal in deals:
    result = await writer.summarize_deal(deal)

# ✅ Good (concurrent with rate limiting)
contexts = [DealSummaryContext(...) for deal in deals]
results = await writer.batch_summarize_deals(contexts, max_concurrent=5)
```

### 3. Provide Context to LLM

```python
# ❌ Bad (minimal context)
context = DealSummaryContext(
    deal_id=1,
    deal_title="Deal",
    stage="Stage",
    owner_name="Owner",
    days_in_stage=0,
    notes=[]
)

# ✅ Good (rich context)
context = DealSummaryContext(
    deal_id=12345,
    deal_title="ACME Corp - Security System Installation",
    stage="Order Received",
    owner_name="John Doe",
    days_in_stage=14,
    notes=[
        "Customer confirmed PO#12345",
        "Waiting for site access approval",
        "Technical specs reviewed and approved",
        "Installation scheduled for next month"
    ]
)
```

### 4. Use Deterministic Rules When Possible

```python
# CashflowPredictionService automatically tries deterministic rules first
# If you have custom rules, implement them in DeterministicRules class

# Example: For simple stage-based estimates, use rules instead of LLM
from cmd_center.backend.services.deterministic_rules import DeterministicRules

rules = DeterministicRules()
estimate_days = rules.get_stage_estimate("Order Received")  # 10 days
```

### 5. Monitor Token Usage

```python
from cmd_center.backend.integrations.llm_client import get_llm_client

client = get_llm_client()

# Periodic monitoring
metrics = client.get_metrics()
if metrics["total_cost_usd"] > 10.0:
    print(f"WARNING: LLM costs at ${metrics['total_cost_usd']:.2f}")
```

---

## Model Tiers

| Tier | Model | Use Case | Speed | Cost |
|------|-------|----------|-------|------|
| **fast** | claude-3-haiku | Simple tasks, high volume | Very Fast | Low |
| **balanced** | claude-3.5-sonnet | Most tasks (default) | Fast | Medium |
| **advanced** | claude-opus-4 | Complex analysis | Slower | High |

Set tier in prompt configuration:
```python
PromptTemplate(
    ...,
    model_tier="fast"  # Will use Haiku instead of Sonnet
)
```

---

## Common Patterns

### Pattern 1: Email + Reminder Workflow

```python
# 1. Draft email
email = await writer.draft_email(EmailDraftContext(...))

# 2. If email not sent, create reminder
if not email_sent:
    reminder = await writer.draft_reminder(ReminderDraftContext(
        channel="whatsapp",
        urgency="high",
        ...
    ))
```

### Pattern 2: Deal Analysis Pipeline

```python
# 1. Summarize deal
summary = await writer.summarize_deal(DealSummaryContext(...))

# 2. Check compliance
compliance = await writer.analyze_compliance(ComplianceContext(...))

# 3. If order received, check end user
if stage == "Order Received":
    order_analysis = await writer.analyze_order_received(OrderReceivedContext(...))
```

### Pattern 3: Cashflow Forecasting

```python
# 1. Predict cashflow
result = await cashflow_service.predict_cashflow(CashflowPredictionInput(...))

# 2. Filter high-confidence predictions
high_confidence = [p for p in result.per_deal_predictions if p.confidence >= 0.7]

# 3. Generate report
forecast_table = cashflow_service.generate_forecast_table(high_confidence, ForecastOptions(...))
assumptions = cashflow_service.explain_assumptions(high_confidence)
```

---

**Last Updated:** December 2024
