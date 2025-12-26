"""Shared constants for pipeline name/ID mappings and enums."""

from enum import Enum


# ============================================================================
# Target Types - Used for linking entities (tasks, notes, reminders, etc.)
# ============================================================================

class TargetType(str, Enum):
    """Valid target types for entity linking."""
    DEAL = "deal"
    EMPLOYEE = "employee"
    DEPARTMENT = "department"
    DOCUMENT = "document"
    WORKSHOP_PROJECT = "workshop_project"
    TASK = "task"
    NOTE = "note"
    BONUS = "bonus"
    GENERAL = "general"  # No specific target


# ============================================================================
# Reminder Enums
# ============================================================================

class ReminderStatus(str, Enum):
    """Reminder lifecycle statuses."""
    PENDING = "pending"
    SENT = "sent"
    DISMISSED = "dismissed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReminderChannel(str, Enum):
    """Available reminder notification channels."""
    IN_APP = "in_app"
    EMAIL = "email"


# ============================================================================
# Action Types - Used for intervention/audit logging
# ============================================================================

class ActionType(str, Enum):
    """Action types for intervention logging."""
    # Employee actions
    EMPLOYEE_CREATED = "employee_created"
    EMPLOYEE_UPDATED = "employee_updated"
    EMPLOYEE_DEACTIVATED = "employee_deactivated"

    # Task actions
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    TASK_CANCELLED = "task_cancelled"

    # Note actions
    NOTE_ADDED = "note_added"
    NOTE_UPDATED = "note_updated"
    NOTE_ARCHIVED = "note_archived"

    # Reminder actions
    REMINDER_CREATED = "reminder_created"
    REMINDER_SENT = "reminder_sent"
    REMINDER_DISMISSED = "reminder_dismissed"
    REMINDER_CANCELLED = "reminder_cancelled"
    REMINDER_FAILED = "reminder_failed"

    # Communication
    EMAIL_SENT = "email_sent"
    WHATSAPP_SENT = "whatsapp_sent"
    CALL_LOGGED = "call_logged"

    # Documents
    DOCUMENT_CREATED = "document_created"
    DOCUMENT_UPDATED = "document_updated"
    DOCUMENT_RENEWED = "document_renewed"
    DOCUMENT_EXPIRED = "document_expired"

    # Bonuses
    BONUS_PROMISED = "bonus_promised"
    BONUS_APPROVED = "bonus_approved"
    BONUS_PAID = "bonus_paid"
    BONUS_CANCELLED = "bonus_cancelled"

    # Employee logs
    EMPLOYEE_LOG_ADDED = "employee_log_added"
    SKILL_RATED = "skill_rated"

    # System/Loop actions
    LOOP_FINDING = "loop_finding"
    SYNC_COMPLETED = "sync_completed"
    SYNC_FAILED = "sync_failed"


# ============================================================================
# Pipeline Mappings
# ============================================================================

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
    from .db import Stage
    
    stage = session.exec(select(Stage).where(Stage.id == stage_id)).first()
    return stage.name if stage else "Unknown"


__all__ = [
    # Enums
    "TargetType",
    "ReminderStatus",
    "ReminderChannel",
    "ActionType",
    # Pipeline mappings
    "PIPELINE_NAME_TO_ID",
    "PIPELINE_ID_TO_NAME",
    "SYNC_PIPELINES",
    # Utility functions
    "build_stage_key_to_id",
    "get_stage_name",
]
