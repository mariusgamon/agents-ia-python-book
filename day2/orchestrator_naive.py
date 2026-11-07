# orchestrator_naive.py
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
    instructions="Tu es un assistant. Utilise tes outils si nécessaire pour répondre.",
    tools=[
        content_finder.as_tool(
            tool_name="find_content",
            tool_description="Cherche dans la base documentaire et retourne les extraits pertinents.",
        ),
    ],
)

result = await Runner.run(orchestrator, input="Trouve-moi la doc sur l'API auth")
print(result.final_output)
# → "Je n'ai pas trouvé de document correspondant."
