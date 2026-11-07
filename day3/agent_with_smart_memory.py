# agent_with_smart_memory.py — use targeted lookup instead of dumping all memories
import config

from agents import Agent, Runner
from smart_memory_lookup import build_memory_context
from memory_store import init_db
import asyncio

USER_ID = "primary_user"  # ⚠ Demo only — NEVER hardcode in production.
# In a real service, get user_id from your auth layer (cookie, JWT, header) or the Runner context.

def classify_query(question: str) -> list[str]:
    """
    Decide which memory categories to fetch based on the question.
    Simple version: keyword matching. Production: stable rules/tags first,
    fall back to a small LLM only if questions vary too much.
    """
    q = question.lower()
    categories = []

    # Technical context
    if any(w in q for w in ["framework", "library", "test", "deploy", "api"]):
        categories += ["language", "framework", "preferred_testing"]

    # Project context
    if any(w in q for w in ["project", "architecture", "feature"]):
        categories += ["current_project", "tech_stack", "team_size"]

    # Style context
    if any(w in q for w in ["code", "convention", "style"]):
        categories += ["code_style", "linter", "naming_convention"]

    return categories or ["language", "level"]  # sensible default

async def ask(question: str) -> str:
    # Fetch only the memories relevant to THIS question
    relevant_categories = classify_query(question)
    memory_context = await build_memory_context(USER_ID, relevant_categories)

    # Build the system prompt dynamically with the compact context
    base_instructions = "You are a personal development assistant."
    instructions = (
        f"{base_instructions}\n\n{memory_context}"
        if memory_context
        else base_instructions
    )

    agent = Agent(
        name="SmartAssistant",
        instructions=instructions,
        model=config.DEFAULT_MODEL,
    )

    result = await Runner.run(agent, input=question)
    return result.final_output

async def main():
    await init_db()  # crée la table si agent_with_memory.py n'a jamais tourné
    questions = [
        "Which testing framework do you recommend?",
        "How should I structure my project into microservices?",
        "What naming conventions should I use for my variables?",
    ]
    for q in questions:
        print(f"\nQ: {q}")
        print(f"A: {await ask(q)}")

asyncio.run(main())
