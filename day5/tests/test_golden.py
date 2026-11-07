# tests/test_golden.py — load golden_cases.json and check each one
import json
import pytest
from pathlib import Path
from agents import Runner
from my_agents import billing_agent  # your production agent

GOLDEN = json.loads(Path("tests/golden_cases.json").read_text())

def normalize(text: str) -> str:
    """Supprime les espaces, y compris insécables : « 1 200 » et « 1200 » deviennent identiques."""
    for space in ("\u202f", "\u00a0", " "):
        text = text.replace(space, "")
    return text.lower()

@pytest.mark.asyncio
@pytest.mark.parametrize("case", GOLDEN, ids=lambda c: c["input"][:40])
async def test_golden_case(case):
    result = await Runner.run(billing_agent, input=case["input"], max_turns=3)

    # 1. The expected tool was called
    tools_called = [
        item.raw_item.name
        for item in result.new_items
        if item.type == "tool_call_item"
    ]
    assert case["expected_tool"] in tools_called, (
        f"Expected {case['expected_tool']}, got {tools_called}"
    )

    # 2. The output contains the expected substrings
    output = normalize(result.final_output)
    for needle in case["expected_contains"]:
        assert normalize(needle) in output, f"Missing '{needle}' in output: {output[:200]}"

    # 3. Cost regression: a prompt change that doubles tokens is a red flag
    if "max_tokens" in case:
        used = result.context_wrapper.usage.total_tokens
        assert used <= case["max_tokens"], (
            f"Cost regression: {used} tokens used, max {case['max_tokens']}. "
            f"A prompt change probably bloated the context."
        )
