# my_agents.py — l'agent « de production » testé par tests/test_golden.py et tests/test_snapshot.py
# (fichier du repo companion : le livre ne montre que les tests)
import config
from agents import Agent
from tools.vat import calculate_vat
from tools.weather import get_weather

billing_agent = Agent(
    name="BillingAssistant",
    instructions=(
        "You are a billing assistant. Use calculate_vat for any tax question "
        "and get_weather for any weather question. Answer in the user's language."
    ),
    tools=[calculate_vat, get_weather],
    model=config.DEFAULT_MODEL,
)
