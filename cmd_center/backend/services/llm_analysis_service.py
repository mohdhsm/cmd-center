"""LLM analysis service for deal intelligence.

⚠️ DEPRECATED - This service is deprecated and will be removed in a future version.

Migration Guide:
----------------
This service has been superseded by WriterService which provides better separation
of concerns, type safety, and reliability.

OLD CODE (llm_analysis_service):
    service = get_llm_analysis_service()
    compliance = await service.analyze_compliance("Aramco Projects")

NEW CODE (writer_service):
    from cmd_center.backend.services.writer_service import get_writer_service
    from cmd_center.backend.models import ComplianceContext

    writer = get_writer_service()
    result = await writer.analyze_compliance(ComplianceContext(
        deal_id=deal.id,
        deal_title=deal.title,
        stage="Order Received",
        notes=notes,
        check_survey=True,
        check_quality_docs=True
    ))

Migration Mappings:
-------------------
- analyze_order_received() → writer.analyze_order_received(OrderReceivedContext(...))
- analyze_compliance() → writer.analyze_compliance(ComplianceContext(...))
- summarize_recent_deals() → writer.summarize_deal(DealSummaryContext(...))
- For batch operations → writer.batch_summarize_deals()

See docs/LLM_Architecture_Implementation.md for complete migration guide.
"""

import warnings
from typing import List, Optional

from ..models import OrderReceivedAnalysis, ComplianceStatus, DealSummary, DealNote
from ..integrations import get_pipedrive_client, get_llm_client
from .deal_health_service import get_deal_health_service

# Issue deprecation warning when module is imported
warnings.warn(
    "llm_analysis_service is deprecated and will be removed in a future version. "
    "Use writer_service instead. See module docstring for migration guide.",
    DeprecationWarning,
    stacklevel=2
)


class LLMAnalysisService:
    """Service for LLM-powered deal analysis.

    ⚠️ DEPRECATED - Use WriterService instead.
    """

    def __init__(self):
        warnings.warn(
            "LLMAnalysisService is deprecated. Use WriterService instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.pipedrive = get_pipedrive_client()
        self.llm = get_llm_client()
        self.deal_health = get_deal_health_service()

    async def analyze_order_received(
        self,
        pipeline_name: str = "Aramco Projects",
        min_days: int = 30,
    ) -> List[OrderReceivedAnalysis]:
        """Analyze deals in 'Order received' stage.

        ⚠️ DEPRECATED - Use writer.analyze_order_received(OrderReceivedContext(...)) instead.
        """
        warnings.warn(
            "analyze_order_received() is deprecated. "
            "Use writer.analyze_order_received(OrderReceivedContext(...)) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # Get stuck deals (which includes order received)
        stuck_deals = self.deal_health.get_stuck_deals(pipeline_name, min_days)
        
        # Filter for "Order received" stage (simplified - would need stage mapping)
        order_received_deals = [d for d in stuck_deals if "order" in d.stage.lower()]
        
        results = []
        for deal in order_received_deals[:10]:  # Limit to avoid excessive API calls
            # Get deal notes
            notes_dto = await self.pipedrive.get_deal_notes(deal.id)
            notes = [note.content for note in notes_dto]
            
            # Analyze with LLM
            analysis = await self.llm.analyze_order_received(deal.title, notes)
            
            order_analysis = OrderReceivedAnalysis(
                **deal.model_dump(),
                end_user_identified=analysis.get("end_user_identified"),
                end_user_requests_count=analysis.get("end_user_requests_count", 0),
            )
            results.append(order_analysis)
        
        return results
    
    async def analyze_compliance(
        self,
        pipeline_name: str = "Aramco Projects",
    ) -> List[ComplianceStatus]:
        """Analyze deals for compliance documentation.

        ⚠️ DEPRECATED - Use writer.analyze_compliance(ComplianceContext(...)) instead.
        """
        warnings.warn(
            "analyze_compliance() is deprecated. "
            "Use writer.analyze_compliance(ComplianceContext(...)) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        pipeline_id = await self.pipedrive.get_pipeline_id(pipeline_name)
        if not pipeline_id:
            return []
        
        deals_dto = await self.pipedrive.get_deals(pipeline_id=pipeline_id, limit=50)
        
        results = []
        for dto in deals_dto:
            # Get deal notes
            notes_dto = await self.pipedrive.get_deal_notes(dto.id)
            notes = [note.content for note in notes_dto]
            
            # Get base deal info
            deal_base = self.deal_health.get_deal_detail(dto.id)
            if not deal_base:
                continue
            
            # Analyze compliance
            compliance = await self.llm.analyze_deal_compliance(
                dto.title,
                "Unknown",  # Would map stage_id
                notes,
            )
            
            compliance_status = ComplianceStatus(
                **deal_base.model_dump(),
                survey_checklist_present=compliance.get("survey_checklist"),
                quality_docs_present=compliance.get("quality_docs"),
                comment=compliance.get("comment", ""),
            )
            results.append(compliance_status)
        
        return results
    
    async def summarize_recent_deals(
        self,
        pipeline_name: str = "pipeline",
        days: int = 14,
    ) -> List[DealSummary]:
        """Generate summaries for recently active deals.

        ⚠️ DEPRECATED - Use writer.summarize_deal(DealSummaryContext(...)) instead.
        """
        warnings.warn(
            "summarize_recent_deals() is deprecated. "
            "Use writer.summarize_deal(DealSummaryContext(...)) or batch_summarize_deals() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        pipeline_id = await self.pipedrive.get_pipeline_id(pipeline_name)
        if not pipeline_id:
            return []
        
        deals_dto = await self.pipedrive.get_deals(pipeline_id=pipeline_id, limit=20)
        
        results = []
        for dto in deals_dto:
            # Get deal notes
            notes_dto = await self.pipedrive.get_deal_notes(dto.id)
            notes = [note.content for note in notes_dto]
            
            # Get base deal info
            deal_base = self.deal_health.get_deal_detail(dto.id)
            if not deal_base:
                continue
            
            # Generate summary
            summary_data = await self.llm.summarize_deal(
                dto.title,
                "Unknown",  # Would map stage_id
                notes,
            )
            
            deal_summary = DealSummary(
                **deal_base.model_dump(),
                llm_summary=summary_data.get("summary", "No summary available"),
                next_action=summary_data.get("next_action"),
            )
            results.append(deal_summary)
        
        return results
    
    async def get_deal_notes(self, deal_id: int) -> List[DealNote]:
        """Get notes for a specific deal."""
        notes_dto = await self.pipedrive.get_deal_notes(deal_id)
        
        notes = []
        for dto in notes_dto:
            note = DealNote(
                id=dto.id,
                date=dto.add_time,
                author=None,  # Would map user_id to name
                content=dto.content,
            )
            notes.append(note)
        
        return notes


# Global service instance
_llm_analysis_service: Optional[LLMAnalysisService] = None


def get_llm_analysis_service() -> LLMAnalysisService:
    """Get or create LLM analysis service singleton."""
    global _llm_analysis_service
    if _llm_analysis_service is None:
        _llm_analysis_service = LLMAnalysisService()
    return _llm_analysis_service