# tech_watch.py
import config

from agents import Agent, Runner, WebSearchTool
from datetime import datetime
import asyncio
import httpx
import os

# Envoi Slack via Incoming Webhook : fonction Python ordinaire, appelée par le code
# (pas par l'agent). Une fonction décorée @function_tool devient un objet FunctionTool
# qu'on ne peut plus appeler directement.
async def send_slack_notification(message: str) -> dict:
    """
    Envoie un message sur le canal Slack configuré pour ce webhook.

    Note: avec un Incoming Webhook, le canal cible est défini côté config
    Slack et ne peut pas être surchargé dans le payload. Pour choisir
    dynamiquement le canal à l'exécution, utilisez l'API Slack
    chat.postMessage avec un bot token et le scope channels:write.
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return {"error": "SLACK_WEBHOOK_URL not configured"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(webhook_url, json={"text": message})

    if resp.status_code == 200:
        return {"status": "sent"}
    return {"error": f"Slack HTTP {resp.status_code}"}

# L'agent utilise WebSearchTool() (intégré au SDK) pour chercher les news.
# Pas besoin d'un outil custom — le SDK gère les appels de recherche nativement.

WATCH_TOPICS = [
    "OpenAI Agents SDK new features",
    "Python 3.13 update",
    "FastAPI changelog",
    "LangGraph new features",
]

# One agent per topic = deterministic coverage.
# Letting a single LLM call "search all topics" often skips one or two.
watch_agent = Agent(
    name="WatchAgent",
    model=config.DEFAULT_MODEL,
    instructions="""You are a tech-watch agent for Python developers.

For the topic given in the input, you must:
1. Use web search to find what changed in the last 24-48 hours
2. Filter only items with a real impact on daily development
3. Ignore marketing announcements without technical substance
4. Return a short bullet list (max 3 points) — or "No relevant change" if nothing matters

Be factual. Cite the source URL on each bullet.""",
    tools=[WebSearchTool()],
)

async def run_daily_watch():
    print(f"[{datetime.now().strftime('%H:%M')}] Lancement de la veille tech...")
    today = datetime.now().strftime('%Y-%m-%d')
    findings: list[str] = []

    # Loop in Python — each topic gets its own Runner.run().
    # This guarantees coverage and lets you parallelize with asyncio.gather later.
    for topic in WATCH_TOPICS:
        try:
            result = await Runner.run(
                watch_agent,
                input=f"Topic: {topic}\nDate: {today}\nLook at the last 24-48h.",
                max_turns=5,
            )
            findings.append(f"### {topic}\n{result.final_output}")
        except Exception as e:
            findings.append(f"### {topic}\nError: {e}")

    # Synthesize once, with all findings already collected — deterministic.
    summary = f"*Tech Watch — {today}*\n\n" + "\n\n".join(findings)
    await send_slack_notification(summary)
    print(f"[OK] Veille terminée\u202f: {len(findings)} topics traités")

if __name__ == "__main__":
    asyncio.run(run_daily_watch())
