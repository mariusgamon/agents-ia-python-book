# observe_with_langfuse.py — tracer un agent avec Langfuse (SDK Langfuse v3 et suivants)
import config
from langfuse import observe, get_client
from agents import Agent, Runner
import asyncio

# Le client lit LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY et LANGFUSE_BASE_URL
# (ou LANGFUSE_HOST) dans l'environnement : rien à passer en dur.
langfuse = get_client()

agent = Agent(
    name="TracedAssistant",
    instructions="You are a helpful assistant.",
    model=config.DEFAULT_MODEL,
)


@observe(as_type="generation")  # ← chaque appel crée une observation dans Langfuse
async def ask_agent(question: str) -> str:
    # Métadonnées pour filtrer dans le dashboard
    langfuse.update_current_generation(
        model=config.DEFAULT_MODEL,
        metadata={"agent": "TracedAssistant", "version": "1.0"},
    )
    result = await Runner.run(agent, input=question)

    # Tokens du run complet (context_wrapper.usage agrège tous les appels)
    usage = result.context_wrapper.usage
    langfuse.update_current_generation(
        usage_details={"input": usage.input_tokens, "output": usage.output_tokens},
    )
    return result.final_output


async def main():
    answer = await ask_agent("Quelle est la différence entre une list et un tuple ?")
    print(answer)
    langfuse.flush()  # force l'envoi avant de quitter


asyncio.run(main())
