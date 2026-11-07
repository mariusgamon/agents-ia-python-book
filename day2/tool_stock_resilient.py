# tool_stock_resilient.py
from agents import function_tool
import httpx

# Granular timeouts: each phase has its own limit
TOOL_TIMEOUT = httpx.Timeout(
    connect=3.0,   # 3s to establish TCP connection
    read=10.0,     # 10s to receive response bytes
    write=5.0,     # 5s to send request body
    pool=5.0       # 5s to acquire connection from pool
)

@function_tool
async def get_stock_price(ticker: str) -> dict:
    """Récupère le prix actuel d'une action pour un ticker donné."""
    try:
        async with httpx.AsyncClient(timeout=TOOL_TIMEOUT) as client:
            resp = await client.get(
                f"https://api.marketdata.example/v1/quote/{ticker}"
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.ConnectTimeout:
        return {
            "error": f"Cannot reach market API (connect timeout for {ticker})",
            "hint": "API server may be down — retry in 30s or use cached price"
        }
    except httpx.ReadTimeout:
        return {
            "error": f"Market API too slow for {ticker} (read timeout)",
            "hint": "Server accepted connection but did not respond in time"
        }
    except httpx.PoolTimeout:
        return {
            "error": "Connection pool exhausted — too many concurrent tool calls",
            "hint": "Reduce parallelism or increase pool size"
        }
    except httpx.HTTPStatusError as e:
        return {
            "error": f"Market API returned HTTP {e.response.status_code} for {ticker}",
            "raw": e.response.text[:200]
        }
