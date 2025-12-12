import asyncio
import httpx
import os
from sqlmodel import Session, select

from cmd_center.backend.db import engine, Pipeline, Deal
from cmd_center.backend.integrations.config import get_config


async def main():
    # Configuration from env vars with defaults
    max_deals = int(os.getenv("MAX_DEALS", "10"))
    limit_per_deal = int(os.getenv("LIMIT_PER_DEAL", "5"))
    pipeline_names = os.getenv("PIPELINE_NAMES", "Aramco Projects,PIPELINE").split(",")

    config = get_config()
    token = config.pipedrive_api_token
    base_url = config.pipedrive_api_url

    if not token:
        print("Error: Pipedrive API token not found in config.")
        return

    # Query pipelines by name
    with Session(engine) as session:
        pipelines = session.exec(
            select(Pipeline).where(Pipeline.name.in_(pipeline_names))
        ).all()
        pipeline_dict = {p.name: p.id for p in pipelines}
        pipeline_ids = [pid for pid in pipeline_dict.values() if pid is not None]

    if not pipeline_ids:
        print(f"No target pipelines found for names: {pipeline_names}")
        return

    # Query eligible open deals
    with Session(engine) as session:
        deals = session.exec(
            select(Deal).where(
                Deal.status == "open",
                Deal.pipeline_id.in_(pipeline_ids)
            )
        ).all()

    eligible_deals = len(deals)
    print(f"Eligible open deals found: {eligible_deals}")

    if not deals:
        print("No eligible deals to test.")
        return

    # Test up to max_deals
    tested_deals = min(max_deals, len(deals))
    total_notes = 0
    zero_notes = 0
    api_errors = 0

    async with httpx.AsyncClient() as client:
        for i, deal in enumerate(deals[:tested_deals]):
            try:
                params = {
                    "api_token": token,
                    "deal_id": deal.id,
                    "start": 0,
                    "limit": limit_per_deal,
                    "sort": "add_time DESC"
                }
                res = await client.get(f"{base_url}/notes", params=params, timeout=30.0)
                res.raise_for_status()
                data = res.json()
                items = data.get("data", [])

                print(f"\nDeal {deal.id} ({deal.title or 'No title'}, Pipeline {deal.pipeline_id}): {len(items)} notes")

                # Verify constraints
                assert len(items) <= limit_per_deal, f"Returned {len(items)} notes, exceeds limit {limit_per_deal}"

                # Verify sort if add_time present
                if items and all('add_time' in n for n in items):
                    add_times = [n['add_time'] for n in items]
                    assert add_times == sorted(add_times, reverse=True), "Notes not sorted descending by add_time"

                # Print notes
                for n in items:
                    content_preview = n.get('content', '')[:80]
                    print(f"  Note {n['id']}: add_time={n.get('add_time')}, update_time={n.get('update_time')} - {content_preview}...")

                total_notes += len(items)
                if len(items) == 0:
                    zero_notes += 1

            except Exception as e:
                print(f"API Error for deal {deal.id}: {e}")
                api_errors += 1

            # Polite delay between requests
            await asyncio.sleep(0.2)

    # Summary
    print("\n=== Summary ===")
    print(f"Eligible deals: {eligible_deals}")
    print(f"Tested deals: {tested_deals}")
    print(f"Total notes retrieved: {total_notes}")
    print(f"Deals with 0 notes: {zero_notes}")
    print(f"API errors: {api_errors}")


if __name__ == "__main__":
    asyncio.run(main())