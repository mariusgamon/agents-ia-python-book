# naive_retry.py — this pattern can easily burn ~€100 in a single incident
import config

import asyncio
from agents import Agent, Runner
from openai import RateLimitError, APIStatusError

agent = Agent(name="BatchProcessor", instructions="You rewrite product descriptions for SEO.", model="gpt-5.4")

async def process_document(document: str) -> str:
    """Retry with exponential backoff — no cap, no limit, no budget."""
    delay = 1.0
    while True:  # <-- the expensive line
        try:
            result = await Runner.run(agent, input=document)
            return result.final_output
        except (RateLimitError, APIStatusError):
            await asyncio.sleep(delay)
            delay *= 2  # 1s, 2s, 4s, 8s, 16s... forever
