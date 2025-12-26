"""Employee API endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..services.employee_service import get_employee_service
from ..models.employee_models import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeWithAggregates,
    EmployeeListResponse,
    EmployeeFilters,
)

router = APIRouter()


@router.get("", response_model=EmployeeListResponse)
async def list_employees(
    department: Optional[str] = Query(None, description="Filter by department"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    reports_to_employee_id: Optional[int] = Query(None, description="Filter by manager"),
    search: Optional[str] = Query(None, description="Search by name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
):
    """List employees with optional filters.

    Returns a paginated list of employees. Use query parameters to filter.
    """
    service = get_employee_service()
    filters = EmployeeFilters(
        department=department,
        is_active=is_active,
        reports_to_employee_id=reports_to_employee_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    return service.get_employees(filters)


@router.get("/{employee_id}", response_model=EmployeeWithAggregates)
async def get_employee(employee_id: int):
    """Get an employee by ID with aggregated counts.

    Returns the employee with deal counts, task counts, etc.
    """
    service = get_employee_service()
    employee = service.get_employee_with_aggregates(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.post("", response_model=EmployeeResponse, status_code=201)
async def create_employee(
    data: EmployeeCreate,
    actor: str = Query("api", description="Who is creating the employee"),
):
    """Create a new employee.

    Creates the employee and logs an intervention for audit.
    """
    service = get_employee_service()
    return service.create_employee(data, actor=actor)


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    actor: str = Query("api", description="Who is updating the employee"),
):
    """Update an employee.

    Only provided fields are updated. Logs an intervention for audit.
    """
    service = get_employee_service()
    employee = service.update_employee(employee_id, data, actor=actor)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.delete("/{employee_id}", status_code=204)
async def delete_employee(
    employee_id: int,
    actor: str = Query("api", description="Who is deleting the employee"),
):
    """Soft delete an employee (sets is_active=False).

    The employee record is not removed, just deactivated.
    """
    service = get_employee_service()
    deleted = service.delete_employee(employee_id, actor=actor)
    if not deleted:
        raise HTTPException(status_code=404, detail="Employee not found")
    return None


@router.get("/by-pipedrive/{pipedrive_owner_id}", response_model=EmployeeResponse)
async def get_employee_by_pipedrive_owner(pipedrive_owner_id: int):
    """Get an employee by their Pipedrive owner ID.

    Useful for linking Pipedrive deals to internal employees.
    """
    service = get_employee_service()
    employee = service.get_employee_by_pipedrive_owner_id(pipedrive_owner_id)
    if not employee:
        raise HTTPException(
            status_code=404,
            detail=f"No employee linked to Pipedrive owner {pipedrive_owner_id}",
        )
    return employee
