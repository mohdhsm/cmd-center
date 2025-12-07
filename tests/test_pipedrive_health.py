"""
Ad-hoc API checks for Aramco endpoints.

Uses the in-process FastAPI app to hit the Aramco routes and pretty-print
JSON so you can visually verify the responses.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict

import httpx

# Ensure repo root is on the import path so cmd_center can be imported when run directly
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cmd_center.backend.main import app

async def fetch(client: httpx.AsyncClient, path: str, **params) -> Dict[str, Any]:
    response = await client.get(path, params=params)
    return {"status": response.status_code, "json": response.json()}


async def run_checks():
    routes = {
        "/aramco/overdue": {"min_days": 7, "limit":50 },
        "/aramco/stuck": {"min_days": 30,"limit":50 },
        #"/aramco/order_received": {"min_days": 30, "limit":5 },
        #"/aramco/compliance": {},
        #"/aramco/cashflow_projection": {"period_type": "week", "periods_ahead": 12},
    }

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        for path, params in routes.items():
            result = await fetch(client, path, **params)
            print(f"\n### GET {path} params={params}")
            print(f"Status: {result['status']}")
            print(json.dumps(result["json"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(run_checks())
