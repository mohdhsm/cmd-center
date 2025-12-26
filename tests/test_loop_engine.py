"""Unit tests for Loop Engine."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session

from cmd_center.backend.services.loop_engine import (
    BaseLoop,
    LoopRegistry,
    LoopService,
    get_loop_service,
)
from cmd_center.backend.db import LoopRun, LoopFinding
from cmd_center.backend.constants import LoopStatus, FindingSeverity
from cmd_center.backend.models.loop_models import LoopRunFilters, LoopFindingFilters


class SimpleTestLoop(BaseLoop):
    """A simple loop for testing."""
    name = "test_loop"
    description = "Test loop for unit tests"
    interval_minutes = 5

    def __init__(self, should_fail: bool = False, findings_to_add: int = 0):
        super().__init__()
        self.should_fail = should_fail
        self.findings_to_add = findings_to_add

    def execute(self, session: Session) -> None:
        if self.should_fail:
            raise ValueError("Intentional test failure")

        for i in range(self.findings_to_add):
            self.add_finding(
                session=session,
                severity=FindingSeverity.WARNING.value,
                target_type="test",
                target_id=i + 1,
                message=f"Test finding {i + 1}",
                recommended_action="Test action",
            )


class TestBaseLoop:
    """Test cases for BaseLoop."""

    def test_run_creates_loop_run_record(self, override_db):
        """Running loop creates LoopRun record."""
        loop = SimpleTestLoop()
        result = loop.run()

        assert result.id is not None
        assert result.loop_name == "test_loop"
        assert result.status == LoopStatus.COMPLETED.value
        assert result.finished_at is not None

    def test_run_captures_findings(self, override_db):
        """Findings are captured and counted."""
        loop = SimpleTestLoop(findings_to_add=3)
        result = loop.run()

        assert result.findings_count == 3

    def test_loop_failure_logged(self, override_db):
        """Failed loop sets status=failed with error."""
        loop = SimpleTestLoop(should_fail=True)
        result = loop.run()

        assert result.status == LoopStatus.FAILED.value
        assert result.error_message == "Intentional test failure"
        assert result.finished_at is not None

    def test_finding_deduplication(self, override_db):
        """Duplicate findings within 24h are skipped."""
        loop = SimpleTestLoop(findings_to_add=2)

        # First run
        result1 = loop.run()
        assert result1.findings_count == 2

        # Second run - should deduplicate
        loop2 = SimpleTestLoop(findings_to_add=2)
        result2 = loop2.run()
        assert result2.findings_count == 0  # All duplicates

    def test_finding_signature_generation(self, override_db):
        """Finding signature is generated correctly."""
        loop = SimpleTestLoop()
        signature = loop._generate_signature("document", 123, "Test message")

        assert signature is not None
        assert len(signature) == 32  # SHA256 truncated to 32 chars


class TestLoopRegistry:
    """Test cases for LoopRegistry."""

    def test_register_and_get_loop(self, override_db):
        """Can register and retrieve a loop."""
        registry = LoopRegistry()
        loop = SimpleTestLoop()

        registry.register(loop)
        retrieved = registry.get("test_loop")

        assert retrieved is loop

    def test_get_nonexistent_loop(self, override_db):
        """Returns None for non-existent loop."""
        registry = LoopRegistry()
        result = registry.get("nonexistent")

        assert result is None

    def test_all_loops(self, override_db):
        """Returns all registered loops."""
        registry = LoopRegistry()
        loop1 = SimpleTestLoop()
        loop1.name = "loop1"
        loop2 = SimpleTestLoop()
        loop2.name = "loop2"

        registry.register(loop1)
        registry.register(loop2)

        all_loops = registry.all()
        assert len(all_loops) == 2

    def test_run_all(self, override_db):
        """Runs all enabled loops."""
        registry = LoopRegistry()
        loop1 = SimpleTestLoop()
        loop1.name = "loop1"
        loop2 = SimpleTestLoop()
        loop2.name = "loop2"
        loop3 = SimpleTestLoop()
        loop3.name = "loop3"
        loop3.is_enabled = False

        registry.register(loop1)
        registry.register(loop2)
        registry.register(loop3)

        results = registry.run_all()

        assert len(results) == 2  # Only enabled loops
        assert all(r.status == LoopStatus.COMPLETED.value for r in results)

    def test_run_by_name(self, override_db):
        """Runs a specific loop by name."""
        registry = LoopRegistry()
        loop = SimpleTestLoop()

        registry.register(loop)
        result = registry.run_by_name("test_loop")

        assert result is not None
        assert result.loop_name == "test_loop"

    def test_run_by_name_disabled(self, override_db):
        """Returns None for disabled loop."""
        registry = LoopRegistry()
        loop = SimpleTestLoop()
        loop.is_enabled = False

        registry.register(loop)
        result = registry.run_by_name("test_loop")

        assert result is None


class TestLoopService:
    """Test cases for LoopService."""

    def test_get_loop_runs(self, override_db):
        """Get paginated list of loop runs."""
        # Create some runs
        loop = SimpleTestLoop()
        loop.run()
        loop.run()
        loop.run()

        service = LoopService()
        result = service.get_loop_runs()

        assert result.total == 3
        assert len(result.items) == 3

    def test_get_loop_runs_filter_by_name(self, override_db):
        """Filter runs by loop name."""
        loop1 = SimpleTestLoop()
        loop1.name = "loop1"
        loop2 = SimpleTestLoop()
        loop2.name = "loop2"

        loop1.run()
        loop2.run()

        service = LoopService()
        result = service.get_loop_runs(LoopRunFilters(loop_name="loop1"))

        assert result.total == 1
        assert result.items[0].loop_name == "loop1"

    def test_get_loop_runs_filter_by_status(self, override_db):
        """Filter runs by status."""
        successful = SimpleTestLoop()
        failed = SimpleTestLoop(should_fail=True)

        successful.run()
        failed.run()

        service = LoopService()
        result = service.get_loop_runs(LoopRunFilters(status=LoopStatus.FAILED.value))

        assert result.total == 1
        assert result.items[0].status == LoopStatus.FAILED.value

    def test_get_loop_run_by_id(self, override_db):
        """Get loop run with findings."""
        loop = SimpleTestLoop(findings_to_add=2)
        run_result = loop.run()

        service = LoopService()
        result = service.get_loop_run_by_id(run_result.id)

        assert result is not None
        assert result.id == run_result.id
        assert len(result.findings) == 2

    def test_get_loop_run_not_found(self, override_db):
        """Returns None for non-existent run."""
        service = LoopService()
        result = service.get_loop_run_by_id(99999)

        assert result is None

    def test_get_findings(self, override_db):
        """Get paginated list of findings."""
        loop = SimpleTestLoop(findings_to_add=5)
        loop.run()

        service = LoopService()
        result = service.get_findings()

        assert result.total == 5
        assert len(result.items) == 5

    def test_get_findings_filter_by_severity(self, override_db):
        """Filter findings by severity."""
        loop = SimpleTestLoop(findings_to_add=3)
        loop.run()

        service = LoopService()
        result = service.get_findings(
            LoopFindingFilters(severity=FindingSeverity.WARNING.value)
        )

        assert result.total == 3

    def test_get_status(self, override_db):
        """Get status of all loops."""
        registry = LoopRegistry()
        loop = SimpleTestLoop()
        registry.register(loop)
        loop.run()

        service = LoopService()
        result = service.get_status(registry)

        assert len(result.loops) == 1
        assert result.loops[0].name == "test_loop"
        assert result.loops[0].last_run is not None
        assert result.total_runs_today >= 1


class TestLoopServiceSingleton:
    """Test singleton pattern for LoopService."""

    def test_get_loop_service_returns_same_instance(self, override_db):
        """Singleton returns same instance."""
        # Reset singleton for test
        import cmd_center.backend.services.loop_engine as loop_engine_module
        loop_engine_module._loop_service = None

        service1 = get_loop_service()
        service2 = get_loop_service()

        assert service1 is service2
