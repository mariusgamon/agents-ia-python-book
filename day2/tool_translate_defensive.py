# tool_translate_defensive.py
import json
import httpx
from agents import function_tool

@function_tool
async def translate_text(text: str, target_lang: str) -> dict:
    """Traduit le texte vers la langue cible via une API externe."""
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=3.0, read=10.0)
        ) as client:
            resp = await client.post(
                "https://api.translate.example/v2/translate",
                json={"text": text, "target": target_lang}
            )

            # Layer 1: Check content type BEFORE parsing
            content_type = resp.headers.get("content-type", "")
            if "application/json" not in content_type:
                return {
                    "error": f"API returned {content_type} instead of JSON",
                    "status_code": resp.status_code,
                    "body_preview": resp.text[:200]
                }

            # Layer 2: Parse JSON defensively
            try:
                data = resp.json()
            except json.JSONDecodeError as e:
                return {
                    "error": f"Invalid JSON from API: {e}",
                    "body_preview": resp.text[:200]
                }

            # Layer 3: Validate structure AND values
            translated = None
            if "translations" in data and len(data["translations"]) > 0:
                translated = data["translations"][0].get("text")
            elif "result" in data and isinstance(data.get("result"), dict):
                translated = data["result"].get("text")

            if not translated:
                return {
                    "error": "API returned empty or missing translation",
                    "keys_received": list(data.keys()),
                    "body_preview": json.dumps(data)[:300]
                }

            return {"translated": translated}

    except httpx.TimeoutException:
        return {"error": "Translation API timed out — retry or use fallback"}
    except Exception:
        # Ne JAMAIS exposer str(e) au LLM en production (voir §2.5 Pattern 1).
        # Loguez le détail côté serveur, retournez un message safe au LLM.
        logger.exception("Unexpected translation tool error")
        return {
            "error": "Unexpected translation service error.",
            "action": "Tell the user the translation could not be completed right now.",
        }
