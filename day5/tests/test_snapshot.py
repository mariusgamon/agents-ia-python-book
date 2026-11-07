# tests/test_snapshot.py
# pip install syrupy
# 1er lancement : pytest tests/test_snapshot.py --snapshot-update  (crée le snapshot)
# Lancements suivants : pytest compare. Un diff = changement de comportement à valider.
import pytest
from agents import Runner
from my_agents import billing_agent  # votre agent de production

@pytest.mark.asyncio
async def test_agent_tool_sequence_snapshot(snapshot):
    result = await Runner.run(billing_agent, input="TVA sur 1000 € à 20 %", max_turns=3)
    # On ne snapshotte pas le texte brut du LLM : il change à chaque appel.
    # On snapshotte la séquence d'outils appelés, qui doit rester stable.
    tools_called = [
        item.raw_item.name
        for item in result.new_items
        if item.type == "tool_call_item"
    ]
    assert tools_called == snapshot
