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
│  - Calls query layer for data                                           │
│  - Calls LLM integration for analysis                                   │
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
│  External: Pipedrive API, Microsoft Graph API, OpenRouter LLM           │
└─────────────────────────────────────────────────────────────────────────┘
```

### Layer Rules

| Layer | Can Call | Cannot Call |
|-------|----------|-------------|
| UI (Textual) | FastAPI endpoints | Services, Database, Pipedrive |
| API (FastAPI) | Services | Database directly, Pipedrive |
| Services | db_queries.py, llm_client | Pipedrive directly |
| db_queries.py | SQLite (read-only) | Pipedrive, external APIs |
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
│   │   ├── llm_analysis_service.py
│   │   ├── cashflow_service.py
│   │   ├── owner_kpi_service.py
│   │   ├── email_service.py
│   │   ├── dashboard_service.py
│   │   ├── db_queries.py           # Read-only query functions
│   │   ├── aramco_summary_service.py  # CEO Radar summaries
│   │   ├── pipedrive_sync.py       # Sync functions
│   │   └── sync_scheduler.py       # Background sync scheduler
│   │
│   ├── models/                     # Pydantic models (API contracts)
│   │   ├── deal_models.py          # Includes summary response models
│   │   ├── cashflow_models.py
│   │   ├── kpi_models.py
│   │   ├── dashboard_models.py
│   │   └── email_models.py
│   │
│   └── integrations/               # External API clients
│       ├── config.py               # Pydantic settings
│       ├── pipedrive_client.py     # Used by sync layer only
│       ├── llm_client.py           # OpenRouter client
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
| `owner_kpi_service` | `get_deals_by_owner`, PipedriveClient for activities |
| `dashboard_service` | Aggregates from other services |
| `email_service` | Uses other services + llm_client |
| `llm_analysis_service` | `get_notes_for_deal` + llm_client |
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
| `llm_client` | `llm_analysis_service` | Send prompts, parse JSON responses |
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

### 9.2 llm_client.py

**Key Methods:**
- `generate_completion(prompt, system_prompt, max_tokens, temperature)` → `str`
- `analyze_deal_compliance(deal_title, stage, notes)` → `Dict`
- `analyze_order_received(deal_title, notes)` → `Dict`
- `summarize_deal(deal_title, stage, notes)` → `Dict`

**Model Used:** `anthropic/claude-3.5-sonnet` (configurable)

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

**API:**
- All endpoints: `cmd_center/backend/api/`
- Routing: `cmd_center/backend/api/__init__.py`

**Integrations:**
- All clients: `cmd_center/backend/integrations/`
- Config: `cmd_center/backend/integrations/config.py`

**Screens:**
- All screens: `cmd_center/screens/`

**Database Cache:**
- SQLite: `pipedrive_cache.db`

---

End of Architecture.md
