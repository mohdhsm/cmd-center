"""Loop Engine for automated monitoring and background processing.

This module provides the framework for running monitoring loops that:
- Check for expiring documents
- Monitor overdue tasks
- Process pending reminders
- Track bonus due dates
"""

import hashlib
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlmodel import Session, select, func

from .. import db
from ..db import LoopRun, LoopFinding
from ..models.loop_models import (
    LoopRunResponse,
    LoopRunWithFindings,
    LoopRunListResponse,
    LoopFindingResponse,
    LoopFindingListResponse,
    LoopInfo,
    LoopStatusResponse,
    LoopRunFilters,
    LoopFindingFilters,
)
from ..constants import LoopStatus, FindingSeverity, ActionType
from .intervention_service import log_action

logger = logging.getLogger(__name__)


class BaseLoop(ABC):
    """Base class for all monitoring loops."""

    # Override in subclasses
    name: str = "base_loop"
    description: str = "Base loop"
    interval_minutes: int = 60
    is_enabled: bool = True

    def __init__(self):
        self._current_run: Optional[LoopRun] = None
        self._findings: list[dict] = []

    @abstractmethod
    def execute(self, session: Session) -> None:
        """Execute the loop logic. Override in subclasses."""
        pass

    def run(self) -> LoopRunResponse:
        """Run the loop with tracking."""
        with Session(db.engine) as session:
            # Create loop run record
            run = LoopRun(
                loop_name=self.name,
                status=LoopStatus.RUNNING.value,
            )
            session.add(run)
            session.commit()
            session.refresh(run)

            self._current_run = run
            self._findings = []

            try:
                # Execute loop logic
                self.execute(session)

                # Update run status
                run.status = LoopStatus.COMPLETED.value
                run.finished_at = datetime.now(timezone.utc)
                run.findings_count = len(self._findings)

                session.add(run)
                session.commit()
                session.refresh(run)

                logger.info(
                    f"Loop '{self.name}' completed with {len(self._findings)} findings"
                )

            except Exception as e:
                # Handle failure
                run.status = LoopStatus.FAILED.value
                run.finished_at = datetime.now(timezone.utc)
                run.error_message = str(e)

                session.add(run)
                session.commit()
                session.refresh(run)

                logger.error(f"Loop '{self.name}' failed: {e}")

            return LoopRunResponse.model_validate(run)

    def add_finding(
        self,
        session: Session,
        severity: str,
        target_type: str,
        target_id: int,
        message: str,
        recommended_action: Optional[str] = None,
    ) -> Optional[LoopFinding]:
        """Add a finding to the current loop run with deduplication."""
        if not self._current_run:
            raise RuntimeError("Cannot add finding outside of loop execution")

        # Generate signature for deduplication
        signature = self._generate_signature(target_type, target_id, message)

        # Check for duplicate within last 24 hours
        if self._is_duplicate(session, signature):
            logger.debug(f"Skipping duplicate finding: {message}")
            return None

        # Create finding
        finding = LoopFinding(
            loop_run_id=self._current_run.id,
            severity=severity,
            target_type=target_type,
            target_id=target_id,
            message=message,
            recommended_action=recommended_action,
            signature=signature,
        )
        session.add(finding)
        session.commit()
        session.refresh(finding)

        self._findings.append({
            "id": finding.id,
            "severity": severity,
            "target_type": target_type,
            "target_id": target_id,
            "message": message,
        })

        # Log intervention for critical findings
        if severity == FindingSeverity.CRITICAL.value:
            log_action(
                actor="loop_engine",
                object_type=target_type,
                object_id=target_id,
                action_type=ActionType.LOOP_FINDING.value,
                summary=f"[{self.name}] {message}",
                details={
                    "severity": severity,
                    "recommended_action": recommended_action,
                },
            )

        return finding

    def _generate_signature(
        self,
        target_type: str,
        target_id: int,
        message: str,
    ) -> str:
        """Generate a signature for deduplication."""
        content = f"{self.name}:{target_type}:{target_id}:{message}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def _is_duplicate(self, session: Session, signature: str) -> bool:
        """Check if a finding with this signature exists in last 24 hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        query = (
            select(LoopFinding)
            .where(LoopFinding.signature == signature)
            .where(LoopFinding.created_at >= cutoff)
            .limit(1)
        )
        existing = session.exec(query).first()
        return existing is not None


class LoopRegistry:
    """Registry for all monitoring loops."""

    def __init__(self):
        self._loops: dict[str, BaseLoop] = {}

    def register(self, loop: BaseLoop) -> None:
        """Register a loop."""
        self._loops[loop.name] = loop
        logger.info(f"Registered loop: {loop.name}")

    def get(self, name: str) -> Optional[BaseLoop]:
        """Get a loop by name."""
        return self._loops.get(name)

    def all(self) -> list[BaseLoop]:
        """Get all registered loops."""
        return list(self._loops.values())

    def run_all(self) -> list[LoopRunResponse]:
        """Run all enabled loops."""
        results = []
        for loop in self._loops.values():
            if loop.is_enabled:
                result = loop.run()
                results.append(result)
        return results

    def run_by_name(self, name: str) -> Optional[LoopRunResponse]:
        """Run a specific loop by name."""
        loop = self._loops.get(name)
        if loop and loop.is_enabled:
            return loop.run()
        return None


class LoopService:
    """Service for managing loop runs and findings."""

    def get_loop_runs(
        self,
        filters: Optional[LoopRunFilters] = None,
    ) -> LoopRunListResponse:
        """Get paginated list of loop runs."""
        if filters is None:
            filters = LoopRunFilters()

        with Session(db.engine) as session:
            query = select(LoopRun)

            if filters.loop_name:
                query = query.where(LoopRun.loop_name == filters.loop_name)
            if filters.status:
                query = query.where(LoopRun.status == filters.status)
            if filters.from_date:
                query = query.where(LoopRun.started_at >= filters.from_date)
            if filters.to_date:
                query = query.where(LoopRun.started_at <= filters.to_date)

            count_query = select(func.count()).select_from(query.subquery())
            total = session.exec(count_query).one()

            query = query.order_by(LoopRun.started_at.desc())
            query = query.offset((filters.page - 1) * filters.page_size)
            query = query.limit(filters.page_size)

            runs = session.exec(query).all()

            return LoopRunListResponse(
                items=[LoopRunResponse.model_validate(r) for r in runs],
                total=total,
                page=filters.page,
                page_size=filters.page_size,
            )

    def get_loop_run_by_id(self, run_id: int) -> Optional[LoopRunWithFindings]:
        """Get a loop run by ID with its findings."""
        with Session(db.engine) as session:
            run = session.get(LoopRun, run_id)
            if not run:
                return None

            findings_query = (
                select(LoopFinding)
                .where(LoopFinding.loop_run_id == run_id)
                .order_by(LoopFinding.created_at.desc())
            )
            findings = session.exec(findings_query).all()

            return LoopRunWithFindings(
                id=run.id,
                loop_name=run.loop_name,
                started_at=run.started_at,
                finished_at=run.finished_at,
                status=run.status,
                findings_count=run.findings_count,
                error_message=run.error_message,
                findings=[LoopFindingResponse.model_validate(f) for f in findings],
            )

    def get_findings(
        self,
        filters: Optional[LoopFindingFilters] = None,
    ) -> LoopFindingListResponse:
        """Get paginated list of loop findings."""
        if filters is None:
            filters = LoopFindingFilters()

        with Session(db.engine) as session:
            query = select(LoopFinding)

            if filters.loop_name:
                # Join with LoopRun to filter by loop name
                query = query.join(LoopRun).where(LoopRun.loop_name == filters.loop_name)
            if filters.severity:
                query = query.where(LoopFinding.severity == filters.severity)
            if filters.target_type:
                query = query.where(LoopFinding.target_type == filters.target_type)
            if filters.from_date:
                query = query.where(LoopFinding.created_at >= filters.from_date)
            if filters.to_date:
                query = query.where(LoopFinding.created_at <= filters.to_date)

            count_query = select(func.count()).select_from(query.subquery())
            total = session.exec(count_query).one()

            query = query.order_by(LoopFinding.created_at.desc())
            query = query.offset((filters.page - 1) * filters.page_size)
            query = query.limit(filters.page_size)

            findings = session.exec(query).all()

            return LoopFindingListResponse(
                items=[LoopFindingResponse.model_validate(f) for f in findings],
                total=total,
                page=filters.page,
                page_size=filters.page_size,
            )

    def get_status(self, registry: LoopRegistry) -> LoopStatusResponse:
        """Get status of all registered loops."""
        with Session(db.engine) as session:
            loops_info = []
            for loop in registry.all():
                # Get last run for this loop
                last_run_query = (
                    select(LoopRun)
                    .where(LoopRun.loop_name == loop.name)
                    .order_by(LoopRun.started_at.desc())
                    .limit(1)
                )
                last_run = session.exec(last_run_query).first()

                loops_info.append(LoopInfo(
                    name=loop.name,
                    description=loop.description,
                    interval_minutes=loop.interval_minutes,
                    last_run=LoopRunResponse.model_validate(last_run) if last_run else None,
                    is_enabled=loop.is_enabled,
                ))

            # Count today's runs and findings
            today_start = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            runs_today_query = (
                select(func.count())
                .select_from(LoopRun)
                .where(LoopRun.started_at >= today_start)
            )
            total_runs_today = session.exec(runs_today_query).one()

            findings_today_query = (
                select(func.count())
                .select_from(LoopFinding)
                .where(LoopFinding.created_at >= today_start)
            )
            total_findings_today = session.exec(findings_today_query).one()

            return LoopStatusResponse(
                loops=loops_info,
                total_runs_today=total_runs_today,
                total_findings_today=total_findings_today,
            )


# Global registry instance
loop_registry = LoopRegistry()

# Singleton pattern for service
_loop_service: Optional[LoopService] = None


def get_loop_service() -> LoopService:
    global _loop_service
    if _loop_service is None:
        _loop_service = LoopService()
    return _loop_service


__all__ = [
    "BaseLoop",
    "LoopRegistry",
    "LoopService",
    "loop_registry",
    "get_loop_service",
]
