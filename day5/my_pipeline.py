# my_pipeline.py — le « code qui appelle Runner.run() » testé par tests/test_pipeline.py
# (fichier du repo companion : le livre ne montre que le test)
import config
from agents import Agent, Runner

FALLBACK_MESSAGE = "Désolé, je n'ai pas pu générer de réponse. Réessayez dans un instant."

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant. Answer concisely.",
    model=config.DEFAULT_MODEL,
)


async def process_request(user_input: str) -> dict:
    result = await Runner.run(agent, input=user_input, max_turns=5)
    output = (result.final_output or "").strip()

    # Agent muet : on renvoie un message de repli plutôt qu'une réponse vide
    if not output:
        return {"status": "empty_response", "fallback_used": True, "output": FALLBACK_MESSAGE}
    return {"status": "ok", "fallback_used": False, "output": output}
