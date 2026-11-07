# model_split_config.py
# The cost-effective way to configure multi-agent systems
# Use cheap models for leaf agents, expensive ones for orchestration

from agents import Agent, Runner

# Leaf agents — high volume, simple tasks → cheap model
collection_agent = Agent(
    name="Collector",
    model="gpt-5.4-mini",  # $0.75/$4.50 per million tokens (April 2026)
    instructions="Collect raw data. Return facts only.",
)

formatting_agent = Agent(
    name="Formatter",
    model="gpt-6-luna",  # $0.10/$0.50 — luna is enough for pure formatting
    instructions="Format input into structured output.",
)

# Orchestrator — low volume, complex decisions → capable model
orchestrator = Agent(
    name="Orchestrator",
    model="gpt-5.4",  # $2.50/$15.00 — flagship for routing decisions
    instructions="Coordinate agents. Decide what to delegate and when.",
)

# max_turns is set per run, not on the Agent:
#   await Runner.run(collection_agent, input=..., max_turns=5)
#   await Runner.run(formatting_agent, input=..., max_turns=3)
#   await Runner.run(orchestrator,      input=..., max_turns=10)
