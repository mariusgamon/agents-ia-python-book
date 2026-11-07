# first_agent.py
import config  # charge le .env et valide la clé

from agents import Agent, Runner
import asyncio

agent = Agent(
    name="DevAssistant",
    model=config.DEFAULT_MODEL,
    instructions="You are a Python developer assistant. Answer concisely and precisely.",
)

async def main():
    result = await Runner.run(
        agent,
        input="What's the difference between a list and a tuple in Python?"
    )
    print(result.final_output)

asyncio.run(main())
