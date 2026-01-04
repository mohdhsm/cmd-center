"""HR tools for the agent."""

from typing import Optional

from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult
from ...backend.services.bonus_service import get_bonus_service


class GetUnpaidBonusesParams(BaseModel):
    """Parameters for get_unpaid_bonuses tool."""

    employee_id: Optional[int] = Field(
        default=None,
        description="Filter by specific employee ID",
    )
    limit: int = Field(
        default=50,
        description="Maximum number of bonuses to return (1-100)",
        ge=1,
        le=100,
    )


class GetUnpaidBonuses(BaseTool):
    """Get pending/unpaid bonus records."""

    name = "get_unpaid_bonuses"
    description = (
        "Get pending or unpaid bonus records. Use to track outstanding compensation, "
        "identify bonuses that haven't been paid yet, and monitor bonus payment status."
    )
    parameters_model = GetUnpaidBonusesParams

    def execute(self, params: GetUnpaidBonusesParams) -> ToolResult:
        """Execute the tool to get unpaid bonuses.

        Args:
            params: Parameters with optional employee_id and limit filters

        Returns:
            ToolResult with list of unpaid bonuses, count, and total amount
        """
        try:
            service = get_bonus_service()
            bonuses = service.get_unpaid_bonuses(
                employee_id=params.employee_id,
                limit=params.limit,
            )

            bonuses_data = [
                {
                    "id": b.id,
                    "employee_id": b.employee_id,
                    "title": b.title,
                    "description": b.description,
                    "amount": b.amount,
                    "currency": b.currency,
                    "bonus_type": b.bonus_type,
                    "status": b.status,
                    "promised_date": b.promised_date.isoformat() if b.promised_date else None,
                    "due_date": b.due_date.isoformat() if b.due_date else None,
                    "created_at": b.created_at.isoformat() if b.created_at else None,
                    "updated_at": b.updated_at.isoformat() if b.updated_at else None,
                }
                for b in bonuses
            ]

            total_amount = sum(b.amount for b in bonuses)

            return ToolResult(
                success=True,
                data={
                    "bonuses": bonuses_data,
                    "count": len(bonuses_data),
                    "total_amount": total_amount,
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
