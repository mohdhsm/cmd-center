"""Dashboard service for aggregating today's focus items."""

from typing import List
from datetime import datetime

from ..models import DashboardItem, DealBase
from .deal_health_service import get_deal_health_service
from .llm_analysis_service import get_llm_analysis_service
from .cashflow_service import get_cashflow_service


class DashboardService:
    """Service for generating dashboard items."""
    
    def __init__(self):
        self.deal_health = get_deal_health_service()
        self.llm_analysis = get_llm_analysis_service()
        self.cashflow = get_cashflow_service()
    
    async def get_dashboard_items(
        self,
        pipelines: List[str] = None,
    ) -> List[DashboardItem]:
        """Get all dashboard items sorted by priority."""
        if pipelines is None:
            pipelines = ["Aramco Projects", "pipeline"]
        
        items = []
        priority_counter = 1
        
        for pipeline in pipelines:
            # Get overdue deals (≥7 days)
            overdue = self.deal_health.get_overdue_deals(pipeline, min_days=7)
            for deal in overdue[:5]:  # Top 5 overdue
                item = DashboardItem(
                    type="overdue",
                    pipeline=pipeline,
                    priority=priority_counter,
                    flag=f"Overdue ≥{deal.overdue_days}d",
                    deal=DealBase(**deal.model_dump()),
                )
                items.append(item)
                priority_counter += 1
            
            # Get stuck deals (≥30 days)
            stuck = self.deal_health.get_stuck_deals(pipeline, min_days=30)
            for deal in stuck[:5]:  # Top 5 stuck
                item = DashboardItem(
                    type="stuck",
                    pipeline=pipeline,
                    priority=priority_counter,
                    flag=f"Stuck {deal.days_in_stage}d",
                    deal=DealBase(**deal.model_dump()),
                )
                items.append(item)
                priority_counter += 1
        
        # Get compliance issues (Aramco only)
        if "Aramco Projects" in pipelines:
            compliance = await self.llm_analysis.analyze_compliance("Aramco Projects")
            for comp in compliance[:5]:  # Top 5 compliance issues
                issues = []
                if not comp.survey_checklist_present:
                    issues.append("No survey")
                if not comp.quality_docs_present:
                    issues.append("No quality docs")
                
                if issues:
                    item = DashboardItem(
                        type="compliance",
                        pipeline="Aramco Projects",
                        priority=priority_counter,
                        flag=", ".join(issues),
                        deal=DealBase(**comp.model_dump()),
                    )
                    items.append(item)
                    priority_counter += 1
        
        # Get cashflow items (near invoice)
        if "Aramco Projects" in pipelines:
            cashflow_buckets = await self.cashflow.get_cashflow_projection("Aramco Projects")
            for bucket in cashflow_buckets[:3]:  # Next 3 periods
                if bucket.deal_count > 0:
                    item = DashboardItem(
                        type="cashflow",
                        pipeline="Aramco Projects",
                        priority=priority_counter,
                        flag=f"{bucket.period}: {bucket.deal_count} deals",
                        deal=None,  # Cashflow items don't have a single deal
                    )
                    items.append(item)
                    priority_counter += 1
        
        # Sort by priority
        items.sort(key=lambda x: x.priority)
        
        return items[:20]  # Return top 20 items


# Global service instance
_dashboard_service = None


def get_dashboard_service() -> DashboardService:
    """Get or create dashboard service singleton."""
    global _dashboard_service
    if _dashboard_service is None:
        _dashboard_service = DashboardService()
    return _dashboard_service