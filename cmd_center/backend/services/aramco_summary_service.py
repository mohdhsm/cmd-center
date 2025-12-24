"""Aramco Summary Service for generating CEO radar dashboards.

MIGRATION NOTE: This service has been enhanced to use WriterService
for LLM-powered deal summarization and recommendations.
See docs/LLM_Architecture_Implementation.md for migration details.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict
from statistics import median

from sqlmodel import Session, select

from ..db import Deal, Note, Stage, DealStageSpan, engine
from ..models import (
    OverdueSummaryResponse,
    OverdueSnapshot,
    PMOverduePerformance,
    CEOInterventionDeal,
    StuckSummaryResponse,
    StuckSnapshot,
    PMStuckControl,
    WorstStuckDeal,
    StageBottleneck,
    OrderReceivedSummaryResponse,
    OrderReceivedSnapshot,
    PMPipelineAcceleration,
    BlockersChecklistSummary,
    FastWinDeal,
    DealSummaryContext,
)
from .writer_service import get_writer_service

logger = logging.getLogger(__name__)


# Custom field key for End User (from Pipedrive schema)
END_USER_FIELD_KEY = "bd7bb3b2758ca81feebf015ca60bf528eafe47f0"

# Order Received stage IDs (from docs/pipedrive_Schema_info.md)
ORDER_RECEIVED_STAGE_IDS = [27, 28, 29, 45]


class AramcoSummaryService:
    """Service for generating mode-specific CEO radar summaries.

    Enhanced with WriterService for LLM-powered insights including:
    - Deal blocking detection
    - Suggested next steps
    - Risk assessment
    """

    def __init__(self):
        self.session = Session(engine)
        self.writer = get_writer_service()

    def generate_overdue_summary(self, pipeline_name: str = "Aramco Projects") -> OverdueSummaryResponse:
        """
        Generate overdue summary modal data.

        Calculates executive snapshot, PM performance metrics, and CEO intervention list
        for overdue deals.
        """
        # Get all overdue deals (deals not updated in last 7+ days)
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        two_weeks_ago = today - timedelta(days=14)

        # Fetch overdue deals
        statement = select(Deal).where(
            Deal.status == "open",
            Deal.update_time < week_ago
        )
        overdue_deals = self.session.exec(statement).all()

        if not overdue_deals:
            # Return empty response
            return OverdueSummaryResponse(
                snapshot=OverdueSnapshot(
                    overdue_now_count=0,
                    overdue_now_sar=0.0,
                    overdue_soon_count=0,
                    overdue_soon_sar=0.0,
                    worst_overdue=[]
                ),
                pm_performance=[],
                intervention_list=[]
            )

        # Calculate days overdue for each deal
        deals_with_metrics = []
        for deal in overdue_deals:
            if deal.update_time:
                days_overdue = (today - deal.update_time).days
                deals_with_metrics.append({
                    "deal": deal,
                    "days_overdue": days_overdue,
                    "days_since_update": days_overdue,
                })

        # === EXECUTIVE SNAPSHOT ===

        # Overdue now (>7 days)
        overdue_now = [d for d in deals_with_metrics if d["days_overdue"] >= 7]
        overdue_now_count = len(overdue_now)
        overdue_now_sar = sum(d["deal"].value for d in overdue_now)

        # Overdue soon (deals with next_activity in next 7-14 days from now)
        statement_soon = select(Deal).where(
            Deal.status == "open",
            Deal.next_activity_date.is_not(None),
            Deal.next_activity_date >= today,
            Deal.next_activity_date <= today + timedelta(days=14)
        )
        soon_deals = self.session.exec(statement_soon).all()
        overdue_soon_count = len(soon_deals)
        overdue_soon_sar = sum(d.value for d in soon_deals)

        # Worst overdue (top 5 by days)
        sorted_overdue = sorted(deals_with_metrics, key=lambda x: x["days_overdue"], reverse=True)
        worst_overdue = [
            {
                "deal_id": d["deal"].id,
                "title": d["deal"].title,
                "days": d["days_overdue"],
                "sar": d["deal"].value
            }
            for d in sorted_overdue[:5]
        ]

        snapshot = OverdueSnapshot(
            overdue_now_count=overdue_now_count,
            overdue_now_sar=overdue_now_sar,
            overdue_soon_count=overdue_soon_count,
            overdue_soon_sar=overdue_soon_sar,
            worst_overdue=worst_overdue
        )

        # === PM PERFORMANCE TABLE ===

        # Group by PM (owner)
        pm_metrics = defaultdict(lambda: {
            "overdue_now": [],
            "due_soon": [],
            "updated_this_week": 0,
            "has_next_activity": 0,
        })

        for item in deals_with_metrics:
            deal = item["deal"]
            pm_name = deal.owner_name or "Unknown"

            if item["days_overdue"] >= 7:
                pm_metrics[pm_name]["overdue_now"].append(deal)

        # Add soon deals to PM metrics
        for deal in soon_deals:
            pm_name = deal.owner_name or "Unknown"
            pm_metrics[pm_name]["due_soon"].append(deal)

        # Count updated this week and has next activity
        statement_all = select(Deal).where(Deal.status == "open")
        all_deals = self.session.exec(statement_all).all()

        for deal in all_deals:
            pm_name = deal.owner_name or "Unknown"
            if deal.update_time and deal.update_time >= week_ago:
                pm_metrics[pm_name]["updated_this_week"] += 1
            if deal.next_activity_date:
                pm_metrics[pm_name]["has_next_activity"] += 1

        # Build PM performance list
        pm_performance = []
        for pm_name, metrics in pm_metrics.items():
            overdue_count = len(metrics["overdue_now"])
            overdue_sar = sum(d.value for d in metrics["overdue_now"])
            due_soon_count = len(metrics["due_soon"])
            due_soon_sar = sum(d.value for d in metrics["due_soon"])

            # Calculate average days overdue
            if metrics["overdue_now"]:
                avg_days = sum(
                    (today - d.update_time).days for d in metrics["overdue_now"] if d.update_time
                ) / len(metrics["overdue_now"])
            else:
                avg_days = 0.0

            # Calculate risk score
            no_activity_count = overdue_count - metrics["has_next_activity"]
            risk_score = self._calculate_risk_score(
                overdue_count, due_soon_count, max(0, no_activity_count)
            )

            pm_performance.append(
                PMOverduePerformance(
                    pm_name=pm_name,
                    overdue_now_count=overdue_count,
                    overdue_now_sar=overdue_sar,
                    due_soon_count=due_soon_count,
                    due_soon_sar=due_soon_sar,
                    avg_days_overdue=avg_days,
                    updated_this_week_count=metrics["updated_this_week"],
                    has_next_activity_count=metrics["has_next_activity"],
                    risk_score=risk_score
                )
            )

        # Sort by risk score descending
        pm_performance.sort(key=lambda x: x.risk_score, reverse=True)

        # === CEO INTERVENTION LIST ===

        intervention_list = []
        for item in sorted_overdue[:10]:  # Top 10
            deal = item["deal"]

            # Get last note snippet
            note_stmt = select(Note).where(Note.deal_id == deal.id).order_by(Note.add_time.desc()).limit(1)
            notes = self.session.exec(note_stmt).all()
            last_note = notes[0].content[:100] if notes else None

            # Get stage name
            stage_stmt = select(Stage).where(Stage.id == deal.stage_id)
            stage = self.session.exec(stage_stmt).first()
            stage_name = stage.name if stage else "Unknown"

            intervention_list.append(
                CEOInterventionDeal(
                    deal_id=deal.id,
                    title=deal.title,
                    pm_name=deal.owner_name or "Unknown",
                    stage=stage_name,
                    overdue_by_days=item["days_overdue"],
                    days_since_update=item["days_since_update"],
                    last_note_snippet=last_note,
                    next_activity_date=deal.next_activity_date.isoformat() if deal.next_activity_date else None,
                    next_activity_exists=deal.next_activity_date is not None
                )
            )

        return OverdueSummaryResponse(
            snapshot=snapshot,
            pm_performance=pm_performance,
            intervention_list=intervention_list
        )

    def generate_stuck_summary(self, pipeline_name: str = "Aramco Projects") -> StuckSummaryResponse:
        """
        Generate stuck summary modal data.

        Calculates executive snapshot, PM stuck control metrics, worst stuck deals,
        and stage bottleneck analysis.
        """
        today = datetime.now()
        thirty_days_ago = today - timedelta(days=30)

        # Get all stuck deals (days_in_stage > 30)
        statement = select(Deal).where(
            Deal.status == "open",
            Deal.stage_change_time.is_not(None),
            Deal.stage_change_time < thirty_days_ago
        )
        stuck_deals = self.session.exec(statement).all()

        if not stuck_deals:
            return StuckSummaryResponse(
                snapshot=StuckSnapshot(
                    stuck_no_updates_count=0,
                    stuck_no_updates_sar=0.0,
                    bucket_30_45_count=0,
                    bucket_30_45_sar=0.0,
                    bucket_46_60_count=0,
                    bucket_46_60_sar=0.0,
                    bucket_60_plus_count=0,
                    bucket_60_plus_sar=0.0,
                    no_activity_count=0,
                    oldest_stuck=[]
                ),
                pm_control=[],
                worst_deals=[],
                stage_bottlenecks=[],
                top_bottleneck_stage="N/A"
            )

        # Calculate days in stage
        deals_with_metrics = []
        for deal in stuck_deals:
            if deal.stage_change_time:
                days_in_stage = (today - deal.stage_change_time).days
                days_since_update = (today - deal.update_time).days if deal.update_time else 0
                deals_with_metrics.append({
                    "deal": deal,
                    "days_in_stage": days_in_stage,
                    "days_since_update": days_since_update,
                })

        # === EXECUTIVE SNAPSHOT ===

        # Stuck >30d & no updates in last 30 days
        no_updates = [d for d in deals_with_metrics if d["days_since_update"] > 30]
        stuck_no_updates_count = len(no_updates)
        stuck_no_updates_sar = sum(d["deal"].value for d in no_updates)

        # Severity buckets
        bucket_30_45 = [d for d in deals_with_metrics if 30 <= d["days_in_stage"] < 46]
        bucket_46_60 = [d for d in deals_with_metrics if 46 <= d["days_in_stage"] < 61]
        bucket_60_plus = [d for d in deals_with_metrics if d["days_in_stage"] >= 61]

        # No next activity
        no_activity = [d for d in deals_with_metrics if d["deal"].next_activity_date is None]

        # Oldest stuck (top 5)
        sorted_stuck = sorted(deals_with_metrics, key=lambda x: x["days_in_stage"], reverse=True)
        oldest_stuck = [
            {
                "deal_id": d["deal"].id,
                "title": d["deal"].title,
                "days_in_stage": d["days_in_stage"],
                "sar": d["deal"].value
            }
            for d in sorted_stuck[:5]
        ]

        snapshot = StuckSnapshot(
            stuck_no_updates_count=stuck_no_updates_count,
            stuck_no_updates_sar=stuck_no_updates_sar,
            bucket_30_45_count=len(bucket_30_45),
            bucket_30_45_sar=sum(d["deal"].value for d in bucket_30_45),
            bucket_46_60_count=len(bucket_46_60),
            bucket_46_60_sar=sum(d["deal"].value for d in bucket_46_60),
            bucket_60_plus_count=len(bucket_60_plus),
            bucket_60_plus_sar=sum(d["deal"].value for d in bucket_60_plus),
            no_activity_count=len(no_activity),
            oldest_stuck=oldest_stuck
        )

        # === PM STUCK CONTROL TABLE ===

        pm_metrics = defaultdict(lambda: {"deals": [], "no_activity_sar": 0.0})

        for item in deals_with_metrics:
            deal = item["deal"]
            pm_name = deal.owner_name or "Unknown"
            pm_metrics[pm_name]["deals"].append(item)
            if deal.next_activity_date is None:
                pm_metrics[pm_name]["no_activity_sar"] += deal.value

        pm_control = []
        for pm_name, metrics in pm_metrics.items():
            stuck_count = len(metrics["deals"])
            stuck_sar = sum(d["deal"].value for d in metrics["deals"])
            avg_days = sum(d["days_in_stage"] for d in metrics["deals"]) / stuck_count if stuck_count > 0 else 0.0
            days_since_update_list = [d["days_since_update"] for d in metrics["deals"]]
            median_days_update = median(days_since_update_list) if days_since_update_list else 0.0

            # Calculate recovery rate using stage history
            # Get all stage IDs where this PM has stuck deals
            stuck_stage_ids = list({d["deal"].stage_id for d in metrics["deals"]})
            recovery_rate = self._calculate_recovery_rate_30d(pm_name, stuck_stage_ids)

            pm_control.append(
                PMStuckControl(
                    pm_name=pm_name,
                    stuck_count=stuck_count,
                    stuck_sar=stuck_sar,
                    stuck_no_activity_sar=metrics["no_activity_sar"],
                    avg_days_in_stage=avg_days,
                    median_days_since_update=median_days_update,
                    recovery_rate_30d=recovery_rate
                )
            )

        # Sort by SAR descending
        pm_control.sort(key=lambda x: x.stuck_sar, reverse=True)

        # === WORST STUCK DEALS LIST ===

        worst_deals = []
        for item in sorted_stuck[:10]:
            deal = item["deal"]

            # Get last note
            note_stmt = select(Note).where(Note.deal_id == deal.id).order_by(Note.add_time.desc()).limit(1)
            notes = self.session.exec(note_stmt).all()
            last_note = notes[0].content[:100] if notes else None

            # Get stage name
            stage_stmt = select(Stage).where(Stage.id == deal.stage_id)
            stage = self.session.exec(stage_stmt).first()
            stage_name = stage.name if stage else "Unknown"

            # Get recent notes for LLM analysis
            recent_notes_stmt = select(Note).where(Note.deal_id == deal.id).order_by(Note.add_time.desc()).limit(5)
            recent_notes = self.session.exec(recent_notes_stmt).all()
            notes_content = [note.content for note in recent_notes if note.content]

            # Use WriterService to analyze deal and generate insights
            blocking_flag = None
            suggested_next_step = None
            try:
                summary_result = self._analyze_stuck_deal_async(
                    deal_id=deal.id,
                    deal_title=deal.title,
                    stage=stage_name,
                    owner_name=deal.owner_name or "Unknown",
                    days_in_stage=item["days_in_stage"],
                    notes=notes_content
                )
                if summary_result:
                    # Extract blockers as blocking_flag
                    if summary_result.blockers:
                        blocking_flag = summary_result.blockers[0]  # Primary blocker
                    # Use next_action as suggested_next_step
                    suggested_next_step = summary_result.next_action
            except Exception as e:
                logger.warning(f"Failed to analyze stuck deal {deal.id} with LLM: {e}")
                # Continue without LLM insights

            worst_deals.append(
                WorstStuckDeal(
                    deal_id=deal.id,
                    title=deal.title,
                    pm_name=deal.owner_name or "Unknown",
                    stage=stage_name,
                    days_in_stage=item["days_in_stage"],
                    last_update_age=item["days_since_update"],
                    last_note_snippet=last_note,
                    blocking_flag=blocking_flag,
                    suggested_next_step=suggested_next_step
                )
            )

        # === STAGE BOTTLENECK VIEW ===

        stage_metrics = defaultdict(lambda: {"count": 0, "sar": 0.0})

        for item in deals_with_metrics:
            deal = item["deal"]
            stage_stmt = select(Stage).where(Stage.id == deal.stage_id)
            stage = self.session.exec(stage_stmt).first()
            stage_name = stage.name if stage else "Unknown"

            stage_metrics[stage_name]["count"] += 1
            stage_metrics[stage_name]["sar"] += deal.value

        stage_bottlenecks = [
            StageBottleneck(
                stage_name=stage_name,
                stuck_count=metrics["count"],
                stuck_sar=metrics["sar"]
            )
            for stage_name, metrics in stage_metrics.items()
        ]

        # Sort by SAR descending
        stage_bottlenecks.sort(key=lambda x: x.stuck_sar, reverse=True)

        top_bottleneck_stage = stage_bottlenecks[0].stage_name if stage_bottlenecks else "N/A"

        return StuckSummaryResponse(
            snapshot=snapshot,
            pm_control=pm_control,
            worst_deals=worst_deals,
            stage_bottlenecks=stage_bottlenecks,
            top_bottleneck_stage=top_bottleneck_stage
        )

    def generate_order_received_summary(self, pipeline_name: str = "Aramco Projects") -> OrderReceivedSummaryResponse:
        """
        Generate Order Received summary modal data.

        Calculates executive snapshot, PM pipeline acceleration metrics,
        blockers checklist, and fast wins opportunities.
        """
        today = datetime.now()

        # Get all Order Received deals
        statement = select(Deal).where(
            Deal.status == "open",
            Deal.stage_id.in_(ORDER_RECEIVED_STAGE_IDS)
        )
        order_deals = self.session.exec(statement).all()

        if not order_deals:
            return OrderReceivedSummaryResponse(
                snapshot=OrderReceivedSnapshot(
                    open_count=0,
                    open_sar=0.0,
                    bucket_0_7_count=0,
                    bucket_0_7_sar=0.0,
                    bucket_8_14_count=0,
                    bucket_8_14_sar=0.0,
                    bucket_15_30_count=0,
                    bucket_15_30_sar=0.0,
                    bucket_30_plus_count=0,
                    bucket_30_plus_sar=0.0,
                    oldest_deal={},
                    conversion_rate_30d=None
                ),
                pm_acceleration=[],
                blockers_checklist=BlockersChecklistSummary(
                    missing_end_user_count=0,
                    missing_next_activity_count=0
                ),
                fast_wins=[]
            )

        # Calculate age (days_in_stage)
        deals_with_metrics = []
        for deal in order_deals:
            if deal.stage_change_time:
                age_days = (today - deal.stage_change_time).days
            else:
                age_days = 0

            # Extract custom fields
            has_end_user = self._extract_custom_field(deal, END_USER_FIELD_KEY) is not None

            deals_with_metrics.append({
                "deal": deal,
                "age_days": age_days,
                "has_end_user": has_end_user,
            })

        # === EXECUTIVE SNAPSHOT ===

        open_count = len(order_deals)
        open_sar = sum(d.value for d in order_deals)

        # Aging buckets
        bucket_0_7 = [d for d in deals_with_metrics if 0 <= d["age_days"] <= 7]
        bucket_8_14 = [d for d in deals_with_metrics if 8 <= d["age_days"] <= 14]
        bucket_15_30 = [d for d in deals_with_metrics if 15 <= d["age_days"] <= 30]
        bucket_30_plus = [d for d in deals_with_metrics if d["age_days"] > 30]

        # Oldest deal
        sorted_by_age = sorted(deals_with_metrics, key=lambda x: x["age_days"], reverse=True)
        oldest_deal = {
            "deal_id": sorted_by_age[0]["deal"].id,
            "title": sorted_by_age[0]["deal"].title,
            "age_days": sorted_by_age[0]["age_days"]
        } if sorted_by_age else {}

        # Calculate conversion rate: Order Received -> Approved
        # Stage 28 = Approved (from ORDER_RECEIVED_STAGE_IDS)
        approved_stage_id = 28
        conversion_rate = self._calculate_conversion_rate_30d(ORDER_RECEIVED_STAGE_IDS, approved_stage_id)

        snapshot = OrderReceivedSnapshot(
            open_count=open_count,
            open_sar=open_sar,
            bucket_0_7_count=len(bucket_0_7),
            bucket_0_7_sar=sum(d["deal"].value for d in bucket_0_7),
            bucket_8_14_count=len(bucket_8_14),
            bucket_8_14_sar=sum(d["deal"].value for d in bucket_8_14),
            bucket_15_30_count=len(bucket_15_30),
            bucket_15_30_sar=sum(d["deal"].value for d in bucket_15_30),
            bucket_30_plus_count=len(bucket_30_plus),
            bucket_30_plus_sar=sum(d["deal"].value for d in bucket_30_plus),
            oldest_deal=oldest_deal,
            conversion_rate_30d=conversion_rate
        )

        # === PM PIPELINE ACCELERATION TABLE ===

        pm_metrics = defaultdict(lambda: {"deals": []})

        for item in deals_with_metrics:
            deal = item["deal"]
            pm_name = deal.owner_name or "Unknown"
            pm_metrics[pm_name]["deals"].append(item)

        pm_acceleration = []
        for pm_name, metrics in pm_metrics.items():
            deals = metrics["deals"]
            open_count = len(deals)
            open_sar = sum(d["deal"].value for d in deals)
            avg_age = sum(d["age_days"] for d in deals) / open_count if open_count > 0 else 0.0

            # % with end-user identified
            has_end_user_count = sum(1 for d in deals if d["has_end_user"])
            pct_end_user = (has_end_user_count / open_count * 100) if open_count > 0 else 0.0

            # % with next activity
            has_activity_count = sum(1 for d in deals if d["deal"].next_activity_date is not None)
            pct_next_activity = (has_activity_count / open_count * 100) if open_count > 0 else 0.0

            # Get approved deals in last 30 days
            approved_count, approved_sar = self._get_approved_deals_30d(pm_name, approved_stage_id)

            pm_acceleration.append(
                PMPipelineAcceleration(
                    pm_name=pm_name,
                    open_count=open_count,
                    open_sar=open_sar,
                    avg_age_days=avg_age,
                    pct_end_user_identified=pct_end_user,
                    pct_next_activity_scheduled=pct_next_activity,
                    approved_30d_count=approved_count,
                    approved_30d_sar=approved_sar
                )
            )

        # === BLOCKERS CHECKLIST ===

        missing_end_user_count = sum(1 for d in deals_with_metrics if not d["has_end_user"])
        missing_next_activity_count = sum(1 for d in order_deals if d.next_activity_date is None)

        blockers_checklist = BlockersChecklistSummary(
            missing_end_user_count=missing_end_user_count,
            missing_site_contact_count=None,  # TODO: field key unknown
            missing_po_count=None,  # TODO
            missing_dates_count=None,  # TODO
            missing_product_type_count=None,  # TODO
            missing_quantity_count=None,  # TODO
            missing_next_activity_count=missing_next_activity_count
        )

        # === FAST WINS LIST ===

        # Deals missing only 1-2 items, high value (>50K) OR old (>15 days)
        fast_wins = []
        for item in deals_with_metrics:
            deal = item["deal"]
            missing_items = []

            if not item["has_end_user"]:
                missing_items.append("End user")
            if deal.next_activity_date is None:
                missing_items.append("Next activity")

            # Check if qualifies as fast win
            missing_count = len(missing_items)
            if 1 <= missing_count <= 2 and (deal.value > 50000 or item["age_days"] > 15):
                suggested_action = f"Add {', '.join(missing_items).lower()} to unlock deal"

                fast_wins.append(
                    FastWinDeal(
                        deal_id=deal.id,
                        title=deal.title,
                        pm_name=deal.owner_name or "Unknown",
                        value_sar=deal.value,
                        age_days=item["age_days"],
                        missing_items=missing_items,
                        suggested_action=suggested_action
                    )
                )

        # Sort by value descending, limit to 10
        fast_wins.sort(key=lambda x: x.value_sar, reverse=True)
        fast_wins = fast_wins[:10]

        return OrderReceivedSummaryResponse(
            snapshot=snapshot,
            pm_acceleration=pm_acceleration,
            blockers_checklist=blockers_checklist,
            fast_wins=fast_wins
        )

    # === LLM-POWERED ANALYSIS METHODS ===

    def _analyze_stuck_deal_async(
        self,
        deal_id: int,
        deal_title: str,
        stage: str,
        owner_name: str,
        days_in_stage: int,
        notes: list[str]
    ):
        """Analyze stuck deal using WriterService.

        This is a synchronous wrapper that will be called within an async context.
        For now, we return None and log - proper async integration would require
        making generate_stuck_summary async.

        Args:
            deal_id: Deal ID
            deal_title: Deal title
            stage: Current stage name
            owner_name: Owner name
            days_in_stage: Days in current stage
            notes: Recent notes

        Returns:
            DealSummaryResult or None if analysis fails
        """
        # TODO: Make generate_stuck_summary async to properly await LLM calls
        # For now, we skip LLM analysis to avoid blocking I/O
        logger.info(
            f"Skipping LLM analysis for deal {deal_id} - "
            f"generate_stuck_summary needs to be made async"
        )
        return None

        # Future async implementation:
        # context = DealSummaryContext(
        #     deal_id=deal_id,
        #     deal_title=deal_title,
        #     stage=stage,
        #     owner_name=owner_name,
        #     days_in_stage=days_in_stage,
        #     notes=notes,
        #     include_recommendations=True,
        #     include_blockers=True,
        # )
        # return await self.writer.summarize_deal(context)

    # === HELPER METHODS ===

    def _calculate_recovery_rate_30d(self, pm_name: str, current_stage_ids: list[int]) -> Optional[float]:
        """
        Calculate recovery rate: % of deals that moved OUT of stuck stages in last 30 days.

        Recovery rate = (deals that left stage in last 30d) / (deals that were in stage 30d ago) * 100
        """
        thirty_days_ago = datetime.now() - timedelta(days=30)

        # Find deals that LEFT the current stuck stages in the last 30 days
        # These are spans where left_at is within last 30 days and stage_id matches
        statement = select(DealStageSpan).join(Deal).where(
            DealStageSpan.stage_id.in_(current_stage_ids),
            DealStageSpan.left_at.is_not(None),
            DealStageSpan.left_at >= thirty_days_ago,
            Deal.owner_name == pm_name
        )
        recovered_spans = self.session.exec(statement).all()
        recovered_count = len(recovered_spans)

        # Find deals that were in these stages 30 days ago
        # These are spans where entered_at <= 30d ago and (left_at is None OR left_at >= 30d ago)
        statement_total = select(DealStageSpan).join(Deal).where(
            DealStageSpan.stage_id.in_(current_stage_ids),
            DealStageSpan.entered_at <= thirty_days_ago,
            Deal.owner_name == pm_name
        ).where(
            (DealStageSpan.left_at.is_(None)) | (DealStageSpan.left_at >= thirty_days_ago)
        )
        total_spans = self.session.exec(statement_total).all()
        total_count = len(total_spans)

        if total_count == 0:
            return None

        return (recovered_count / total_count) * 100

    def _calculate_conversion_rate_30d(self, from_stage_ids: list[int], to_stage_id: int) -> Optional[float]:
        """
        Calculate conversion rate: % of deals that moved from Order Received stages to Approved in last 30 days.

        Conversion rate = (deals that moved to Approved in last 30d) / (deals in Order Received at start of period) * 100
        """
        thirty_days_ago = datetime.now() - timedelta(days=30)

        # Find spans where deal moved TO the approved stage in last 30 days
        # These are spans where stage_id = to_stage_id and entered_at is within last 30 days
        # AND the previous stage was one of the from_stage_ids
        statement_converted = select(DealStageSpan).where(
            DealStageSpan.stage_id == to_stage_id,
            DealStageSpan.entered_at >= thirty_days_ago,
            DealStageSpan.from_stage_id.in_(from_stage_ids)
        )
        converted_spans = self.session.exec(statement_converted).all()
        converted_count = len(converted_spans)

        # Find deals that were in from_stage_ids 30 days ago
        statement_total = select(DealStageSpan).where(
            DealStageSpan.stage_id.in_(from_stage_ids),
            DealStageSpan.entered_at <= thirty_days_ago
        ).where(
            (DealStageSpan.left_at.is_(None)) | (DealStageSpan.left_at >= thirty_days_ago)
        )
        total_spans = self.session.exec(statement_total).all()
        total_count = len(total_spans)

        if total_count == 0:
            return None

        return (converted_count / total_count) * 100

    def _get_approved_deals_30d(self, pm_name: str, approved_stage_id: int = 28) -> tuple[int, float]:
        """
        Get count and SAR of deals that moved to Approved stage in last 30 days for a specific PM.

        Returns: (count, total_sar)
        """
        thirty_days_ago = datetime.now() - timedelta(days=30)

        # Find spans where deal entered Approved stage in last 30 days
        statement = select(DealStageSpan).join(Deal).where(
            DealStageSpan.stage_id == approved_stage_id,
            DealStageSpan.entered_at >= thirty_days_ago,
            Deal.owner_name == pm_name
        )
        approved_spans = self.session.exec(statement).all()

        # Get unique deals and their values
        deal_ids = {span.deal_id for span in approved_spans}

        if not deal_ids:
            return (0, 0.0)

        # Get deal values
        statement_deals = select(Deal).where(Deal.id.in_(deal_ids))
        deals = self.session.exec(statement_deals).all()

        count = len(deals)
        total_sar = sum(deal.value for deal in deals)

        return (count, total_sar)

    def _calculate_risk_score(self, overdue_count: int, due_soon_count: int, no_activity_count: int) -> float:
        """Calculate PM risk score using weighted formula."""
        return (overdue_count * 3) + (due_soon_count * 2) + (no_activity_count * 5)

    def _extract_custom_field(self, deal: Deal, field_key: str):
        """Extract custom field from raw_json."""
        if deal.raw_json:
            try:
                data = json.loads(deal.raw_json)
                return data.get(field_key)
            except (json.JSONDecodeError, TypeError):
                return None
        return None


# Global service instance
_aramco_summary_service: Optional[AramcoSummaryService] = None


def get_aramco_summary_service() -> AramcoSummaryService:
    """Get or create Aramco summary service singleton."""
    global _aramco_summary_service
    if _aramco_summary_service is None:
        _aramco_summary_service = AramcoSummaryService()
    return _aramco_summary_service
