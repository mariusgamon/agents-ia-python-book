# tool_stock_naive.py
from agents import function_tool
import httpx

@function_tool
async def get_stock_price(ticker: str) -> dict:
    """Récupère le prix actuel d'une action pour un ticker donné."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.marketdata.example/v1/quote/{ticker}"
        )
        return resp.json()
