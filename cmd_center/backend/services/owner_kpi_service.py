"""Owner KPI service for salesperson metrics."""

from typing import List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from ..models import OwnerKPI
from ..integrations import get_pipedrive_client


class OwnerKPIService:
    """Service for calculating owner/salesperson KPIs."""
    
    def __init__(self):
        self.pipedrive = get_pipedrive_client()
    
    async def get_owner_kpis(
        self,
        pipeline_names: List[str] = None,
        days_back: int = 30,
    ) -> List[OwnerKPI]:
        """Get KPIs for all owners/salespeople."""
        if pipeline_names is None:
            pipeline_names = ["Aramco Projects", "pipeline"]
        
        # Aggregate metrics by owner
        owner_metrics = defaultdict(lambda: {
            "activities_count": 0,
            "projects_count": 0,
            "estimated_value_sar": 0.0,
            "moved_to_production_count": 0,
            "overdue_deals_count": 0,
            "stuck_deals_count": 0,
        })
        
        now = datetime.now()
        cutoff_date = now - timedelta(days=days_back)
        
        for pipeline_name in pipeline_names:
            pipeline_id = await self.pipedrive.get_pipeline_id(pipeline_name)
            if not pipeline_id:
                continue
            
            deals_dto = await self.pipedrive.get_deals(pipeline_id=pipeline_id)
            
            for dto in deals_dto:
                owner_id = str(dto.owner_id)  # Simplified - would map to name
                owner_name = f"Owner-{owner_id}"  # Placeholder
                
                # Count projects
                owner_metrics[owner_name]["projects_count"] += 1
                
                # Sum value
                if dto.value:
                    owner_metrics[owner_name]["estimated_value_sar"] += dto.value
                
                # Check if moved to production (simplified)
                if dto.status and "won" in dto.status.lower():
                    owner_metrics[owner_name]["moved_to_production_count"] += 1
                
                # Check overdue
                if dto.last_activity_date:
                    last_activity = datetime.fromisoformat(dto.last_activity_date.replace('Z', '+00:00'))
                    if (now - last_activity).days >= 7:
                        owner_metrics[owner_name]["overdue_deals_count"] += 1
                
                # Check stuck
                if dto.update_time:
                    update_time = datetime.fromisoformat(dto.update_time.replace('Z', '+00:00'))
                    if (now - update_time).days >= 30:
                        owner_metrics[owner_name]["stuck_deals_count"] += 1
                
                # Activities count (simplified - would query activities endpoint)
                owner_metrics[owner_name]["activities_count"] += 1
        
        # Convert to OwnerKPI objects
        results = []
        for owner_name, metrics in owner_metrics.items():
            kpi = OwnerKPI(
                owner=owner_name,
                **metrics
            )
            results.append(kpi)
        
        return sorted(results, key=lambda k: k.estimated_value_sar, reverse=True)


# Global service instance
_owner_kpi_service: Optional[OwnerKPIService] = None


def get_owner_kpi_service() -> OwnerKPIService:
    """Get or create owner KPI service singleton."""
    global _owner_kpi_service
    if _owner_kpi_service is None:
        _owner_kpi_service = OwnerKPIService()
    return _owner_kpi_service