# Architecture.md

## Command Center Architecture Specification (for LLMs)

> ⚠️ **IMPORTANT FOR LLMS**
> - Treat this document as the **source of truth for architecture**.
> - Maintain strict separation between layers.
> - The **database is the single source of truth** for the UI and services.
> - Pipedrive API is accessed **only** through the sync layer.

The system is a keyboard-driven command center built on FastAPI + Textual + SQLite.

---

## 0. Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Frontend (TUI) | Textual | 0.48.2 |
| Backend API | FastAPI | 0.109.0 |
| Server | Uvicorn | 0.27.0 |
| Database | SQLite + SQLModel | 0.0.14 |
| Validation | Pydantic | 2.5.3 |
| HTTP Client | httpx (async) | 0.26.0 |
| LLM Provider | OpenRouter (Claude 3.5 Sonnet) | - |
| Email | SMTP (Gmail-compatible) | - |
| Microsoft Integration | Microsoft Graph API + MSAL | - |
| Background Tasks | FastAPI lifespan + asyncio | - |

---

## 1. Architecture Layers

The application follows a **5-layer architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Layer 1: UI (Textual)                                                  │
│  - Screens, widgets, keyboard handling, modal dialogs                   │
│  - Calls FastAPI endpoints only                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Layer 2: API (FastAPI)                                                 │
│  - HTTP endpoints                                                       │
│  - Request validation, response serialization                           │
│  - Calls service layer                                                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Layer 3: Service Layer                                                 │
│  - Business logic (deal_health, cashflow, kpis, emails, summaries)      │
│  - WriterService: LLM-powered content generation                        │
│  - CashflowPredictionService: Deterministic forecasting (no LLM)        │
│  - Calls query layer for data                                           │
│  - Uses PromptRegistry for LLM prompts (WriterService only)             │
│  - Uses DeterministicRules for cashflow predictions                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Layer 4: Database Layer                                                │
│  - SQLite database (pipedrive_cache.db)                                 │
│  - SQLModel for ORM                                                     │
│  - db_queries.py for read operations                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Layer 5: Sync Layer (Background)                                       │
│  - pipedrive_sync.py + sync_scheduler.py                                │
│  - Fetches from Pipedrive API                                           │
│  - Upserts into SQLite                                                  │
│  - Runs on schedule (deals: 60 min, notes: 30 min) or on-demand         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Infrastructure Layer (LLM, External APIs)                              │
│  - LLMClient: Transport, retries, structured output                     │
│  - Pipedrive API, Microsoft Graph API, OpenRouter LLM                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Layer Rules

| Layer | Can Call | Cannot Call |
|-------|----------|-------------|
| UI (Textual) | FastAPI endpoints | Services, Database, Pipedrive |
| API (FastAPI) | Services | Database directly, Pipedrive |
| Services | db_queries.py, WriterService, CashflowPredictionService, PromptRegistry | Pipedrive directly |
| WriterService | LLMClient, PromptRegistry, db_queries | Pipedrive, direct LLM business logic |
| CashflowPredictionService | DeterministicRules, db_queries | LLMClient (disabled), Pipedrive |
| db_queries.py | SQLite (read-only) | Pipedrive, external APIs |
| LLMClient | OpenRouter API (infrastructure only) | Business logic, prompts |
| pipedrive_sync.py | Pipedrive API, SQLite (write) | Services, API |

---

## 2. Data Flow

### 2.1 Read Path (User Requests Data)

This is the **fast path** used for all UI operations:

```
Textual Screen
    │
    ▼ HTTP GET /aramco/overdue
FastAPI Endpoint
    │
    ▼ get_overdue_deals()
Service Layer (deal_health_service)
    │
    ▼ get_overdue_deals_for_pipeline()
db_queries.py
    │
    ▼ SELECT * FROM deal WHERE ...
SQLite Database
    │
    ▼ List[Deal]
    │
    ▼ Transform to List[OverdueDeal]
Service Layer
    │
    ▼ JSON Response
FastAPI Endpoint
    │
    ▼ Render DataTable
Textual Screen
```

**Key characteristics:**
- No network calls to Pipedrive
- Sub-100ms response times
- Synchronous database queries (SQLite is fast)

### 2.2 Sync Path (Background Data Refresh)

This runs **independently** of user requests:

```
Scheduler (deals: every 60 min, notes: every 30 min) OR Manual Trigger
    │
    ▼ sync_deals_for_pipeline() / sync_notes_for_open_deals()
pipedrive_sync.py
    │
    ▼ GET /pipelines, /stages, /deals, /notes, /activities, /files
Pipedrive API
    │
    ▼ JSON responses
    │
    ▼ Transform & upsert
SQLite Database
    │
    ▼ Update sync_metadata table
Done (UI will see fresh data on next query)
```

**Key characteristics:**
- Runs in background (doesn't block UI)
- Full sync on first run (bootstrap), incremental after
- Tracks last sync time per entity type
- Concurrent note/activity fetching for performance

### 2.3 On-Demand Sync (User Triggers Refresh)

When user presses `R` (Reload) in TUI:

```
Textual Screen (user presses R)
    │
    ▼ HTTP POST /sync/trigger
FastAPI Endpoint
    │
    ▼ BackgroundTask: sync_deals_for_pipeline()
pipedrive_sync.py
    │
    ▼ (sync happens in background)
    │
FastAPI returns immediately: {"status": "sync_started"}
    │
Textual Screen
    │
    ▼ (polls or waits, then reloads)
    │
    ▼ HTTP GET /aramco/overdue
    │
    ▼ (fresh data from database)
```

---

## 3. Project Structure

```
cmd_center/
├── app.py                          # Textual application entry point
├── screens/                        # Textual screens
│   ├── dashboard_screen.py
│   ├── aramco_screen.py
│   ├── commercial_screen.py
│   ├── owner_kpi_screen.py
│   ├── deal_detail_screen.py
│   ├── email_drafts_screen.py
│   ├── notes_modal_screen.py       # Modal for viewing/adding notes
│   ├── overdue_summary_modal.py    # CEO Radar: overdue summary
│   ├── stuck_summary_modal.py      # CEO Radar: stuck summary
│   └── order_received_summary_modal.py  # CEO Radar: order received summary
├── design/                         # CSS and design assets
│
├── backend/
│   ├── main.py                     # FastAPI application entry point
│   ├── db.py                       # SQLModel ORM & database schema
│   ├── constants.py                # Pipeline/stage ID mappings, sync configs
│   │
│   ├── api/                        # FastAPI routers
│   │   ├── __init__.py             # Router registration
│   │   ├── health.py
│   │   ├── dashboard.py
│   │   ├── aramco.py               # Includes summary endpoints
│   │   ├── commercial.py
│   │   ├── owners.py
│   │   ├── deals.py
│   │   ├── emails.py
│   │   └── sync.py                 # Sync trigger endpoints
│   │
│   ├── services/                   # Business logic
│   │   ├── deal_health_service.py
│   │   ├── llm_analysis_service.py  # ⚠️ DEPRECATED - use WriterService
│   │   ├── cashflow_service.py
│   │   ├── cashflow_prediction_service.py  # Deterministic forecasting (LLM disabled)
│   │   ├── owner_kpi_service.py
│   │   ├── email_service.py
│   │   ├── dashboard_service.py
│   │   ├── db_queries.py           # Read-only query functions
│   │   ├── aramco_summary_service.py  # CEO Radar summaries
│   │   ├── pipedrive_sync.py       # Sync functions
│   │   ├── sync_scheduler.py       # Background sync scheduler
│   │   ├── writer_service.py       # ✨ NEW - LLM content generation
│   │   ├── prompt_registry.py      # ✨ NEW - Centralized prompt management
│   │   └── deterministic_rules.py  # Primary cashflow prediction engine
│   │
│   ├── models/                     # Pydantic models (API contracts)
│   │   ├── deal_models.py          # Includes summary response models
│   │   ├── cashflow_models.py      # Extended with prediction models
│   │   ├── writer_models.py        # ✨ NEW - WriterService input/output models
│   │   ├── kpi_models.py
│   │   ├── dashboard_models.py
│   │   └── email_models.py
│   │
│   └── integrations/               # External API clients
│       ├── config.py               # Pydantic settings
│       ├── pipedrive_client.py     # Used by sync layer only
│       ├── llm_client.py           # ✨ REFACTORED - Infrastructure only
│       ├── email_client.py         # SMTP client
│       └── microsoft_client.py     # Microsoft Graph API client
│
├── pipedrive_cache.db              # SQLite database file
├── .env                            # Environment variables
└── requirements.txt
```

---

## 4. Database Schema

### 4.1 Core Tables

| Table | Purpose | Sync Frequency |
|-------|---------|----------------|
| `pipeline` | Pipeline metadata | On startup / on-demand |
| `stage` | Stage metadata | On startup / on-demand |
| `deal` | Deal records (open) | Every 60 minutes |
| `note` | Deal notes | Every 30 minutes |
| `activity` | Deal activities/tasks | Every 30 minutes |
| `file` | Deal file attachments | Every 30 minutes |
| `comment` | Comments on deals/activities | On-demand |
| `sync_metadata` | Tracks sync state | Updated after each sync |

### 4.2 Entity Relationships

```
pipeline (1) ──────< (many) stage
    │
    └──────< (many) deal ──────< (many) note
                        │
                        ├──────< (many) activity
                        │
                        ├──────< (many) file
                        │
                        └──────< (many) comment
```

### 4.3 SQLModel Table Definitions

```python
class Pipeline(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    order_nr: int = 0
    is_deleted: bool = False
    is_deal_probability_enabled: bool = False
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

class Stage(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    order_nr: int = 0
    pipeline_id: int
    deal_probability: Optional[int] = None
    days_to_rotten: Optional[int] = None
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

class Deal(SQLModel, table=True):
    id: int = Field(primary_key=True)
    title: str
    pipeline_id: int
    stage_id: int
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    org_id: Optional[int] = None
    org_name: Optional[str] = None
    value: Optional[float] = None
    currency: str = "SAR"
    status: str = "open"
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    stage_change_time: Optional[datetime] = None
    last_activity_time: Optional[datetime] = None
    activities_count: int = 0
    done_activities_count: int = 0
    notes_count: int = 0
    files_count: int = 0
    email_messages_count: int = 0
    raw_json: Optional[str] = None  # Full Pipedrive response

class Note(SQLModel, table=True):
    id: int = Field(primary_key=True)
    deal_id: int
    content: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    active_flag: bool = True

class Activity(SQLModel, table=True):
    id: int = Field(primary_key=True)
    deal_id: int
    subject: Optional[str] = None
    type: Optional[str] = None
    note: Optional[str] = None
    due_date: Optional[datetime] = None
    done: bool = False
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

class File(SQLModel, table=True):
    id: int = Field(primary_key=True)
    deal_id: int
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    file_url: Optional[str] = None
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

class Comment(SQLModel, table=True):
    id: int = Field(primary_key=True)
    object_id: int
    object_type: str  # "deal", "activity", etc.
    content: Optional[str] = None
    updater_id: Optional[int] = None
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

class SyncMetadata(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    entity_type: str          # "pipelines", "stages", "deals_5", etc.
    last_sync_time: datetime
    duration_ms: int = 0
    records_synced: int = 0
    records_updated: int = 0
    status: str = "success"   # "success", "failed", "in_progress"
    error_message: Optional[str] = None
```

---

## 5. Domain Models

### 5.1 Database Models (SQLModel - in `db.py`)

Used for database operations:
- `Pipeline`
- `Stage`
- `Deal`
- `Note`
- `Activity`
- `File`
- `Comment`
- `SyncMetadata`

### 5.2 API Models (Pydantic - in `models/`)

Used for API responses:
- `DealBase`
- `OverdueDeal`
- `StuckDeal`
- `OrderReceivedAnalysis`
- `ComplianceStatus`
- `DealSummary`
- `CashflowBucket`
- `OwnerKPI`, `OwnerKPIWithComment`
- `DashboardItem`
- `EmailDraft`, `DealIssue`
- `DealNote`, `DealActivity`, `DealFile`, `DealComment`

### 5.3 CEO Radar Summary Models

For executive dashboard summaries:
- `OverdueSummaryResponse` - Overdue snapshot, PM performance, intervention list
- `StuckSummaryResponse` - Stuck snapshot, PM control metrics, worst deals, bottlenecks
- `OrderReceivedSummaryResponse` - Order snapshot, PM acceleration, blockers, fast wins

### 5.4 Cashflow Prediction Models

For deterministic cashflow forecasting (LLM disabled):

**Input Models:**
- `DealForPrediction` - Deal data prepared for prediction
- `PredictionOptions` - Prediction parameters (horizon, confidence threshold)
- `CashflowPredictionInput` - Request parameters
- `ForecastOptions` - Forecast formatting options

**Output Models:**
- `DealPrediction` - Single deal prediction with dates, confidence, reasoning
- `PredictionMetadata` - Prediction run statistics
- `CashflowPredictionResult` - Complete result with per-deal and aggregated forecasts
- `ForecastPeriod` - Forecast data for one period (week/month)
- `ForecastTotals` - Total forecast values
- `ForecastTable` - Formatted table view
- `AssumptionsReport` - Explanation of assumptions used

### 5.5 WriterService Models (NEW)

For LLM-powered content generation:

**Input Context Models:**
- `EmailDraftContext` - Email drafting parameters
- `ReminderDraftContext` - Multi-channel reminder context (WhatsApp/Email/SMS)
- `DealSummaryContext` - Deal analysis parameters
- `ComplianceContext` - Compliance check parameters
- `OrderReceivedContext` - Order analysis parameters
- `NoteSummaryContext` - Note summarization parameters

**Output Result Models (all include confidence scores 0.0-1.0):**
- `DraftEmailResult` - Email with subject, body, HTML, suggestions
- `DraftReminderResult` - Reminder with short/long versions, tags
- `DealSummaryResult` - Summary with next action, blockers, recommendations
- `ComplianceResult` - Compliance status with missing items
- `OrderReceivedResult` - End user analysis
- `NoteSummaryResult` - Summary with action items and owners

### 5.4 Model Transformation

Services transform database models to API models:

```python
# In deal_health_service.py
def get_overdue_deals(pipeline_name: str, min_days: int = 7) -> list[OverdueDeal]:
    # Query returns db.Deal objects
    deals = db_queries.get_overdue_deals_for_pipeline(
        pipeline_name=pipeline_name,
        min_days=min_days
    )

    # Transform to API model
    return [
        OverdueDeal(
            id=d.id,
            title=d.title,
            pipeline=PIPELINE_ID_TO_NAME[d.pipeline_id],
            stage=get_stage_name(d.stage_id),
            owner=d.owner_name or "Unknown",
            value_sar=d.value,
            overdue_days=calculate_overdue_days(d.update_time),
            # ... other fields
        )
        for d in deals
    ]
```

---

## 6. API Endpoints

### 6.1 Data Endpoints (Read from Database)

| Endpoint | Method | Service | Description |
|----------|--------|---------|-------------|
| `/health` | GET | - | Liveness check |
| `/dashboard/today` | GET | dashboard_service | Today's focus items |
| `/aramco/overdue` | GET | deal_health_service | Overdue Aramco deals (min_days=7) |
| `/aramco/stuck` | GET | deal_health_service | Stuck Aramco deals (min_days=30) |
| `/aramco/order_received` | GET | deal_health_service | Order received analysis |
| `/aramco/compliance` | GET | deal_health_service | Compliance status |
| `/aramco/cashflow_projection` | GET | cashflow_service | Cashflow forecast |
| `/commercial/inactive` | GET | deal_health_service | Inactive commercial deals (min_days=60) |
| `/commercial/recent_summary` | GET | deal_health_service | Recent deal summaries |
| `/owners/kpis` | GET | owner_kpi_service | Per-owner KPIs |
| `/deals/{id}/detail` | GET | deal_health_service | Single deal deep-dive |
| `/deals/{id}/notes` | GET | deal_health_service | Deal notes (limit param) |

### 6.2 CEO Radar Summary Endpoints

| Endpoint | Method | Service | Description |
|----------|--------|---------|-------------|
| `/aramco/overdue_summary` | GET | aramco_summary_service | Executive summary for overdue deals |
| `/aramco/stuck_summary` | GET | aramco_summary_service | Executive summary for stuck deals |
| `/aramco/order_received_summary` | GET | aramco_summary_service | Executive summary for order received |

### 6.3 Action Endpoints

| Endpoint | Method | Service | Description |
|----------|--------|---------|-------------|
| `/emails/followups/generate` | POST | email_service | Generate email drafts |
| `/emails/followups/send` | POST | email_service | Send emails |

### 6.4 Sync Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sync/status` | GET | Get last sync times and status |
| `/sync/stages` | POST | Manually trigger stages sync |
| `/sync/trigger` | POST | Trigger immediate sync |
| `/sync/trigger/{entity}` | POST | Trigger sync for specific entity |

---

## 7. Services

### 7.1 Service → Query Mapping

| Service | Uses Queries/Functions |
|---------|------------------------|
| `deal_health_service` | `get_overdue_deals_for_pipeline`, `get_stuck_deals_for_pipeline`, `get_deal_by_id`, `get_notes_for_deal` |
| `aramco_summary_service` | Direct SQLModel sessions, calculates PM metrics, snapshots |
| `cashflow_service` | `get_deals_near_invoicing`, `get_deals_by_stage` |
| `cashflow_prediction_service` | `db_queries`, `DeterministicRules` (LLM disabled) |
| `owner_kpi_service` | `get_deals_by_owner`, PipedriveClient for activities |
| `dashboard_service` | Aggregates from other services |
| `email_service` | Uses other services + WriterService (planned) |
| `writer_service` | `LLMClient`, `PromptRegistry`, `db_queries` (read-only) |
| `llm_analysis_service` | **⚠️ DEPRECATED** - `get_notes_for_deal` + llm_client (use WriterService instead) |
| `db_queries` | SQLite read operations |

### 7.2 Service Characteristics

All services:
- Are **synchronous** for database queries (SQLite is fast)
- May be **async** for LLM calls
- Return **Pydantic models** (API models, not DB models)
- Do **not** call Pipedrive directly
- May call `llm_client` for analysis

### 7.3 Key Services

#### deal_health_service.py
- `get_overdue_deals(pipeline_name, min_days)` → `List[OverdueDeal]`
- `get_stuck_deals(pipeline_name, min_days)` → `List[StuckDeal]`
- `get_order_received_deals(pipeline_name)` → `List[OrderReceivedAnalysis]`
- `get_deal_detail(deal_id)` → `DealBase`
- `get_deal_notes(deal_id, limit)` → `List[DealNote]`

#### aramco_summary_service.py (CEO Radar)
- `generate_overdue_summary(pipeline_name)` → `OverdueSummaryResponse`
- `generate_stuck_summary(pipeline_name)` → `StuckSummaryResponse`
- `generate_order_received_summary(pipeline_name)` → `OrderReceivedSummaryResponse`

Calculates:
- Snapshot metrics (total, critical counts, value at risk)
- PM performance tables (best/worst performers)
- Intervention lists (deals needing attention)
- Stage bottleneck analysis

#### writer_service.py (NEW)
LLM-powered content generation service:
- `draft_email(context: EmailDraftContext)` → `DraftEmailResult`
- `draft_reminder(context: ReminderDraftContext)` → `DraftReminderResult`
- `summarize_deal(context: DealSummaryContext)` → `DealSummaryResult`
- `analyze_compliance(context: ComplianceContext)` → `ComplianceResult`
- `analyze_order_received(context: OrderReceivedContext)` → `OrderReceivedResult`
- `summarize_notes(context: NoteSummaryContext)` → `NoteSummaryResult`
- `batch_summarize_deals(contexts, max_concurrent=5)` → `List[DealSummaryResult]`

Features:
- Uses PromptRegistry for centralized prompt management
- Structured output with Pydantic validation
- Confidence scoring (0.0-1.0)
- Graceful fallbacks on LLM failures
- Concurrent batch processing with rate limiting

#### cashflow_prediction_service.py
Deterministic cashflow forecasting (LLM disabled):
- `predict_cashflow(input: CashflowPredictionInput)` → `CashflowPredictionResult`
- `predict_deal_dates(deals, options, today)` → `List[DealPrediction]`
- `generate_forecast_table(predictions, options)` → `ForecastTable`
- `explain_assumptions(predictions)` → `AssumptionsReport`

Features:
- Pure deterministic rules (LLM code commented out)
- Stage-based cycle time estimates (DeterministicRules)
- Staleness adjustments for stuck deals
- Post-processing validation and sanity checks
- Confidence-based filtering
- Explainability reporting with assumptions

#### prompt_registry.py (NEW)
Centralized prompt template management:
- `get_prompt(prompt_id)` → `PromptTemplate`
- `render_prompt(prompt_id, variables)` → `(system_prompt, user_prompt)`
- `list_prompts()` → `list[dict]`
- `get_prompt_config(prompt_id)` → `dict`

**Registered Prompts:**
1. `deal.summarize.v1` - Deal summarization
2. `deal.compliance_check.v1` - Compliance analysis
3. `deal.order_received_analysis.v1` - End user identification
4. `email.followup.v1` - Email drafting
5. `reminder.whatsapp.v1` - WhatsApp reminders
6. `reminder.email.v1` - Email reminders
7. `notes.summarize.v1` - Note summarization
8. `cashflow.predict_dates.v1` - Invoice/payment prediction

Features:
- Jinja2 template rendering
- Variable validation
- Version support for A/B testing
- Metadata tracking (model tier, temperature, tokens)

#### deterministic_rules.py
Rule-based prediction logic for cashflow (primary prediction engine):
- `predict_deal(deal, today)` → `DealPrediction`
- `precheck_deal(deal, today)` → `Optional[DealPrediction]`
- `apply_overrides(prediction, deal, today)` → `DealPrediction`
- `validate_prediction(prediction, today)` → `list[str]` (warnings)
- `get_stage_estimate(stage)` → `Optional[int]` (days)

**Stage Cycle Times (Realistic estimates, days to invoice):**
| Stage | Days |
|-------|------|
| Order Received (< 100 SQM) | 36 |
| Order Received (100-400 SQM) | 42 |
| Order Received (> 400 SQM) | 50 |
| Approved | 29 |
| Awaiting Payment | 27 |
| Awaiting Site Readiness | 22 |
| Everything Ready | 17 |
| Under Progress | 12 |
| Awaiting MDD | 12 |
| Awaiting GCC | 10 |
| Awaiting GR | 7 |

**Staleness Adjustments:**
- 30+ days in stage: +7 days, -5% confidence
- 60+ days in stage: +14 days, -10% confidence

**Payment Terms:**
- Aramco: 7 days after invoice
- Commercial: 45 days after invoice

**Confidence Levels:**
- High (0.85): Late stages (Awaiting GR/GCC/MDD)
- Medium (0.70): Normal stages
- Low (0.50): Unknown stages or stuck deals

---

## 8. Sync Layer

### 8.1 Sync Functions (pipedrive_sync.py)

| Function | Syncs | Strategy |
|----------|-------|----------|
| `sync_pipelines()` | Pipeline table | Full replace |
| `sync_stages()` | Stage table | Full replace |
| `sync_deals_for_pipeline(id, status, incremental)` | Deal table | Upsert (incremental capable) |
| `sync_notes_for_open_deals(limit, ttl, concurrency)` | Note table | Concurrent fetch |
| `sync_activities_for_deal(id)` | Activity table | Per-deal fetch |
| `sync_files_for_deal(id)` | File table | Per-deal fetch |

### 8.2 Sync Strategy

| Entity | Initial Sync | Periodic Sync | Interval |
|--------|--------------|---------------|----------|
| Pipelines | All | On startup | Bootstrap |
| Stages | All | On startup | Bootstrap |
| Deals (open) | All | Incremental | 60 minutes |
| Notes | All open deals | TTL-based | 30 minutes |
| Activities | All open deals | With notes | 30 minutes |
| Files | All open deals | With notes | 30 minutes |
| Deals (won/lost) | Skip | Skip | N/A |

### 8.3 Scheduler (sync_scheduler.py)

The sync scheduler runs as a background task using FastAPI lifespan:

```python
@asynccontextmanager
async def lifespan_manager(app: FastAPI):
    # Bootstrap sync on startup
    await bootstrap_sync()  # pipelines, stages

    # Start background sync tasks
    task_deals = asyncio.create_task(run_deals_sync())
    task_notes = asyncio.create_task(run_notes_sync())

    yield

    # Cleanup on shutdown
    await stop_scheduler()

async def run_deals_sync():
    while True:
        await sync_all_deals()
        await asyncio.sleep(60 * 60)  # 60 minutes

async def run_notes_sync():
    while True:
        await sync_notes_for_open_deals()
        await asyncio.sleep(30 * 60)  # 30 minutes
```

### 8.4 Incremental Sync Logic

```python
async def sync_deals_incremental(pipeline_id: int):
    """Sync only deals updated since last sync."""

    # 1. Get last sync time
    last_sync = get_last_sync_time(f"deals_{pipeline_id}")

    # 2. Fetch all open deals (Pipedrive doesn't support modified_since)
    all_deals = await fetch_all_deals(pipeline_id, status="open")

    # 3. Filter to only updated deals
    if last_sync:
        deals_to_upsert = [
            d for d in all_deals
            if parse_datetime(d["update_time"]) > last_sync
        ]
    else:
        deals_to_upsert = all_deals

    # 4. Upsert only changed deals
    upsert_deals(deals_to_upsert)

    # 5. Update sync metadata
    set_last_sync_time(f"deals_{pipeline_id}", datetime.utcnow())
```

---

## 9. Integration Clients

| Client | Used By | Purpose |
|--------|---------|---------|
| `pipedrive_client` | `pipedrive_sync.py` only | Fetch data from Pipedrive API |
| `llm_client` | `writer_service`, `cashflow_prediction_service` | **Infrastructure only** - HTTP transport, retries, structured output |
| `email_client` | `email_service` | Send SMTP emails |
| `microsoft_client` | Services (future) | SharePoint & OneDrive integration |

### 9.1 pipedrive_client.py

**Key Classes:**
- `PipedriveDealDTO` - Deal data transfer object (normalizes nested API response)
- `PipedriveNoteDTO` - Note DTO

**Key Methods:**
- `get_pipeline_id(name)` → `Optional[int]`
- `get_pipelines()` → `List[Pipeline]`
- `get_stages(pipeline_id)` → `List[Stage]`
- `get_deals(pipeline_id, status, limit)` → `List[PipedriveDealDTO]`
- `get_deal_notes(deal_id)` → `List[PipedriveNoteDTO]`
- `get_activities(deal_id)` → `List[Activity]`
- `get_files(deal_id)` → `List[File]`
- `search_deals(term)` → `List[PipedriveDealDTO]`

### 9.2 llm_client.py (REFACTORED)

**⚠️ BREAKING CHANGE:** LLMClient now provides infrastructure only. Business logic moved to WriterService.

**New Classes:**
- `LLMError` - Base exception for LLM errors
- `LLMRateLimitError` - Rate limit exceeded
- `LLMValidationError` - Schema validation failed
- `TokenUsage` - Token usage statistics with cost estimates
- `LLMResponse` - Complete response with metadata
- `LLMClient` - Main client class

**Key Methods:**
- `generate_completion(prompt, system_prompt, max_tokens, temperature, model)` → `LLMResponse`
- `generate_structured_completion(schema: Type[T], prompt, system_prompt, ...)` → `T` (Pydantic instance)
- `stream_completion(prompt, system_prompt, ...)` → `AsyncIterator[str]`
- `get_metrics()` → `dict` (request_count, total_tokens, total_cost_usd)
- `reset_metrics()` → `None`

**Features:**
- ✅ Async HTTP client with connection pooling (httpx)
- ✅ Exponential backoff retry logic (max 3 retries, configurable)
- ✅ Rate limit detection (429 status code)
- ✅ Structured output with Pydantic schema validation
- ✅ Token usage tracking and cost estimation
- ✅ Comprehensive logging (request/response/errors)
- ✅ Streaming support for real-time responses
- ✅ Timeout handling (60s default, configurable)
- ✅ Markdown code block parsing for JSON extraction

**Removed Methods (moved to WriterService):**
- ❌ `analyze_deal_compliance()` → Use `WriterService.analyze_compliance()`
- ❌ `analyze_order_received()` → Use `WriterService.analyze_order_received()`
- ❌ `summarize_deal()` → Use `WriterService.summarize_deal()`

**Model Used:** `anthropic/claude-3.5-sonnet` (configurable)

**Cost Estimation:** Approximate pricing per million tokens:
- Input: $3.00
- Output: $15.00

### 9.3 email_client.py

**Key Methods:**
- `send_email(to_email, subject, body, body_html)` → `bool`
- `send_bulk_emails(emails)` → `dict[str, bool]`

### 9.4 microsoft_client.py

**Purpose:** Microsoft Graph API integration for SharePoint & OneDrive

**Key Methods:**
- `_get_access_token()` - MSAL client credentials flow
- `list_files(drive_id)` - List OneDrive files
- `get_file_info(drive_id, file_id)` - Get file metadata
- `download_file_url(drive_id, file_id)` - Get download URL
- `upload_file(drive_id, file_name, file_content)` - Upload file
- `list_sharepoint_list_items(site_id, list_id)` - Query SharePoint list
- `create_sharepoint_list_item(site_id, list_id, fields)` - Create list item

**Auth Method:** Azure AD client credentials (app-only)

---

## 10. TUI Integration

### 10.1 Main Application (app.py)

**Class:** `CommandCenterApp(App)`

**Global Bindings:**
| Key | Action |
|-----|--------|
| `q` | Quit application |
| `d` | Dashboard screen |
| `a` | Aramco pipeline screen |
| `c` | Commercial pipeline screen |
| `o` | Owner KPIs screen |
| `e` | Email drafts screen |

### 10.2 Screens

| Screen | File | Purpose |
|--------|------|---------|
| Dashboard | `dashboard_screen.py` | Today's focus with priority items |
| Aramco Pipeline | `aramco_screen.py` | 5 modes: Overdue, Stuck, Order, Compliance, Cashflow |
| Commercial | `commercial_screen.py` | Inactive deals + LLM summaries |
| Owner KPIs | `owner_kpi_screen.py` | Salesperson performance metrics |
| Deal Detail | `deal_detail_screen.py` | Single deal deep-dive |
| Email Drafts | `email_drafts_screen.py` | Generate and send follow-up emails |

### 10.3 Modal Screens (CEO Radar)

| Modal | File | Purpose |
|-------|------|---------|
| Overdue Summary | `overdue_summary_modal.py` | Snapshot, PM performance, intervention list |
| Stuck Summary | `stuck_summary_modal.py` | Snapshot, PM control, worst deals, bottlenecks |
| Order Received Summary | `order_received_summary_modal.py` | Snapshot, PM acceleration, blockers, fast wins |
| Notes Modal | `notes_modal_screen.py` | View/add notes to deals |

### 10.4 Screen Data Loading

Each screen loads data from FastAPI:

```python
class AramcoPipelineScreen(Screen):

    async def on_mount(self):
        await self.load_data()

    async def load_data(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE}/aramco/overdue")
            deals = response.json()

        table = self.query_one("#aramco-table")
        table.clear()
        for deal in deals:
            table.add_row(...)
```

### 10.5 Client-Side Features

The Aramco screen supports:
- **Group By:** None / Owner / Stage
- **Sort By:** Overdue Days / Value / Last Updated
- **View Summary:** Open executive dashboard modal
- **Deal Actions:**
  - Check last 5 notes
  - Generate follow-up email
  - Get Summary
  - Add Note
  - Check Compliance

---

## 11. Key Features Implemented

✅ **Dashboard** - Today's focus with priority items
✅ **Aramco Pipeline** - 5 analysis modes (Overdue, Stuck, Order, Compliance, Cashflow)
✅ **Commercial Pipeline** - Inactive deals + LLM summaries
✅ **Owner KPIs** - Salesperson performance tracking
✅ **Deal Details** - Full deal view with notes/activities
✅ **Email Management** - LLM-generated follow-up emails
✅ **CEO Radar** - Executive summaries with PM metrics
✅ **Pipedrive Sync** - Background incremental sync (60 min deals, 30 min notes)
✅ **LLM Integration** - Deal analysis via OpenRouter
✅ **Microsoft Integration** - SharePoint & OneDrive support
✅ **Multi-Pipeline Support** - Aramco + Commercial focused
✅ **Local Caching** - SQLite for fast reads, async sync for updates
✅ **Notes Modal** - View and add notes to deals

---

## 12. Pipeline & Stage Mappings

### 12.1 Pipeline IDs

```python
PIPELINE_NAME_TO_ID = {
    "Pipeline": 1,                  # Commercial
    "Prospecting": 2,
    "Aramco Inquiries": 3,
    "Aramco PO": 4,
    "Aramco Projects": 5,           # Main Aramco pipeline
    "Bidding Projects": 6,
    "Design Development": 10,
    "Problematic & Stuck Orders": 11,
}

SYNC_PIPELINES = [5, 1, 4]  # Aramco Projects, Commercial, Aramco PO
```

### 12.2 Key Stage IDs

```python
# Selected key stages
STAGE_IDS = {
    "Order Received": 27,
    "Underprogress": 30,
    "Awaiting GR": 43,
    "Awaiting MDD": 82,
    "Production /Supplying": 5,
    # ... see constants.py for full list
}
```

---

## 13. Configuration

All configuration via environment variables (`.env`):

```bash
# Pipedrive
PIPEDRIVE_API_TOKEN=xxx
PIPEDRIVE_API_URL=https://api.pipedrive.com/v1
PIPEDRIVE_API_URL_V2=https://api.pipedrive.com/v2

# LLM (OpenRouter)
OPENROUTER_API_KEY=xxx
OPENROUTER_API_URL=https://openrouter.ai/api/v1
LLM_MODEL=anthropic/claude-3.5-sonnet

# Microsoft Graph
AZURE_CLIENT_ID=xxx
AZURE_CLIENT_SECRET=xxx
AZURE_TENANT_ID=xxx
MICROSOFT_SCOPE=https://graph.microsoft.com/.default

# OneDrive / SharePoint
ONEDRIVE_FILE_ID=xxx
ONEDRIVE_DRIVE_ID=xxx
ONEDRIVE_USER_ID=xxx

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=xxx
SMTP_PASSWORD=xxx
SMTP_FROM_EMAIL=xxx

# FastAPI
API_HOST=127.0.0.1
API_PORT=8000

# Pipeline Names
ARAMCO_PIPELINE_NAME=Aramco Projects
COMMERCIAL_PIPELINE_NAME=pipeline
```

---

## 14. Testing Strategy

| Layer | Test Type | Tools |
|-------|-----------|-------|
| db_queries.py | Unit tests | pytest + test SQLite DB |
| Services | Unit tests | pytest + mocked queries |
| API endpoints | Integration tests | pytest + TestClient |
| Sync layer | Integration tests | pytest + mocked Pipedrive |
| TUI | Manual testing | Run app locally |

---

## 15. Critical File Locations

**Core Files:**
- App Entry: `cmd_center/app.py`
- API Entry: `cmd_center/backend/main.py`
- Database: `cmd_center/backend/db.py`
- Constants: `cmd_center/backend/constants.py`

**Services:**
- All services: `cmd_center/backend/services/`
- Main sync: `cmd_center/backend/services/pipedrive_sync.py`
- Query helper: `cmd_center/backend/services/db_queries.py`
- Summary service: `cmd_center/backend/services/aramco_summary_service.py`
- **LLM Services (NEW):**
  - Writer service: `cmd_center/backend/services/writer_service.py`
  - Cashflow prediction: `cmd_center/backend/services/cashflow_prediction_service.py`
  - Prompt registry: `cmd_center/backend/services/prompt_registry.py`
  - Deterministic rules: `cmd_center/backend/services/deterministic_rules.py`

**API:**
- All endpoints: `cmd_center/backend/api/`
- Routing: `cmd_center/backend/api/__init__.py`

**Integrations:**
- All clients: `cmd_center/backend/integrations/`
- LLM client (refactored): `cmd_center/backend/integrations/llm_client.py`
- LLM observability (NEW): `cmd_center/backend/integrations/llm_observability.py`
- LLM circuit breaker (NEW): `cmd_center/backend/integrations/llm_circuit_breaker.py`
- Config: `cmd_center/backend/integrations/config.py`

**Models:**
- All models: `cmd_center/backend/models/`
- Writer models (NEW): `cmd_center/backend/models/writer_models.py`
- Cashflow models (extended): `cmd_center/backend/models/cashflow_models.py`

**Screens:**
- All screens: `cmd_center/screens/`

**Database Cache:**
- SQLite: `pipedrive_cache.db`

**Documentation:**
- Architecture: `docs/Architecture.md` (this file)
- LLM Implementation: `docs/LLM_Architecture_Implementation.md`
- LLM Quick Reference: `docs/LLM_Quick_Reference.md`

---

## 16. LLM Architecture (December 2024 Update)

### 16.1 Architecture Principles

The LLM infrastructure follows a **strict separation of concerns**:

```
┌─────────────────────────────────────────────────────────────┐
│  Business Logic Layer (Services)                            │
│  - WriterService: Content generation (uses LLM)             │
│  - CashflowPredictionService: Deterministic only (no LLM)   │
│  - Uses prompts from PromptRegistry (WriterService)         │
│  - Applies business rules via DeterministicRules            │
└─────────────────────────────────────────────────────────────┘
                            │
           ┌────────────────┴────────────────┐
           ▼                                 ▼
┌─────────────────────────────┐  ┌─────────────────────────────┐
│  Prompt Management Layer    │  │  Deterministic Rules Layer  │
│  - PromptRegistry           │  │  - DeterministicRules       │
│  - Jinja2 templates         │  │  - Stage duration table     │
│  (WriterService only)       │  │  (CashflowPrediction only)  │
└─────────────────────────────┘  └─────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│  Infrastructure Layer (LLMClient) - WriterService only      │
│  - HTTP transport with connection pooling                  │
│  - Retry logic with exponential backoff                    │
│  - Structured output enforcement (JSON → Pydantic)         │
│  - Metrics tracking (tokens, cost, latency)                │
│  - Error handling & logging                                │
└─────────────────────────────────────────────────────────────┘
```

### 16.2 Key Design Decisions

1. **LLMClient is infrastructure-only**: No business logic, prompts, or use-case-specific methods
2. **PromptRegistry centralizes all prompts**: Version-controlled, Jinja2 templates
3. **Services own business logic**: WriterService and CashflowPredictionService contain all use cases
4. **Deterministic-only for cashflow**: LLM predictions disabled, pure rule-based approach for reliability and speed
5. **Confidence scoring**: All outputs include confidence (0.0-1.0) for downstream decision-making
6. **Graceful degradation**: Fallbacks on LLM failures with clear warnings

> **Note**: CashflowPredictionService was originally designed for hybrid LLM + rules, but LLM code has been
> commented out in favor of pure deterministic predictions. This provides faster response times, no API costs,
> and consistent, predictable results.

### 16.3 Migration from Old Architecture

**Before (deprecated):**
```python
from cmd_center.backend.integrations.llm_client import get_llm_client

llm = get_llm_client()
result = await llm.summarize_deal(deal_title, stage, notes)  # ❌ No longer exists
```

**After (current):**
```python
from cmd_center.backend.services.writer_service import get_writer_service
from cmd_center.backend.models import DealSummaryContext

writer = get_writer_service()
result = await writer.summarize_deal(DealSummaryContext(
    deal_id=deal_id,
    deal_title=deal_title,
    stage=stage,
    owner_name=owner_name,
    days_in_stage=days_in_stage,
    notes=notes
))
# ✅ Returns DealSummaryResult with summary, next_action, blockers, confidence
```

### 16.4 Usage Patterns

**Pattern 1: Content Generation**
```python
from cmd_center.backend.services.writer_service import get_writer_service
from cmd_center.backend.models import EmailDraftContext

writer = get_writer_service()
result = await writer.draft_email(EmailDraftContext(...))
if result.confidence >= 0.7:
    # High confidence - auto-approve
    send_email(result.subject, result.body)
else:
    # Low confidence - flag for review
    queue_for_review(result)
```

**Pattern 2: Cashflow Prediction (Deterministic)**
```python
from cmd_center.backend.services.cashflow_prediction_service import get_cashflow_prediction_service
from cmd_center.backend.models import CashflowPredictionInput

service = get_cashflow_prediction_service()
result = await service.predict_cashflow(CashflowPredictionInput(
    pipeline_name="Aramco Projects",
    horizon_days=90
))

# Predictions use deterministic rules based on stage durations
for pred in result.per_deal_predictions:
    print(f"Deal: {pred.deal_title}")
    print(f"Stage: {pred.stage} → Invoice in {pred.predicted_invoice_date}")
    print(f"Confidence: {pred.confidence} ({', '.join(pred.assumptions)})")
```

### 16.5 Observability

**Metrics Available:**
```python
from cmd_center.backend.integrations.llm_client import get_llm_client

client = get_llm_client()
metrics = client.get_metrics()
# Returns: {"request_count": 42, "total_tokens": 125000, "total_cost_usd": 1.875}
```

**Logging:**
- INFO: Successful completions, batch operations
- WARNING: Retries, fallbacks, low confidence
- ERROR: LLM failures, validation errors

### 16.6 Phase 4 - Integration & Migration (COMPLETED)

**Completed:**
- ✅ Updated `email_service.py` to use WriterService
  - Confidence-based auto-send logic with thresholds
  - Intelligent tone selection based on urgency
  - Fallback email generation on LLM failures
  - New filtering methods: `get_emails_for_review()`, `get_emails_ready_to_send()`
- ✅ Enhanced `aramco_summary_service.py` with WriterService integration
  - Infrastructure for LLM-powered deal analysis (blocking detection, suggested next steps)
  - Note: Requires async refactoring for full integration
- ✅ Deprecated `llm_analysis_service.py`
  - Comprehensive deprecation warnings on import and method calls
  - Complete migration guide in docstrings

### 16.7 Phase 5 - Advanced Features (COMPLETED)

**1. Structured Logging & Observability** (`llm_observability.py`)
- ✅ `LLMObservabilityLogger` for structured JSON logging
- ✅ `LLMRequestContext` dataclass for request tracking
- ✅ Context manager `observe_llm_request()` for easy instrumentation
- ✅ Automatic alerts for high costs (>$0.50) and latency (>5000ms)
- ✅ Event tracking: request_start, request_complete, request_error, validation_error, retry, cost_alert, latency_alert
- ✅ Integrated into WriterService.draft_email() as example

**2. Circuit Breaker & Resilience** (`llm_circuit_breaker.py`)
- ✅ Full circuit breaker pattern with 3 states: CLOSED, OPEN, HALF_OPEN
- ✅ Configurable thresholds (default: 5 failures → open, 60s timeout)
- ✅ Token bucket rate limiter (default: 60 RPM)
- ✅ `LLMResilience` wrapper combining both patterns
- ✅ Comprehensive statistics tracking
- ✅ Optional fallback functions when circuit is open

**3. Prompt Versioning & A/B Testing** (`prompt_registry.py`)
- ✅ `PromptExperiment` class for A/B testing with traffic splitting
- ✅ `PromptVariantStats` tracking usage, confidence, success rate, cost, latency
- ✅ Intelligent winner selection based on composite score
- ✅ Experiment lifecycle: create, test, analyze, promote winner
- ✅ Methods: `create_experiment()`, `render_prompt_with_experiment()`, `record_experiment_result()`, `get_experiment_stats()`, `promote_winner()`, `list_experiments()`

**Key Features:**
- Statistical significance requirement (min 10 uses per variant)
- Composite scoring: `(confidence × success_rate) / (cost × latency)`
- Automatic or manual traffic splitting
- Experiment deactivation after winner promotion

### 16.8 Observability Reference

**Structured Logging Example:**
```python
from cmd_center.backend.integrations.llm_observability import observe_llm_request

with observe_llm_request("writer_service", "draft_email", "claude-3.5-sonnet") as ctx:
    result = await llm.generate_completion(...)
    ctx.prompt_tokens = result.usage.prompt_tokens
    ctx.completion_tokens = result.usage.completion_tokens
    ctx.cost_usd = result.usage.estimated_cost_usd
    ctx.response_time_ms = result.response_time_ms
# Automatically logs completion with metrics and alerts on anomalies
```

**Circuit Breaker Example:**
```python
from cmd_center.backend.integrations.llm_circuit_breaker import get_llm_resilience

resilience = get_llm_resilience()
result = await resilience.execute(
    lambda: llm.generate_completion(...),
    fallback=lambda: "LLM unavailable, using cached response"
)
# Automatically applies rate limiting and circuit breaker protection
```

**A/B Testing Example:**
```python
from cmd_center.backend.services.prompt_registry import get_prompt_registry

registry = get_prompt_registry()

# Create experiment
experiment = registry.create_experiment(
    experiment_id="email_tone_test",
    base_prompt_id="email.followup.v1",
    variants={
        "formal": PromptTemplate(...),
        "friendly": PromptTemplate(...),
    },
    traffic_split={"formal": 0.5, "friendly": 0.5}
)

# Use in production
system_prompt, user_prompt, variant_id = registry.render_prompt_with_experiment(
    "email_tone_test",
    variables={...}
)

# Record result
registry.record_experiment_result(
    "email_tone_test",
    variant_id,
    success=True,
    confidence=0.85,
    cost_usd=0.007,
    latency_ms=1200
)

# Get stats and promote winner
stats = registry.get_experiment_stats("email_tone_test")
winner = registry.promote_winner("email_tone_test", replace_base=True)
```

### 16.9 Cost Optimization

**Token Usage Estimates:**
| Use Case | Prompt Tokens | Completion Tokens | Cost (USD) |
|----------|---------------|-------------------|------------|
| Email Draft | ~500 | ~300 | ~$0.007 |
| Deal Summary | ~400 | ~250 | ~$0.006 |
| Compliance Check | ~300 | ~150 | ~$0.004 |
| Cashflow Prediction | N/A | N/A | **$0.00** (deterministic) |

**Optimization Strategies:**
1. Use deterministic rules when possible (DeterministicRules)
2. Batch operations to reduce overhead
3. Confidence-based filtering to reduce unnecessary calls
4. Prompt optimization for minimal token usage
5. Rate limiting to stay within API quotas (LLMResilience)
6. Circuit breaker to prevent cascading failures and wasted API calls

### 16.10 Future Enhancements

**Planned Additions:**
- Response caching (LRU with TTL) to reduce duplicate LLM calls
- Multi-model support (Haiku/Sonnet/Opus tier selection)
- Prometheus metrics export for production monitoring
- Async refactoring of aramco_summary_service for full LLM integration
- Batch retry strategies for failed LLM calls
- Dynamic prompt optimization based on A/B test results

### 16.11 Reference Documentation

For detailed implementation information, see:
- `docs/LLM_Architecture_Implementation.md` - Complete implementation guide
- `docs/LLM_Quick_Reference.md` - API quick reference

---

End of Architecture.md
