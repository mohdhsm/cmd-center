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
| Email (SMTP) | SMTP (Gmail-compatible) | - |
| Email (MSGraph) | Microsoft Graph API | App-only auth |
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
│   ├── order_received_summary_modal.py  # CEO Radar: order received summary
│   └── ceo_dashboard_screen.py     # Main CEO Dashboard (default on launch)
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
│   │   ├── sync.py                 # Sync trigger endpoints
│   │   ├── employees.py            # Employee CRUD (CEO Dashboard)
│   │   ├── reminders.py            # Unified reminder system
│   │   ├── tasks.py                # Task management
│   │   ├── notes.py                # Internal notes
│   │   ├── documents.py            # Legal document tracking
│   │   ├── bonuses.py              # Bonus tracking
│   │   ├── employee_logs.py        # Employee log entries
│   │   ├── skills.py               # Skills and ratings
│   │   ├── loops.py                # Loop engine endpoints
│   │   └── ceo_dashboard.py        # CEO Dashboard aggregate metrics
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
│   │   ├── writer_service.py       # ✨ LLM content generation
│   │   ├── prompt_registry.py      # ✨ Centralized prompt management
│   │   ├── deterministic_rules.py  # Primary cashflow prediction engine
│   │   │
│   │   │   # CEO Dashboard Services
│   │   ├── employee_service.py     # Employee CRUD
│   │   ├── intervention_service.py # Audit logging
│   │   ├── reminder_service.py     # Unified reminder system
│   │   ├── task_service.py         # Task management with reminders
│   │   ├── note_service.py         # Internal notes with reviews
│   │   ├── document_service.py     # Legal document tracking
│   │   ├── bonus_service.py        # Bonus and payment tracking
│   │   ├── employee_log_service.py # Employee log entries
│   │   ├── skill_service.py        # Skills and ratings
│   │   │
│   │   │   # Loop Engine
│   │   ├── loop_engine.py          # BaseLoop, LoopRegistry, LoopService
│   │   ├── loop_setup.py           # Loop registration on startup
│   │   └── loops/                  # Individual loop implementations
│   │       ├── __init__.py
│   │       ├── docs_expiry_loop.py     # Document expiry monitoring
│   │       ├── bonus_due_loop.py       # Bonus due date monitoring
│   │       ├── task_overdue_loop.py    # Overdue task monitoring
│   │       └── reminder_processing_loop.py  # Reminder processing
│   │   └── ceo_dashboard_service.py  # CEO Dashboard aggregate service
│   │
│   ├── models/                     # Pydantic models (API contracts)
│   │   ├── deal_models.py          # Includes summary response models
│   │   ├── cashflow_models.py      # Extended with prediction models
│   │   ├── writer_models.py        # WriterService input/output models
│   │   ├── kpi_models.py
│   │   ├── dashboard_models.py
│   │   ├── email_models.py
│   │   │   # CEO Dashboard Models
│   │   ├── employee_models.py      # Employee CRUD models
│   │   ├── reminder_models.py      # Reminder system models
│   │   ├── task_models.py          # Task management models
│   │   ├── note_models.py          # Internal note models
│   │   ├── document_models.py      # Legal document models
│   │   ├── bonus_models.py         # Bonus and payment models
│   │   ├── employee_log_models.py  # Employee log models
│   │   ├── skill_models.py         # Skill and rating models
│   │   ├── loop_models.py          # Loop engine models
│   │   └── ceo_dashboard_models.py # CEO Dashboard aggregate models
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

### 4.1 Core Tables (Pipedrive Sync)

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

### 4.2 Management Tables (CEO Dashboard)

| Table | Purpose | Key Features |
|-------|---------|--------------|
| `employee` | Employee directory | Hierarchy, departments, Pipedrive linking |
| `intervention` | Audit log | All system actions tracked |
| `reminder` | Unified reminders | Target-agnostic, multi-channel |
| `task` | Task tracking | Assignees, priorities, due dates |
| `internal_note` | Internal notes | Reviews, pinning, tags |

### 4.3 Tracker Tables (Compliance & HR)

| Table | Purpose | Key Features |
|-------|---------|--------------|
| `legal_document` | Document tracking | Expiry dates, status lifecycle |
| `legal_document_file` | Document attachments | File metadata |
| `employee_bonus` | Bonus tracking | Multi-currency, due dates |
| `employee_bonus_payment` | Bonus payments | Partial payments, audit trail |
| `employee_log_entry` | Employee logs | Achievements, issues, feedback |
| `skill` | Skill definitions | Categories, descriptions |
| `employee_skill_rating` | Skill ratings | Rating history, 1-5 scale |

### 4.4 Loop Engine Tables

| Table | Purpose | Key Features |
|-------|---------|--------------|
| `loop_run` | Loop execution records | Status, duration, findings count |
| `loop_finding` | Loop findings/alerts | Severity, deduplication via signature |

### 4.8 Email Cache Tables (Microsoft Graph)

| Table | Purpose | Sync Frequency |
|-------|---------|----------------|
| `cached_email` | Cached email messages | Every 15 minutes |
| `cached_email_attachment` | Attachment metadata | With emails |
| `cached_mail_folder` | Folder structure | With emails |

### 4.5 Entity Relationships

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

### 4.6 SQLModel Table Definitions (Pipedrive)

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

### 4.7 SQLModel Table Definitions (CEO Dashboard)

```python
class Employee(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    role_title: str
    department: Optional[str] = None
    reports_to_employee_id: Optional[int] = Field(default=None, foreign_key="employee.id")
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    pipedrive_owner_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class Intervention(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime
    actor: str
    object_type: str
    object_id: int
    action_type: str
    status: str = "done"
    summary: str
    details_json: Optional[str] = None

class Reminder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    target_type: str  # "task", "note", "document", "bonus", etc.
    target_id: int
    remind_at: datetime
    channel: str = "in_app"  # "in_app", "email"
    message: Optional[str] = None
    status: str = "pending"  # "pending", "sent", "dismissed", "failed", "cancelled"
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    assignee_employee_id: Optional[int] = Field(default=None, foreign_key="employee.id")
    created_by: Optional[str] = None
    status: str = "open"  # open, in_progress, done, cancelled
    priority: str = "medium"  # low, medium, high
    is_critical: bool = False
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_archived: bool = False

class InternalNote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str
    created_by: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    review_at: Optional[datetime] = None
    pinned: bool = False
    tags: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_archived: bool = False

class LegalDocument(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    document_type: str  # license, contract, insurance, certification, permit, other
    description: Optional[str] = None
    expiry_date: Optional[datetime] = None
    status: str = "active"  # draft, active, renewal_in_progress, expired, archived
    responsible_employee_id: Optional[int] = Field(default=None, foreign_key="employee.id")
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class EmployeeBonus(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.id")
    title: str
    description: Optional[str] = None
    amount: float
    currency: str = "SAR"
    due_date: Optional[datetime] = None
    status: str = "pending"  # pending, partial, paid, cancelled
    created_at: datetime
    updated_at: Optional[datetime] = None

class Skill(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category: str
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime

class EmployeeSkillRating(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.id")
    skill_id: int = Field(foreign_key="skill.id")
    rating: int  # 1-5
    rated_by: Optional[str] = None
    notes: Optional[str] = None
    rated_at: datetime

class LoopRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    loop_name: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed
    findings_count: int = 0
    error_message: Optional[str] = None

class LoopFinding(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    loop_run_id: int = Field(foreign_key="loop_run.id")
    severity: str  # info, warning, critical
    target_type: str
    target_id: int
    message: str
    recommended_action: Optional[str] = None
    signature: Optional[str] = None  # SHA256 for deduplication
    created_at: datetime
```

---

## 5. Domain Models

### 5.1 Database Models (SQLModel - in `db.py`)

**Pipedrive Sync Models:**
- `Pipeline`, `Stage`, `Deal`, `Note`, `Activity`, `File`, `Comment`, `SyncMetadata`

**CEO Dashboard Models:**
- `Employee`, `Intervention`, `Reminder`, `Task`, `InternalNote`

**Tracker Models:**
- `LegalDocument`, `LegalDocumentFile`, `EmployeeBonus`, `EmployeeBonusPayment`
- `EmployeeLogEntry`, `Skill`, `EmployeeSkillRating`

**Loop Engine Models:**
- `LoopRun`, `LoopFinding`

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

### 5.6 MSGraph Email Models

For email service interface (distinct from DTOs in microsoft_client.py):

**Input Models:**
- `EmailRecipientInput` - Email recipient for composing (email, name)
- `EmailAttachmentInput` - Attachment with file path, optional name/content_type
- `EmailComposeRequest` - Full email composition request
- `EmailSearchFilters` - Search filters (subject, sender, dates, folder)

**Response Models:**
- `EmailAddress` - Address with optional name
- `EmailAttachment` - Attachment metadata (id, name, content_type, size, is_inline)
- `EmailMessage` - Full message with body, recipients, dates, attachments
- `MailFolder` - Folder with name, counts
- `EmailListResponse` - Paginated email list
- `FolderListResponse` - Folder list with total

### 5.7 CEO Dashboard Aggregate Models

For the executive dashboard single-endpoint response:
- `CashHealth` - Runway, collections, velocity with status indicators
- `UrgentDeal` - Deal requiring attention with reason and days stuck
- `StageVelocity` - Stage name with average days and deal count
- `PipelineVelocity` - Stages, current cycle, target, trend
- `StrategicPriority` - Name, current, target, percentage, status
- `DepartmentScorecard` - Sales metrics (pipeline, won, overdue, status)
- `CEODashboardMetrics` - Complete dashboard response

### 5.8 Model Transformation

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

### 6.5 CEO Dashboard Endpoints (Management)

#### Employees
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/employees` | GET | List employees with filters |
| `/employees/{id}` | GET | Get employee details |
| `/employees` | POST | Create employee |
| `/employees/{id}` | PUT | Update employee |
| `/employees/{id}` | DELETE | Soft delete (deactivate) |

#### Reminders
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reminders` | POST | Create reminder |
| `/reminders` | GET | List reminders with filters |
| `/reminders/pending` | GET | List pending reminders |
| `/reminders/{id}` | GET | Get reminder details |
| `/reminders/{id}/dismiss` | POST | Dismiss reminder |
| `/reminders/{id}` | DELETE | Cancel reminder |

#### Tasks
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tasks` | POST | Create task (with optional reminder) |
| `/tasks` | GET | List tasks with filters |
| `/tasks/{id}` | GET | Get task details |
| `/tasks/{id}` | PUT | Update task |
| `/tasks/{id}/complete` | POST | Mark complete (cancels reminders) |
| `/tasks/{id}` | DELETE | Cancel task |
| `/tasks/{id}/reminders` | GET | List task reminders |

#### Notes
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/notes` | POST | Create note (with optional review) |
| `/notes` | GET | List notes with filters |
| `/notes/{id}` | GET | Get note details |
| `/notes/{id}` | PUT | Update note |
| `/notes/{id}` | DELETE | Archive note |
| `/notes/{id}/reminders` | GET | List note reminders |

### 6.6 CEO Dashboard Endpoints (Tracker)

#### Documents
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/documents` | POST | Create document |
| `/documents` | GET | List documents with filters |
| `/documents/expiring` | GET | Documents expiring within N days |
| `/documents/{id}` | GET | Get document details |
| `/documents/{id}` | PUT | Update document |
| `/documents/{id}` | DELETE | Archive document |
| `/documents/{id}/files` | POST | Attach file |
| `/documents/{id}/files` | GET | List attachments |

#### Bonuses
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/bonuses` | POST | Create bonus |
| `/bonuses` | GET | List bonuses with filters |
| `/bonuses/unpaid` | GET | List unpaid bonuses |
| `/bonuses/{id}` | GET | Get bonus details |
| `/bonuses/{id}` | PUT | Update bonus |
| `/bonuses/{id}/payments` | POST | Record payment |
| `/bonuses/{id}/payments` | GET | List payments |
| `/bonuses/{id}` | DELETE | Cancel bonus |

#### Employee Logs
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/employee-logs` | POST | Create log entry |
| `/employee-logs` | GET | List logs with filters |
| `/employee-logs/{id}` | GET | Get log details |
| `/employee-logs/{id}` | PUT | Update log |
| `/employee-logs/{id}` | DELETE | Delete log |

#### Skills
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/skills` | POST | Create skill definition |
| `/skills` | GET | List skills by category |
| `/skills/{id}` | GET | Get skill details |
| `/skills/{id}` | PUT | Update skill |
| `/skills/{id}` | DELETE | Deactivate skill |
| `/skills/{id}/ratings` | POST | Rate employee |
| `/skills/{id}/ratings` | GET | Get ratings for skill |
| `/employees/{id}/skills` | GET | Employee skill card |

### 6.7 Loop Engine Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/loops/status` | GET | Get all loops with run statistics |
| `/loops/{name}/run` | POST | Manually trigger specific loop |
| `/loops/run-all` | POST | Trigger all enabled loops |
| `/loops/runs` | GET | List loop runs with filters |
| `/loops/runs/{id}` | GET | Get run details with findings |
| `/loops/findings` | GET | List all findings with filters |

### 6.8 CEO Dashboard Metrics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ceo-dashboard/metrics` | GET | Aggregate dashboard with cash health, urgent deals, pipeline velocity, priorities, scorecard |

### 6.9 Interventions (Audit Log)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/interventions` | GET | List audit log entries with filters |

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
| **CEO Dashboard Services** | |
| `employee_service` | Employee CRUD, hierarchy management |
| `intervention_service` | Audit logging via `log_action()` |
| `reminder_service` | Unified reminder CRUD, target linking |
| `task_service` | Task CRUD, uses `reminder_service` |
| `note_service` | Note CRUD, uses `reminder_service` |
| `document_service` | Document CRUD, file attachments |
| `bonus_service` | Bonus CRUD, payment tracking |
| `employee_log_service` | Employee log entries |
| `skill_service` | Skill definitions, employee ratings |
| **Loop Engine** | |
| `loop_engine` | BaseLoop, LoopRegistry, LoopService |
| `docs_expiry_loop` | Uses `document_service`, `reminder_service`, `task_service` |
| `bonus_due_loop` | Uses `bonus_service`, `reminder_service` |
| `task_overdue_loop` | Uses `task_service`, `reminder_service` |
| `reminder_processing_loop` | Uses `reminder_service` |
| **CEO Dashboard** | |
| `ceo_dashboard_service` | Uses `cashflow_prediction_service`, `deal_health_service`, db_queries |
| **Microsoft Graph Email** | |
| `msgraph_email_service` | Uses `microsoft_client` for email operations (no DB storage) |
| **Email Sync** | |
| `email_sync` | Uses `msgraph_email_service`, writes to `CachedEmail`, `CachedMailFolder` |

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

### 7.4 CEO Dashboard Aggregate Service

#### ceo_dashboard_service.py
Executive dashboard aggregation with configurable targets:
- `get_dashboard_metrics()` → `CEODashboardMetrics` (all sections in one call)
- `_get_cash_health()` → `CashHealth` (runway, collections, velocity)
- `_get_urgent_deals()` → `List[UrgentDeal]` (top 5 attention-required deals)
- `_get_pipeline_velocity()` → `PipelineVelocity` (stage averages, cycle time, trend)
- `_get_strategic_priorities()` → `List[StrategicPriority]` (cost reduction, sales, commercial share)
- `_get_department_scorecard()` → `DepartmentScorecard` (sales MVP metrics)

**Configuration (`CEODashboardConfig`):**
- `weekly_collection_target`: 200,000 SAR
- `monthly_burn_rate`: 50,000 SAR
- `cash_balance`: 200,000 SAR (placeholder)
- `commercial_collected_week`: 0 SAR (placeholder)
- `cost_reduction_target`: 20%
- `weekly_sales_target`: 500,000 SAR
- `commercial_share_target`: 40%

**Status Thresholds:**
- Runway: green >3mo, yellow 1-3mo, red <1mo
- Velocity: green >80%, yellow 50-80%, red <50%
- Priorities: green >=90%, yellow >=70%, red <70%

### 7.5 Microsoft Graph Email Service

#### msgraph_email_service.py
High-level email operations via Microsoft Graph API (no database storage):

**Reading:**
- `get_emails(mailbox, folder, unread_only, limit)` → `List[EmailMessage]`
- `get_email_by_id(message_id, mailbox)` → `Optional[EmailMessage]`
- `search_emails(mailbox, subject, sender, from_date, to_date, folder)` → `List[EmailMessage]`

**Sending:**
- `send_email(from_mailbox, to, subject, body, cc, bcc, attachments)` → `bool`

**Actions:**
- `reply(message_id, mailbox, comment, reply_all)` → `bool`
- `forward(message_id, to, mailbox, comment)` → `bool`
- `move_to_folder(message_id, destination_folder, mailbox)` → `bool`
- `mark_as_read(message_id, mailbox)` → `bool`
- `delete_email(message_id, mailbox)` → `bool`

**Attachments:**
- `get_attachments(message_id, mailbox)` → `List[EmailAttachment]`
- `download_attachment(message_id, attachment_id, mailbox, save_dir)` → `Path`
- `download_all_attachments(message_id, mailbox, save_dir)` → `List[Path]`

**Folders:**
- `get_folders(mailbox)` → `List[MailFolder]`
- `create_folder(folder_name, parent_folder_id, mailbox)` → `MailFolder`
- `get_folder_by_name(folder_name, mailbox)` → `Optional[MailFolder]`

**Features:**
- ✅ App-only authentication (client credentials flow)
- ✅ Default mailbox: `mohammed@gyptech.com.sa`
- ✅ Support for multiple mailboxes (delegated access)
- ✅ Well-known folder name resolution (inbox, sentitems, drafts, etc.)
- ✅ OData filter building for search queries
- ✅ Automatic DTO conversion between client and service layers
- ✅ Async/await throughout
- ✅ No database storage (real-time Graph API calls)

**Usage:**
```python
from cmd_center.backend.services import get_msgraph_email_service
from cmd_center.backend.models import EmailAttachmentInput
from pathlib import Path

service = get_msgraph_email_service()

# Get unread emails
emails = await service.get_emails(unread_only=True)

# Search emails
results = await service.search_emails(subject="Invoice", sender="vendor@example.com")

# Send email with attachment
await service.send_email(
    from_mailbox="mohammed@gyptech.com.sa",
    to=["recipient@example.com"],
    subject="Report",
    body="<p>Please find attached.</p>",
    attachments=[EmailAttachmentInput(file_path=Path("report.pdf"))]
)

# Reply to email
await service.reply("msg-123", comment="Thanks for the update!")

# Move to folder
await service.move_to_folder("msg-123", destination_folder="Archive")
```

### 7.6 CEO Dashboard CRUD Services

#### employee_service.py
- `create_employee(data)` → `EmployeeResponse`
- `get_employee(id)` → `Optional[EmployeeResponse]`
- `get_employees(filters)` → `EmployeeListResponse`
- `update_employee(id, data)` → `Optional[EmployeeResponse]`
- `delete_employee(id)` → `bool` (soft delete)

#### intervention_service.py
- `log_action(actor, object_type, object_id, action_type, summary, details)` → `None`
- `get_interventions(filters)` → `InterventionListResponse`

#### reminder_service.py
- `create_reminder(data, actor)` → `ReminderResponse`
- `get_pending_reminders(before, limit)` → `list[ReminderResponse]`
- `get_reminders_for_target(target_type, target_id)` → `list[ReminderResponse]`
- `dismiss_reminder(id, actor)` → `Optional[ReminderResponse]`
- `cancel_reminder(id, actor)` → `bool`
- `cancel_reminders_for_target(target_type, target_id)` → `int`
- `mark_reminder_sent(id)` → `Optional[ReminderResponse]`
- `mark_reminder_failed(id, error)` → `Optional[ReminderResponse]`

#### task_service.py
- `create_task(data, actor)` → `TaskResponse` (auto-creates reminder if due_at set)
- `get_task(id)` → `Optional[TaskResponse]`
- `get_tasks(filters)` → `TaskListResponse`
- `complete_task(id, actor)` → `Optional[TaskResponse]` (cancels reminders)
- `cancel_task(id, actor)` → `bool`
- `get_overdue_tasks()` → `list[TaskResponse]`

#### note_service.py
- `create_note(data, actor)` → `NoteResponse` (auto-creates reminder if review_at set)
- `get_note(id)` → `Optional[NoteResponse]`
- `get_notes(filters)` → `NoteListResponse` (pinned first)
- `archive_note(id, actor)` → `bool` (cancels reminders)

#### document_service.py
- `create_document(data, actor)` → `DocumentResponse`
- `get_expiring_documents(days)` → `list[DocumentResponse]`
- `attach_file(document_id, data)` → `DocumentFileResponse`

#### bonus_service.py
- `create_bonus(data, actor)` → `BonusResponse`
- `record_payment(bonus_id, data, actor)` → `BonusPaymentResponse` (auto-updates status)
- `get_unpaid_bonuses()` → `list[BonusResponse]`

#### skill_service.py
- `create_skill(data, actor)` → `SkillResponse`
- `rate_employee(skill_id, data, actor)` → `SkillRatingResponse`
- `get_employee_skill_card(employee_id)` → `list[SkillWithRating]`
- `get_latest_ratings(skill_id)` → `list[SkillRatingResponse]`

### 7.7 Loop Engine

#### loop_engine.py

**BaseLoop (Abstract Class):**
```python
class BaseLoop(ABC):
    name: str           # Unique loop identifier
    description: str    # Human-readable description
    interval_minutes: int  # How often to run
    enabled: bool = True

    @abstractmethod
    def execute(self, session: Session) -> None:
        """Execute the loop logic. Override in subclass."""
        pass

    def run(self) -> LoopRunResponse:
        """Run the loop with automatic tracking."""
        # Creates LoopRun record, calls execute(), handles errors

    def add_finding(self, session, severity, target_type, target_id, message, recommended_action) -> Optional[LoopFinding]:
        """Add finding with 24-hour deduplication."""
```

**LoopRegistry:**
- `register(loop)` - Register a loop instance
- `get(name)` → `Optional[BaseLoop]`
- `all()` → `list[BaseLoop]`
- `run_all()` → `list[LoopRunResponse]`
- `run_by_name(name)` → `Optional[LoopRunResponse]`

**LoopService:**
- `get_loop_runs(filters)` → `LoopRunListResponse`
- `get_loop_run(id)` → `Optional[LoopRunWithFindings]`
- `get_findings(filters)` → `LoopFindingListResponse`
- `get_status()` → `LoopStatusResponse`

#### Loop Implementations

| Loop | Interval | Thresholds | Actions |
|------|----------|------------|---------|
| `docs_expiry_loop` | 6 hours | 30 days warning, 7 days critical | Creates reminders + renewal tasks |
| `bonus_due_loop` | 12 hours | 30 days warning, 7 days critical | Creates payment reminders |
| `task_overdue_loop` | 1 hour | 24 hours warning, 0 hours critical | Creates escalation reminders |
| `reminder_processing_loop` | 5 minutes | N/A | Sends pending reminders via email/in-app |

**Finding Deduplication:**
- Signature = SHA256(loop_name + severity + target_type + target_id + message)
- Duplicate findings within 24 hours are skipped
- Prevents alert fatigue from repeated runs

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
| Emails (inbox) | Last 90 days | Incremental (7 days) | 15 minutes |
| Folders | All | Full | With emails |

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

**Purpose:** Microsoft Graph API integration for SharePoint, OneDrive, and Email

**Auth Method:** Azure AD client credentials (app-only)

**SharePoint & OneDrive Methods:**
- `_get_access_token()` - MSAL client credentials flow
- `list_files(drive_id)` - List OneDrive files
- `get_file_info(drive_id, file_id)` - Get file metadata
- `download_file_url(drive_id, file_id)` - Get download URL
- `upload_file(drive_id, file_name, file_content)` - Upload file
- `list_sharepoint_list_items(site_id, list_id)` - Query SharePoint list
- `create_sharepoint_list_item(site_id, list_id, fields)` - Create list item

**Email DTOs:**
- `EmailAddress` - Email address with optional name
- `EmailRecipient` - Wrapper for Graph API recipient format
- `EmailBody` - Email body with content type (text/html)
- `EmailAttachmentDTO` - Attachment metadata (id, name, content_type, size)
- `EmailMessageDTO` - Full email message with all fields
- `MailFolderDTO` - Folder metadata with counts

**Email Methods:**
- `get_mail_folders(mailbox, include_hidden)` → `List[MailFolderDTO]`
- `get_mail_folder_by_name(mailbox, folder_name)` → `Optional[MailFolderDTO]`
- `create_mail_folder(mailbox, display_name, parent_folder_id)` → `MailFolderDTO`
- `get_messages(mailbox, folder_id, top, filter_query, order_by, select)` → `List[EmailMessageDTO]`
- `get_message_by_id(mailbox, message_id)` → `Optional[EmailMessageDTO]`
- `send_mail(mailbox, subject, body, to_recipients, cc_recipients, bcc_recipients, body_content_type, attachments, save_to_sent)` → `bool`
- `reply_to_message(mailbox, message_id, comment, reply_all)` → `bool`
- `forward_message(mailbox, message_id, to_recipients, comment)` → `bool`
- `move_message(mailbox, message_id, destination_folder_id)` → `Optional[EmailMessageDTO]`
- `update_message(mailbox, message_id, is_read, importance)` → `bool`
- `delete_message(mailbox, message_id)` → `bool`
- `get_message_attachments(mailbox, message_id)` → `List[EmailAttachmentDTO]`
- `download_attachment(mailbox, message_id, attachment_id)` → `bytes`

**HTTP Helper Methods:**
- `_patch(endpoint, data)` - PATCH request with JSON response
- `_delete(endpoint)` - DELETE request
- `_get_binary(endpoint)` - GET request for binary content
- `_post_no_response(endpoint, data)` - POST with no response body (204 expected)

---

## 10. TUI Integration

### 10.1 Main Application (app.py)

**Class:** `CommandCenterApp(App)`

**Global Bindings:**
| Key | Action |
|-----|--------|
| `q` | Quit application |
| `d` | CEO Dashboard screen (default) |
| `a` | Aramco pipeline screen |
| `c` | Commercial pipeline screen |
| `o` | Owner KPIs screen |
| `e` | Email drafts screen |
| `m` | Management screen |
| `t` | Tracker screen |
| `p` | Team screen |
| `l` | Loop monitor screen |
| `w` | War Room (old dashboard) |

### 10.2 Screens

| Screen | File | Purpose |
|--------|------|---------|
| CEO Dashboard | `ceo_dashboard_screen.py` | Main executive dashboard (default on launch) - cash health, urgent deals, velocity, priorities |
| War Room | `dashboard_screen.py` | Today's focus with priority items |
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

### 11.1 Pipedrive Integration
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

### 11.2 CEO Dashboard Features (December 2024)

**Foundation:**
✅ **Employee Directory** - Full CRUD with hierarchy and department management
✅ **Audit Logging** - All system actions tracked via intervention service

**Management Module:**
✅ **Task Management** - Tasks with assignees, priorities, due dates, and reminder integration
✅ **Internal Notes** - Notes with review reminders, pinning, and tagging
✅ **Unified Reminders** - Target-agnostic reminder system (in-app, email)

**Tracker Module:**
✅ **Document Tracking** - Legal documents with expiry dates and file attachments
✅ **Bonus Management** - Bonus tracking with partial payments and status auto-calculation
✅ **Employee Logs** - Achievement, issue, and feedback logging
✅ **Skills & Ratings** - Skill definitions with employee rating history

**Loop Engine:**
✅ **Background Monitoring** - Automated loops for proactive alerts
✅ **Document Expiry Loop** - Monitors documents expiring within 30 days
✅ **Bonus Due Loop** - Monitors bonuses due within 30 days
✅ **Task Overdue Loop** - Monitors overdue and soon-due tasks
✅ **Reminder Processing** - Processes and sends pending reminders
✅ **Finding Deduplication** - 24-hour deduplication using SHA256 signatures

**CEO Dashboard (Executive View):**
✅ **CEO Dashboard Screen** - Main executive dashboard (default on launch)
✅ **Cash Health Monitor** - Runway, weekly collections, 14-day forecast, velocity
✅ **Urgent Deals** - Top 5 attention-required deals with reasons
✅ **Pipeline Velocity** - Stage-by-stage averages, cycle time, trend indicators
✅ **Strategic Priorities** - Cost reduction, sales targets, commercial share
✅ **Department Scorecard** - Sales MVP with pipeline, won, overdue metrics
✅ **Configurable Targets** - Via CEODashboardConfig class

### 11.3 Microsoft Graph Email Service (January 2025)

**Email Operations (Service Layer Only - No API/UI):**
✅ **Email Caching** - Local SQLite cache for fast email reads
✅ **Email Reading** - Get emails from any mailbox folder with filtering
✅ **Email Search** - Search by subject, sender, date range with OData queries
✅ **Email Sending** - Send HTML emails with attachments to multiple recipients
✅ **Email Actions** - Reply, forward, move, mark as read, delete
✅ **Attachment Handling** - Download single or all attachments to disk
✅ **Folder Management** - List, create, and lookup folders by name
✅ **Multi-Mailbox Support** - Access any mailbox with proper permissions
✅ **DTO Conversion** - Automatic conversion between client/service layers

**Supported Mailboxes:**
- `mohammed@gyptech.com.sa` (default)
- `info@gyptech.com.sa`
- Future team members (configurable)

### 11.4 Test Coverage
✅ **324+ tests passing** - Unit tests + integration tests across all phases
✅ **pytest infrastructure** - Async support, in-memory SQLite, reusable fixtures
✅ **Email Service Tests** - 31 unit tests covering service initialization, DTO conversion, email operations

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
- **LLM Services:**
  - Writer service: `cmd_center/backend/services/writer_service.py`
  - Cashflow prediction: `cmd_center/backend/services/cashflow_prediction_service.py`
  - Prompt registry: `cmd_center/backend/services/prompt_registry.py`
  - Deterministic rules: `cmd_center/backend/services/deterministic_rules.py`
- **CEO Dashboard Services:**
  - Employee: `cmd_center/backend/services/employee_service.py`
  - Intervention: `cmd_center/backend/services/intervention_service.py`
  - Reminder: `cmd_center/backend/services/reminder_service.py`
  - Task: `cmd_center/backend/services/task_service.py`
  - Note: `cmd_center/backend/services/note_service.py`
  - Document: `cmd_center/backend/services/document_service.py`
  - Bonus: `cmd_center/backend/services/bonus_service.py`
  - Employee Log: `cmd_center/backend/services/employee_log_service.py`
  - Skill: `cmd_center/backend/services/skill_service.py`
- **Loop Engine:**
  - Engine: `cmd_center/backend/services/loop_engine.py`
  - Setup: `cmd_center/backend/services/loop_setup.py`
  - Loops: `cmd_center/backend/services/loops/`
- **CEO Dashboard (Aggregate):**
  - Service: `cmd_center/backend/services/ceo_dashboard_service.py`
  - API: `cmd_center/backend/api/ceo_dashboard.py`
  - Models: `cmd_center/backend/models/ceo_dashboard_models.py`
  - Screen: `cmd_center/screens/ceo_dashboard_screen.py`
- **Microsoft Graph Email:**
  - Service: `cmd_center/backend/services/msgraph_email_service.py`
  - Models: `cmd_center/backend/models/msgraph_email_models.py`
  - Client: `cmd_center/backend/integrations/microsoft_client.py`

**API:**
- All endpoints: `cmd_center/backend/api/`
- Routing: `cmd_center/backend/api/__init__.py`
- **CEO Dashboard APIs:** `employees.py`, `reminders.py`, `tasks.py`, `notes.py`, `documents.py`, `bonuses.py`, `employee_logs.py`, `skills.py`, `loops.py`

**Integrations:**
- All clients: `cmd_center/backend/integrations/`
- LLM client (refactored): `cmd_center/backend/integrations/llm_client.py`
- LLM observability: `cmd_center/backend/integrations/llm_observability.py`
- LLM circuit breaker: `cmd_center/backend/integrations/llm_circuit_breaker.py`
- Config: `cmd_center/backend/integrations/config.py`

**Models:**
- All models: `cmd_center/backend/models/`
- Writer models: `cmd_center/backend/models/writer_models.py`
- Cashflow models (extended): `cmd_center/backend/models/cashflow_models.py`
- **CEO Dashboard Models:** `employee_models.py`, `reminder_models.py`, `task_models.py`, `note_models.py`, `document_models.py`, `bonus_models.py`, `employee_log_models.py`, `skill_models.py`, `loop_models.py`

**Screens:**
- All screens: `cmd_center/screens/`

**Database Cache:**
- SQLite: `pipedrive_cache.db`

**Tests:**
- All tests: `tests/`
- Config: `tests/conftest.py`
- Integration tests: `tests/integration/`
- Unit tests: `tests/unit/`
- Contract tests: `tests/contract/`
- Email service tests: `tests/unit/test_msgraph_email_service.py`

**Documentation:**
- Architecture: `docs/Architecture.md` (this file)
- Implementation Summary: `docs/implementation_summary.md`
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
