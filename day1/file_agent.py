# file_agent.py
import config  # charge le .env et valide la clé

from agents import Agent, Runner, function_tool
import asyncio

# Load file content once at startup — not inside the tool
with open("data/notes.txt", "r", encoding="utf-8") as f:
    FILE_CONTENT = f.read()

@function_tool
def read_notes() -> str:
    """Retourne le contenu des notes de réunion."""
    return FILE_CONTENT

agent = Agent(
    name="NotesAssistant",
    model=config.DEFAULT_MODEL,
    instructions="""You are an assistant that answers questions about meeting notes.
    Use the read_notes() tool to access the content.
    Answer directly and precisely.""",
    tools=[read_notes],
)

async def main():
    questions = [
        "Quel est le budget marketing ?",
        "Qui est le contact client prioritaire ?",
        "Quelle est la deadline pour l'API v2 ?",
    ]
    
    for question in questions:
        print(f"\nQuestion : {question}")
        result = await Runner.run(agent, input=question)
        print(f"Réponse : {result.final_output}")

asyncio.run(main())
