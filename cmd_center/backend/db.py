"""SQLite cache setup and SQLModel tables for Pipedrive data."""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field, create_engine, Index

# SQLite cache file; adjust path if needed
engine = create_engine("sqlite:///pipedrive_cache.db", echo=False, connect_args={"check_same_thread": False})

# Pipeline saving
class Pipeline(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    order_nr: int
    is_deleted: bool = False
    is_deal_probability_enabled: bool = False
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class Stage(SQLModel, table=True):
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


# this for the deal
class Deal(SQLModel, table=True):
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
    next_activity_date: Optional[datetime] = None
    next_activity_id: Optional[int] = None
    lost_reason: Optional[str] = None
    close_time: Optional[datetime] = None
    won_time: Optional[datetime] = None
    lost_time: Optional[datetime] = None
    file_count: int = 0
    notes_count: int = 0
    email_messages_count: int = 0
    activities_count: int = 0
    done_activities_count: int = 0
    last_incoming_mail_time: Optional[datetime] = None
    last_outgoing_mail_time: Optional[datetime] = None
    
    # Store full JSON for debugging or accessing unmapped fields
    raw_json: Optional[str] = None


class Note(SQLModel, table=True):
    """Deal note for LLM analysis."""
    id: int = Field(primary_key=True)
    deal_id: int = Field(index=True)
    active_flag: bool = True
    user_name: Optional[str] = None
    user_id: Optional[int] = None
    content: str
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    lead_id: Optional[int] = None


class Activity(SQLModel, table=True):
    """Deal activity record from pipedrive for LLM analysis and view"""
    id: int = Field(primary_key=True)
    deal_id: int = Field(index=True)
    active_flag: bool = True
    user_name: Optional[str] = None
    owner_id: Optional[int] = None
    subject: Optional[str] = None
    activity_type: Optional[str] = None
    note: Optional[str] = None
    due_date: Optional[datetime] = None
    due_time: Optional[str] = None
    done: bool = False
    mark_as_done_time: Optional[datetime] = None
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    lead_id: Optional[int] = None


class File(SQLModel, table=True):
    """Deal file for LLM analysis and to download."""
    id: int = Field(primary_key=True)
    deal_id: int = Field(index=True)
    user_id: Optional[int] = None
    activity_id: Optional[int] = None
    person_id: Optional[int] = None
    org_id: Optional[int] = None
    lead_id: Optional[str] = None
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    file_url: Optional[str] = None
    file_nickname: Optional[str] = None
    remote_location: Optional[str] = None
    remote_id: Optional[str] = None
    active_flag: bool = True
    deal_name: Optional[str] = None


class Comment(SQLModel, table=True):
    """Deal comment record for LLM analysis from pipedrive."""
    id: int = Field(primary_key=True)
    active_flag: bool = True
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    content: Optional[str] = None
    object_id: Optional[int] = None
    object_type: Optional[str] = None
    updater_id: Optional[int] = None
    user_id: Optional[int] = None


class SyncMetadata(SQLModel, table=True):
    """Tracks sync state for incremental updates."""
    __tablename__ = "sync_metadata"

    id: Optional[int] = Field(default=None, primary_key=True)
    entity_type: str = Field(unique=True)
    last_sync_time: datetime
    last_sync_duration_ms: int = 0
    records_synced: int = 0
    records_total: int = 0
    status: str = "success"  # "success", "failed", "in_progress"
    error_message: Optional[str] = None


class DealChangeEvent(SQLModel, table=True):
    """Raw deal change event from Pipedrive flow API."""
    __tablename__ = "deal_change_event"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Event identification
    pipedrive_event_id: int = Field(index=True)  # data.id from Pipedrive
    deal_id: int = Field(index=True, foreign_key="deal.id")

    # Event metadata
    timestamp: datetime = Field(index=True)  # object.timestamp
    log_time: datetime = Field(index=True)  # data.log_time

    # Change details
    field_key: str = Field(index=True)  # e.g., "stage_id", "stage_change_time"
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    # Context
    user_id: Optional[int] = None
    change_source: Optional[str] = None  # "app", "api", etc.
    origin: Optional[str] = None

    # Raw data for future extensibility
    raw_json: str  # Full JSON for unmapped fields

    # Sync tracking
    synced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DealStageSpan(SQLModel, table=True):
    """Derived table: time spent in each stage."""
    __tablename__ = "deal_stage_span"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Identification
    deal_id: int = Field(index=True, foreign_key="deal.id")
    stage_id: int = Field(index=True, foreign_key="stage.id")

    # Timeline
    entered_at: datetime = Field(index=True)
    left_at: Optional[datetime] = Field(default=None, index=True)  # NULL if currently in stage

    # Computed metrics
    duration_hours: Optional[float] = None  # Auto-computed on insert/update

    # Context
    from_stage_id: Optional[int] = Field(default=None, foreign_key="stage.id")  # Previous stage
    next_stage_id: Optional[int] = Field(default=None, foreign_key="stage.id")  # Next stage (NULL if still in)

    # Transition metadata
    transition_user_id: Optional[int] = None
    transition_source: Optional[str] = None  # "app", "api"

    # Sync tracking
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


# ============================================================================
# CEO Dashboard - New Feature Tables
# ============================================================================

class Employee(SQLModel, table=True):
    """Employee directory - foundation for people features.

    Links to Pipedrive via pipedrive_owner_id for deal associations.
    Supports organizational hierarchy via reports_to_employee_id.
    """
    __tablename__ = "employee"

    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str = Field(index=True)
    role_title: str
    department: Optional[str] = Field(default=None, index=True)

    # Organizational hierarchy
    reports_to_employee_id: Optional[int] = Field(
        default=None,
        foreign_key="employee.id"
    )

    # Contact information
    email: Optional[str] = None
    phone: Optional[str] = None

    # Status
    is_active: bool = Field(default=True, index=True)

    # Pipedrive integration - links to deal.owner_id
    pipedrive_owner_id: Optional[int] = Field(default=None, index=True)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class Intervention(SQLModel, table=True):
    """Audit log / flight recorder for all system events.

    Every significant action in the system should create an intervention record.
    This provides a complete audit trail for debugging, compliance, and analytics.
    """
    __tablename__ = "intervention"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )

    # Who performed the action
    actor: str = Field(index=True)  # User name, email, or "system"

    # What object was affected
    object_type: str = Field(index=True)  # "employee", "task", "note", "deal", etc.
    object_id: int = Field(index=True)

    # What action was taken
    action_type: str = Field(index=True)  # See ActionType enum in constants.py

    # Result of the action
    status: str = Field(default="done", index=True)  # "done", "failed", "planned"

    # Human-readable summary
    summary: str

    # Additional structured data (JSON)
    details_json: Optional[str] = None


class Reminder(SQLModel, table=True):
    """Unified reminder system for all target types.

    Supports reminders for tasks, notes, documents, bonuses, and any future
    entity types. Channels include in-app notifications and email.
    """
    __tablename__ = "reminder"

    id: Optional[int] = Field(default=None, primary_key=True)

    # What entity this reminder is for
    target_type: str = Field(index=True)  # "task", "note", "document", "bonus", etc.
    target_id: int = Field(index=True)

    # When to remind
    remind_at: datetime = Field(index=True)

    # How to notify
    channel: str = Field(default="in_app", index=True)  # "in_app", "email"

    # Reminder content
    message: Optional[str] = None

    # Lifecycle status
    status: str = Field(default="pending", index=True)  # "pending", "sent", "dismissed", "failed", "cancelled"
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None

    # Recurring support (future)
    is_recurring: bool = Field(default=False)
    recurrence_rule: Optional[str] = None  # iCal RRULE format for recurring

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


def init_db() -> None:
    """Create tables if they do not exist."""
    SQLModel.metadata.create_all(engine)


__all__ = [
    "engine",
    "init_db",
    # Pipedrive-synced tables
    "Pipeline",
    "Stage",
    "Deal",
    "Note",
    "Activity",
    "File",
    "Comment",
    "SyncMetadata",
    "DealChangeEvent",
    "DealStageSpan",
    # CEO Dashboard tables
    "Employee",
    "Intervention",
    "Reminder",
]
