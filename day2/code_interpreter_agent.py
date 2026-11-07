# code_interpreter_agent.py
import config

from agents import Agent, Runner, CodeInterpreterTool, enable_verbose_stdout_logging
import asyncio

# Print every internal SDK event to stdout (turn start, LLM call, tool call, output).
# Useful for tools whose effect is not obvious in the final answer —
# you can see whether CodeInterpreterTool was actually invoked, or if the model
# just computed the result itself. Drop this line once you trust the agent.
enable_verbose_stdout_logging()

agent = Agent(
    name="AnalysisAgent",
    # Use a model documented as compatible with Code Interpreter (Responses API).
    # Older official examples use gpt-4.1, retired in January 2027. If you change
    # the model, test the tool call explicitly — not all models support all tools.
    model="gpt-5.4",
    instructions=(
        "You analyze data and produce precise statistics. "
        "Use the python tool to run computations rather than calculating by hand."
    ),
    tools=[
        CodeInterpreterTool(
            tool_config={
                "type": "code_interpreter",
                "container": {"type": "auto"},
            }
        )
    ],
)

async def main():
    result = await Runner.run(
        agent,
        input="""Here are monthly sales: [12000, 15000, 9000, 18000, 22000, 19000].
        Calculate the mean, the median, and identify the weakest month.
        Use the python tool to run the computations."""
    )
    print(result.final_output)

asyncio.run(main())
