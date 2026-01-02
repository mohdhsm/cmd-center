"""Read helpers for the SQLite cache to support fast TUI loads."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlmodel import Session, select, func

from ..db import engine, Pipeline, Stage, Deal, Note, Activity, File, Comment, SyncMetadata
from ..constants import PIPELINE_NAME_TO_ID

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

def get_open_deals_for_pipeline(pipeline_name: str) -> List[Deal]:
    """Get all open deals for a pipeline by name."""
    pipeline_id = PIPELINE_NAME_TO_ID.get(pipeline_name)
    if not pipeline_id:
        return []
    with Session(engine) as session:
        stmt = select(Deal).where(Deal.pipeline_id == pipeline_id).where(Deal.status == "open")
        return list(session.exec(stmt).all())


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


def get_overdue_deals_for_pipeline(pipeline_name: str, min_days: int = 7) -> List[Deal]:
    """
    Get deals that haven't been updated in `min_days` days.
    
    "Overdue" = update_time is older than the threshold.
    """
    pipeline_id = PIPELINE_NAME_TO_ID.get(pipeline_name)
    if not pipeline_id:
        return []
    cutoff = datetime.utcnow() - timedelta(days=min_days)
    with Session(engine) as session:
        stmt = (
            select(Deal)
            .where(Deal.pipeline_id == pipeline_id)
            .where(Deal.status == "open")
            .where(Deal.update_time < cutoff)
            .order_by(Deal.update_time)
        )
        return list(session.exec(stmt).all())


def get_stuck_deals_for_pipeline(pipeline_name: str, min_days: int = 30) -> List[Deal]:
    """
    Get deals that have been in the same stage for `min_days` days.
    
    Uses stage_change_time if available, otherwise falls back to update_time.
    """
    pipeline_id = PIPELINE_NAME_TO_ID.get(pipeline_name)
    if not pipeline_id:
        return []
    cutoff = datetime.utcnow() - timedelta(days=min_days)
    with Session(engine) as session:
        stmt = (
            select(Deal)
            .where(Deal.pipeline_id == pipeline_id)
            .where(Deal.status == "open")
            .where(
                # Prefer stage_change_time, fallback to update_time
                func.coalesce(Deal.stage_change_time, Deal.update_time) < cutoff
            )
            .order_by(func.coalesce(Deal.stage_change_time, Deal.update_time))
        )
        return list(session.exec(stmt).all())


def get_deals_by_stage(
    pipeline_id: int,
    stage_name: str,
    min_days_in_stage: int = 0
) -> list[Deal]:
    """Get deals in a specific stage, optionally filtered by days in stage."""
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

def get_notes_for_deal(deal_id: int, limit: int) -> list[Note]:
    """Get all notes for a deal, ordered by date."""
    with Session(engine) as session:
        return list(session.exec(
            select(Note)
            .where(Note.deal_id == deal_id)
            .order_by(Note.add_time)
            .limit(limit)
        ).all())

# =============================================================================
# Activity Queries
# =============================================================================

def get_activities_for_deal(deal_id: int) -> list[Activity]:
    """Get all activities for a deal, ordered by date."""
    with Session(engine) as session:
        return list(session.exec(
            select(Activity)
            .where(Activity.deal_id == deal_id)
            .where(Activity.active_flag == True)
            .order_by(Activity.add_time)
        ).all())


def get_pending_activities_for_deal(deal_id: int) -> list[Activity]:
    """Get pending (not done) activities for a deal."""
    with Session(engine) as session:
        return list(session.exec(
            select(Activity)
            .where(Activity.deal_id == deal_id)
            .where(Activity.active_flag == True)
            .where(Activity.done == False)
            .order_by(Activity.due_date)
        ).all())


# =============================================================================
# File Queries
# =============================================================================

def get_files_for_deal(deal_id: int) -> list[File]:
    """Get all files for a deal."""
    with Session(engine) as session:
        return list(session.exec(
            select(File)
            .where(File.deal_id == deal_id)
            .where(File.active_flag == True)
            .order_by(File.add_time)
        ).all())


# =============================================================================
# Comment Queries
# =============================================================================

def get_comments_for_object(object_id: int, object_type: str) -> list[Comment]:
    """Get all comments for a specific object (deal, activity, etc.)."""
    with Session(engine) as session:
        return list(session.exec(
            select(Comment)
            .where(Comment.object_id == object_id)
            .where(Comment.object_type == object_type)
            .where(Comment.active_flag == True)
            .order_by(Comment.add_time)
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
        if meta:
            dt = meta.last_sync_time
            if dt.tzinfo is None:
                # Naive datetime from DB, treat as UTC
                return dt.replace(tzinfo=timezone.utc)
            else:
                # Already aware, normalize to UTC
                return dt.astimezone(timezone.utc)
        return None


# =============================================================================
# Stage History Queries
# =============================================================================

def get_stage_spans_for_deal(deal_id: int):
    """Get all stage spans for a deal, ordered chronologically."""
    from ..db import DealStageSpan
    with Session(engine) as session:
        return list(session.exec(
            select(DealStageSpan)
            .where(DealStageSpan.deal_id == deal_id)
            .order_by(DealStageSpan.entered_at)
        ).all())


def get_current_stage_span(deal_id: int):
    """Get the current open stage span for a deal."""
    from ..db import DealStageSpan
    with Session(engine) as session:
        return session.exec(
            select(DealStageSpan)
            .where(
                DealStageSpan.deal_id == deal_id,
                DealStageSpan.left_at == None
            )
        ).first()


def get_deals_stuck_in_stage(
    stage_id: int,
    min_hours: int = 168  # 7 days default
):
    """Get deals stuck in a specific stage for more than min_hours.

    Returns list of (Deal, DealStageSpan) tuples.
    """
    from ..db import DealStageSpan
    cutoff = datetime.now(timezone.utc) - timedelta(hours=min_hours)

    with Session(engine) as session:
        stmt = (
            select(Deal, DealStageSpan)
            .join(DealStageSpan, Deal.id == DealStageSpan.deal_id)
            .where(
                DealStageSpan.stage_id == stage_id,
                DealStageSpan.left_at == None,  # Currently in stage
                DealStageSpan.entered_at < cutoff
            )
            .order_by(DealStageSpan.entered_at)
        )
        return list(session.exec(stmt).all())


def get_stage_duration_stats(stage_id: int, days: int = 90) -> dict:
    """Get duration statistics for a stage over last N days.

    Returns:
        {
            'avg_hours': float,
            'median_hours': float,
            'min_hours': float,
            'max_hours': float,
            'total_transitions': int
        }
    """
    from ..db import DealStageSpan
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    with Session(engine) as session:
        spans = session.exec(
            select(DealStageSpan)
            .where(
                DealStageSpan.stage_id == stage_id,
                DealStageSpan.entered_at >= cutoff,
                DealStageSpan.duration_hours != None
            )
        ).all()

        if not spans:
            return {
                'avg_hours': 0,
                'median_hours': 0,
                'min_hours': 0,
                'max_hours': 0,
                'total_transitions': 0
            }

        durations = sorted([s.duration_hours for s in spans if s.duration_hours])

        return {
            'avg_hours': sum(durations) / len(durations),
            'median_hours': durations[len(durations) // 2],
            'min_hours': min(durations),
            'max_hours': max(durations),
            'total_transitions': len(durations)
        }


def get_deal_change_events(
    deal_id: int,
    field_keys: Optional[list[str]] = None
):
    """Get raw change events for a deal, optionally filtered by field.

    Args:
        deal_id: Deal ID
        field_keys: Optional list of field keys to filter (e.g., ["stage_id", "value"])
    """
    from ..db import DealChangeEvent
    with Session(engine) as session:
        stmt = select(DealChangeEvent).where(DealChangeEvent.deal_id == deal_id)

        if field_keys:
            stmt = stmt.where(DealChangeEvent.field_key.in_(field_keys))

        stmt = stmt.order_by(DealChangeEvent.log_time)

        return list(session.exec(stmt).all())


__all__ = [
    "get_pipeline_by_name",
    "get_stage_by_id",
    "get_stages_for_pipeline",
    "get_open_deals_for_pipeline",
    "get_deals_for_pipeline",
    "get_overdue_deals_for_pipeline",
    "get_stuck_deals_for_pipeline",
    "get_deals_by_stage",
    "get_deals_by_owner",
    "get_deal_by_id",
    "get_deals_near_invoicing",
    "search_deals",
    "get_notes_for_deal",
    "get_activities_for_deal",
    "get_pending_activities_for_deal",
    "get_files_for_deal",
    "get_comments_for_object",
    "get_deal_counts_by_owner",
    "get_deal_value_by_owner",
    "get_sync_status",
    "get_last_sync_time",
    "get_stage_spans_for_deal",
    "get_current_stage_span",
    "get_deals_stuck_in_stage",
    "get_stage_duration_stats",
    "get_deal_change_events",
]
