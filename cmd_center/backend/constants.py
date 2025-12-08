"""Shared constants for pipeline name/ID mappings."""

PIPELINE_NAME_TO_ID = {
    "Pipeline": 1,              # Commercial
    "Prospecting": 2,
    "Aramco Inquiries": 3,
    "Aramco PO": 4,
    "Aramco Projects": 5,
    "Bidding Projects": 6,
    "Design Development": 10,
    "Problematic & Stuck Orders": 11,
}

PIPELINE_ID_TO_NAME = {v: k for k, v in PIPELINE_NAME_TO_ID.items()}

# Pipelines to sync regularly
SYNC_PIPELINES = [
    PIPELINE_NAME_TO_ID["Aramco Projects"],
    PIPELINE_NAME_TO_ID["Pipeline"],  # Commercial
    PIPELINE_NAME_TO_ID["Aramco PO"],
]


def build_stage_key_to_id(stages: list[dict]) -> dict[tuple[int, str], int]:
    """
    Build a mapping from (pipeline_id, stage_name) -> stage_id.
    
    Usage:
        stages = session.exec(select(Stage)).all()
        STAGE_KEY_TO_ID = build_stage_key_to_id([s.dict() for s in stages])
    """
    return {
        (s["pipeline_id"], s["name"]): s["id"]
        for s in stages
    }


def get_stage_name(session, stage_id: int) -> str:
    """Get stage name by ID from database."""
    from sqlmodel import select
    from .db import Stage
    
    stage = session.exec(select(Stage).where(Stage.id == stage_id)).first()
    return stage.name if stage else "Unknown"


__all__ = [
    "PIPELINE_NAME_TO_ID",
    "PIPELINE_ID_TO_NAME",
    "SYNC_PIPELINES",
    "build_stage_key_to_id",
    "get_stage_name",
]
