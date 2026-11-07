# orchestrator_relay.py
from agents import Agent, Runner

content_finder = Agent(
    name="content_finder",
    model="gpt-5.4-mini",
    instructions="Tu cherches dans la base documentaire et retournes les extraits pertinents.",
    tools=[search_docs],
)

orchestrator = Agent(
    name="orchestrator",
    model="gpt-5.4-mini",
    instructions=(
        "Tu es un assistant. Pour toute demande de recherche documentaire, "
        "transfère la main à content_finder. Pour les autres demandes, réponds directement."
    ),
    handoffs=[content_finder],  # transfert complet, pas de réinterprétation
)

result = await Runner.run(orchestrator, input="Trouve-moi la doc sur l'API auth")
print(result.final_output)
# → Sortie de content_finder, intacte.
