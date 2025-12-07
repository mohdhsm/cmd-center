"""Cashflow projection service."""

from typing import List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from ..models import CashflowBucket
from ..integrations import get_pipedrive_client


class CashflowService:
    """Service for cashflow projection analysis."""
    
    def __init__(self):
        self.pipedrive = get_pipedrive_client()
    
    def _get_week_label(self, date: datetime) -> str:
        """Get week label (e.g., '2026-W01')."""
        year = date.isocalendar()[0]
        week = date.isocalendar()[1]
        return f"{year}-W{week:02d}"
    
    def _get_month_label(self, date: datetime) -> str:
        """Get month label (e.g., '2026-01')."""
        return date.strftime("%Y-%m")
    
    async def get_cashflow_projection(
        self,
        pipeline_name: str = "Aramco Projects",
        period_type: str = "week",  # "week" or "month"
        weeks_ahead: int = 12,
    ) -> List[CashflowBucket]:
        """Get cashflow projection by period."""
        pipeline_id = await self.pipedrive.get_pipeline_id(pipeline_name)
        if not pipeline_id:
            return []
        
        # Get all deals in pipeline
        deals_dto = await self.pipedrive.get_deals(pipeline_id=pipeline_id)
        
        # Group deals by period
        buckets: dict[str, dict] = defaultdict(lambda: {
            "expected_invoice_value_sar": 0.0,
            "deal_count": 0,
            "deals": []
        })
        
        now = datetime.now()
        
        for dto in deals_dto:
            # Simplified: Use update_time as proxy for expected invoice date
            # In production, would use custom fields for expected invoice date
            if not dto.update_time:
                continue
            
            deal_date = datetime.fromisoformat(dto.update_time.replace('Z', '+00:00'))
            
            # Only include future deals or recent ones
            if deal_date > now - timedelta(days=7):
                if period_type == "week":
                    period_label = self._get_week_label(deal_date)
                else:
                    period_label = self._get_month_label(deal_date)
                
                value = dto.value or 0.0
                buckets[period_label]["expected_invoice_value_sar"] += value
                buckets[period_label]["deal_count"] += 1
                buckets[period_label]["deals"].append(dto.title)
        
        # Convert to CashflowBucket objects
        results = []
        for period, data in sorted(buckets.items()):
            bucket = CashflowBucket(
                period=period,
                expected_invoice_value_sar=data["expected_invoice_value_sar"],
                deal_count=data["deal_count"],
                comment=f"{data['deal_count']} deals ready for invoicing",
            )
            results.append(bucket)
        
        return results[:weeks_ahead]


# Global service instance
_cashflow_service: Optional[CashflowService] = None


def get_cashflow_service() -> CashflowService:
    """Get or create cashflow service singleton."""
    global _cashflow_service
    if _cashflow_service is None:
        _cashflow_service = CashflowService()
    return _cashflow_service