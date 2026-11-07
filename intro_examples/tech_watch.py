# tech_watch.py — version simplifiée, code complet au Jour 7
import config
import asyncio
from agents import Agent, Runner, WebSearchTool, function_tool
import os, httpx

@function_tool
async def send_slack_notification(message: str) -> dict:
    """Sends a message to the Slack channel configured for this Incoming Webhook."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return {"error": "SLACK_WEBHOOK_URL not configured"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(webhook_url, json={"text": message})
        return {"status": "sent"} if resp.status_code == 200 else {"error": f"HTTP {resp.status_code}"}

WATCH_TOPICS = ["OpenAI Agents SDK", "Python 3.13", "FastAPI changelog"]

watch_agent = Agent(
    name="WatchAgent",
    model=config.DEFAULT_MODEL,
    instructions=f"""Tech-watch agent for Python developers.
    Search news from the last 24h for each topic, filter what matters,
    send a bullet-point summary to Slack (max 5 points).
    Topics: {', '.join(WATCH_TOPICS)}""",
    tools=[WebSearchTool(), send_slack_notification],
)

async def run_daily_watch():
    result = await Runner.run(
        watch_agent,
        input="Run the tech watch for today.",
        max_turns=15,
    )
    print(f"Report sent. {result.final_output}")

if __name__ == "__main__":
    asyncio.run(run_daily_watch())
