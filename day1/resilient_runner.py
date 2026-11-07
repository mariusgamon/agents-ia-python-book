# resilient_runner.py — retry with exponential backoff
# pip install backoff
import config

import asyncio
import backoff
from agents import Agent, Runner
from openai import RateLimitError, APITimeoutError, APIConnectionError

agent = Agent(
    name="ResilientWorker",
    model=config.DEFAULT_MODEL,
    instructions="Process the data step by step. Save intermediate results.",
)

@backoff.on_exception(
    backoff.expo,
    (RateLimitError, APITimeoutError, APIConnectionError),
    max_tries=4,
    max_value=60,
    jitter=backoff.full_jitter,
)
async def run_with_retry(input_text: str):
    """Backoff exponentiel + jitter sur les erreurs transitoires (429, timeouts, 5xx)."""
    return await Runner.run(agent, input=input_text, max_turns=10)

async def main():
    result = await run_with_retry(
        "Analyze this Q3 data and extract the 3 key metrics: "
        "Revenue 1.2M (+15% YoY), Costs 800K (+8% YoY), "
        "Active customers 4500 (+12% YoY)."
    )
    print(result.final_output)

asyncio.run(main())
