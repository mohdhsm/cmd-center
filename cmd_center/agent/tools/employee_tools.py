"""Employee-related tools for the agent."""

from typing import Optional
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult
from ...backend.services.employee_service import get_employee_service
from ...backend.models.employee_models import EmployeeFilters


class GetEmployeesParams(BaseModel):
    """Parameters for get_employees tool."""
    department: Optional[str] = Field(
        default=None,
        description="Filter by department: 'sales', 'operations', 'finance', etc."
    )
    is_active: Optional[bool] = Field(
        default=True,
        description="Filter by active status"
    )
    search: Optional[str] = Field(
        default=None,
        description="Search by name"
    )


class GetEmployees(BaseTool):
    """Get list of employees."""

    name = "get_employees"
    description = "Get employees with optional filtering by department or search term. Use this to find team members."
    parameters_model = GetEmployeesParams

    def execute(self, params: GetEmployeesParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_employee_service()
            filters = EmployeeFilters(
                department=params.department,
                is_active=params.is_active,
                search=params.search,
            )
            result = service.get_employees(filters)

            employees_data = [
                {
                    "id": e.id,
                    "full_name": e.full_name,
                    "role_title": e.role_title,
                    "department": e.department,
                    "email": e.email,
                }
                for e in result.items
            ]

            return ToolResult(
                success=True,
                data={
                    "employees": employees_data,
                    "count": len(employees_data),
                    "total": result.total,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetEmployeeDetailsParams(BaseModel):
    """Parameters for get_employee_details tool."""
    employee_id: int = Field(description="The ID of the employee")


class GetEmployeeDetails(BaseTool):
    """Get detailed information about a specific employee."""

    name = "get_employee_details"
    description = "Get full details about a specific employee including role, department, and contact info."
    parameters_model = GetEmployeeDetailsParams

    def execute(self, params: GetEmployeeDetailsParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_employee_service()
            employee = service.get_employee_by_id(params.employee_id)

            if employee is None:
                return ToolResult(
                    success=False,
                    error=f"Employee {params.employee_id} not found"
                )

            return ToolResult(
                success=True,
                data={
                    "employee": {
                        "id": employee.id,
                        "full_name": employee.full_name,
                        "role_title": employee.role_title,
                        "department": employee.department,
                        "email": employee.email,
                        "phone": employee.phone,
                        "is_active": employee.is_active,
                    }
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
