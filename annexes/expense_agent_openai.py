# expense_agent_openai.py
from agents import Agent, GuardrailFunctionOutput, Runner, function_tool, input_guardrail
import re

@function_tool
def check_policy(category: str, amount: float) -> dict:
    """Look up expense policy for a category. Returns approval limit.
    Valid categories: meals, travel, software, other."""
    limits = {"meals": 75.0, "travel": 500.0, "software": 200.0, "other": 50.0}
    return {
        "category": category,
        "limit": limits.get(category.lower(), 50.0),
        "requires_receipt": amount > 25.0,
    }

@input_guardrail
def has_dollar_amount(ctx, agent, user_input: str) -> GuardrailFunctionOutput:
    has_amount = bool(re.search(r"\$\d+", user_input))
    return GuardrailFunctionOutput(
        output_info={"has_amount": has_amount},
        tripwire_triggered=not has_amount,
    )

expense_agent = Agent(
    name="Expense Approver",
    instructions=(
        "You approve or flag expense submissions. "
        "Always call check_policy first to get the limit for the category. "
        "Approve if amount is under the limit; otherwise flag for manager review."
    ),
    tools=[check_policy],
    input_guardrails=[has_dollar_amount],
    model="gpt-5.4-mini",
)

async def run(msg: str) -> str:
    result = await Runner.run(expense_agent, msg)
    return result.final_output
