# first_agent_openrouter.py — premier agent du Jour 1 avec Claude via OpenRouter
from agents import Agent, Runner, set_tracing_disabled
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from openai import AsyncOpenAI
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()  # lit OPENROUTER_API_KEY dans .env

# OpenAI traces ne fonctionnent pas avec un endpoint tiers — on les désactive.
set_tracing_disabled(True)

# Point the OpenAI client at OpenRouter instead of OpenAI.
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Wrap the redirected client in an OpenAIChatCompletionsModel — the SDK's
# Agent() doesn't accept openai_client= directly. Most non-OpenAI providers
# don't support the Responses API, so use Chat Completions explicitly.
model = OpenAIChatCompletionsModel(
    model="anthropic/claude-sonnet-4.6",  # Claude via OpenRouter
    # Other examples: "google/gemini-3-flash", "meta-llama/llama-3.3-70b-instruct"
    openai_client=client,
)

agent = Agent(
    name="DevAssistant",
    instructions="You are a Python developer assistant.",
    model=model,  # pass the wrapped model, not a string
)

async def main():
    result = await Runner.run(agent, input="Difference between list and tuple?")
    print(result.final_output)

asyncio.run(main())
