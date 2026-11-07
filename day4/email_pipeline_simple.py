# email_pipeline_simple.py — Version Python pure (ce qu'ils auraient dû faire)
import config

from openai import AsyncOpenAI

client = AsyncOpenAI()

async def classify_intent(email_body: str) -> str:
    """Classifie l'email : billing, technical, feature_request, ou other."""
    response = await client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[
            {"role": "system", "content": "Classify this support email intent. "
             "Return exactly one of: billing, technical, feature_request, other."},
            {"role": "user", "content": email_body}
        ],
        max_tokens=20
    )
    return response.choices[0].message.content.strip()

async def draft_response(email_body: str, intent: str) -> str:
    """Génère un brouillon de réponse basé sur le contenu de l'email et l'intent classifié."""
    response = await client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[
            {"role": "system", "content": f"Draft a professional response to this "
             f"{intent} support email. Be concise and helpful."},
            {"role": "user", "content": email_body}
        ],
        max_tokens=300
    )
    return response.choices[0].message.content

async def process_support_email(email_body: str) -> dict:
    """Pipeline complet : classifier puis rédiger. Deux appels, zéro framework."""
    intent = await classify_intent(email_body)
    draft = await draft_response(email_body, intent)
    return {"intent": intent, "draft": draft}
