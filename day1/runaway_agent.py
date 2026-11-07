# runaway_agent.py — looks fine until the bill arrives
import config

from agents import Agent, Runner
import asyncio

agent = Agent(
    name="Researcher",
    model=config.DEFAULT_MODEL,
    instructions="""Find the absolute best Python web framework
    by comparing all options. Be thorough and exhaustive.""",
    # No explicit max_turns — relies on the SDK default (10)
)

async def main():
    result = await Runner.run(
        agent,
        input="Compare all Python web frameworks and pick the best one"
    )
    print(result.final_output)

asyncio.run(main())
