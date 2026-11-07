# test_resilient_tool.py — run the resilient pattern against a deliberately slow endpoint
import config

import asyncio
from agents import Agent, Runner, function_tool
import httpx

# Point the tool at httpbin's /delay/N endpoint — public test service
# that responds after N seconds. Handy for testing timeouts without mocking.
SLOW_API_URL = "https://httpbin.org/delay/15"  # sleeps 15s before responding

TOOL_TIMEOUT = httpx.Timeout(
    connect=3.0,
    read=5.0,    # Deliberately shorter than the 15s delay → will trigger ReadTimeout
    write=5.0,
    pool=5.0,
)

@function_tool
async def fetch_slow_data(ticker: str) -> dict:
    """Récupère les données boursières — outil de démo avec timeouts agressifs."""
    try:
        async with httpx.AsyncClient(timeout=TOOL_TIMEOUT) as client:
            resp = await client.get(SLOW_API_URL)
            resp.raise_for_status()
            return {"ticker": ticker, "data": resp.json()}
    except httpx.ReadTimeout:
        return {
            "error": f"API too slow for {ticker} (read timeout)",
            "hint": "Server accepted the connection but did not respond in time",
        }
    except httpx.ConnectTimeout:
        return {
            "error": f"Cannot reach API for {ticker} (connect timeout)",
            "hint": "API server may be down",
        }

agent = Agent(
    name="StockAgent",
    model=config.DEFAULT_MODEL,
    instructions=(
        "You fetch stock data. If the tool returns an error, "
        "explain clearly what went wrong to the user and suggest a retry."
    ),
    tools=[fetch_slow_data],
)

async def main():
    result = await Runner.run(agent, input="Fetch the price for AAPL")
    print(result.final_output)

asyncio.run(main())
