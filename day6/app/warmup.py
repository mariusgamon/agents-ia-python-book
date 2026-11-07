# app/warmup.py — applicative keep-alive (companion to min_instances, not a replacement)
import httpx
import asyncio
import logging

logger = logging.getLogger("warmup")

SELF_URL = "http://localhost:8000/health"
PING_INTERVAL_SECONDS = 240  # 4 minutes — most platforms idle-kill at 5-15 min

async def warmup_loop():
    """Background task that pings the health endpoint at regular intervals.
    Useful on bare-metal/VPS to keep app caches and DB connections warm.
    On serverless platforms (Cloud Run, Lambda, Fly), prefer
    min_instances / provisioned concurrency / min_machines_running.
    """
    await asyncio.sleep(10)  # wait for startup to finish
    async with httpx.AsyncClient() as client:
        while True:
            try:
                resp = await client.get(SELF_URL, timeout=5.0)
                logger.debug(f"warmup ping: {resp.status_code}")
            except Exception as e:
                logger.warning(f"warmup ping failed: {e}")
            await asyncio.sleep(PING_INTERVAL_SECONDS)
