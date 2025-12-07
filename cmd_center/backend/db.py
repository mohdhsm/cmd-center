"""SQLite cache setup and SQLModel tables for Pipedrive data."""

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, create_engine

# SQLite cache file; adjust path if needed
engine = create_engine("sqlite:///pipedrive_cache.db", echo=False)


class Pipeline(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    order_nr: int
    is_deleted: bool
    is_deal_probability_enabled: bool
    add_time: datetime
    update_time: datetime


class Stage(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    order_nr: int
    pipeline_id: int
    deal_probability: int
    is_deal_rot_enabled: bool
    days_to_rotten: Optional[int] = None
    is_deleted: bool
    add_time: datetime
    update_time: datetime


class Deal(SQLModel, table=True):
    id: int = Field(primary_key=True)
    title: str
    pipeline_id: int
    stage_id: int
    owner_name: Optional[str] = None
    org_name: Optional[str] = None
    value: float = 0.0
    status: str
    add_time: datetime
    update_time: datetime
    expected_close_date: Optional[datetime] = None
    last_activity_date: Optional[datetime] = None
    raw_json: Optional[str] = None


class Note(SQLModel, table=True):
    id: int = Field(primary_key=True)
    deal_id: int
    user_name: Optional[str] = None
    content: str
    add_time: datetime


def init_db() -> None:
    """Create tables if they do not exist."""
    SQLModel.metadata.create_all(engine)


__all__ = ["engine", "init_db", "Pipeline", "Stage", "Deal", "Note"]
