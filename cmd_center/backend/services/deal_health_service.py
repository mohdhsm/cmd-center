"""Deal health service for identifying overdue and stuck deals."""

from typing import List, Optional
from datetime import datetime, timedelta, timezone

from ..models import DealBase, OverdueDeal, StuckDeal
from ..integrations import get_pipedrive_client, get_config


class DealHealthService:
    """Service for analyzing deal health (overdue, stuck, etc.)."""
    
    def __init__(self):
        self.pipedrive = get_pipedrive_client()
        self.config = get_config()
        self._pipeline_name_cache: dict[int, str] = {}
        self._stage_name_cache: dict[int, str] = {}
    
    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        # Pipedrive returns "YYYY-MM-DD HH:MM:SS" or ISO with Z
        clean = value.replace("Z", "+00:00") if "Z" in value else value
        try:
            return datetime.fromisoformat(clean)
        except Exception:
            return None

    async def _get_pipeline_name(self, pipeline_id: Optional[int], default: str) -> str:
        if pipeline_id is None:
            return default
        if pipeline_id not in self._pipeline_name_cache:
            pipelines = await self.pipedrive.get_pipelines()
            for p in pipelines:
                pid = p.get("id")
                if pid is not None:
                    self._pipeline_name_cache[pid] = p.get("name", f"Pipeline {pid}")
        return self._pipeline_name_cache.get(pipeline_id, default)

    async def _get_stage_name(self, stage_id: Optional[int], pipeline_id: Optional[int]) -> str:
        if stage_id is None:
            return "Unknown"
        if stage_id not in self._stage_name_cache:
            stages = await self.pipedrive.get_stages(pipeline_id=pipeline_id)
            for s in stages:
                sid = s.get("id")
                if sid is not None:
                    self._stage_name_cache[sid] = s.get("name", f"Stage {sid}")
        return self._stage_name_cache.get(stage_id, f"Stage {stage_id}")

    async def _dto_to_deal_base(self, dto, default_pipeline_name: str) -> DealBase:
        """Convert Pipedrive DTO to DealBase with mapped names."""
        pipeline_name = await self._get_pipeline_name(dto.pipeline_id, default_pipeline_name)
        stage_name = await self._get_stage_name(dto.stage_id, dto.pipeline_id)
        owner_name = getattr(dto, "owner_name", None) or "Unknown"
        org_name = getattr(dto, "org_name", None)

        return DealBase(
            id=dto.id,
            title=dto.title,
            pipeline=pipeline_name,
            stage=stage_name,
            owner=owner_name,
            org_name=org_name,
            value_sar=dto.value,
            status=dto.status,
            add_time=self._parse_datetime(dto.add_time),
            update_time=self._parse_datetime(dto.update_time),
            last_activity_time=self._parse_datetime(dto.last_activity_date),
        )
    
    async def get_overdue_deals(
        self,
        pipeline_name: str = "Aramco Projects",
        min_days: int = 7,limit: int= 500
    ) -> List[OverdueDeal]:
        """Get deals that are overdue."""
        # Get pipeline ID
        pipeline_id = await self.pipedrive.get_pipeline_id(pipeline_name)
        if not pipeline_id:
            return []
        
        # Get all deals in pipeline
        deals_dto = await self.pipedrive.get_deals(pipeline_id=pipeline_id, status="open", limit=limit)
        print("pipeline id is ", pipeline_id) 
        overdue_deals = []
        now = datetime.now(timezone.utc)

        
        for dto in deals_dto:
            if not dto.update_time:
                continue
            
            update_time = self._parse_datetime(dto.update_time)
            print(dto.update_time)
            if not update_time:
                continue
            days_overdue = (now - update_time).days
            
            if days_overdue >= min_days:
                deal_base = await self._dto_to_deal_base(dto, pipeline_name)
                overdue_deal = OverdueDeal(
                    **deal_base.model_dump(),
                    overdue_days=days_overdue,
                )
                overdue_deals.append(overdue_deal)
        
        return sorted(overdue_deals, key=lambda d: d.overdue_days, reverse=True)
    
    async def get_stuck_deals(
        self,
        pipeline_name: str = "Aramco Projects",
        min_days: int = 30, limit: int = 500
    ) -> List[StuckDeal]:
        """Get deals stuck in the same stage."""
        pipeline_id = await self.pipedrive.get_pipeline_id(pipeline_name)
        if not pipeline_id:
            return []
        
        deals_dto = await self.pipedrive.get_deals(pipeline_id=pipeline_id,status="open",limit=limit)
        
        stuck_deals = []
        now = datetime.now(timezone.utc)
        
        for dto in deals_dto:
            if not dto.update_time:
                continue
            
            update_time = self._parse_datetime(dto.update_time)
            if not update_time:
                continue
            days_in_stage = (now - update_time).days
            
            if days_in_stage >= min_days:
                deal_base = await self._dto_to_deal_base(dto, pipeline_name)
                stuck_deal = StuckDeal(
                    **deal_base.model_dump(),
                    days_in_stage=days_in_stage,
                )
                stuck_deals.append(stuck_deal)
        
        return sorted(stuck_deals, key=lambda d: d.days_in_stage, reverse=True)
    
    async def get_deal_detail(self, deal_id: int) -> Optional[DealBase]:
        """Get detailed information for a single deal."""
        dto = await self.pipedrive.get_deal(deal_id)
        
        if dto:
            return await self._dto_to_deal_base(dto, "Aramco Projects")
        
        return None


# Global service instance
_deal_health_service: Optional[DealHealthService] = None


def get_deal_health_service() -> DealHealthService:
    """Get or create deal health service singleton."""
    global _deal_health_service
    if _deal_health_service is None:
        _deal_health_service = DealHealthService()
    return _deal_health_service
