"""Shared constants for pipeline name/ID mappings."""

PIPELINE_NAME_TO_ID = {
    "Pipeline": 1,
    "Prospecting": 2,
    "Aramco Inquiries": 3,
    "Aramco PO": 4,
    "Aramco Projects": 5,
    "Bidding Projects": 6,
    "Design Development": 10,
    "Problematic & Stuck Orders": 11,
}

PIPELINE_ID_TO_NAME = {v: k for k, v in PIPELINE_NAME_TO_ID.items()}

__all__ = ["PIPELINE_NAME_TO_ID", "PIPELINE_ID_TO_NAME"]
