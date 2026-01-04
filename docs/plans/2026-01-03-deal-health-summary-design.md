# Deal Health Summary Feature Design

## Overview

Add a "Get Summary" button to the Aramco screen that provides LLM-powered deal health analysis. The feature analyzes stage duration, communication gaps, and notes to determine deal health status and recommend actions.

## Data Flow

```
User clicks "Get Summary" button
         │
         ▼
aramco_screen.py: _get_selected_deal_id()
         │
         ▼
GET /deals/{id}/health-summary
  - Backend fetches deal details, notes, stage history
  - Calls WriterService.analyze_deal_health()
  - Returns DealHealthResult
         │
         ▼
DealHealthModal displays result
```

## Files to Modify/Create

| File | Action | Description |
|------|--------|-------------|
| `models/writer_models.py` | Modify | Add `DealHealthContext`, `DealHealthResult` |
| `services/prompt_registry.py` | Modify | Register `deal.health_analysis.v1` prompt |
| `services/writer_service.py` | Modify | Add `analyze_deal_health()` method + fallback |
| `api/deals.py` | Modify | Add `GET /deals/{id}/health-summary` endpoint |
| `screens/deal_health_modal.py` | Create | New modal screen |
| `screens/aramco_screen.py` | Modify | Add button handler + import |

## Pydantic Models

### DealHealthContext (Input)

```python
class DealHealthContext(BaseModel):
    """Context for deal health analysis."""
    deal_id: int
    deal_title: str
    stage: str
    stage_code: str  # OR, APR, AP, etc.
    days_in_stage: int
    owner_name: str
    value_sar: Optional[float] = None
    notes: list[dict]  # [{date, author, content}, ...]
    stage_history: list[dict]  # [{stage_name, entered_at, duration_hours}, ...]
    last_activity_date: Optional[datetime] = None
    days_since_last_note: Optional[int] = None
```

### DealHealthResult (Output)

```python
class DealHealthResult(BaseModel):
    """Result from deal health analysis."""
    deal_id: int
    health_status: str  # "healthy", "at_risk", "critical"
    status_flag: Optional[str] = None  # AT_RISK, DELAYED, PAYMENT_ISSUE, etc.
    summary: str  # 2-3 sentence executive summary
    days_in_stage: int
    stage_threshold_warning: int
    stage_threshold_critical: int
    communication_gap_days: Optional[int] = None
    communication_assessment: str  # "Healthy", "Acceptable", "Warning", "Communication Gap"
    blockers: list[str] = []
    attribution: str  # "customer_delay", "employee_gap", "site_blocked", etc.
    recommended_action: str
    confidence: float  # 0.0-1.0
```

## Prompt: deal.health_analysis.v1

**System Prompt:**

```
You are a deal health analyst for a construction/fit-out company. Your job is to analyze deal progress and provide actionable insights for the CEO.

## Stage Reference

| Code | Stage Name              | Description                                                                 |
|------|-------------------------|-----------------------------------------------------------------------------|
| OR   | Order Received          | PO received; need to find end user, confirm materials and colors            |
| APR  | Approved                | End user found, materials approved; preparing purchase order                |
| AP   | Awaiting Payment        | Waiting for advance payment to purchase materials                           |
| ASR  | Awaiting Site Readiness | Materials ready but site not prepared                                       |
| ER   | Everything Ready        | All materials procured, site ready, waiting to start                        |
| UP   | Under Progress          | Active production/installation ongoing                                      |
| MDD  | Awaiting MDD            | Work complete, waiting for Material Delivery Document                       |
| GCC  | Awaiting GCC            | MDD received, waiting for Goods Condition Certificate                       |
| GR   | Awaiting GR             | GCC received, waiting for Goods Receipt                                     |
| INV  | Invoice Issued          | e-GR received, invoice submitted                                            |

## Project Size Categories

| Category | SQM Range   | OR→APR Target |
|----------|-------------|---------------|
| Small    | < 100 SQM   | 7 days        |
| Medium   | 100-400 SQM | 13 days       |
| Large    | > 400 SQM   | 21 days       |

## Stuck Thresholds (Days in Stage)

| Stage | Warning | Critical | Flag at Critical    |
|-------|---------|----------|---------------------|
| OR    | 21      | 45       | AT_RISK             |
| APR   | 5       | 10       | DELAYED             |
| AP    | 7       | 14       | PAYMENT_ISSUE       |
| ASR   | 14      | 30       | SITE_BLOCKED        |
| ER    | 10      | 21       | QUEUE_BACKLOG       |
| UP    | 14      | 28       | PRODUCTION_ISSUE    |
| MDD   | 7       | 14       | DOC_DELAYED         |
| GCC   | 7       | 14       | DOC_DELAYED         |
| GR    | 14      | 30       | GR_BLOCKED          |

## Communication Gap Thresholds

| Gap Duration | Assessment        |
|--------------|-------------------|
| < 5 days     | Healthy           |
| 5-10 days    | Acceptable        |
| 10-14 days   | Warning           |
| > 14 days    | Communication Gap |

## Analysis Rules

1. **Stage Duration**: Compare days_in_stage against thresholds for that stage
2. **Communication Gaps**: Analyze time between notes; gaps > 14 days are concerning
3. **Attribution**:
   - If notes mention "waiting for customer/client/end user" → customer delay
   - If no notes for extended period → employee communication gap
   - If notes show active follow-up with no response → customer fault
   - If note shows awaiting for site → site readiness delay
   - If note shows purchasing submitted, or waiting for payment → procurement fault
   - If notes show phases or partial delivery → partial deliveries project
4. **Blockers**: Extract explicit blockers from notes (payment, site, materials, approvals)
5. **Health Status**:
   - "critical" = any critical threshold exceeded OR multiple warning flags
   - "at_risk" = any warning threshold exceeded OR communication gap > 14 days
   - "healthy" = within thresholds and regular communication

## Response Schema

Respond ONLY with valid JSON:
{
  "health_status": "healthy|at_risk|critical",
  "status_flag": "AT_RISK|DELAYED|PAYMENT_ISSUE|SITE_BLOCKED|QUEUE_BACKLOG|PRODUCTION_ISSUE|DOC_DELAYED|GR_BLOCKED|null",
  "summary": "2-3 sentence executive summary",
  "stage_threshold_warning": int,
  "stage_threshold_critical": int,
  "communication_gap_days": int or null,
  "communication_assessment": "Healthy|Acceptable|Warning|Communication Gap",
  "blockers": ["blocker1", "blocker2"],
  "attribution": "customer_delay|employee_gap|site_blocked|procurement_fault|partial_delivery|none",
  "recommended_action": "specific next step",
  "confidence": 0.0-1.0
}
```

**User Prompt Template:**

```
Analyze this deal:

Deal: {{ deal_title }} (ID: {{ deal_id }})
Stage: {{ stage }} ({{ stage_code }}) - {{ days_in_stage }} days
Owner: {{ owner_name }}
Value: {{ value_sar }} SAR
Days since last note: {{ days_since_last_note }}

Stage History:
{% for s in stage_history %}
- {{ s.stage_name }}: {{ s.duration_hours|round(1) }} hours
{% endfor %}

Recent Notes ({{ notes|length }}):
{% for note in notes[:10] %}
[{{ note.date }}] {{ note.author }}: {{ note.content[:200] }}
{% endfor %}

Provide the health analysis JSON.
```

**Configuration:**
- `max_tokens_estimate`: 600
- `model_tier`: "balanced"
- `temperature`: 0.5

## API Endpoint

```
GET /deals/{deal_id}/health-summary
Response: DealHealthResult
```

The endpoint:
1. Fetches deal details via `get_deal_detail()`
2. Fetches notes via `get_deal_notes(limit=15)`
3. Fetches stage history via `get_stage_history()`
4. Builds `DealHealthContext`
5. Calls `WriterService.analyze_deal_health()`
6. Returns `DealHealthResult`

## Modal UI

`DealHealthModal` displays:
- Header with deal ID and title
- Health status badge (color-coded: green/yellow/red)
- Summary paragraph
- Communication assessment
- Blockers list (if any)
- Attribution
- Recommended action (highlighted box)
- Confidence score
- Close button

## Button Handler

In `aramco_screen.py`:
```python
elif event.button.id == "get-summary-button":
    deal_id = self._get_selected_deal_id()
    if deal_id is None:
        self.notify("Select a deal row first.", severity="warning")
        return

    self.notify("Analyzing deal health...", severity="info")
    modal = DealHealthModal(api_url=self.api_url, deal_id=deal_id)
    self.app.push_screen(modal)
```

## Stage Code Mapping

Helper function to map stage names to codes:

```python
STAGE_NAME_TO_CODE = {
    "Order Received": "OR",
    "Approved": "APR",
    "Awaiting Payment": "AP",
    "Awaiting Site Readiness": "ASR",
    "Everything Ready": "ER",
    "Under Progress": "UP",
    "Underprogress": "UP",
    "Awaiting MDD": "MDD",
    "Awaiting GCC": "GCC",
    "Awaiting GR": "GR",
    "Invoice Issued": "INV",
}
```
