# tool_translate_naive.py
from agents import function_tool
import httpx

@function_tool
async def translate_text(text: str, target_lang: str) -> dict:
    """Traduit le texte vers la langue cible via une API externe."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            "https://api.translate.example/v2/translate",
            json={"text": text, "target": target_lang}
        )
        data = resp.json()
        return {"translated": data["translations"][0]["text"]}
