"""Simple test script to verify database implementation."""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

# Direct imports to avoid circular dependencies
from cmd_center.backend.db import init_db, engine
from cmd_center.backend.services.pipedrive_sync import sync_all
from cmd_center.backend.services import db_queries
from cmd_center.backend.services.deal_health_service import DealHealthService


async def test_implementation():
    """Test the database implementation."""
    print("=" * 60)
    print("Testing Database Implementation")
    print("=" * 60)
    
    # Step 1: Initialize database
    print("\n1. Initializing database...")
    try:
        init_db()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        return
    
    # Step 2: Test sync (optional - only if API token is available)
    print("\n2. Testing sync (if API token available)...")
    try:
        results = await sync_all(incremental=False)
        print(f"✓ Sync completed:")
        print(f"  - Pipelines synced: {results['pipelines']}")
        print(f"  - Stages synced: {results['stages']}")
        print(f"  - Deals synced: {results['deals']}")
    except Exception as e:
        print(f"⚠ Sync skipped or failed: {e}")
        print("  (This is expected if PIPEDRIVE_API_TOKEN is not set)")
    
    # Step 3: Test queries
    print("\n3. Testing database queries...")
    try:
        # Test pipeline query
        pipeline = db_queries.get_pipeline_by_name("Aramco Projects")
        if pipeline:
            print(f"✓ Pipeline query works: Found '{pipeline.name}' (ID: {pipeline.id})")
        else:
            print("⚠ No pipeline found (database may be empty)")
        
        # Test deals query
        deals = db_queries.get_open_deals_for_pipeline("Aramco Projects")
        print(f"✓ Deals query works: Found {len(deals)} open deals")
        
        # Test sync status
        sync_status = db_queries.get_sync_status()
        print(f"✓ Sync status query works: {len(sync_status)} entities tracked")
        
    except Exception as e:
        print(f"✗ Query test failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Test service layer
    print("\n4. Testing service layer...")
    try:
        service = DealHealthService()
        
        # Test overdue deals
        overdue = service.get_overdue_deals("Aramco Projects", min_days=7)
        print(f"✓ Service layer works: Found {len(overdue)} overdue deals")
        
        if overdue:
            example = overdue[0]
            print(f"  Example: '{example.title}' - {example.overdue_days} days overdue")
        
        # Test stuck deals
        stuck = service.get_stuck_deals("Aramco Projects", min_days=30)
        print(f"✓ Service layer works: Found {len(stuck)} stuck deals")
        
    except Exception as e:
        print(f"✗ Service layer test failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60)
    print("All tests completed successfully! ✓")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_implementation())