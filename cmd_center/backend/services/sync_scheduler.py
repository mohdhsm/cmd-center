"""Background scheduler for Pipedrive sync operations."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from ..constants import SYNC_PIPELINES
from ..db import init_db
from .pipedrive_sync import (
    sync_pipelines,
    sync_stages,
    sync_deals_for_pipeline,
    sync_notes_for_open_deals,
    sync_stage_history_for_open_deals,
    get_last_sync_time,
    update_sync_metadata,
)
from fastapi import FastAPI

logger = logging.getLogger(__name__)

# Locks to prevent overlapping runs
deals_lock = asyncio.Lock()
notes_lock = asyncio.Lock()
stage_history_lock = asyncio.Lock()

# Background tasks
deals_task: Optional[asyncio.Task] = None
notes_task: Optional[asyncio.Task] = None
stage_history_task: Optional[asyncio.Task] = None


async def bootstrap_sync():
    """Run bootstrap sync for pipelines and stages if not already done."""
    # Pipelines: sync only first time
    if get_last_sync_time("pipelines") is None:
        logger.info("Bootstrapping pipelines sync...")
        try:
            await sync_pipelines()
            logger.info("Pipelines bootstrap completed successfully")
        except Exception as e:
            logger.error(f"Pipelines bootstrap failed: {e}")

    # Stages: sync only first time
    if get_last_sync_time("stages") is None:
        logger.info("Bootstrapping stages sync...")
        try:
            await sync_stages()
            logger.info("Stages bootstrap completed successfully")
        except Exception as e:
            logger.error(f"Stages bootstrap failed: {e}")

    # Stage history: backfill both pipelines for open deals only
    if get_last_sync_time("stage_history_backfill") is None:
        logger.info("Bootstrapping stage history for Pipeline and Aramco Projects (open deals only)...")
        try:
            # Backfill both tracked pipelines - OPEN DEALS ONLY
            result = await sync_stage_history_for_open_deals(
                pipeline_names=["Pipeline", "Aramco Projects"],
                concurrency=3  # Lower concurrency for bootstrap
            )
            logger.info(
                f"Stage history backfill completed: {result['synced_successfully']} open deals, "
                f"{result['total_events']} events, {result['total_spans']} spans"
            )

            # Mark backfill as complete
            update_sync_metadata("stage_history_backfill", "success",
                               records_synced=result['synced_successfully'],
                               records_total=result['total_deals'])
        except Exception as e:
            logger.error(f"Stage history backfill failed: {e}")


async def run_deals_sync():
    """Run deals sync for all pipelines."""
    async with deals_lock:
        logger.info("Starting deals sync...")
        start_time = asyncio.get_event_loop().time()
        try:
            for pipeline_id in SYNC_PIPELINES:
                await sync_deals_for_pipeline(pipeline_id, status="open", incremental=True)
            duration = asyncio.get_event_loop().time() - start_time
            logger.info(f"Deals sync completed in {duration:.2f}s")
        # This is to stop the application when cancelled.
        except asyncio.CancelledError:
            raise
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            logger.error(f"Deals sync failed after {duration:.2f}s: {e}")


async def run_notes_sync():
    """Run notes sync for open deals."""
    async with notes_lock:
        logger.info("Starting notes sync...")
        start_time = asyncio.get_event_loop().time()
        try:
            await sync_notes_for_open_deals(limit_per_deal=5, ttl_minutes=30, concurrency=8)
            duration = asyncio.get_event_loop().time() - start_time
            logger.info(f"Notes sync completed in {duration:.2f}s")
        # this is to stop the application and exit cleanly when cancelled.
        except asyncio.CancelledError:
            raise
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            logger.error(f"Notes sync failed after {duration:.2f}s: {e}")


async def run_activities_sync():
    """Placeholder for activities sync - TODO: implement when needed."""
    # TODO: Implement activities sync when required
    logger.info("Activities sync placeholder - not implemented yet")


async def run_stage_history_sync():
    """Run stage history sync for open deals."""
    async with stage_history_lock:
        logger.info("Starting stage history sync...")
        start_time = asyncio.get_event_loop().time()
        try:
            result = await sync_stage_history_for_open_deals(
                pipeline_names=["Pipeline", "Aramco Projects"],
                concurrency=5
            )
            duration = asyncio.get_event_loop().time() - start_time
            logger.info(
                f"Stage history sync completed in {duration:.2f}s: "
                f"{result['synced_successfully']}/{result['total_deals']} deals, "
                f"{result['total_events']} events, {result['total_spans']} spans"
            )
            if result['errors']:
                logger.warning(f"Stage history sync had {result['failed']} errors")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            logger.error(f"Stage history sync failed after {duration:.2f}s: {e}")


async def deals_loop():
    """Periodic deals sync loop (every 60 minutes)."""
    while True:
        await asyncio.sleep(60 * 60)  # 60 minutes
        await run_deals_sync()


async def notes_loop():
    """Periodic notes and activities sync loop (every 30 minutes)."""
    while True:
        await asyncio.sleep(30 * 60)  # 30 minutes
        await run_notes_sync()
        await run_activities_sync()


async def stage_history_loop():
    """Periodic stage history sync loop (every 60 minutes)."""
    while True:
        await asyncio.sleep(60 * 60)  # 60 minutes
        await run_stage_history_sync()


async def start_scheduler():
    """Start the background scheduler tasks."""
    global deals_task, notes_task, stage_history_task

    if deals_task is None or deals_task.done():
        deals_task = asyncio.create_task(deals_loop())
        logger.info("Started deals sync loop")

    if notes_task is None or notes_task.done():
        notes_task = asyncio.create_task(notes_loop())
        logger.info("Started notes sync loop")

    if stage_history_task is None or stage_history_task.done():
        stage_history_task = asyncio.create_task(stage_history_loop())
        logger.info("Started stage history sync loop")


async def stop_scheduler():
    """Stop the background scheduler tasks."""
    global deals_task, notes_task, stage_history_task

    if deals_task and not deals_task.done():
        deals_task.cancel()
        try:
            await deals_task
        except asyncio.CancelledError:
            pass
        logger.info("Stopped deals sync loop")

    if notes_task and not notes_task.done():
        notes_task.cancel()
        try:
            await notes_task
        except asyncio.CancelledError:
            pass
        logger.info("Stopped notes sync loop")

    if stage_history_task and not stage_history_task.done():
        stage_history_task.cancel()
        try:
            await stage_history_task
        except asyncio.CancelledError:
            pass
        logger.info("Stopped stage history sync loop")


@asynccontextmanager
async def lifespan_manager(app: FastAPI):
    """Lifespan context manager for FastAPI."""
    from ..integrations import get_config

    # Startup
    config = get_config()
    init_db()
    logger.info(f"Command Center API starting on {config.api_host}:{config.api_port}")
    logger.info("Starting Pipedrive sync scheduler...")

    # Bootstrap
    await bootstrap_sync()

    # Run initial syncs
    await run_deals_sync()
    await run_notes_sync()
    await run_stage_history_sync()

    # Start periodic loops
    await start_scheduler()

    yield

    # Shutdown
    logger.info("Shutting down Pipedrive sync scheduler...")
    await stop_scheduler()
    logger.info("Command Center API shutting down")


async def manual_sync_stages():
    """Manually trigger stages sync."""
    logger.info("Manual stages sync requested...")
    try:
        count = await sync_stages()
        logger.info(f"Manual stages sync completed: {count} stages synced")
        return {"status": "success", "stages_synced": count}
    except Exception as e:
        logger.error(f"Manual stages sync failed: {e}")
        return {"status": "error", "error": str(e)}