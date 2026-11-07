# expense_agent_claude.py
import json
import re
from claude_agent_sdk import (
    tool, create_sdk_mcp_server,
    ClaudeAgentOptions, ClaudeSDKClient,
)

# ─── TOOL — @function_tool → @tool + create_sdk_mcp_server ───
@tool(
    "check_policy",
    "Look up expense policy for a category. Returns approval limit. "
    "Valid categories: meals, travel, software, other.",
    {"category": str, "amount": float},
)
async def check_policy_claude(args):
    limits = {"meals": 75.0, "travel": 500.0, "software": 200.0, "other": 50.0}
    category, amount = args["category"], args["amount"]
    result = {
        "category": category,
        "limit": limits.get(category.lower(), 50.0),
        "requires_receipt": amount > 25.0,
    }
    return {"content": [{"type": "text", "text": json.dumps(result)}]}

policy_server = create_sdk_mcp_server(name="expense", tools=[check_policy_claude])

# ─── AGENT CONFIG — Agent(...) → ClaudeAgentOptions ───
expense_options = ClaudeAgentOptions(
    model="claude-sonnet-4-6",
    system_prompt=(
        "You approve or flag expense submissions. "
        "Always call check_policy first to get the limit for the category. "
        "Approve if amount is under the limit; otherwise flag for manager review."
    ),
    mcp_servers={"expense": policy_server},
    allowed_tools=["mcp__expense__check_policy"],
)

# ─── GUARDRAILS — @input_guardrail → plain function avant la boucle ───
def has_dollar_amount_check(user_input: str) -> tuple[bool, str | None]:
    """Input check — returns (allowed, rejection_message)."""
    if re.search(r"\$\d+", user_input):
        return True, None
    return False, "I need a dollar amount. Please include one (e.g., '$47')."

# ─── RUN — Runner.run() → ClaudeSDKClient context manager ───
async def run(msg: str) -> str:
    # Input guardrail : court-circuit avant que l'agent ne tourne
    allowed, rejection = has_dollar_amount_check(msg)
    if not allowed:
        return rejection

    async with ClaudeSDKClient(options=expense_options) as client:
        await client.query(msg)
        messages = [m async for m in client.receive_response()]
        # receive_response() garantit que ResultMessage est le dernier event
        return messages[-1].result or ""
