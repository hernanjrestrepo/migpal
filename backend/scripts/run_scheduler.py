import os
import asyncio

import httpx

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")


async def trigger_scheduler():
    headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"} if ADMIN_TOKEN else {}
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(f"{API_URL}/planner/sync", headers=headers)
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    result = asyncio.run(trigger_scheduler())
    print("Scheduler synced", result)
