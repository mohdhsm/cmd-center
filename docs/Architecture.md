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

| Component | Technology |
|-----------|------------|
| Frontend (TUI) | Textual |
| Backend API | FastAPI |
| Database | SQLite + SQLModel |
| HTTP Client | httpx (async) |
| Validation | Pydantic |
| LLM Provider | OpenRouter |
| Email | SMTP / email provider |
| Background Tasks | FastAPI BackgroundTasks / APScheduler (optional) |

---

## 1. Architecture Layers

The application follows a **5-layer architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Layer 1: UI (Textual)                                                  │
│  - Screens, widgets, keyboard handling                                  │
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
│  - Business logic (deal_health, cashflow, kpis, emails)                │
│  - Calls query layer for data                                           │
│  - Calls LLM integration for analysis                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Layer 4: Database Layer                                                │
│  - SQLite database (pipedrive_cache.db)                                 │
│  - SQLModel for ORM                                                     │
│  - queries.py for read operations                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Layer 5: Sync Layer (Background)                                       │
│  - pipedrive_sync.py                                                    │
│  - Fetches from Pipedrive API                                           │
│  - Upserts into SQLite                                                  │
│  - Runs on schedule (every 30 min) or on-demand                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  External: Pipedrive API                                                │
└─────────────────────────────────────────────────────────────────────────┘
```

### Layer Rules

| Layer | Can Call | Cannot Call |
|-------|----------|-------------|
| UI (Textual) | FastAPI endpoints | Services, Database, Pipedrive |
| API (FastAPI) | Services | Database directly, Pipedrive |
| Services | queries.py, llm_client | Pipedrive directly |
| queries.py | SQLite (read-only) | Pipedrive, external APIs |
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
    ▼ get_aramco_overdue()
Service Layer
    │
    ▼ get_overdue_deals_for_pipeline()
queries.py
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
Scheduler (every 30 min) OR Manual Trigger
    │
    ▼ sync_all_pipelines()
pipedrive_sync.py
    │
    ▼ GET /pipelines, /stages, /deals
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
- Full sync on first run, incremental after
- Tracks last sync time per entity type

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
├── app.py                      # Textual application entry point
├── screens/                    # Textual screens
│   ├── dashboard.py
│   ├── aramco_pipeline.py
│   ├── commercial_pipeline.py
│   ├── owner_kpi.py
│   ├── deal_detail.py
│   └── email_drafts.py
├── design/                     # CSS and design assets
│
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   │
│   ├── api/                    # FastAPI routers
│   │   ├── health.py
│   │   ├── dashboard.py
│   │   ├── aramco.py
│   │   ├── commercial.py
│   │   ├── owners.py
│   │   ├── deals.py
│   │   ├── emails.py
│   │   └── sync.py             # NEW: Sync trigger endpoints
│   │
│   ├── services/               # Business logic
│   │   ├── deal_health_service.py
│   │   ├── llm_analysis_service.py
│   │   ├── cashflow_service.py
│   │   ├── owner_kpi_service.py
│   │   ├── email_service.py
│   │   └── dashboard_service.py
│   │
│   ├── db/                     # NEW: Database layer
│   │   ├── engine.py           # SQLite engine + init_db()
│   │   ├── models.py           # SQLModel table definitions
│   │   └── queries.py          # Read-only query functions
│   │
│   ├── sync/                   # NEW: Sync layer
│   │   ├── pipedrive_sync.py   # Sync functions
│   │   ├── scheduler.py        # Background sync scheduler
│   │   └── constants.py        # Pipeline/stage ID mappings
│   │
│   ├── models/                 # Pydantic models (API contracts)
│   │   ├── deal_models.py
│   │   ├── cashflow_models.py
│   │   ├── kpi_models.py
│   │   ├── dashboard_models.py
│   │   └── email_models.py
│   │
│   └── integrations/           # External API clients
│       ├── pipedrive_client.py # Used by sync layer only
│       ├── llm_client.py
│       ├── email_client.py
│       └── config.py
│
├── pipedrive_cache.db          # SQLite database file
├── .env                        # Environment variables
└── requirements.txt
```

---

## 4. Database Schema

### 4.1 Core Tables

| Table | Purpose | Sync Frequency |
|-------|---------|----------------|
| `pipeline` | Pipeline metadata | Daily / on-demand |
| `stage` | Stage metadata | Daily / on-demand |
| `deal` | Deal records (open) | Every 30 minutes |
| `note` | Deal notes | On-demand (lazy load) |
| `sync_metadata` | Tracks sync state | Updated after each sync |

### 4.2 Entity Relationships

```
pipeline (1) ──────< (many) stage
    │
    └──────< (many) deal ──────< (many) note
```

### 4.3 SyncMetadata Table

Tracks when each entity type was last synced:

```python
class SyncMetadata(SQLModel, table=True):
    id: int = Field(primary_key=True)
    entity_type: str          # "pipelines", "stages", "deals_5", etc.
    last_sync_time: datetime
    last_sync_duration_ms: int = 0
    records_synced: int = 0
    status: str = "success"   # "success", "failed", "in_progress"
    error_message: Optional[str] = None
```

---

## 5. Domain Models

### 5.1 Database Models (SQLModel - in `db/models.py`)

Used for database operations:
- `Pipeline`
- `Stage`
- `Deal`
- `Note`
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
- `OwnerKPI`
- `DashboardItem`
- `EmailDraft`
- `DealIssue`

### 5.3 Model Transformation

Services transform database models to API models:

```python
# In deal_health_service.py
def get_aramco_overdue(min_days: int = 7) -> list[OverdueDeal]:
    # Query returns db.models.Deal objects
    deals = queries.get_overdue_deals_for_pipeline(
        pipeline_id=PIPELINE_NAME_TO_ID["Aramco Projects"],
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
| `/aramco/overdue` | GET | deal_health_service | Overdue Aramco deals |
| `/aramco/stuck` | GET | deal_health_service | Stuck Aramco deals |
| `/aramco/order_received` | GET | deal_health_service | Order received analysis |
| `/aramco/compliance` | GET | deal_health_service | Compliance status |
| `/aramco/cashflow_projection` | GET | cashflow_service | Cashflow forecast |
| `/commercial/inactive` | GET | deal_health_service | Inactive commercial deals |
| `/commercial/recent_summary` | GET | deal_health_service | Recent deal summaries |
| `/owners/kpis` | GET | owner_kpi_service | Per-owner KPIs |
| `/deals/{id}/detail` | GET | deal_health_service | Single deal deep-dive |
| `/deals/search` | GET | deal_health_service | Search deals |

### 6.2 Action Endpoints

| Endpoint | Method | Service | Description |
|----------|--------|---------|-------------|
| `/emails/followups/generate` | POST | email_service | Generate email drafts |
| `/emails/followups/send` | POST | email_service | Send emails |

### 6.3 Sync Endpoints (NEW)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sync/status` | GET | Get last sync times and status |
| `/sync/trigger` | POST | Trigger immediate sync |
| `/sync/trigger/{entity}` | POST | Trigger sync for specific entity |

---

## 7. Services

### 7.1 Service → Query Mapping

| Service | Uses Queries |
|---------|--------------|
| `deal_health_service` | `get_overdue_deals`, `get_stuck_deals`, `get_deals_by_stage` |
| `cashflow_service` | `get_deals_near_invoicing`, `get_deals_by_stage` |
| `owner_kpi_service` | `get_deals_by_owner`, `get_deal_counts_by_owner` |
| `dashboard_service` | Aggregates from other services |
| `email_service` | Uses other services + llm_client |
| `llm_analysis_service` | `get_notes_for_deal` + llm_client |

### 7.2 Service Characteristics

All services:
- Are **synchronous** (database queries are fast)
- Return **Pydantic models** (API models, not DB models)
- Do **not** call Pipedrive directly
- May call `llm_client` for analysis

---

## 8. Sync Layer

### 8.1 Sync Functions

| Function | Syncs | Strategy |
|----------|-------|----------|
| `sync_pipelines()` | Pipeline table | Full replace |
| `sync_stages()` | Stage table | Full replace |
| `sync_deals_for_pipeline(id)` | Deal table | Upsert (incremental capable) |
| `sync_all_deals()` | All pipelines | Calls above for each |
| `sync_notes_for_deal(id)` | Note table | On-demand only |

### 8.2 Sync Strategy

| Entity | Initial Sync | Periodic Sync | Notes |
|--------|--------------|---------------|-------|
| Pipelines | All | Daily | Rarely changes |
| Stages | All | Daily | Rarely changes |
| Deals (open) | All | Every 30 min | Core data |
| Deals (won/lost) | Skip | Skip | Not needed for active management |
| Notes | None | On-demand | Too many to bulk sync |

### 8.3 Incremental Sync Logic

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

### 8.4 Scheduler

The sync scheduler runs as a background task:

```python
# Option 1: FastAPI lifespan with asyncio
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background sync task
    task = asyncio.create_task(periodic_sync())
    yield
    task.cancel()

async def periodic_sync():
    while True:
        await sync_all_deals()
        await asyncio.sleep(30 * 60)  # 30 minutes

# Option 2: APScheduler (more robust)
scheduler = BackgroundScheduler()
scheduler.add_job(sync_all_deals, 'interval', minutes=30)
scheduler.start()
```

---

## 9. Integration Clients

| Client | Used By | Purpose |
|--------|---------|---------|
| `pipedrive_client` | `pipedrive_sync.py` only | Fetch data from Pipedrive API |
| `llm_client` | `llm_analysis_service` | Send prompts, parse JSON responses |
| `email_client` | `email_service` | Send SMTP emails |

---

## 10. TUI Integration

### 10.1 Screen Data Loading

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

### 10.2 Manual Refresh

When user triggers refresh:

```python
async def action_reload(self):
    # 1. Trigger sync in background
    async with httpx.AsyncClient() as client:
        await client.post(f"{API_BASE}/sync/trigger/deals")
    
    # 2. Wait briefly for sync to complete (or poll)
    await asyncio.sleep(2)
    
    # 3. Reload data from database
    await self.load_data()
```

---

## 11. Implementation Order

### Phase 1: Database Foundation
1. Set up `db/engine.py` with SQLite engine
2. Create `db/models.py` with SQLModel tables
3. Create `db/queries.py` with basic query functions
4. Create `sync/pipedrive_sync.py` with sync functions

### Phase 2: Wire Services to Database
5. Update `deal_health_service.py` to use queries.py
6. Update `cashflow_service.py` to use queries.py
7. Update `owner_kpi_service.py` to use queries.py

### Phase 3: Sync Infrastructure
8. Add `/sync/*` API endpoints
9. Add background sync scheduler
10. Add sync status tracking

### Phase 4: TUI Updates
11. Update screens to handle refresh properly
12. Add sync status indicator to UI

---

## 12. Testing Strategy

| Layer | Test Type | Tools |
|-------|-----------|-------|
| db/queries.py | Unit tests | pytest + test SQLite DB |
| Services | Unit tests | pytest + mocked queries |
| API endpoints | Integration tests | pytest + TestClient |
| Sync layer | Integration tests | pytest + mocked Pipedrive |
| TUI | Manual testing | Run app locally |

---

## 13. Configuration

All configuration via environment variables:

```bash
# Pipedrive
PIPEDRIVE_API_TOKEN=xxx

# Database
DATABASE_URL=sqlite:///pipedrive_cache.db

# LLM
OPENROUTER_API_KEY=xxx

# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=xxx
SMTP_PASSWORD=xxx

# Sync
SYNC_INTERVAL_MINUTES=30
```

---

End of Architecture.md
