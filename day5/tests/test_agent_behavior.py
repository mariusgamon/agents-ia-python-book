# tests/test_agent_behavior.py
import pytest
import config
from agents import Agent, Runner, ModelSettings
from tools.vat import calculate_vat

# Agent de test (même config que production, coût minime)
agent = Agent(
    name="TestAssistant",
    instructions="You are a billing assistant. Use calculate_vat for any tax question.",
    tools=[calculate_vat],
    model="gpt-5.4-mini",  # moins cher pour les tests
)

@pytest.mark.asyncio
async def test_agent_calls_vat_tool():
    """L'agent doit appeler calculate_vat quand on pose une question de TVA."""
    result = await Runner.run(
        agent,
        input="Combien je paie TTC pour 500€ HT ?",
        max_turns=3,
    )
    # Vérifier que l'outil a été appelé
    tool_call_items = [
        item for item in result.new_items
        if item.type == "tool_call_item"
    ]
    assert len(tool_call_items) > 0, "L'agent n'a pas appelé calculate_vat"

@pytest.mark.asyncio
async def test_agent_response_contains_amount():
    """La réponse doit contenir le montant TTC correct."""
    result = await Runner.run(
        agent,
        input="TVA sur 1000€ HT à 20% ?",
        max_turns=3,
    )
    # Les modèles écrivent souvent « 1 200 » avec une espace insécable (U+202F ou U+00A0)
    output = result.final_output
    for space in ("\u202f", "\u00a0", " "):
        output = output.replace(space, "")
    assert "1200" in output

@pytest.mark.asyncio
async def test_agent_stops_on_max_turns():
    """Test déterministe : l'appel d'outil est forcé et un seul tour est autorisé.
    L'agent a besoin d'un second tour pour répondre après l'outil : le SDK doit
    lever MaxTurnsExceeded au lieu de continuer."""
    from agents.exceptions import MaxTurnsExceeded
    forced = agent.clone(model_settings=ModelSettings(tool_choice="required"))
    with pytest.raises(MaxTurnsExceeded):
        await Runner.run(forced, input="TVA sur 100€ HT ?", max_turns=1)
