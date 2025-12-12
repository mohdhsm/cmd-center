"""Deal health service for identifying overdue and stuck deals."""

from typing import List, Optional
from datetime import datetime, timezone

from ..models import DealBase, OverdueDeal, StuckDeal, OrderReceivedAnalysis
from ..constants import PIPELINE_NAME_TO_ID, PIPELINE_ID_TO_NAME
from . import db_queries
from sqlmodel import Session, select
from ..db import Deal


class DealHealthService:
    """Service for analyzing deal health (overdue, stuck, etc.)."""
    
    def __init__(self):
        pass
    
    def _calculate_overdue_days(self, update_time: Optional[datetime]) -> int:
        """Calculate days since last update."""
        if not update_time:
            return 0
        now = datetime.now(timezone.utc)
        # Make update_time timezone-aware if it isn't
        if update_time.tzinfo is None:
            update_time = update_time.replace(tzinfo=timezone.utc)
        delta = now - update_time
        return max(0, delta.days)
    
    def _calculate_days_in_stage(self, stage_change_time: Optional[datetime], update_time: Optional[datetime]) -> int:
        """Calculate days in current stage."""
        # Prefer stage_change_time, fallback to update_time
        change_time = stage_change_time or update_time
        if not change_time:
            return 0
        now = datetime.now(timezone.utc)
        # Make change_time timezone-aware if it isn't
        if change_time.tzinfo is None:
            change_time = change_time.replace(tzinfo=timezone.utc)
        delta = now - change_time
        return max(0, delta.days)
    
    def _get_stage_name(self, stage_id: int) -> str:
        """Helper to get stage name from ID."""
        stage = db_queries.get_stage_by_id(stage_id)
        return stage.name if stage else "Unknown"
    
    def _deal_to_deal_base(self, deal) -> DealBase:
        """Convert Deal SQLModel to DealBase Pydantic model."""
        pipeline_name = PIPELINE_ID_TO_NAME.get(deal.pipeline_id, f"Pipeline {deal.pipeline_id}")
        stage_name = self._get_stage_name(deal.stage_id)
        
        # Make datetimes timezone-aware if they aren't
        add_time = deal.add_time
        if add_time and add_time.tzinfo is None:
            add_time = add_time.replace(tzinfo=timezone.utc)
        
        update_time = deal.update_time
        if update_time and update_time.tzinfo is None:
            update_time = update_time.replace(tzinfo=timezone.utc)
        
        last_activity_time = deal.last_activity_date
        if last_activity_time and last_activity_time.tzinfo is None:
            last_activity_time = last_activity_time.replace(tzinfo=timezone.utc)
        
        next_activity_date = deal.next_activity_date
        if next_activity_date and next_activity_date.tzinfo is None:
            next_activity_date = next_activity_date.replace(tzinfo=timezone.utc)
        
        return DealBase(
            id=deal.id,
            title=deal.title,
            pipeline=pipeline_name,
            stage=stage_name,
            owner=deal.owner_name or "Unknown",
            org_name=deal.org_name,
            value_sar=deal.value,
            add_time=add_time,
            update_time=update_time,
            last_activity_time=last_activity_time,
            next_activity_date=next_activity_date,
            file_count=deal.file_count,
            notes_count=deal.notes_count,
            activities_count=deal.activities_count,
            done_activities_count=deal.done_activities_count,
            email_messages_count=deal.email_messages_count,
        )
    
    def get_overdue_deals(
        self,
        pipeline_name: str = "Aramco Projects",
        min_days: int = 7
    ) -> List[OverdueDeal]:
        """Get deals that are overdue (read from database)."""
        # Query database (fast!)
        deals = db_queries.get_overdue_deals_for_pipeline(pipeline_name, min_days)
        
        # Transform to API model
        overdue_deals = []
        for deal in deals:
            deal_base = self._deal_to_deal_base(deal)
            overdue_days = self._calculate_overdue_days(deal.update_time)
            
            overdue_deal = OverdueDeal(
                **deal_base.model_dump(),
                overdue_days=overdue_days,
            )
            overdue_deals.append(overdue_deal)
        
        return sorted(overdue_deals, key=lambda d: d.overdue_days, reverse=True)
    
    def get_stuck_deals(
        self,
        pipeline_name: str = "Aramco Projects",
        min_days: int = 30
    ) -> List[StuckDeal]:
        """Get deals stuck in the same stage (read from database)."""
        # Query database (fast!)
        deals = db_queries.get_stuck_deals_for_pipeline(pipeline_name, min_days)
        
        # Transform to API model
        stuck_deals = []
        for deal in deals:
            deal_base = self._deal_to_deal_base(deal)
            days_in_stage = self._calculate_days_in_stage(deal.stage_change_time, deal.update_time)
            
            stuck_deal = StuckDeal(
                **deal_base.model_dump(),
                days_in_stage=days_in_stage,
            )
            stuck_deals.append(stuck_deal)
        
        return sorted(stuck_deals, key=lambda d: d.days_in_stage, reverse=True)

    def get_order_received_deals(
        self,
        pipeline_name: str = "Aramco Projects"
    ) -> List[OrderReceivedAnalysis]:
        """Get deals in Order Received stages (read from database)."""
        pipeline_id = PIPELINE_NAME_TO_ID.get(pipeline_name)
        if not pipeline_id:
            return []

        # Stage IDs for Order Received stages
        order_received_stage_ids = [27, 28, 29, 45]  # Order Received, Approved, Awaiting Payment, Everything is read but not started

        # Query database for deals in these stages (similar to get_deals_near_invoicing)
        with Session(db_queries.engine) as session:
            deals = list(session.exec(
                select(Deal)
                .where(Deal.pipeline_id == pipeline_id)
                .where(Deal.stage_id.in_(order_received_stage_ids))
                .where(Deal.status == "open")
            ).all())

        # Transform to API model
        order_received_deals = []
        for deal in deals:
            deal_base = self._deal_to_deal_base(deal)
            days_in_stage = self._calculate_days_in_stage(deal.stage_change_time, deal.update_time)

            order_received_deal = OrderReceivedAnalysis(
                **deal_base.model_dump(),
                days_in_stage=days_in_stage,
                end_user_identified=None,  # Would be set by LLM analysis
                end_user_requests_count=None,  # Would be set by LLM analysis
            )
            order_received_deals.append(order_received_deal)

        return sorted(order_received_deals, key=lambda d: d.days_in_stage, reverse=True)

    def get_deal_detail(self, deal_id: int) -> Optional[DealBase]:
        """Get detailed information for a single deal (read from database)."""
        deal = db_queries.get_deal_by_id(deal_id)
        
        if deal:
            return self._deal_to_deal_base(deal)
        
        return None


# Global service instance
_deal_health_service: Optional[DealHealthService] = None


def get_deal_health_service() -> DealHealthService:
    """Get or create deal health service singleton."""
    global _deal_health_service
    if _deal_health_service is None:
        _deal_health_service = DealHealthService()
    return _deal_health_service
