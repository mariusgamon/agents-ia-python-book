# bounded_agent.py — safe and predictable
import config

from agents import Agent, Runner
import asyncio

agent = Agent(
    name="Researcher",
    model=config.DEFAULT_MODEL,
    instructions="""Compare FastAPI, Django, and Flask for REST APIs.
    Give a clear recommendation in under 200 words.
    Do not over-analyze — one pass is enough.""",
    # Bounded instructions: 3 frameworks, word limit, explicit stop signal
)

async def main():
    result = await Runner.run(
        agent,
        input="Which Python web framework should I use for a REST API?",
        max_turns=5  # Hard ceiling: agent stops after 5 LLM round-trips
    )
    print(result.final_output)

asyncio.run(main())
