# app/agents/assistant.py
from agents import Agent, Runner, WebSearchTool
from openai import RateLimitError
import asyncio

_agent = None

def get_agent() -> Agent:
    """Singleton — crée l'agent une seule fois."""
    global _agent
    if _agent is None:
        _agent = Agent(
            name="AssistantDev",
            model="gpt-5.4-mini",
            instructions="""You are an expert Python development assistant.
            You answer precisely, concisely, and actionably.
            You provide code when it is useful.
            You honestly flag when you are unsure.""",
            tools=[WebSearchTool()],
        )
    return _agent

async def run_agent(message: str, history: list[dict] | None = None) -> tuple[str, int]:
    """
    Lance l'agent et retourne (response, tokens_used).
    Gère les retries automatiquement.

    Note: 'history' est l'historique conversationnel envoyé au LLM via input=,
    PAS le paramètre context= du SDK (qui est de l'état Python local pour les
    tools/hooks, et n'est PAS envoyé au modèle).
    """
    agent = get_agent()

    # Construire le payload envoyé au LLM
    input_items = (history or []) + [{"role": "user", "content": message}]

    for attempt in range(3):
        try:
            result = await asyncio.wait_for(
                Runner.run(agent, input=input_items, max_turns=10),
                timeout=45.0
            )

            # context_wrapper.usage agrège tous les appels LLM du run
            # (multi-tour, tool calls, handoffs) — pas seulement le dernier
            usage = result.context_wrapper.usage
            tokens = usage.total_tokens

            return result.final_output, tokens

        except asyncio.TimeoutError:
            if attempt == 2:
                raise TimeoutError("The agent did not respond within 45 seconds.")
            await asyncio.sleep(1)

        except RateLimitError:
            if attempt == 2:
                raise
            await asyncio.sleep(2 ** attempt)

    raise RuntimeError("The agent failed after 3 attempts.")
