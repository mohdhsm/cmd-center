"""API endpoints for Loop Engine monitoring."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from ..models.loop_models import (
    LoopRunResponse,
    LoopRunWithFindings,
    LoopRunListResponse,
    LoopFindingListResponse,
    LoopStatusResponse,
    LoopRunFilters,
    LoopFindingFilters,
)
from ..services.loop_engine import get_loop_service, loop_registry

router = APIRouter(prefix="/loops", tags=["loops"])


@router.get("/status", response_model=LoopStatusResponse)
def get_loops_status() -> LoopStatusResponse:
    """Get status of all registered loops."""
    service = get_loop_service()
    return service.get_status(loop_registry)


@router.post("/{loop_name}/run", response_model=LoopRunResponse)
def run_loop(loop_name: str) -> LoopRunResponse:
    """Manually trigger a specific loop."""
    result = loop_registry.run_by_name(loop_name)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Loop '{loop_name}' not found or not enabled",
        )
    return result


@router.post("/run-all", response_model=list[LoopRunResponse])
def run_all_loops() -> list[LoopRunResponse]:
    """Manually trigger all enabled loops."""
    return loop_registry.run_all()


@router.get("/runs", response_model=LoopRunListResponse)
def list_loop_runs(
    loop_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> LoopRunListResponse:
    """List loop runs with filters."""
    service = get_loop_service()
    filters = LoopRunFilters(
        loop_name=loop_name,
        status=status,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
    return service.get_loop_runs(filters)


@router.get("/runs/{run_id}", response_model=LoopRunWithFindings)
def get_loop_run(run_id: int) -> LoopRunWithFindings:
    """Get a loop run by ID with its findings."""
    service = get_loop_service()
    run = service.get_loop_run_by_id(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Loop run not found")
    return run


@router.get("/findings", response_model=LoopFindingListResponse)
def list_findings(
    loop_name: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    target_type: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> LoopFindingListResponse:
    """List loop findings with filters."""
    service = get_loop_service()
    filters = LoopFindingFilters(
        loop_name=loop_name,
        severity=severity,
        target_type=target_type,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
    return service.get_findings(filters)
