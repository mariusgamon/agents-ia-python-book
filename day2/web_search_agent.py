# web_search_agent.py
import config

from agents import Agent, Runner, WebSearchTool
import asyncio

agent = Agent(
    name="ResearchAgent",
    model=config.DEFAULT_MODEL,
    instructions="You are a technology watch agent. Search for recent information and synthesize it.",
    tools=[WebSearchTool()],
)

async def main():
    result = await Runner.run(
        agent,
        input="What's the weather in Paris right now, and what are today's main sports headlines?"
    )
    print(result.final_output)

asyncio.run(main())
