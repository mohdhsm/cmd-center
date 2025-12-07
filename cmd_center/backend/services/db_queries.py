"""Read helpers for the SQLite cache to support fast TUI loads."""

from datetime import datetime, timedelta
from typing import List

from sqlmodel import Session, select

from ..db import engine, Deal
from ..constants import PIPELINE_NAME_TO_ID


def get_open_deals_for_pipeline(pipeline_name: str) -> List[Deal]:
    pipeline_id = PIPELINE_NAME_TO_ID.get(pipeline_name)
    if not pipeline_id:
        return []
    with Session(engine) as session:
        stmt = select(Deal).where(Deal.pipeline_id == pipeline_id).where(Deal.status == "open")
        return session.exec(stmt).all()


def get_overdue_deals_for_pipeline(pipeline_name: str, min_days: int = 7) -> List[Deal]:
    pipeline_id = PIPELINE_NAME_TO_ID.get(pipeline_name)
    if not pipeline_id:
        return []
    cutoff = datetime.utcnow() - timedelta(days=min_days)
    with Session(engine) as session:
        stmt = (
            select(Deal)
            .where(Deal.pipeline_id == pipeline_id)
            .where(Deal.status == "open")
            .where(Deal.update_time < cutoff)
        )
        return session.exec(stmt).all()


def get_stuck_deals_for_pipeline(pipeline_name: str, min_days: int = 30) -> List[Deal]:
    pipeline_id = PIPELINE_NAME_TO_ID.get(pipeline_name)
    if not pipeline_id:
        return []
    cutoff = datetime.utcnow() - timedelta(days=min_days)
    with Session(engine) as session:
        stmt = (
            select(Deal)
            .where(Deal.pipeline_id == pipeline_id)
            .where(Deal.status == "open")
            .where(Deal.update_time < cutoff)
        )
        return session.exec(stmt).all()


__all__ = [
    "get_open_deals_for_pipeline",
    "get_overdue_deals_for_pipeline",
    "get_stuck_deals_for_pipeline",
]
