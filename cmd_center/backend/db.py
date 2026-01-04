"""SQLite cache setup and SQLModel tables for Pipedrive data."""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field, create_engine, Index

# Import agent persistence models so they're registered with SQLModel.metadata
from cmd_center.agent.persistence.models import AgentConversation, AgentMessage

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


class Task(SQLModel, table=True):
    """Task management for CEO dashboard.

    Tasks can be linked to any entity (deal, employee, etc.) via target_type/target_id.
    Supports assignment to employees and integration with the reminder system.
    """
    __tablename__ = "task"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Task content
    title: str = Field(index=True)
    description: Optional[str] = None

    # Assignment
    assignee_employee_id: Optional[int] = Field(
        default=None,
        foreign_key="employee.id",
        index=True
    )
    created_by: Optional[str] = None  # Actor who created the task

    # Status and priority
    status: str = Field(default="open", index=True)  # open, in_progress, done, cancelled
    priority: str = Field(default="medium", index=True)  # low, medium, high
    is_critical: bool = Field(default=False, index=True)

    # Timeline
    due_at: Optional[datetime] = Field(default=None, index=True)
    completed_at: Optional[datetime] = None

    # Entity linking (optional - task can be standalone or linked)
    target_type: Optional[str] = Field(default=None, index=True)
    target_id: Optional[int] = Field(default=None, index=True)

    # Archival
    is_archived: bool = Field(default=False, index=True)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class InternalNote(SQLModel, table=True):
    """Internal notes for any entity.

    Notes can be linked to deals, employees, tasks, or any other entity.
    Supports pinning, tagging, and review reminders.
    """
    __tablename__ = "internal_note"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Note content
    content: str

    # Author
    created_by: Optional[str] = None  # Actor who created the note

    # Entity linking (optional - note can be standalone or linked)
    target_type: Optional[str] = Field(default=None, index=True)
    target_id: Optional[int] = Field(default=None, index=True)

    # Review reminder
    review_at: Optional[datetime] = Field(default=None, index=True)

    # Organization
    pinned: bool = Field(default=False, index=True)
    tags: Optional[str] = None  # Comma-separated tags

    # Archival
    is_archived: bool = Field(default=False, index=True)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


# ============================================================================
# Tracker Module - Phase 4 Tables
# ============================================================================

class LegalDocument(SQLModel, table=True):
    """Legal document tracking for compliance.

    Tracks documents like Commercial Registration, licenses, contracts, etc.
    with expiry dates and renewal workflows.
    """
    __tablename__ = "legal_document"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Document info
    title: str = Field(index=True)
    document_type: str = Field(index=True)  # CR, license, contract, etc.
    description: Optional[str] = None

    # Validity
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = Field(default=None, index=True)

    # Status
    status: str = Field(default="active", index=True)  # active, expired, renewal_in_progress, renewed

    # Reference
    reference_number: Optional[str] = None
    issuing_authority: Optional[str] = None

    # Ownership
    responsible_employee_id: Optional[int] = Field(
        default=None,
        foreign_key="employee.id",
        index=True
    )

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class LegalDocumentFile(SQLModel, table=True):
    """File attachments for legal documents."""
    __tablename__ = "legal_document_file"

    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="legal_document.id", index=True)

    # File info
    filename: str
    file_path: str  # Storage path
    file_type: Optional[str] = None  # MIME type
    file_size: Optional[int] = None  # Bytes

    # Version tracking
    version: int = Field(default=1)
    is_current: bool = Field(default=True, index=True)

    # Upload info
    uploaded_by: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmployeeBonus(SQLModel, table=True):
    """Bonus tracking for employees.

    Tracks promised bonuses, their conditions, and payment status.
    """
    __tablename__ = "employee_bonus"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Who
    employee_id: int = Field(foreign_key="employee.id", index=True)

    # What
    title: str
    description: Optional[str] = None
    amount: float
    currency: str = Field(default="SAR")

    # Type and conditions
    bonus_type: str = Field(default="performance", index=True)  # performance, project, annual, other
    conditions: Optional[str] = None  # Conditions for earning the bonus

    # Timeline
    promised_date: datetime = Field(index=True)
    due_date: Optional[datetime] = Field(default=None, index=True)

    # Status
    status: str = Field(default="promised", index=True)  # promised, approved, partial, paid, cancelled

    # Approval
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class EmployeeBonusPayment(SQLModel, table=True):
    """Payment records for bonuses (supports partial payments)."""
    __tablename__ = "employee_bonus_payment"

    id: Optional[int] = Field(default=None, primary_key=True)
    bonus_id: int = Field(foreign_key="employee_bonus.id", index=True)

    # Payment info
    amount: float
    payment_date: datetime = Field(index=True)
    payment_method: Optional[str] = None  # bank_transfer, cash, etc.
    reference: Optional[str] = None  # Transaction reference

    # Who recorded it
    recorded_by: Optional[str] = None
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmployeeLogEntry(SQLModel, table=True):
    """Activity log entries for employees.

    Tracks achievements, issues, feedback, and other notable events.
    """
    __tablename__ = "employee_log_entry"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Who
    employee_id: int = Field(foreign_key="employee.id", index=True)

    # What
    category: str = Field(index=True)  # achievement, issue, feedback, milestone, other
    title: str
    content: str

    # Context
    severity: Optional[str] = None  # For issues: low, medium, high
    is_positive: bool = Field(default=True)  # Quick indicator

    # Who logged it
    logged_by: Optional[str] = None

    # Timestamps
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Skill(SQLModel, table=True):
    """Skill definitions for employee competency tracking."""
    __tablename__ = "skill"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Skill info
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    category: Optional[str] = Field(default=None, index=True)  # technical, soft, domain, etc.

    # Active/inactive
    is_active: bool = Field(default=True, index=True)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmployeeSkillRating(SQLModel, table=True):
    """Skill ratings for employees (tracks history)."""
    __tablename__ = "employee_skill_rating"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Who and what
    employee_id: int = Field(foreign_key="employee.id", index=True)
    skill_id: int = Field(foreign_key="skill.id", index=True)

    # Rating (1-5 scale)
    rating: int = Field(ge=1, le=5)
    notes: Optional[str] = None

    # Who rated
    rated_by: Optional[str] = None

    # Timestamps
    rated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)


# ============================================================================
# Loop Engine Tables
# ============================================================================

class LoopRun(SQLModel, table=True):
    """Tracks execution of monitoring loops."""
    __tablename__ = "loop_run"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Loop identification
    loop_name: str = Field(index=True)

    # Execution timing
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    finished_at: Optional[datetime] = None

    # Status: running, completed, failed
    status: str = Field(default="running", index=True)

    # Results
    findings_count: int = Field(default=0)
    error_message: Optional[str] = None


class LoopFinding(SQLModel, table=True):
    """Findings/alerts generated by monitoring loops."""
    __tablename__ = "loop_finding"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Link to loop run
    loop_run_id: int = Field(foreign_key="loop_run.id", index=True)

    # Severity: info, warning, critical
    severity: str = Field(index=True)

    # What was found
    target_type: str = Field(index=True)  # document, bonus, task, etc.
    target_id: int
    message: str
    recommended_action: Optional[str] = None

    # Deduplication signature (hash of key fields)
    signature: Optional[str] = Field(default=None, index=True)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================================
# Email Cache Tables (Microsoft Graph)
# ============================================================================

class CachedEmail(SQLModel, table=True):
    """Cached email from Microsoft Graph for fast local reads."""
    __tablename__ = "cached_email"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Graph identification
    graph_id: str = Field(index=True)  # MS Graph message ID
    mailbox: str = Field(index=True)  # Which mailbox this belongs to

    # Folder
    folder_id: Optional[str] = Field(default=None, index=True)

    # Content
    subject: Optional[str] = Field(default=None, index=True)
    body_preview: str = ""
    body_content: Optional[str] = None
    body_type: Optional[str] = None  # "text" or "html"

    # Sender
    sender_address: Optional[str] = Field(default=None, index=True)
    sender_name: Optional[str] = None

    # Recipients (JSON arrays)
    to_recipients_json: Optional[str] = None
    cc_recipients_json: Optional[str] = None

    # Timestamps
    received_at: Optional[datetime] = Field(default=None, index=True)
    sent_at: Optional[datetime] = None

    # Flags
    is_read: bool = Field(default=False, index=True)
    has_attachments: bool = Field(default=False, index=True)
    importance: str = Field(default="normal")
    is_draft: bool = Field(default=False)

    # Graph metadata
    conversation_id: Optional[str] = Field(default=None, index=True)
    web_link: Optional[str] = None

    # Sync tracking
    synced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    graph_modified_at: Optional[datetime] = None  # From Graph API

    # Composite unique constraint via __table_args__
    __table_args__ = (
        Index("ix_cached_email_graph_mailbox", "graph_id", "mailbox", unique=True),
    )


class CachedEmailAttachment(SQLModel, table=True):
    """Cached email attachment metadata (not content)."""
    __tablename__ = "cached_email_attachment"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Graph identification
    graph_id: str = Field(index=True)  # MS Graph attachment ID
    email_graph_id: str = Field(index=True)  # Parent email's Graph ID
    mailbox: str = Field(index=True)

    # Metadata
    name: str
    content_type: str = "application/octet-stream"
    size: int = 0
    is_inline: bool = False

    # Sync tracking
    synced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_cached_email_attachment_graph_mailbox", "graph_id", "mailbox", unique=True),
    )


class CachedMailFolder(SQLModel, table=True):
    """Cached mail folder metadata."""
    __tablename__ = "cached_mail_folder"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Graph identification
    graph_id: str = Field(index=True)
    mailbox: str = Field(index=True)

    # Folder info
    display_name: str = Field(index=True)
    parent_folder_id: Optional[str] = None
    child_folder_count: int = 0

    # Counts
    unread_count: int = 0
    total_count: int = 0

    # Sync tracking
    synced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_cached_mail_folder_graph_mailbox", "graph_id", "mailbox", unique=True),
    )


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
    "Task",
    "InternalNote",
    # Tracker Module tables
    "LegalDocument",
    "LegalDocumentFile",
    "EmployeeBonus",
    "EmployeeBonusPayment",
    "EmployeeLogEntry",
    "Skill",
    "EmployeeSkillRating",
    # Loop Engine tables
    "LoopRun",
    "LoopFinding",
    # Email Cache tables
    "CachedEmail",
    "CachedEmailAttachment",
    "CachedMailFolder",
    # Agent Persistence tables
    "AgentConversation",
    "AgentMessage",
]
