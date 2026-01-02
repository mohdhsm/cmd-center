"""CEO Dashboard service for aggregating executive metrics."""

import logging
from typing import Optional
from datetime import datetime, timedelta
from sqlmodel import Session, select, func

from ..db import engine, Deal, DealStageSpan, Stage
from ..constants import PIPELINE_NAME_TO_ID, PIPELINE_ID_TO_NAME
from ..models.ceo_dashboard_models import (
    CashHealth,
    UrgentDeal,
    PipelineStage,
    PipelineVelocity,
    StrategicPriority,
    SalesScorecard,
    DepartmentScorecard,
    CEODashboardMetrics,
)
from ..models.cashflow_models import CashflowPredictionInput
from .cashflow_prediction_service import get_cashflow_prediction_service
from .deal_health_service import get_deal_health_service
from . import db_queries

logger = logging.getLogger(__name__)


# Configurable targets (can be moved to .env or constants.py)
class CEODashboardConfig:
    """Configuration for CEO Dashboard metrics."""

    # Cash health thresholds
    RUNWAY_GREEN_MONTHS = 3.0  # >3 months = green
    RUNWAY_YELLOW_MONTHS = 1.0  # 1-3 months = yellow, <1 = red

    # Collection targets (SAR) - placeholders
    ARAMCO_WEEKLY_TARGET = 200000.0
    COMMERCIAL_WEEKLY_TARGET = 100000.0

    # Commercial placeholder values (until manual input is implemented)
    COMMERCIAL_WEEKLY_COLLECTED = 0.0

    # Velocity thresholds
    VELOCITY_GREEN_PCT = 80.0
    VELOCITY_YELLOW_PCT = 50.0

    # Pipeline targets
    TARGET_CYCLE_DAYS = 21.0

    # Strategic priority targets
    COST_REDUCTION_TARGET_PCT = 20.0
    WEEKLY_SALES_TARGET_SAR = 500000.0
    COMMERCIAL_SHARE_TARGET_PCT = 40.0

    # Key stages for pipeline velocity (Order Received flow)
    KEY_STAGE_IDS = [27, 28, 29, 45]  # Order Received, Approved, Awaiting Payment, etc.


def get_status(value: float, green_threshold: float, yellow_threshold: float) -> str:
    """Determine status based on thresholds."""
    if value >= green_threshold:
        return "green"
    elif value >= yellow_threshold:
        return "yellow"
    else:
        return "red"


def get_runway_status(months: float) -> str:
    """Determine runway status."""
    if months > CEODashboardConfig.RUNWAY_GREEN_MONTHS:
        return "green"
    elif months >= CEODashboardConfig.RUNWAY_YELLOW_MONTHS:
        return "yellow"
    else:
        return "red"


class CEODashboardService:
    """Service for generating CEO Dashboard metrics."""

    def __init__(self):
        self.cashflow_service = get_cashflow_prediction_service()
        self.deal_health_service = get_deal_health_service()

    async def get_dashboard_metrics(self) -> CEODashboardMetrics:
        """Get all CEO Dashboard metrics in a single call."""
        now = datetime.now()

        # Fetch all components
        cash_health = await self._get_cash_health()
        urgent_deals = self._get_urgent_deals()
        pipeline_velocity = self._get_pipeline_velocity()
        strategic_priorities = await self._get_strategic_priorities()
        department_scorecard = self._get_department_scorecard()

        return CEODashboardMetrics(
            cash_health=cash_health,
            urgent_deals=urgent_deals,
            pipeline_velocity=pipeline_velocity,
            strategic_priorities=strategic_priorities,
            department_scorecard=department_scorecard,
            last_updated=now.isoformat(),
            data_freshness="live",
        )

    async def _get_cash_health(self) -> CashHealth:
        """Calculate cash health metrics."""
        # Get Aramco cashflow prediction for next 14 days
        aramco_14d = 0.0
        aramco_collected_week = 0.0

        try:
            prediction_result = await self.cashflow_service.predict_cashflow(
                CashflowPredictionInput(
                    pipeline_name="Aramco Projects",
                    horizon_days=14,
                    granularity="week",
                )
            )

            # Sum up expected values from predictions
            for bucket in prediction_result.aggregated_forecast:
                aramco_14d += bucket.expected_invoice_value_sar

            # Use first week as this week's collection estimate
            if prediction_result.aggregated_forecast:
                aramco_collected_week = prediction_result.aggregated_forecast[0].expected_invoice_value_sar

        except Exception as e:
            logger.warning(f"Failed to get Aramco cashflow prediction: {e}")

        # Commercial collections (placeholder)
        commercial_collected_week = CEODashboardConfig.COMMERCIAL_WEEKLY_COLLECTED
        commercial_target_week = CEODashboardConfig.COMMERCIAL_WEEKLY_TARGET

        # Aramco targets
        aramco_target_week = CEODashboardConfig.ARAMCO_WEEKLY_TARGET

        # Calculate totals
        total_collected = aramco_collected_week + commercial_collected_week
        total_target = aramco_target_week + commercial_target_week

        # Collection percentage
        collection_pct = (total_collected / total_target * 100) if total_target > 0 else 0.0

        # Velocity (same as collection percentage for now)
        velocity_pct = collection_pct
        velocity_status = get_status(
            velocity_pct,
            CEODashboardConfig.VELOCITY_GREEN_PCT,
            CEODashboardConfig.VELOCITY_YELLOW_PCT,
        )

        # Calculate runway (simplified: based on predicted collections)
        monthly_predicted = aramco_14d * 2  # Extrapolate 14d to monthly
        monthly_burn = total_target * 4  # 4 weeks

        runway_months = (monthly_predicted / monthly_burn * 4) if monthly_burn > 0 else 0.0
        runway_status = get_runway_status(runway_months)

        return CashHealth(
            runway_months=round(runway_months, 1),
            runway_status=runway_status,
            aramco_collected_week=aramco_collected_week,
            aramco_target_week=aramco_target_week,
            commercial_collected_week=commercial_collected_week,
            commercial_target_week=commercial_target_week,
            total_collected_week=total_collected,
            total_target_week=total_target,
            collection_pct=round(collection_pct, 1),
            predicted_14d=aramco_14d,
            velocity_pct=round(velocity_pct, 1),
            velocity_status=velocity_status,
        )

    def _get_urgent_deals(self, limit: int = 5) -> list[UrgentDeal]:
        """Get top urgent deals requiring attention."""
        urgent_deals = []

        # Get overdue deals
        overdue_deals = self.deal_health_service.get_overdue_deals(
            pipeline_name="Aramco Projects",
            min_days=7,
        )

        # Get stuck deals
        stuck_deals = self.deal_health_service.get_stuck_deals(
            pipeline_name="Aramco Projects",
            min_days=30,
        )

        # Combine and score deals
        scored_deals = []

        for deal in overdue_deals[:10]:
            score = deal.overdue_days * 3 + (deal.value_sar or 0) / 10000
            scored_deals.append({
                "deal": deal,
                "reason": f"No update {deal.overdue_days}d",
                "days": deal.overdue_days,
                "score": score,
            })

        for deal in stuck_deals[:10]:
            score = deal.days_in_stage * 2 + (deal.value_sar or 0) / 10000
            scored_deals.append({
                "deal": deal,
                "reason": f"Stuck in {deal.stage} {deal.days_in_stage}d",
                "days": deal.days_in_stage,
                "score": score,
            })

        # Sort by score and take top N
        scored_deals.sort(key=lambda x: x["score"], reverse=True)

        for item in scored_deals[:limit]:
            deal = item["deal"]
            urgent_deals.append(UrgentDeal(
                deal_id=deal.id,
                title=deal.title,
                reason=item["reason"],
                value_sar=deal.value_sar or 0.0,
                stage=deal.stage,
                owner=deal.owner,
                days_stuck=item["days"],
            ))

        return urgent_deals

    def _get_pipeline_velocity(self) -> PipelineVelocity:
        """Calculate pipeline velocity metrics."""
        stages = []
        total_avg_days = 0.0
        stage_count = 0

        # Get key stages
        with Session(engine) as session:
            for stage_id in CEODashboardConfig.KEY_STAGE_IDS:
                stage = session.exec(
                    select(Stage).where(Stage.id == stage_id)
                ).first()

                if not stage:
                    continue

                # Get duration stats for this stage
                stats = db_queries.get_stage_duration_stats(stage_id, days=90)

                # Get current deals in stage
                deal_count = len(list(session.exec(
                    select(Deal)
                    .where(Deal.stage_id == stage_id)
                    .where(Deal.status == "open")
                ).all()))

                avg_days = stats.get("avg_duration_hours", 0) / 24  # Convert hours to days

                stages.append(PipelineStage(
                    name=stage.name,
                    stage_id=stage_id,
                    avg_days=round(avg_days, 1),
                    deal_count=deal_count,
                ))

                total_avg_days += avg_days
                stage_count += 1

        # Calculate current cycle time
        current_cycle_days = total_avg_days if stage_count > 0 else 0.0

        # Determine trend (compare to target)
        target = CEODashboardConfig.TARGET_CYCLE_DAYS
        if current_cycle_days < target * 0.9:
            trend = "better"
        elif current_cycle_days > target * 1.1:
            trend = "worse"
        else:
            trend = "stable"

        trend_pct = ((current_cycle_days - target) / target * 100) if target > 0 else 0.0

        return PipelineVelocity(
            stages=stages,
            current_cycle_days=round(current_cycle_days, 1),
            target_cycle_days=target,
            trend=trend,
            trend_pct=round(trend_pct, 1),
        )

    async def _get_strategic_priorities(self) -> list[StrategicPriority]:
        """Get strategic priority metrics."""
        priorities = []

        # Get pipeline values for calculations
        with Session(engine) as session:
            # Total pipeline value (Aramco + Commercial)
            aramco_pipeline_id = PIPELINE_NAME_TO_ID.get("Aramco Projects")
            commercial_pipeline_id = PIPELINE_NAME_TO_ID.get("pipeline")

            aramco_value = 0.0
            commercial_value = 0.0

            if aramco_pipeline_id:
                result = session.exec(
                    select(func.sum(Deal.value))
                    .where(Deal.pipeline_id == aramco_pipeline_id)
                    .where(Deal.status == "open")
                ).first()
                aramco_value = result or 0.0

            if commercial_pipeline_id:
                result = session.exec(
                    select(func.sum(Deal.value))
                    .where(Deal.pipeline_id == commercial_pipeline_id)
                    .where(Deal.status == "open")
                ).first()
                commercial_value = result or 0.0

        total_pipeline = aramco_value + commercial_value

        # 1. Cost Reduction target (placeholder - would need actual cost data)
        cost_current = 15.0  # Placeholder %
        cost_target = CEODashboardConfig.COST_REDUCTION_TARGET_PCT
        cost_pct = (cost_current / cost_target * 100) if cost_target > 0 else 0.0
        priorities.append(StrategicPriority(
            name="Cost Reduction",
            current=cost_current,
            target=cost_target,
            pct=round(cost_pct, 1),
            status=get_status(cost_pct, 80, 50),
            unit="%",
        ))

        # 2. Weekly Sales target
        # For now, use pipeline value as proxy (would need actual sales data)
        sales_current = total_pipeline / 1000  # Convert to K
        sales_target = CEODashboardConfig.WEEKLY_SALES_TARGET_SAR / 1000
        sales_pct = (sales_current / sales_target * 100) if sales_target > 0 else 0.0
        priorities.append(StrategicPriority(
            name="Sales Pipeline",
            current=round(sales_current, 0),
            target=round(sales_target, 0),
            pct=min(round(sales_pct, 1), 200),  # Cap at 200%
            status=get_status(sales_pct, 80, 50),
            unit="K SAR",
        ))

        # 3. Commercial share target
        commercial_pct = (commercial_value / total_pipeline * 100) if total_pipeline > 0 else 0.0
        commercial_target = CEODashboardConfig.COMMERCIAL_SHARE_TARGET_PCT
        commercial_achievement = (commercial_pct / commercial_target * 100) if commercial_target > 0 else 0.0
        priorities.append(StrategicPriority(
            name="Commercial Share",
            current=round(commercial_pct, 1),
            target=commercial_target,
            pct=round(commercial_achievement, 1),
            status=get_status(commercial_achievement, 80, 50),
            unit="%",
        ))

        return priorities

    def _get_department_scorecard(self) -> DepartmentScorecard:
        """Get department scorecard metrics (MVP: Sales only)."""
        with Session(engine) as session:
            # Get all open deals across pipelines
            deals = session.exec(
                select(Deal).where(Deal.status == "open")
            ).all()

            pipeline_value = sum(deal.value or 0 for deal in deals)
            active_count = len(deals)

            # Get won deals this month
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            won_deals = session.exec(
                select(Deal)
                .where(Deal.status == "won")
                .where(Deal.won_time >= month_start)
            ).all()
            won_value = sum(deal.value or 0 for deal in won_deals)

        # Get overdue count
        overdue_deals = self.deal_health_service.get_overdue_deals(
            pipeline_name="Aramco Projects",
            min_days=7,
        )
        overdue_count = len(overdue_deals)

        # Determine sales status
        if overdue_count <= 2:
            status = "green"
        elif overdue_count <= 5:
            status = "yellow"
        else:
            status = "red"

        sales = SalesScorecard(
            pipeline_value=pipeline_value,
            won_value=won_value,
            active_deals_count=active_count,
            overdue_count=overdue_count,
            status=status,
        )

        return DepartmentScorecard(sales=sales)


# Global service instance
_ceo_dashboard_service: Optional[CEODashboardService] = None


def get_ceo_dashboard_service() -> CEODashboardService:
    """Get or create CEO Dashboard service singleton."""
    global _ceo_dashboard_service
    if _ceo_dashboard_service is None:
        _ceo_dashboard_service = CEODashboardService()
    return _ceo_dashboard_service
