# multi_agent_orchestration.py
import config

from agents import Agent, Runner, WebSearchTool
import asyncio

# Specialized agent: research
research_agent = Agent(
    name="ResearchAgent",
    model=config.DEFAULT_MODEL,
    instructions="""You search for precise technical information.
    You return verifiable facts, no opinions.""",
    tools=[WebSearchTool()],
)

# Specialized agent: writing
writer_agent = Agent(
    name="WriterAgent",
    model=config.DEFAULT_MODEL,
    instructions="""You receive raw information and transform it into clear content.
    You write for developers. You get straight to the point.
    No repetition, no filler.""",
)

# Wrap each specialist as a tool the orchestrator can call.
# This pattern keeps the orchestrator in control of the flow:
# it calls research_tool, gets the facts back, then calls writer_tool.
research_tool = research_agent.as_tool(
    tool_name="research_technical_facts",
    tool_description="Find precise, verifiable technical facts on a given topic.",
)

writer_tool = writer_agent.as_tool(
    tool_name="write_developer_summary",
    tool_description="Transform raw facts into a concise developer-facing summary.",
)

# The orchestrator agent that coordinates the specialists
orchestrator = Agent(
    name="Orchestrator",
    model=config.DEFAULT_MODEL,
    instructions="""You coordinate technical content production.
    1. Use research_technical_facts to gather verifiable facts on the topic.
    2. Use write_developer_summary to produce the final summary from those facts.
    3. Return the final content to the user.""",
    tools=[research_tool, writer_tool],
)

async def main():
    result = await Runner.run(
        orchestrator,
        input="Write a summary of the main new features in Python 3.13"
    )
    print(result.final_output)

asyncio.run(main())
