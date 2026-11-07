# handoff_triage.py
import config

from agents import Agent, Runner
import asyncio

# Chaque agent de langue produit la réponse FINALE dans sa langue
french_agent = Agent(
    name="FrenchAgent",
    model=config.DEFAULT_MODEL,
    instructions="Tu réponds toujours en français, clairement et sans détour.",
)

spanish_agent = Agent(
    name="SpanishAgent",
    model=config.DEFAULT_MODEL,
    instructions="Respondes siempre en español, de forma clara y directa.",
)

# L'agent de tri aiguille puis s'efface : il ne répond jamais lui-même
triage_agent = Agent(
    name="TriageAgent",
    model=config.DEFAULT_MODEL,
    instructions="""Détecte la langue de la question.
    Si c'est du français, transfère à FrenchAgent.
    Si c'est de l'espagnol, transfère à SpanishAgent.
    Ne réponds pas toi-même.""",
    handoffs=[french_agent, spanish_agent],
)

async def main():
    result = await Runner.run(triage_agent, input="¿Qué es un agente de IA?")
    # La réponse vient de SpanishAgent, pas du triage
    print(result.final_output)

asyncio.run(main())
