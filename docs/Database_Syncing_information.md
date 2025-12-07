# Database_Syncing_information.md

This document is a **guideline for an LLM** that will implement database caching and syncing for the Command Center application.

---

## Goals

1. **Make the TUI fast:** All screens read from a **local SQLite database**, never from Pipedrive API directly.
2. **Hide network latency:** Pipedrive is accessed through a **sync layer** that updates SQLite in the background.
3. **Minimize API calls:** Use **incremental sync** to only fetch changed data after initial sync.
4. **Keep it simple:** SQLite + SQLModel, no complex infrastructure.

---

## 0. Architecture Overview

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           READ PATH (Fast)                              │
│                                                                         │
│   Textual Screen                                                        │
│        │                                                                │
│        ▼  HTTP GET /aramco/overdue                                      │
│   FastAPI Endpoint                                                      │
│        │                                                                │
│        ▼  get_aramco_overdue()                                          │
│   Service Layer (deal_health_service.py)                                │
│        │                                                                │
│        ▼  get_overdue_deals_for_pipeline()                              │
│   Query Layer (queries.py)                                              │
│        │                                                                │
│        ▼  SELECT * FROM deal WHERE ...                                  │
│   SQLite Database (pipedrive_cache.db)                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         SYNC PATH (Background)                          │
│                                                                         │
│   Scheduler (every 30 min) OR Manual Trigger (/sync/trigger)            │
│        │                                                                │
│        ▼  sync_all()                                                    │
│   Sync Layer (pipedrive_sync.py)                                        │
│        │                                                                │
│        ▼  GET /pipelines, /stages, /deals                               │
│   Pipedrive API                                                         │
│        │                                                                │
│        ▼  Transform JSON → SQLModel objects                             │
│        │                                                                │
│        ▼  session.merge() (upsert)                                      │
│   SQLite Database                                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Core Rules

| Component | Reads From | Writes To | Calls Pipedrive? |
|-----------|------------|-----------|------------------|
| Textual screens | FastAPI | - | ❌ Never |
| FastAPI endpoints | Services | - | ❌ Never |
| Services | queries.py | - | ❌ Never |
| queries.py | SQLite | - | ❌ Never |
| pipedrive_sync.py | Pipedrive API | SQLite | ✅ Yes |

---

## 1. Database Engine Setup

Create `backend/db/engine.py`:

```python
from sqlmodel import SQLModel, create_engine, Session
from contextlib import contextmanager
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///pipedrive_cache.db")

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}  # Required for SQLite + FastAPI
)

def init_db():
    """Create all tables. Call once at startup."""
    SQLModel.metadata.create_all(engine)

@contextmanager
def get_session():
    """Context manager for database sessions."""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_session_dependency():
    """FastAPI dependency for database sessions."""
    with Session(engine) as session:
        yield session
```

---

## 2. Database Models (SQLModel)

Create `backend/db/models.py`:

```python
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

# =============================================================================
# Core Pipedrive Models
# =============================================================================

class Pipeline(SQLModel, table=True):
    """Pipedrive pipeline (e.g., 'Aramco Projects', 'Pipeline')."""
    id: int = Field(primary_key=True)
    name: str
    order_nr: int
    is_deleted: bool = False
    is_deal_probability_enabled: bool = False
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class Stage(SQLModel, table=True):
    """Pipedrive stage within a pipeline."""
    id: int = Field(primary_key=True)
    name: str
    order_nr: int
    pipeline_id: int = Field(index=True)
    deal_probability: int = 0
    is_deal_rot_enabled: bool = False
    days_to_rotten: Optional[int] = None
    is_deleted: bool = False
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class Deal(SQLModel, table=True):
    """Pipedrive deal record."""
    id: int = Field(primary_key=True)
    title: str
    pipeline_id: int = Field(index=True)
    stage_id: int = Field(index=True)
    owner_name: Optional[str] = None
    owner_id: Optional[int] = None
    org_name: Optional[str] = None
    org_id: Optional[int] = None
    value: float = 0.0
    currency: str = "SAR"
    status: str = Field(default="open", index=True)  # "open", "won", "lost"
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = Field(default=None, index=True)
    stage_change_time: Optional[datetime] = None
    expected_close_date: Optional[datetime] = None
    last_activity_date: Optional[datetime] = None
    
    # Store full JSON for debugging or accessing unmapped fields
    raw_json: Optional[str] = None


class Note(SQLModel, table=True):
    """Deal note for LLM analysis."""
    id: int = Field(primary_key=True)
    deal_id: int = Field(index=True)
    user_name: Optional[str] = None
    user_id: Optional[int] = None
    content: str
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


# =============================================================================
# Sync Metadata
# =============================================================================

class SyncMetadata(SQLModel, table=True):
    """Tracks sync state for incremental updates."""
    __tablename__ = "sync_metadata"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    entity_type: str = Field(unique=True)  # e.g., "pipelines", "stages", "deals_5"
    last_sync_time: datetime
    last_sync_duration_ms: int = 0
    records_synced: int = 0
    records_total: int = 0
    status: str = "success"  # "success", "failed", "in_progress"
    error_message: Optional[str] = None
```

### Model Notes for LLM

- **owner_name**: Extract from `deal["owner_name"]` or fallback to `deal["owner_id"]["name"]`
- **stage_change_time**: Use this to calculate "days in stage"
- **status**: Only sync `"open"` deals by default
- **raw_json**: Store for debugging; can be used to access fields not explicitly mapped

---

## 3. Known Pipedrive IDs

Create `backend/sync/constants.py`:

```python
# =============================================================================
# Pipeline Mappings
# =============================================================================

PIPELINE_NAME_TO_ID = {
    "Pipeline": 1,              # Commercial
    "Prospecting": 2,
    "Aramco Inquiries": 3,
    "Aramco PO": 4,
    "Aramco Projects": 5,
    "Bidding Projects": 6,
    "Design Development": 10,
    "Problematic & Stuck Orders": 11,
}

PIPELINE_ID_TO_NAME = {v: k for k, v in PIPELINE_NAME_TO_ID.items()}

# Pipelines to sync regularly
SYNC_PIPELINES = [
    PIPELINE_NAME_TO_ID["Aramco Projects"],
    PIPELINE_NAME_TO_ID["Pipeline"],  # Commercial
    PIPELINE_NAME_TO_ID["Aramco PO"],
]

# =============================================================================
# Stage Mappings
# =============================================================================

# Stage names can be duplicated across pipelines!
# Always use (pipeline_id, stage_name) as the key.

def build_stage_key_to_id(stages: list[dict]) -> dict[tuple[int, str], int]:
    """
    Build a mapping from (pipeline_id, stage_name) -> stage_id.
    
    Usage:
        stages = session.exec(select(Stage)).all()
        STAGE_KEY_TO_ID = build_stage_key_to_id([s.dict() for s in stages])
    """
    return {
        (s["pipeline_id"], s["name"]): s["id"]
        for s in stages
    }

def get_stage_name(session, stage_id: int) -> str:
    """Get stage name by ID from database."""
    from sqlmodel import select
    from .models import Stage
    
    stage = session.exec(select(Stage).where(Stage.id == stage_id)).first()
    return stage.name if stage else "Unknown"
```

---

## 4. Sync Layer

Create `backend/sync/pipedrive_sync.py`:

```python
import os
import json
import httpx
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Session, select

from backend.db.engine import engine
from backend.db.models import Pipeline, Stage, Deal, Note, SyncMetadata

# =============================================================================
# Configuration
# =============================================================================

PIPEDRIVE_API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
BASE_URL = "https://api.pipedrive.com/v1"

if not PIPEDRIVE_API_TOKEN:
    raise ValueError("PIPEDRIVE_API_TOKEN environment variable is required")

# =============================================================================
# HTTP Client
# =============================================================================

async def pd_get(client: httpx.AsyncClient, path: str, **params) -> dict:
    """Make a GET request to Pipedrive API."""
    params["api_token"] = PIPEDRIVE_API_TOKEN
    response = await client.get(f"{BASE_URL}{path}", params=params, timeout=30.0)
    response.raise_for_status()
    return response.json()

# =============================================================================
# Sync Metadata Helpers
# =============================================================================

def get_last_sync_time(entity_type: str) -> Optional[datetime]:
    """Get the last successful sync time for an entity type."""
    with Session(engine) as session:
        meta = session.exec(
            select(SyncMetadata).where(SyncMetadata.entity_type == entity_type)
        ).first()
        if meta and meta.status == "success":
            return meta.last_sync_time
        return None

def update_sync_metadata(
    entity_type: str,
    status: str,
    records_synced: int = 0,
    records_total: int = 0,
    duration_ms: int = 0,
    error_message: Optional[str] = None
):
    """Update sync metadata after a sync operation."""
    with Session(engine) as session:
        meta = session.exec(
            select(SyncMetadata).where(SyncMetadata.entity_type == entity_type)
        ).first()
        
        if meta:
            meta.last_sync_time = datetime.now(timezone.utc)
            meta.status = status
            meta.records_synced = records_synced
            meta.records_total = records_total
            meta.last_sync_duration_ms = duration_ms
            meta.error_message = error_message
        else:
            meta = SyncMetadata(
                entity_type=entity_type,
                last_sync_time=datetime.now(timezone.utc),
                status=status,
                records_synced=records_synced,
                records_total=records_total,
                last_sync_duration_ms=duration_ms,
                error_message=error_message,
            )
            session.add(meta)
        
        session.commit()

# =============================================================================
# Sync Functions
# =============================================================================

async def sync_pipelines():
    """Sync all pipelines from Pipedrive."""
    start_time = datetime.now()
    
    try:
        async with httpx.AsyncClient() as client:
            payload = await pd_get(client, "/pipelines")
        
        items = payload.get("data") or []
        
        with Session(engine) as session:
            for p in items:
                pipeline = Pipeline(
                    id=p["id"],
                    name=p["name"],
                    order_nr=p["order_nr"],
                    is_deleted=p.get("is_deleted", False),
                    is_deal_probability_enabled=p.get("is_deal_probability_enabled", False),
                    add_time=p.get("add_time"),
                    update_time=p.get("update_time"),
                )
                session.merge(pipeline)
            session.commit()
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        update_sync_metadata("pipelines", "success", len(items), len(items), duration_ms)
        
        return len(items)
    
    except Exception as e:
        update_sync_metadata("pipelines", "failed", error_message=str(e))
        raise


async def sync_stages():
    """Sync all stages from Pipedrive."""
    start_time = datetime.now()
    
    try:
        async with httpx.AsyncClient() as client:
            payload = await pd_get(client, "/stages")
        
        items = payload.get("data") or []
        
        with Session(engine) as session:
            for s in items:
                stage = Stage(
                    id=s["id"],
                    name=s["name"],
                    order_nr=s["order_nr"],
                    pipeline_id=s["pipeline_id"],
                    deal_probability=s.get("deal_probability", 0),
                    is_deal_rot_enabled=s.get("is_deal_rot_enabled", False),
                    days_to_rotten=s.get("days_to_rotten"),
                    is_deleted=s.get("is_deleted", False),
                    add_time=s.get("add_time"),
                    update_time=s.get("update_time"),
                )
                session.merge(stage)
            session.commit()
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        update_sync_metadata("stages", "success", len(items), len(items), duration_ms)
        
        return len(items)
    
    except Exception as e:
        update_sync_metadata("stages", "failed", error_message=str(e))
        raise


async def sync_deals_for_pipeline(
    pipeline_id: int,
    status: str = "open",
    incremental: bool = True
):
    """
    Sync deals for a specific pipeline.
    
    Args:
        pipeline_id: Pipedrive pipeline ID
        status: Deal status filter ("open", "won", "lost", "all_not_deleted")
        incremental: If True, only upsert deals updated since last sync
    """
    entity_type = f"deals_{pipeline_id}"
    start_time = datetime.now()
    last_sync = get_last_sync_time(entity_type) if incremental else None
    
    try:
        # Fetch all deals (Pipedrive doesn't support modified_since filter)
        all_deals = []
        start = 0
        limit = 500
        
        async with httpx.AsyncClient() as client:
            while True:
                payload = await pd_get(
                    client,
                    "/deals",
                    pipeline_id=pipeline_id,
                    status=status,
                    start=start,
                    limit=limit,
                )
                items = payload.get("data") or []
                if not items:
                    break
                
                all_deals.extend(items)
                
                # Check pagination
                additional = payload.get("additional_data") or {}
                pagination = additional.get("pagination") or {}
                if not pagination.get("more_items_in_collection"):
                    break
                
                start = pagination.get("next_start", 0)
        
        # Filter to only updated deals if incremental
        if last_sync and incremental:
            deals_to_upsert = [
                d for d in all_deals
                if _parse_datetime(d.get("update_time")) > last_sync
            ]
        else:
            deals_to_upsert = all_deals
        
        # Upsert deals
        with Session(engine) as session:
            for d in deals_to_upsert:
                # Extract owner name
                owner_name = d.get("owner_name")
                if not owner_name:
                    owner = d.get("owner_id") or {}
                    if isinstance(owner, dict):
                        owner_name = owner.get("name")
                
                # Extract org name
                org_name = d.get("org_name")
                if not org_name:
                    org = d.get("org_id") or {}
                    if isinstance(org, dict):
                        org_name = org.get("name")
                
                deal = Deal(
                    id=d["id"],
                    title=d["title"],
                    pipeline_id=d["pipeline_id"],
                    stage_id=d["stage_id"],
                    owner_name=owner_name,
                    owner_id=d.get("owner_id") if isinstance(d.get("owner_id"), int) else None,
                    org_name=org_name,
                    org_id=d.get("org_id") if isinstance(d.get("org_id"), int) else None,
                    value=float(d.get("value") or 0.0),
                    currency=d.get("currency", "SAR"),
                    status=d["status"],
                    add_time=d.get("add_time"),
                    update_time=d.get("update_time"),
                    stage_change_time=d.get("stage_change_time"),
                    expected_close_date=d.get("expected_close_date"),
                    last_activity_date=d.get("last_activity_date"),
                    raw_json=json.dumps(d),
                )
                session.merge(deal)
            session.commit()
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        update_sync_metadata(
            entity_type, "success",
            records_synced=len(deals_to_upsert),
            records_total=len(all_deals),
            duration_ms=duration_ms
        )
        
        return len(deals_to_upsert), len(all_deals)
    
    except Exception as e:
        update_sync_metadata(entity_type, "failed", error_message=str(e))
        raise


async def sync_notes_for_deal(deal_id: int):
    """
    Sync notes for a specific deal.
    
    Called on-demand when viewing deal details (not bulk synced).
    """
    entity_type = f"notes_{deal_id}"
    start_time = datetime.now()
    
    try:
        async with httpx.AsyncClient() as client:
            payload = await pd_get(client, "/notes", deal_id=deal_id)
        
        items = payload.get("data") or []
        
        with Session(engine) as session:
            for n in items:
                user = n.get("user") or {}
                note = Note(
                    id=n["id"],
                    deal_id=n["deal_id"],
                    user_name=user.get("name") if isinstance(user, dict) else None,
                    user_id=user.get("id") if isinstance(user, dict) else None,
                    content=n.get("content", ""),
                    add_time=n.get("add_time"),
                    update_time=n.get("update_time"),
                )
                session.merge(note)
            session.commit()
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        update_sync_metadata(entity_type, "success", len(items), len(items), duration_ms)
        
        return len(items)
    
    except Exception as e:
        update_sync_metadata(entity_type, "failed", error_message=str(e))
        raise


# =============================================================================
# Full Sync Functions
# =============================================================================

async def sync_all(incremental: bool = True):
    """
    Sync all entities from Pipedrive.
    
    Args:
        incremental: If True, only sync deals updated since last sync
    """
    from backend.sync.constants import SYNC_PIPELINES
    
    results = {
        "pipelines": 0,
        "stages": 0,
        "deals": {},
    }
    
    # Sync pipelines and stages (always full)
    results["pipelines"] = await sync_pipelines()
    results["stages"] = await sync_stages()
    
    # Sync deals for each tracked pipeline
    for pipeline_id in SYNC_PIPELINES:
        synced, total = await sync_deals_for_pipeline(
            pipeline_id,
            status="open",
            incremental=incremental
        )
        results["deals"][pipeline_id] = {"synced": synced, "total": total}
    
    return results


async def full_sync():
    """Force a full sync of all entities (ignore last sync time)."""
    return await sync_all(incremental=False)


# =============================================================================
# Helpers
# =============================================================================

def _parse_datetime(value) -> Optional[datetime]:
    """Parse a datetime string from Pipedrive."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        # Pipedrive format: "2025-01-15 10:30:00"
        return datetime.fromisoformat(value.replace(" ", "T"))
    except (ValueError, AttributeError):
        return None
```

---

## 5. Query Layer (Read-Only)

Create `backend/db/queries.py`:

```python
"""
Read-only query functions for the service layer.

These functions query the SQLite database and return SQLModel objects.
Services transform these into Pydantic API models.
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlmodel import Session, select, func

from backend.db.engine import engine
from backend.db.models import Pipeline, Stage, Deal, Note, SyncMetadata
from backend.sync.constants import PIPELINE_NAME_TO_ID

# =============================================================================
# Pipeline & Stage Queries
# =============================================================================

def get_pipeline_by_name(name: str) -> Optional[Pipeline]:
    """Get a pipeline by name."""
    with Session(engine) as session:
        return session.exec(
            select(Pipeline).where(Pipeline.name == name)
        ).first()

def get_stage_by_id(stage_id: int) -> Optional[Stage]:
    """Get a stage by ID."""
    with Session(engine) as session:
        return session.exec(
            select(Stage).where(Stage.id == stage_id)
        ).first()

def get_stages_for_pipeline(pipeline_id: int) -> list[Stage]:
    """Get all stages for a pipeline."""
    with Session(engine) as session:
        return list(session.exec(
            select(Stage)
            .where(Stage.pipeline_id == pipeline_id)
            .order_by(Stage.order_nr)
        ).all())

# =============================================================================
# Deal Queries
# =============================================================================

def get_deals_for_pipeline(
    pipeline_id: int,
    status: str = "open"
) -> list[Deal]:
    """Get all deals for a pipeline."""
    with Session(engine) as session:
        return list(session.exec(
            select(Deal)
            .where(Deal.pipeline_id == pipeline_id)
            .where(Deal.status == status)
        ).all())

def get_overdue_deals_for_pipeline(
    pipeline_id: int,
    min_days: int = 7
) -> list[Deal]:
    """
    Get deals that haven't been updated in `min_days` days.
    
    "Overdue" = update_time is older than the threshold.
    """
    cutoff = datetime.utcnow() - timedelta(days=min_days)
    
    with Session(engine) as session:
        return list(session.exec(
            select(Deal)
            .where(Deal.pipeline_id == pipeline_id)
            .where(Deal.status == "open")
            .where(Deal.update_time < cutoff)
            .order_by(Deal.update_time)
        ).all())

def get_stuck_deals_for_pipeline(
    pipeline_id: int,
    min_days: int = 30
) -> list[Deal]:
    """
    Get deals that have been in the same stage for `min_days` days.
    
    Uses stage_change_time if available, otherwise falls back to update_time.
    """
    cutoff = datetime.utcnow() - timedelta(days=min_days)
    
    with Session(engine) as session:
        return list(session.exec(
            select(Deal)
            .where(Deal.pipeline_id == pipeline_id)
            .where(Deal.status == "open")
            .where(
                # Prefer stage_change_time, fallback to update_time
                func.coalesce(Deal.stage_change_time, Deal.update_time) < cutoff
            )
            .order_by(func.coalesce(Deal.stage_change_time, Deal.update_time))
        ).all())

def get_deals_by_stage(
    pipeline_id: int,
    stage_name: str,
    min_days_in_stage: int = 0
) -> list[Deal]:
    """Get deals in a specific stage, optionally filtered by days in stage."""
    # First get the stage ID
    with Session(engine) as session:
        stage = session.exec(
            select(Stage)
            .where(Stage.pipeline_id == pipeline_id)
            .where(Stage.name == stage_name)
        ).first()
        
        if not stage:
            return []
        
        query = (
            select(Deal)
            .where(Deal.pipeline_id == pipeline_id)
            .where(Deal.stage_id == stage.id)
            .where(Deal.status == "open")
        )
        
        if min_days_in_stage > 0:
            cutoff = datetime.utcnow() - timedelta(days=min_days_in_stage)
            query = query.where(
                func.coalesce(Deal.stage_change_time, Deal.update_time) < cutoff
            )
        
        return list(session.exec(query).all())

def get_deals_by_owner(
    owner_name: str,
    pipeline_ids: Optional[list[int]] = None,
    status: str = "open"
) -> list[Deal]:
    """Get all deals for a specific owner."""
    with Session(engine) as session:
        query = (
            select(Deal)
            .where(Deal.owner_name == owner_name)
            .where(Deal.status == status)
        )
        
        if pipeline_ids:
            query = query.where(Deal.pipeline_id.in_(pipeline_ids))
        
        return list(session.exec(query).all())

def get_deal_by_id(deal_id: int) -> Optional[Deal]:
    """Get a single deal by ID."""
    with Session(engine) as session:
        return session.exec(
            select(Deal).where(Deal.id == deal_id)
        ).first()

def get_deals_near_invoicing(
    pipeline_id: int,
    stage_names: list[str]
) -> list[Deal]:
    """Get deals in stages that are close to invoicing."""
    with Session(engine) as session:
        # Get stage IDs for the given names
        stages = session.exec(
            select(Stage)
            .where(Stage.pipeline_id == pipeline_id)
            .where(Stage.name.in_(stage_names))
        ).all()
        
        stage_ids = [s.id for s in stages]
        
        if not stage_ids:
            return []
        
        return list(session.exec(
            select(Deal)
            .where(Deal.pipeline_id == pipeline_id)
            .where(Deal.stage_id.in_(stage_ids))
            .where(Deal.status == "open")
        ).all())

def search_deals(
    query: str,
    pipeline_id: Optional[int] = None,
    owner_name: Optional[str] = None,
    limit: int = 50
) -> list[Deal]:
    """Search deals by title or org name."""
    with Session(engine) as session:
        stmt = (
            select(Deal)
            .where(Deal.status == "open")
            .where(
                (Deal.title.ilike(f"%{query}%")) |
                (Deal.org_name.ilike(f"%{query}%"))
            )
        )
        
        if pipeline_id:
            stmt = stmt.where(Deal.pipeline_id == pipeline_id)
        
        if owner_name:
            stmt = stmt.where(Deal.owner_name == owner_name)
        
        stmt = stmt.limit(limit)
        
        return list(session.exec(stmt).all())

# =============================================================================
# Note Queries
# =============================================================================

def get_notes_for_deal(deal_id: int) -> list[Note]:
    """Get all notes for a deal, ordered by date."""
    with Session(engine) as session:
        return list(session.exec(
            select(Note)
            .where(Note.deal_id == deal_id)
            .order_by(Note.add_time)
        ).all())

# =============================================================================
# Aggregation Queries
# =============================================================================

def get_deal_counts_by_owner(
    pipeline_ids: Optional[list[int]] = None,
    status: str = "open"
) -> dict[str, int]:
    """Get deal counts grouped by owner."""
    with Session(engine) as session:
        query = (
            select(Deal.owner_name, func.count(Deal.id))
            .where(Deal.status == status)
            .where(Deal.owner_name.isnot(None))
            .group_by(Deal.owner_name)
        )
        
        if pipeline_ids:
            query = query.where(Deal.pipeline_id.in_(pipeline_ids))
        
        results = session.exec(query).all()
        return {owner: count for owner, count in results}

def get_deal_value_by_owner(
    pipeline_ids: Optional[list[int]] = None,
    status: str = "open"
) -> dict[str, float]:
    """Get total deal value grouped by owner."""
    with Session(engine) as session:
        query = (
            select(Deal.owner_name, func.sum(Deal.value))
            .where(Deal.status == status)
            .where(Deal.owner_name.isnot(None))
            .group_by(Deal.owner_name)
        )
        
        if pipeline_ids:
            query = query.where(Deal.pipeline_id.in_(pipeline_ids))
        
        results = session.exec(query).all()
        return {owner: value or 0.0 for owner, value in results}

# =============================================================================
# Sync Status Queries
# =============================================================================

def get_sync_status() -> list[SyncMetadata]:
    """Get sync status for all entity types."""
    with Session(engine) as session:
        return list(session.exec(
            select(SyncMetadata).order_by(SyncMetadata.entity_type)
        ).all())

def get_last_sync_time(entity_type: str) -> Optional[datetime]:
    """Get the last sync time for a specific entity type."""
    with Session(engine) as session:
        meta = session.exec(
            select(SyncMetadata).where(SyncMetadata.entity_type == entity_type)
        ).first()
        return meta.last_sync_time if meta else None
```

---

## 6. Service Layer Integration

Services now call `queries.py` instead of Pipedrive:

```python
# backend/services/deal_health_service.py

from backend.db import queries
from backend.sync.constants import PIPELINE_NAME_TO_ID, PIPELINE_ID_TO_NAME
from backend.models.deal_models import OverdueDeal, StuckDeal

def get_aramco_overdue(min_days: int = 7) -> list[OverdueDeal]:
    """Get overdue deals from Aramco Projects pipeline."""
    pipeline_id = PIPELINE_NAME_TO_ID["Aramco Projects"]
    
    # Query database (fast!)
    deals = queries.get_overdue_deals_for_pipeline(pipeline_id, min_days)
    
    # Transform to API model
    return [
        OverdueDeal(
            id=d.id,
            title=d.title,
            pipeline=PIPELINE_ID_TO_NAME[d.pipeline_id],
            stage=_get_stage_name(d.stage_id),
            owner=d.owner_name or "Unknown",
            org_name=d.org_name,
            value_sar=d.value,
            add_time=d.add_time,
            update_time=d.update_time,
            last_activity_time=d.last_activity_date,
            overdue_days=_calculate_overdue_days(d.update_time),
        )
        for d in deals
    ]

def _get_stage_name(stage_id: int) -> str:
    """Helper to get stage name from ID."""
    stage = queries.get_stage_by_id(stage_id)
    return stage.name if stage else "Unknown"

def _calculate_overdue_days(update_time) -> int:
    """Calculate days since last update."""
    if not update_time:
        return 0
    from datetime import datetime
    delta = datetime.utcnow() - update_time
    return max(0, delta.days)
```

---

## 7. Sync API Endpoints

Create `backend/api/sync.py`:

```python
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from backend.db import queries
from backend.sync import pipedrive_sync

router = APIRouter(prefix="/sync", tags=["sync"])

class SyncStatus(BaseModel):
    entity_type: str
    last_sync_time: Optional[datetime]
    status: str
    records_synced: int
    records_total: int
    duration_ms: int

class SyncTriggerResponse(BaseModel):
    status: str
    message: str

@router.get("/status", response_model=list[SyncStatus])
def get_sync_status():
    """Get sync status for all entity types."""
    metadata = queries.get_sync_status()
    return [
        SyncStatus(
            entity_type=m.entity_type,
            last_sync_time=m.last_sync_time,
            status=m.status,
            records_synced=m.records_synced,
            records_total=m.records_total,
            duration_ms=m.last_sync_duration_ms,
        )
        for m in metadata
    ]

@router.post("/trigger", response_model=SyncTriggerResponse)
async def trigger_full_sync(background_tasks: BackgroundTasks):
    """Trigger a full sync of all entities."""
    background_tasks.add_task(pipedrive_sync.sync_all, incremental=True)
    return SyncTriggerResponse(
        status="started",
        message="Sync started in background"
    )

@router.post("/trigger/{entity}", response_model=SyncTriggerResponse)
async def trigger_entity_sync(
    entity: str,
    background_tasks: BackgroundTasks
):
    """Trigger sync for a specific entity type."""
    if entity == "pipelines":
        background_tasks.add_task(pipedrive_sync.sync_pipelines)
    elif entity == "stages":
        background_tasks.add_task(pipedrive_sync.sync_stages)
    elif entity.startswith("deals_"):
        pipeline_id = int(entity.split("_")[1])
        background_tasks.add_task(
            pipedrive_sync.sync_deals_for_pipeline,
            pipeline_id=pipeline_id
        )
    else:
        return SyncTriggerResponse(
            status="error",
            message=f"Unknown entity type: {entity}"
        )
    
    return SyncTriggerResponse(
        status="started",
        message=f"Sync for {entity} started in background"
    )
```

---

## 8. Background Scheduler

Create `backend/sync/scheduler.py`:

```python
import asyncio
import logging
from datetime import datetime

from backend.sync.pipedrive_sync import sync_all

logger = logging.getLogger(__name__)

SYNC_INTERVAL_SECONDS = 30 * 60  # 30 minutes

async def periodic_sync():
    """Run sync periodically in the background."""
    while True:
        try:
            logger.info(f"Starting periodic sync at {datetime.utcnow()}")
            results = await sync_all(incremental=True)
            logger.info(f"Periodic sync completed: {results}")
        except Exception as e:
            logger.error(f"Periodic sync failed: {e}")
        
        await asyncio.sleep(SYNC_INTERVAL_SECONDS)

def start_scheduler():
    """Start the background sync scheduler."""
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_sync())
    logger.info("Background sync scheduler started")
```

### FastAPI Lifespan Integration

In `backend/main.py`:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

from backend.db.engine import init_db
from backend.sync.scheduler import start_scheduler
from backend.sync.pipedrive_sync import sync_all

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    
    # Initial sync if database is empty
    # (or always do a full sync on startup)
    await sync_all(incremental=False)
    
    # Start background scheduler
    start_scheduler()
    
    yield
    
    # Shutdown (cleanup if needed)
    pass

app = FastAPI(lifespan=lifespan)
```

---

## 9. Implementation Checklist

### Phase 1: Database Foundation
- [ ] Create `backend/db/engine.py`
- [ ] Create `backend/db/models.py`
- [ ] Test database initialization

### Phase 2: Sync Layer
- [ ] Create `backend/sync/constants.py`
- [ ] Create `backend/sync/pipedrive_sync.py`
- [ ] Test sync functions individually

### Phase 3: Query Layer
- [ ] Create `backend/db/queries.py`
- [ ] Test query functions with sample data

### Phase 4: Wire Services
- [ ] Update `deal_health_service.py`
- [ ] Update `cashflow_service.py`
- [ ] Update `owner_kpi_service.py`
- [ ] Update `dashboard_service.py`

### Phase 5: API & Scheduler
- [ ] Create `backend/api/sync.py`
- [ ] Create `backend/sync/scheduler.py`
- [ ] Update `backend/main.py` with lifespan

### Phase 6: TUI Updates
- [ ] Add sync status indicator
- [ ] Wire reload buttons to `/sync/trigger`

---

## 10. Performance Expectations

| Operation | Expected Time |
|-----------|---------------|
| Database query (simple) | < 10ms |
| Database query (complex) | < 50ms |
| API endpoint response | < 100ms |
| Initial full sync | 30-60 seconds |
| Incremental sync | 5-15 seconds |

---

End of `Database_Syncing_information.md`
