# agent_with_loop_guard.py
import config

from agents import Agent, Runner, function_tool
import asyncio

# --- Level 1: Tool-level call counter (in-module state, reset per run) ---
_call_counts: dict[str, int] = {}
MAX_SEARCHES = 3

@function_tool
async def web_search(query: str) -> dict:
    """Search the web for recent information.
    You have a MAXIMUM of 3 searches per user question.
    Check _calls_remaining in the result — when it hits 0, stop and synthesize.
    """
    # Inline guard: count this invocation
    _call_counts["web_search"] = _call_counts.get("web_search", 0) + 1
    count = _call_counts["web_search"]

    if count > MAX_SEARCHES:
        return {
            "error": f"web_search reached the {MAX_SEARCHES} call limit",
            "action": "Stop searching and synthesize from what you already have.",
        }

    # --- Real search would go here. For the demo we return a placeholder. ---
    # In production, replace this block with your actual search API call:
    #   - httpx call to your search provider
    #   - or tavily/serper/brave-search SDK
    #   - or a local RAG against your docs
    fake_results = [
        {"title": f"Result {i} for '{query}'", "url": f"https://example.com/{i}"}
        for i in range(1, 4)
    ]

    return {
        "query": query,
        "results": fake_results,
        "_calls_remaining": MAX_SEARCHES - count,
    }

# --- Level 2: Agent instructions with explicit stop criterion ---
agent = Agent(
    name="ResearchAgent",
    model=config.DEFAULT_MODEL,
    instructions="""You research topics for the user. Strict rules:
    - MAXIMUM 3 web searches per question. No exceptions.
    - After each search, ask yourself: can I answer with what I have?
    - If yes → stop searching, write your synthesis.
    - If no → search again, but ONLY if previous results were truly off-topic.
    - NEVER reformulate a query to get "better" results on the same topic.
    - When _calls_remaining hits 0, you MUST answer with existing data.""",
    tools=[web_search],
)

# --- Level 3: Runner hard stop ---
async def main():
    _call_counts.clear()  # reset counters for this run
    result = await Runner.run(
        agent,
        input="Summarize this week's tech news",
        max_turns=10,  # Hard ceiling: 10 LLM turns including tool calls
    )
    print(result.final_output)
    print(f"\n[Total searches made: {_call_counts.get('web_search', 0)}]")

asyncio.run(main())
