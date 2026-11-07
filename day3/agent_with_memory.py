# agent_with_memory.py
import config

from agents import Agent, Runner, function_tool
from memory_store import init_db, save_memory, get_memory
from memory_store import get_all_memories as fetch_all_memories
from memory_store import add_to_history, get_recent_history
import asyncio

USER_ID = "primary_user"  # ⚠ Demo only — NEVER hardcode in production.
# In a real service, get user_id from your auth layer (cookie, JWT, header) or the Runner context.
# Note: init_db() is async — we call it from main() below, not at import time.

@function_tool
async def memorize(key: str, value: str) -> str:
    """
    Stocke une information sur l'utilisateur pour les sessions futures.

    Args:
        key: Identifiant de l'information (ex: "preferred_language", "framework", "level")
        value: L'information à retenir
    """
    await save_memory(USER_ID, key, value)
    return f"Memorized: {key} = {value}"

@function_tool
async def recall(key: str) -> str:
    """
    Rappelle une information stockée sur l'utilisateur.

    Args:
        key: L'information à rappeler
    """
    value = await get_memory(USER_ID, key)
    if value:
        return f"{key}: {value}"
    return f"No stored information for '{key}'"

@function_tool
async def get_all_memories() -> str:
    """Retourne toutes les informations stockées sur l'utilisateur."""
    memories = await fetch_all_memories(USER_ID)
    if not memories:
        return "No information stored yet."
    return "\n".join([f"- {k}: {v}" for k, v in memories.items()])

agent = Agent(
    name="PersonalAssistant",
    model=config.DEFAULT_MODEL,
    instructions="""You are a personal development assistant.
    
    You MUST memorize important information about the user when they mention it:
    - Their preferred language/framework
    - Their level (junior, senior, etc.)
    - Their current projects
    - Their preferences (code style, tools, etc.)
    
    At the start of each conversation, check what you already know via get_all_memories().
    Adapt your responses based on the stored profile.""",
    tools=[memorize, recall, get_all_memories],
)

async def main():
    # Initialiser la DB au démarrage
    await init_db()

    # Récupérer l'historique récent (await indispensable: la fonction est async)
    history = await get_recent_history(USER_ID, limit=6)

    print("=== Session started ===\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in ["quit", "exit", "q"]:
            break

        messages = history + [{"role": "user", "content": question}]

        result = await Runner.run(
            agent,
            input=messages,
        )

        print(f"\nAgent: {result.final_output}\n")

        # Sauvegarder dans l'historique persistant (audit, transcript role/content).
        # La table conversation_history garde un transcript simplifié pour audit ;
        # la variable `history` ci-dessous garde le contexte SDK complet pour le LLM.
        await add_to_history(USER_ID, "user", question)
        await add_to_history(USER_ID, "assistant", result.final_output)

        # to_input_list() conserve l'historique complet du run :
        # messages, tool calls (memorize, recall...), tool outputs, handoffs.
        #
        # ⚠ Ne PAS slicer naïvement (history[-N:]) : on risque de couper une paire
        # tool_call / tool_call_output et de casser l'API au tour suivant avec
        # "No tool call found for function call output".
        #
        # Pour une conversation longue en production, préférez SQLiteSession
        # (vu en 3.2) qui gère le truncage intelligemment, ou implémentez vous-même
        # un truncage qui respecte les paires call_id.
        history = result.to_input_list()

asyncio.run(main())
