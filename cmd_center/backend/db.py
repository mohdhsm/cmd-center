"""SQLite cache setup and SQLModel tables for Pipedrive data."""

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, create_engine

# SQLite cache file; adjust path if needed
engine = create_engine("sqlite:///pipedrive_cache.db", echo=False, connect_args={"check_same_thread": False})

# Pipeline saving
class Pipeline(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    order_nr: int
    is_deleted: bool = False
    is_deal_probability_enabled: bool = False
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class Stage(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    order_nr: int
    pipeline_id: int = Field(index=True)
    deal_probability: int = 0
    is_deal_rot_enabled: bool = False
    days_to_rotten: Optional[int] = None
    is_deleted: bool = False
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


# this for the deal
class Deal(SQLModel, table=True):
    id: int = Field(primary_key=True)
    title: str
    pipeline_id: int = Field(index=True)
    stage_id: int = Field(index=True)
    owner_name: Optional[str] = None
    owner_id: Optional[int] = None
    org_name: Optional[str] = None
    org_id: Optional[int] = None
    value: float = 0.0
    currency: str = "SAR"
    status: str = Field(default="open", index=True)
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = Field(default=None, index=True)
    stage_change_time: Optional[datetime] = None
    expected_close_date: Optional[datetime] = None
    last_activity_date: Optional[datetime] = None
    raw_json: Optional[str] = None


class Note(SQLModel, table=True):
    id: int = Field(primary_key=True)
    deal_id: int = Field(index=True)
    user_name: Optional[str] = None
    user_id: Optional[int] = None
    content: str
    add_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class SyncMetadata(SQLModel, table=True):
    """Tracks sync state for incremental updates."""
    __tablename__ = "sync_metadata"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    entity_type: str = Field(unique=True)
    last_sync_time: datetime
    last_sync_duration_ms: int = 0
    records_synced: int = 0
    records_total: int = 0
    status: str = "success"  # "success", "failed", "in_progress"
    error_message: Optional[str] = None


def init_db() -> None:
    """Create tables if they do not exist."""
    SQLModel.metadata.create_all(engine)


__all__ = ["engine", "init_db", "Pipeline", "Stage", "Deal", "Note", "SyncMetadata"]
