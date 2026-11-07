# robust_agent_config.py — the 4 lines that save your weekend budget
from agents import Agent, Runner

class BudgetExhaustedError(RuntimeError):
    """Raised when the token budget for a job is exhausted."""

# Lines 1-2: max_turns goes on Runner.run(), not on Agent() —
#            kills infinite loops (no support ticket needs 10+ tool calls)
agent = Agent(
    name="SupportAgent",
    instructions="You process support tickets and draft responses.",
    model="gpt-5.4",
)

# Lines 3-4: budget guard stops the pipeline before the bill explodes
MAX_TOKENS_PER_JOB = 5_000_000  # ~$31.25 with a blended cost of $6.25/M (varies per model)

async def run_with_budget_guard(agent, prompt, budget_remaining):
    """Halts execution when token budget is exhausted."""
    if budget_remaining <= 0:
        raise BudgetExhaustedError(
            f"Token budget blown: {MAX_TOKENS_PER_JOB - budget_remaining} used"
        )
    result = await Runner.run(agent, input=prompt, max_turns=10)
    # context_wrapper.usage aggregates ALL LLM calls in the run
    # (tool calls, handoffs, multi-turn) — not just the last response.
    tokens_used = result.context_wrapper.usage.total_tokens
    return result, budget_remaining - tokens_used
