"""Unit tests for InterventionService."""

import pytest
import json
from datetime import datetime, timedelta, timezone

from cmd_center.backend.db import Intervention
from cmd_center.backend.services.intervention_service import (
    log_action,
    InterventionService,
    get_intervention_service,
)
from cmd_center.backend.models.employee_models import InterventionFilters


class TestLogAction:
    """Tests for the log_action function."""

    def test_log_action_creates_intervention(self, override_db):
        """log_action creates intervention record."""
        intervention = log_action(
            actor="test_user",
            object_type="employee",
            object_id=123,
            action_type="employee_created",
            summary="Created employee: Test User",
        )

        assert intervention.id is not None
        assert intervention.actor == "test_user"
        assert intervention.object_type == "employee"
        assert intervention.object_id == 123
        assert intervention.action_type == "employee_created"
        assert intervention.summary == "Created employee: Test User"
        assert intervention.status == "done"

    def test_log_action_with_details_json(self, override_db):
        """Details dict is serialized to JSON."""
        details = {
            "full_name": "John Doe",
            "changes": {"department": {"from": "Sales", "to": "Engineering"}},
        }

        intervention = log_action(
            actor="admin",
            object_type="employee",
            object_id=456,
            action_type="employee_updated",
            summary="Updated employee",
            details=details,
        )

        assert intervention.details_json is not None
        parsed = json.loads(intervention.details_json)
        assert parsed["full_name"] == "John Doe"
        assert parsed["changes"]["department"]["from"] == "Sales"

    def test_log_action_with_status(self, override_db):
        """Can log failed or planned actions."""
        failed = log_action(
            actor="system",
            object_type="reminder",
            object_id=1,
            action_type="reminder_sent",
            summary="Failed to send reminder",
            status="failed",
        )

        assert failed.status == "failed"

        planned = log_action(
            actor="ceo",
            object_type="task",
            object_id=2,
            action_type="task_created",
            summary="Planned task",
            status="planned",
        )

        assert planned.status == "planned"

    def test_log_action_timestamp(self, override_db):
        """Intervention has created_at timestamp."""
        before = datetime.now(timezone.utc)

        intervention = log_action(
            actor="test",
            object_type="note",
            object_id=1,
            action_type="note_added",
            summary="Added note",
        )

        after = datetime.now(timezone.utc)

        assert intervention.created_at is not None
        # Handle timezone-naive comparison
        created_at = intervention.created_at.replace(tzinfo=None)
        assert before.replace(tzinfo=None) <= created_at <= after.replace(tzinfo=None)


class TestInterventionService:
    """Tests for InterventionService queries."""

    def test_get_interventions_filters_by_actor(self, override_db):
        """Can filter interventions by actor."""
        # Create interventions by different actors
        log_action(
            actor="user1", object_type="test", object_id=1,
            action_type="test", summary="By user1"
        )
        log_action(
            actor="user2", object_type="test", object_id=2,
            action_type="test", summary="By user2"
        )
        log_action(
            actor="user1", object_type="test", object_id=3,
            action_type="test", summary="By user1 again"
        )

        service = InterventionService()
        result = service.get_interventions(InterventionFilters(actor="user1"))

        assert result.total == 2
        assert all(i.actor == "user1" for i in result.items)

    def test_get_interventions_filters_by_object_type(self, override_db):
        """Can filter by object_type."""
        log_action(
            actor="test", object_type="employee", object_id=1,
            action_type="test", summary="Employee action"
        )
        log_action(
            actor="test", object_type="task", object_id=1,
            action_type="test", summary="Task action"
        )
        log_action(
            actor="test", object_type="employee", object_id=2,
            action_type="test", summary="Another employee action"
        )

        service = InterventionService()
        result = service.get_interventions(InterventionFilters(object_type="employee"))

        assert result.total == 2
        assert all(i.object_type == "employee" for i in result.items)

    def test_get_interventions_filters_by_action_type(self, override_db):
        """Can filter by action_type."""
        log_action(
            actor="test", object_type="task", object_id=1,
            action_type="task_created", summary="Created"
        )
        log_action(
            actor="test", object_type="task", object_id=2,
            action_type="task_completed", summary="Completed"
        )
        log_action(
            actor="test", object_type="task", object_id=3,
            action_type="task_created", summary="Created another"
        )

        service = InterventionService()
        result = service.get_interventions(
            InterventionFilters(action_type="task_created")
        )

        assert result.total == 2
        assert all(i.action_type == "task_created" for i in result.items)

    def test_get_interventions_filters_by_status(self, override_db):
        """Can filter by status."""
        log_action(
            actor="test", object_type="test", object_id=1,
            action_type="test", summary="Done", status="done"
        )
        log_action(
            actor="test", object_type="test", object_id=2,
            action_type="test", summary="Failed", status="failed"
        )

        service = InterventionService()
        result = service.get_interventions(InterventionFilters(status="failed"))

        assert result.total == 1
        assert result.items[0].status == "failed"

    def test_get_intervention_by_id(self, override_db):
        """Can get intervention by ID."""
        intervention = log_action(
            actor="test", object_type="test", object_id=1,
            action_type="test", summary="Test"
        )

        service = InterventionService()
        result = service.get_intervention_by_id(intervention.id)

        assert result is not None
        assert result.id == intervention.id
        assert result.summary == "Test"

    def test_get_intervention_by_id_not_found(self, override_db):
        """Returns None for non-existent intervention."""
        service = InterventionService()
        result = service.get_intervention_by_id(99999)

        assert result is None

    def test_get_interventions_for_object(self, override_db):
        """Get all interventions for a specific object."""
        # Create interventions for different objects
        log_action(
            actor="test", object_type="employee", object_id=123,
            action_type="employee_created", summary="Created"
        )
        log_action(
            actor="test", object_type="employee", object_id=123,
            action_type="employee_updated", summary="Updated"
        )
        log_action(
            actor="test", object_type="employee", object_id=456,
            action_type="employee_created", summary="Different employee"
        )

        service = InterventionService()
        result = service.get_interventions_for_object("employee", 123)

        assert len(result) == 2
        assert all(i.object_id == 123 for i in result)

    def test_get_interventions_for_object_ordered_by_recent(self, override_db):
        """Interventions for object are ordered most recent first."""
        for i in range(3):
            log_action(
                actor="test", object_type="task", object_id=1,
                action_type=f"action_{i}", summary=f"Action {i}"
            )

        service = InterventionService()
        result = service.get_interventions_for_object("task", 1)

        # Most recent should be first
        assert result[0].action_type == "action_2"
        assert result[-1].action_type == "action_0"

    def test_get_recent_interventions_by_actor(self, override_db):
        """Get recent interventions by a specific actor."""
        # Create interventions by different actors
        for i in range(5):
            log_action(
                actor="admin", object_type="test", object_id=i,
                action_type="test", summary=f"Admin action {i}"
            )
        for i in range(3):
            log_action(
                actor="user", object_type="test", object_id=i,
                action_type="test", summary=f"User action {i}"
            )

        service = InterventionService()
        result = service.get_recent_interventions_by_actor("admin", limit=3)

        assert len(result) == 3
        assert all(i.actor == "admin" for i in result)

    def test_get_interventions_pagination(self, override_db):
        """Pagination works correctly."""
        # Create 10 interventions
        for i in range(10):
            log_action(
                actor="test", object_type="test", object_id=i,
                action_type="test", summary=f"Action {i}"
            )

        service = InterventionService()

        # Get page 1
        page1 = service.get_interventions(InterventionFilters(page=1, page_size=3))
        assert page1.total == 10
        assert len(page1.items) == 3

        # Get page 2
        page2 = service.get_interventions(InterventionFilters(page=2, page_size=3))
        assert len(page2.items) == 3

        # Different interventions on each page
        page1_ids = {i.id for i in page1.items}
        page2_ids = {i.id for i in page2.items}
        assert page1_ids.isdisjoint(page2_ids)


class TestInterventionServiceSingleton:
    """Test singleton pattern."""

    def test_get_intervention_service_returns_same_instance(self, override_db):
        """get_intervention_service returns the same instance."""
        # Reset singleton for this test
        import cmd_center.backend.services.intervention_service as module
        module._intervention_service = None

        service1 = get_intervention_service()
        service2 = get_intervention_service()

        assert service1 is service2
