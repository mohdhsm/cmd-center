"""Sync Pipedrive data into the local SQLite cache."""

import json
from typing import Any, Dict, List, Optional

import httpx
from sqlmodel import Session

from ..integrations.config import get_config
from ..db import engine, Pipeline, Stage, Deal, Note


class PipedriveSyncError(Exception):
    """Raised when sync cannot proceed (e.g., missing token)."""


def _get_token_and_base() -> tuple[str, str]:
    config = get_config()
    token = config.pipedrive_api_token
    if not token:
        raise PipedriveSyncError("pipedrive_api_token missing; set it in .env")
    return token, config.pipedrive_api_url


async def _pd_get(client: httpx.AsyncClient, path: str, token: str, base_url: str, **params) -> Dict[str, Any]:
    params["api_token"] = token
    res = await client.get(f"{base_url}/{path}", params=params)
    res.raise_for_status()
    return res.json()


async def sync_pipelines() -> None:
    token, base_url = _get_token_and_base()
    async with httpx.AsyncClient() as client:
        payload = await _pd_get(client, "pipelines", token, base_url)
    items = payload.get("data") or []

    with Session(engine) as session:
        for p in items:
            pipeline = Pipeline(
                id=p["id"],
                name=p["name"],
                order_nr=p["order_nr"],
                is_deleted=p["is_deleted"],
                is_deal_probability_enabled=p["is_deal_probability_enabled"],
                add_time=p["add_time"],
                update_time=p["update_time"],
            )
            session.merge(pipeline)
        session.commit()


async def sync_stages(pipeline_id: Optional[int] = None) -> None:
    token, base_url = _get_token_and_base()
    params: Dict[str, Any] = {}
    if pipeline_id:
        params["pipeline_id"] = pipeline_id

    async with httpx.AsyncClient() as client:
        payload = await _pd_get(client, "stages", token, base_url, **params)
    items = payload.get("data") or []

    with Session(engine) as session:
        for s in items:
            stage = Stage(
                id=s["id"],
                name=s["name"],
                order_nr=s["order_nr"],
                pipeline_id=s["pipeline_id"],
                deal_probability=s["deal_probability"],
                is_deal_rot_enabled=s["is_deal_rot_enabled"],
                days_to_rotten=s.get("days_to_rotten"),
                is_deleted=s["is_deleted"],
                add_time=s["add_time"],
                update_time=s["update_time"],
            )
            session.merge(stage)
        session.commit()


async def sync_deals_for_pipeline(pipeline_id: int, status: str = "open") -> None:
    token, base_url = _get_token_and_base()
    all_deals: List[Dict[str, Any]] = []
    start = 0
    limit = 500

    async with httpx.AsyncClient() as client:
        while True:
            payload = await _pd_get(
                client,
                "deals",
                token,
                base_url,
                pipeline_id=pipeline_id,
                status=status,
                start=start,
                limit=limit,
            )
            items = payload.get("data") or []
            if not items:
                break

            all_deals.extend(items)

            additional = payload.get("additional_data") or {}
            pagination = additional.get("pagination") or {}
            if not pagination.get("more_items_in_collection"):
                break

            start = pagination.get("next_start", 0)

    with Session(engine) as session:
        for d in all_deals:
            owner_name = d.get("owner_name")
            if not owner_name:
                owner = d.get("owner_id") or {}
                owner_name = owner.get("name")

            deal = Deal(
                id=d["id"],
                title=d["title"],
                pipeline_id=d["pipeline_id"],
                stage_id=d["stage_id"],
                owner_name=owner_name,
                org_name=d.get("org_name"),
                value=float(d.get("value") or 0.0),
                status=d["status"],
                add_time=d["add_time"],
                update_time=d["update_time"],
                expected_close_date=d.get("expected_close_date"),
                last_activity_date=d.get("last_activity_date"),
                raw_json=json.dumps(d),
            )
            session.merge(deal)

        session.commit()


async def sync_notes_for_deal(deal_id: int) -> None:
    token, base_url = _get_token_and_base()
    async with httpx.AsyncClient() as client:
        payload = await _pd_get(client, "notes", token, base_url, deal_id=deal_id)
    items = payload.get("data") or []

    with Session(engine) as session:
        for n in items:
            note = Note(
                id=n["id"],
                deal_id=n["deal_id"],
                user_name=(n.get("user") or {}).get("name"),
                content=n["content"],
                add_time=n["add_time"],
            )
            session.merge(note)
        session.commit()


__all__ = [
    "sync_pipelines",
    "sync_stages",
    "sync_deals_for_pipeline",
    "sync_notes_for_deal",
    "PipedriveSyncError",
]
