# tests/test_agent_with_respx.py
import respx
import httpx
import pytest
from agents import Agent, Runner

@respx.mock
@pytest.mark.asyncio
async def test_agent_parses_tool_call():
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{
                "message": {
                    "role": "assistant",
                    "tool_calls": [{
                        "id": "call_1", "type": "function",
                        "function": {"name": "get_weather",
                                     "arguments": '{"city": "Paris"}'}
                    }]
                },
                "finish_reason": "tool_calls"
            }]
        })
    )
    # ... lancez Runner.run() et vérifiez que le tool a bien été appelé
