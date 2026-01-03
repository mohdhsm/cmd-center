"""Pipeline and deal-related tools for the agent."""

from typing import Optional, List
from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult
from ...backend.services.deal_health_service import get_deal_health_service


class GetOverdueDealsParams(BaseModel):
    """Parameters for get_overdue_deals tool."""
    pipeline: str = Field(
        default="aramco",
        description="Pipeline to query: 'aramco' or 'commercial'"
    )
    min_days: int = Field(
        default=7,
        description="Minimum days without activity to be considered overdue"
    )


class GetOverdueDeals(BaseTool):
    """Get deals with no recent activity (overdue)."""

    name = "get_overdue_deals"
    description = "Get overdue deals that have had no activity for a specified number of days. Use this to find deals that need attention."
    parameters_model = GetOverdueDealsParams

    def execute(self, params: GetOverdueDealsParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_deal_health_service()
            pipeline_name = "Aramco Projects" if params.pipeline == "aramco" else "Commercial"
            deals = service.get_overdue_deals(pipeline_name, params.min_days)

            deals_data = [
                {
                    "id": d.id,
                    "title": d.title,
                    "owner": d.owner,
                    "stage": d.stage,
                    "overdue_days": d.overdue_days,
                    "value_sar": d.value,
                }
                for d in deals
            ]

            return ToolResult(
                success=True,
                data={
                    "deals": deals_data,
                    "count": len(deals_data),
                    "pipeline": params.pipeline,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetStuckDealsParams(BaseModel):
    """Parameters for get_stuck_deals tool."""
    pipeline: str = Field(
        default="aramco",
        description="Pipeline to query: 'aramco' or 'commercial'"
    )
    min_days: int = Field(
        default=30,
        description="Minimum days in current stage to be considered stuck"
    )


class GetStuckDeals(BaseTool):
    """Get deals stuck in their current stage."""

    name = "get_stuck_deals"
    description = "Get deals that have been in their current stage for too long. Use this to identify bottlenecks."
    parameters_model = GetStuckDealsParams

    def execute(self, params: GetStuckDealsParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_deal_health_service()
            pipeline_name = "Aramco Projects" if params.pipeline == "aramco" else "Commercial"
            deals = service.get_stuck_deals(pipeline_name, params.min_days)

            deals_data = [
                {
                    "id": d.id,
                    "title": d.title,
                    "owner": d.owner,
                    "stage": d.stage,
                    "days_in_stage": d.days_in_stage,
                    "value_sar": d.value,
                }
                for d in deals
            ]

            return ToolResult(
                success=True,
                data={
                    "deals": deals_data,
                    "count": len(deals_data),
                    "pipeline": params.pipeline,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetDealDetailsParams(BaseModel):
    """Parameters for get_deal_details tool."""
    deal_id: int = Field(description="The ID of the deal to get details for")


class GetDealDetails(BaseTool):
    """Get detailed information about a specific deal."""

    name = "get_deal_details"
    description = "Get full details about a specific deal including stage, owner, value, and activity counts."
    parameters_model = GetDealDetailsParams

    def execute(self, params: GetDealDetailsParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_deal_health_service()
            deal = service.get_deal_detail(params.deal_id)

            if deal is None:
                return ToolResult(
                    success=False,
                    error=f"Deal {params.deal_id} not found"
                )

            return ToolResult(
                success=True,
                data={
                    "deal": {
                        "id": deal.id,
                        "title": deal.title,
                        "pipeline": deal.pipeline,
                        "stage": deal.stage,
                        "owner": deal.owner,
                        "org_name": deal.org_name,
                        "value_sar": deal.value_sar,
                        "notes_count": deal.notes_count,
                        "activities_count": deal.activities_count,
                        "email_messages_count": deal.email_messages_count,
                    }
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GetDealNotesParams(BaseModel):
    """Parameters for get_deal_notes tool."""
    deal_id: int = Field(description="The ID of the deal to get notes for")
    limit: int = Field(default=10, description="Maximum number of notes to return")


class GetDealNotes(BaseTool):
    """Get notes for a specific deal."""

    name = "get_deal_notes"
    description = "Get the most recent notes for a deal. Use this to understand deal history and context."
    parameters_model = GetDealNotesParams

    def execute(self, params: GetDealNotesParams) -> ToolResult:
        """Execute the tool."""
        try:
            service = get_deal_health_service()
            notes = service.get_deal_notes(params.deal_id, params.limit)

            notes_data = [
                {
                    "content": n.content,
                    "author": n.author,
                    "date": n.date.isoformat() if n.date else None,
                }
                for n in notes
            ]

            return ToolResult(
                success=True,
                data={
                    "notes": notes_data,
                    "count": len(notes_data),
                    "deal_id": params.deal_id,
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
