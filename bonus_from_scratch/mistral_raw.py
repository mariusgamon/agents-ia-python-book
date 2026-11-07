import httpx
import os
from dotenv import load_dotenv

load_dotenv()  # lit MISTRAL_API_KEY dans .env

MISTRAL_API_KEY = os.environ["MISTRAL_API_KEY"]
MISTRAL_URL     = "https://api.mistral.ai/v1/chat/completions"


def llm(messages: list[dict], model: str = "mistral-small-latest") -> str:
    """
    Appel direct à l'API Mistral — aucun SDK, juste du HTTP.

    messages : liste de dicts {"role": "user"|"assistant"|"system", "content": "..."}
    retourne  : le texte de la réponse (content du premier choix)
    """
    response = httpx.post(
        MISTRAL_URL,
        headers={
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type":  "application/json",
        },
        json={
            "model":       model,
            "messages":    messages,
            "temperature": 0.2,      # faible pour des décisions reproductibles
        },
        timeout=30.0,
    )
    response.raise_for_status()     # lève une exception sur 4xx / 5xx
    return response.json()["choices"][0]["message"]["content"]


def extract_json(text: str) -> str:
    """Retire les balises ```json ... ``` que certains modèles ajoutent autour du JSON."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else ""   # retire la ligne ```json
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


# Test rapide
if __name__ == "__main__":
    reply = llm([{"role": "user", "content": "Dis bonjour en une phrase."}])
    print(reply)


# À ajouter à la fin de mistral_raw.py : la boucle du §B.5 l'importe depuis ce module.
SYSTEM_PROMPT = """Tu es un assistant intelligent qui peut utiliser des outils.

Quand tu as besoin d'un outil pour répondre, réponds UNIQUEMENT avec ce JSON
(rien d'autre, pas de texte avant ou après) :

{"tool": "nom_de_l_outil", "args": {"param1": "valeur1", ...}}

Outils disponibles :
- get_weather(city: str)          → météo actuelle de la ville
- calculate(expression: str)      → calcul mathématique Python-safe
- search_web_snippets(query: str, n: int) → n snippets web (DuckDuckGo, pas une API news)

Quand tu as la réponse finale sans outil, écris-la normalement (pas de JSON).

IMPORTANT : n'invente jamais le résultat d'un outil. Appelle-le toujours."""
