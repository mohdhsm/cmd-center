"""ActionExecutor for executing confirmed actions.

This service executes confirmed PendingActions and logs interventions
for audit purposes.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..tools.base import PendingAction, run_async
from ...backend.services.task_service import TaskService
from ...backend.services.note_service import NoteService
from ...backend.services.reminder_service import ReminderService
from ...backend.services.intervention_service import log_action
from ...backend.services.msgraph_email_service import get_msgraph_email_service
from ...backend.integrations.pipedrive_client import get_pipedrive_client
from ...backend.models.task_models import TaskCreate
from ...backend.models.note_models import NoteCreate
from ...backend.models.reminder_models import ReminderCreate
from ...backend.constants import ActionType

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Executes confirmed actions and logs interventions."""

    def __init__(self, actor: str = "omnious"):
        """Initialize executor with actor name.

        Args:
            actor: Name of the actor for audit logging (default: "omnious")
        """
        self.actor = actor

    def execute(self, action: PendingAction) -> Dict[str, Any]:
        """Execute a confirmed pending action.

        Dispatches to appropriate handler based on tool_name and logs
        intervention after successful execution.

        Args:
            action: The pending action to execute

        Returns:
            Dict with success status and optional result/error
        """
        handlers = {
            "request_create_task": self._execute_create_task,
            "request_create_note": self._execute_create_note,
            "request_create_reminder": self._execute_create_reminder,
            "request_send_email": self._execute_send_email,
            "request_update_deal": self._execute_update_deal,
            "request_add_deal_note": self._execute_add_deal_note,
        }

        handler = handlers.get(action.tool_name)
        if handler is None:
            return {
                "success": False,
                "error": f"Unknown/unsupported tool: {action.tool_name}",
            }

        try:
            return handler(action)
        except Exception as e:
            logger.exception(f"Error executing action {action.tool_name}")
            return {
                "success": False,
                "error": str(e),
            }

    def _execute_create_task(self, action: PendingAction) -> Dict[str, Any]:
        """Execute task creation."""
        payload = action.payload

        # Parse due_at if provided
        due_at = None
        if payload.get("due_at"):
            due_at = datetime.fromisoformat(payload["due_at"].replace("Z", "+00:00"))

        task_data = TaskCreate(
            title=payload["title"],
            description=payload.get("description"),
            priority=payload.get("priority", "medium"),
            assignee_employee_id=payload.get("assignee_employee_id"),
            due_at=due_at,
            target_type=payload.get("target_type"),
            target_id=payload.get("target_id"),
        )

        service = TaskService(actor=self.actor)
        result = service.create_task(task_data, actor=self.actor)

        # Log intervention for executor action
        log_action(
            actor=self.actor,
            object_type="task",
            object_id=result.id,
            action_type=ActionType.TASK_CREATED.value,
            summary=f"Agent created task: {payload['title']}",
            details={"payload": payload, "tool": action.tool_name},
        )

        logger.info(f"Executed create_task: {result.id}")

        return {
            "success": True,
            "result": {"task_id": result.id, "title": payload["title"]},
        }

    def _execute_create_note(self, action: PendingAction) -> Dict[str, Any]:
        """Execute note creation."""
        payload = action.payload

        note_data = NoteCreate(
            content=payload["content"],
            target_type=payload["target_type"],
            target_id=payload["target_id"],
            pinned=payload.get("pinned", False),
        )

        service = NoteService(actor=self.actor)
        result = service.create_note(note_data, actor=self.actor)

        # Log intervention
        log_action(
            actor=self.actor,
            object_type="note",
            object_id=result.id,
            action_type=ActionType.NOTE_ADDED.value,
            summary=f"Agent created note for {payload['target_type']}:{payload['target_id']}",
            details={"payload": payload, "tool": action.tool_name},
        )

        logger.info(f"Executed create_note: {result.id}")

        return {
            "success": True,
            "result": {"note_id": result.id},
        }

    def _execute_create_reminder(self, action: PendingAction) -> Dict[str, Any]:
        """Execute reminder creation."""
        payload = action.payload

        # Parse remind_at
        remind_at = datetime.fromisoformat(payload["remind_at"].replace("Z", "+00:00"))

        reminder_data = ReminderCreate(
            target_type=payload["target_type"],
            target_id=payload["target_id"],
            remind_at=remind_at,
            message=payload["message"],
            channel=payload.get("channel", "in_app"),
        )

        service = ReminderService(actor=self.actor)
        result = service.create_reminder(reminder_data, actor=self.actor)

        # Log intervention
        log_action(
            actor=self.actor,
            object_type="reminder",
            object_id=result.id,
            action_type=ActionType.REMINDER_CREATED.value,
            summary=f"Agent created reminder for {payload['target_type']}:{payload['target_id']}",
            details={"payload": payload, "tool": action.tool_name},
        )

        logger.info(f"Executed create_reminder: {result.id}")

        return {
            "success": True,
            "result": {"reminder_id": result.id},
        }

    def _execute_send_email(self, action: PendingAction) -> Dict[str, Any]:
        """Execute sending email."""
        payload = action.payload

        email_service = get_msgraph_email_service()

        # Prepare recipients
        to_recipients = [payload["to"]]
        cc_recipients = [payload["cc"]] if payload.get("cc") else None
        from_mailbox = payload.get("from_mailbox") or email_service.default_mailbox

        # Send email (async)
        success = run_async(email_service.send_email(
            from_mailbox=from_mailbox,
            to=to_recipients,
            subject=payload["subject"],
            body=payload["body"],
            cc=cc_recipients,
        ))

        if not success:
            return {
                "success": False,
                "error": "Failed to send email",
            }

        # Log intervention (we don't have a specific email ID, use 0)
        log_action(
            actor=self.actor,
            object_type="email",
            object_id=0,
            action_type=ActionType.EMAIL_SENT.value,
            summary=f"Agent sent email to {payload['to']}: {payload['subject']}",
            details={"payload": payload, "tool": action.tool_name},
        )

        logger.info(f"Executed send_email to {payload['to']}")

        return {
            "success": True,
            "result": {"sent_to": payload["to"], "subject": payload["subject"]},
        }

    def _execute_update_deal(self, action: PendingAction) -> Dict[str, Any]:
        """Execute Pipedrive deal update."""
        payload = action.payload

        client = get_pipedrive_client()

        # Update deal (async)
        result = run_async(client.update_deal(
            deal_id=payload["deal_id"],
            title=payload.get("title"),
            status=payload.get("status"),
            stage_id=payload.get("stage_id"),
            value=payload.get("value"),
        ))

        if result is None:
            return {
                "success": False,
                "error": "Failed to update deal",
            }

        # Log intervention
        log_action(
            actor=self.actor,
            object_type="deal",
            object_id=payload["deal_id"],
            action_type=ActionType.DEAL_UPDATED.value,
            summary=f"Agent updated deal {payload['deal_id']}",
            details={"payload": payload, "tool": action.tool_name},
        )

        logger.info(f"Executed update_deal: {payload['deal_id']}")

        return {
            "success": True,
            "result": {"deal_id": payload["deal_id"]},
        }

    def _execute_add_deal_note(self, action: PendingAction) -> Dict[str, Any]:
        """Execute adding note to Pipedrive deal."""
        payload = action.payload

        client = get_pipedrive_client()

        # Add note (async)
        result = run_async(client.add_deal_note(
            deal_id=payload["deal_id"],
            content=payload["content"],
            pinned=payload.get("pinned", False),
        ))

        if result is None:
            return {
                "success": False,
                "error": "Failed to add deal note",
            }

        note_id = result.get("id", 0)

        # Log intervention
        log_action(
            actor=self.actor,
            object_type="deal_note",
            object_id=note_id,
            action_type=ActionType.DEAL_NOTE_ADDED.value,
            summary=f"Agent added note to deal {payload['deal_id']}",
            details={"payload": payload, "tool": action.tool_name},
        )

        logger.info(f"Executed add_deal_note to deal {payload['deal_id']}")

        return {
            "success": True,
            "result": {"deal_id": payload["deal_id"], "note_id": note_id},
        }


# Singleton instance
_executor: Optional[ActionExecutor] = None


def get_executor(actor: str = "omnious") -> ActionExecutor:
    """Get or create ActionExecutor singleton.

    Note: The actor parameter is only used on first initialization.
    Subsequent calls return the existing singleton regardless of actor value.

    Args:
        actor: Actor name for audit logging (only used on first call)

    Returns:
        ActionExecutor instance
    """
    global _executor
    if _executor is None:
        _executor = ActionExecutor(actor=actor)
    return _executor


__all__ = [
    "ActionExecutor",
    "get_executor",
]
