"""Sync Pipedrive data into the local SQLite cache."""

import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

import httpx
from sqlmodel import Session, select

from ..integrations.config import get_config
from ..db import engine, Pipeline, Stage, Deal, Note, SyncMetadata
from ..constants import SYNC_PIPELINES


class PipedriveSyncError(Exception):
    """Raised when sync cannot proceed (e.g., missing token)."""


def _get_token_and_base() -> tuple[str, str]:
    config = get_config()
    token = config.pipedrive_api_token
    if not token:
        raise PipedriveSyncError("pipedrive_api_token missing; set it in .env")
    return token, config.pipedrive_api_url


async def _pd_get(client: httpx.AsyncClient, path: str, token: str, base_url: str, **params) -> Dict[str, Any]:
    params["api_token"] = token
    res = await client.get(f"{base_url}/{path}", params=params, timeout=30.0)
    res.raise_for_status()
    return res.json()


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
            dt = meta.last_sync_time
            if dt.tzinfo is None:
                # Naive datetime from DB, treat as UTC
                return dt.replace(tzinfo=timezone.utc)
            else:
                # Already aware, normalize to UTC
                return dt.astimezone(timezone.utc)
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

async def sync_pipelines() -> int:
    """Sync all pipelines from Pipedrive."""
    start_time = datetime.now()
    
    try:
        token, base_url = _get_token_and_base()
        async with httpx.AsyncClient() as client:
            payload = await _pd_get(client, "pipelines", token, base_url)
        
        items = payload.get("data") or []
        
        with Session(engine) as session:
            for p in items:
                pipeline = Pipeline(
                    id=p["id"],
                    name=p["name"],
                    order_nr=p["order_nr"],
                    is_deleted=p.get("is_deleted", False),
                    is_deal_probability_enabled=p.get("is_deal_probability_enabled", False),
                    add_time=_parse_datetime(p.get("add_time")),
                    update_time=_parse_datetime(p.get("update_time")),
                )
                session.merge(pipeline)
            session.commit()
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        update_sync_metadata("pipelines", "success", len(items), len(items), duration_ms)
        
        return len(items)
    
    except Exception as e:
        update_sync_metadata("pipelines", "failed", error_message=str(e))
        raise


async def sync_stages(pipeline_id: Optional[int] = None) -> int:
    """Sync all stages from Pipedrive."""
    start_time = datetime.now()
    
    try:
        token, base_url = _get_token_and_base()
        params: Dict[str, Any] = {}
        if pipeline_id:
            params["pipeline_id"] = pipeline_id

        async with httpx.AsyncClient() as client:
            payload = await _pd_get(client, "stages", token, base_url, **params)
        
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
                    add_time=_parse_datetime(s.get("add_time")),
                    update_time=_parse_datetime(s.get("update_time")),
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
) -> tuple[int, int]:
    """
    Sync deals for a specific pipeline.
    
    Args:
        pipeline_id: Pipedrive pipeline ID
        status: Deal status filter ("open", "won", "lost", "all_not_deleted")
        incremental: If True, only upsert deals updated since last sync
    
    Returns:
        Tuple of (records_synced, records_total)
    """
    entity_type = f"deals_{pipeline_id}"
    start_time = datetime.now()
    last_sync = get_last_sync_time(entity_type) if incremental else None
    
    try:
        token, base_url = _get_token_and_base()
        
        # Fetch all deals (Pipedrive doesn't support modified_since filter)
        all_deals: List[Dict[str, Any]] = []
        start = 0
        limit = 500
        
        async with httpx.AsyncClient() as client:
            while True:
                payload = await _pd_get(
                    client,
                    "deals",
                    token,
                    base_url,
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
                if _parse_datetime(d.get("update_time")) and _parse_datetime(d.get("update_time")) > last_sync
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
                    add_time=_parse_datetime(d.get("add_time")),
                    update_time=_parse_datetime(d.get("update_time")),
                    stage_change_time=_parse_datetime(d.get("stage_change_time")),
                    expected_close_date=_parse_datetime(d.get("expected_close_date")),
                    last_activity_date=_parse_datetime(d.get("last_activity_date")),
                    next_activity_date=_parse_datetime(d.get("next_activity_date")),
                    next_activity_id=d.get("next_activity_id"),
                    lost_reason=d.get("lost_reason"),
                    close_time=_parse_datetime(d.get("close_time")),
                    won_time=_parse_datetime(d.get("won_time")),
                    lost_time=_parse_datetime(d.get("lost_time")),
                    file_count=d.get("files_count", 0),
                    notes_count=d.get("notes_count", 0),
                    email_messages_count=d.get("email_messages_count", 0),
                    activities_count=d.get("activities_count", 0),
                    done_activities_count=d.get("done_activities_count", 0),
                    last_incoming_mail_time=_parse_datetime(d.get("last_incoming_mail_time")),
                    last_outgoing_mail_time=_parse_datetime(d.get("last_outgoing_mail_time")),
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


async def sync_notes_for_deal(deal_id: int) -> int:
    """
    Sync notes for a specific deal.
    
    Called on-demand when viewing deal details (not bulk synced).
    """
    entity_type = f"notes_{deal_id}"
    start_time = datetime.now()
    
    try:
        token, base_url = _get_token_and_base()
        async with httpx.AsyncClient() as client:
            payload = await _pd_get(client, "notes", token, base_url, deal_id=deal_id)
        
        items = payload.get("data") or []
        
        with Session(engine) as session:
            for n in items:
                user = n.get("user") or {}
                note = Note(
                    id=n["id"],
                    deal_id=n.get("deal_id"),
                    active_flag=n.get("active_flag", True),
                    user_name=user.get("name") if isinstance(user, dict) else None,
                    user_id=user.get("id") if isinstance(user, dict) else None,
                    content=n.get("content", ""),
                    add_time=_parse_datetime(n.get("add_time")),
                    update_time=_parse_datetime(n.get("update_time")),
                    lead_id=n.get("lead_id"),
                )
                session.merge(note)
            session.commit()
        
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        update_sync_metadata(entity_type, "success", len(items), len(items), duration_ms)
        
        return len(items)
    
    except Exception as e:
        update_sync_metadata(entity_type, "failed", error_message=str(e))
        raise


async def sync_notes_for_open_deals(limit_per_deal: int = 5, ttl_minutes: int = 30, concurrency: int = 8) -> dict:
    """Sync the most recent notes for open deals in specified pipelines."""
    # 1. Query pipelines
    with Session(engine) as session:
        pipelines = session.exec(
            select(Pipeline).where(Pipeline.name.in_(["Aramco Projects", "PIPELINE"]))
        ).all()
        pipeline_dict = {"Aramco Projects": None, "PIPELINE": None}
        for p in pipelines:
            pipeline_dict[p.name] = p.id
        pipeline_ids = [pid for pid in pipeline_dict.values() if pid is not None]
        pipeline_id_to_name = {id: name for name, id in pipeline_dict.items() if id is not None}

    # 2. If no pipelines, return early
    if not pipeline_ids:
        return {
            "pipelines": pipeline_dict,
            "eligible_open_deals": 0,
            "synced_deals": 0,
            "skipped_fresh": 0,
            "errors": [{"error": "No target pipelines found", "pipelines": pipeline_dict}]
        }

    # 3. Query open deals
    with Session(engine) as session:
        deals = session.exec(
            select(Deal).where(
                Deal.status == "open",
                Deal.pipeline_id.in_(pipeline_ids)
            )
        ).all()

    eligible_open_deals = len(deals)

    # 4. Determine stale deals
    stale_deals = []
    for deal in deals:
        entity_type = f"notes_{deal.id}"
        last_sync = get_last_sync_time(entity_type)
        if last_sync is None or (datetime.now(timezone.utc) - last_sync).total_seconds() / 60 > ttl_minutes:
            stale_deals.append(deal)

    skipped_fresh = eligible_open_deals - len(stale_deals)

    # 5. Prepare shared resources
    token, base_url = _get_token_and_base()
    sort_value = "add_time DESC"
    semaphore = asyncio.Semaphore(concurrency)

    # 6. Wrap in async with httpx.AsyncClient() as client:
    async with httpx.AsyncClient() as client:
        # 7. Define sync_one_deal
        async def sync_one_deal(deal) -> dict:
            async with semaphore:
                try:
                    start_time = datetime.now()
                    # Use GET /v1/notes with deal_id, start=0, limit=limit_per_deal, sort="add_time DESC" (sort supports add_time per docs)
                    payload = await _pd_get(
                        client, "notes", token, base_url,
                        deal_id=deal.id, start=0, limit=limit_per_deal, sort=sort_value
                    )
                    items = payload.get("data") or []

                    # Upsert notes
                    with Session(engine) as session:
                        for n in items:
                            user = n.get("user") or {}
                            note = Note(
                                id=n["id"],
                                deal_id=n.get("deal_id"),
                                active_flag=n.get("active_flag", True),
                                user_name=user.get("name") if isinstance(user, dict) else None,
                                user_id=user.get("id") if isinstance(user, dict) else None,
                                content=n.get("content", ""),
                                add_time=_parse_datetime(n.get("add_time")),
                                update_time=_parse_datetime(n.get("update_time")),
                                lead_id=n.get("lead_id"),
                            )
                            session.merge(note)
                        session.commit()

                    duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                    update_sync_metadata(f"notes_{deal.id}", "success", len(items), len(items), duration_ms)
                    return {"deal_id": deal.id, "ok": True, "notes_synced": len(items)}
                except Exception as e:
                    update_sync_metadata(f"notes_{deal.id}", "failed", error_message=str(e))
                    return {
                        "deal_id": deal.id,
                        "ok": False,
                        "error": str(e),
                        "context": {
                            "pipeline_id": deal.pipeline_id,
                            "pipeline_name": pipeline_id_to_name.get(deal.pipeline_id),
                            "limit_per_deal": limit_per_deal,
                            "ttl_minutes": ttl_minutes,
                            "sort": sort_value,
                        }
                    }

        # 8. Run tasks
        results = await asyncio.gather(*(sync_one_deal(d) for d in stale_deals))

    # 9. Compute
    synced_deals = sum(1 for r in results if r["ok"])
    errors = [
        {
            "deal_id": r["deal_id"],
            "error": r["error"],
            **r.get("context", {})
        }
        for r in results if not r["ok"]
    ]

    # 10. Return
    return {
        "pipelines": pipeline_dict,
        "eligible_open_deals": eligible_open_deals,
        "synced_deals": synced_deals,
        "skipped_fresh": skipped_fresh,
        "errors": errors
    }


# =============================================================================
# Full Sync Functions
# =============================================================================

async def sync_all(incremental: bool = True):
    """
    Sync all entities from Pipedrive.
    
    Args:
        incremental: If True, only sync deals updated since last sync
    
    Returns:
        Dictionary with sync results
    """
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
    """Parse a datetime string from Pipedrive and ensure it's timezone-aware UTC."""
    if not value:
        return None
    if isinstance(value, datetime):
        # If already a datetime, ensure it's timezone-aware UTC
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        else:
            return value.astimezone(timezone.utc)
    try:
        # Pipedrive format: "2025-01-15 10:30:00"
        dt = datetime.fromisoformat(value.replace(" ", "T"))
        # Pipedrive times are typically UTC, ensure timezone-aware
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        else:
            return dt.astimezone(timezone.utc)
    except (ValueError, AttributeError):
        return None


def _test_timezone_handling():
    """Self-check function to verify timezone handling works correctly."""
    from datetime import datetime, timezone

    # Test 1: Simulate naive datetime from DB (get_last_sync_time logic)
    naive_dt = datetime(2023, 1, 1, 12, 0, 0)  # No tzinfo

    if naive_dt.tzinfo is None:
        aware_dt = naive_dt.replace(tzinfo=timezone.utc)
    else:
        aware_dt = naive_dt.astimezone(timezone.utc)

    assert aware_dt.tzinfo == timezone.utc, f"Expected UTC timezone, got {aware_dt.tzinfo}"

    now = datetime.now(timezone.utc)
    diff = now - aware_dt
    assert diff.total_seconds() > 0, "Subtraction should work with aware datetimes"

    # Test 2: Pipedrive datetime parsing
    pipedrive_time_str = "2025-01-15 10:30:00"
    parsed_dt = _parse_datetime(pipedrive_time_str)
    
    assert parsed_dt is not None, "Should parse valid datetime string"
    assert parsed_dt.tzinfo == timezone.utc, f"Parsed datetime should be UTC-aware, got {parsed_dt.tzinfo}"
    
    # Test comparison between parsed datetime and now (this is where the error occurred)
    comparison_result = parsed_dt > now  # Should not raise an error
    assert isinstance(comparison_result, bool), "Comparison should work without errors"

    print("Timezone handling test passed: DB conversion works, Pipedrive parsing works, comparisons succeed")


__all__ = [
    "sync_pipelines",
    "sync_stages",
    "sync_deals_for_pipeline",
    "sync_notes_for_deal",
    "sync_notes_for_open_deals",
    "sync_all",
    "full_sync",
    "PipedriveSyncError",
    "_test_timezone_handling",
]
