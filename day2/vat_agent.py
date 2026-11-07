# vat_agent.py — agent with a custom tool, end-to-end
import config  # charge le .env et valide la clé

from agents import Agent, Runner, function_tool
import asyncio

@function_tool
def calculate_vat(amount_excl_tax: float, rate: float = 0.20) -> dict:
    """
    Calculate VAT and the total amount including tax.

    Args:
        amount_excl_tax: Amount excluding tax in euros
        rate: VAT rate (default 20%)

    Returns:
        Dictionary with vat_amount and amount_incl_tax
    """
    vat = amount_excl_tax * rate
    total = amount_excl_tax + vat
    return {"vat_amount": round(vat, 2), "amount_incl_tax": round(total, 2)}

# Create an agent with the tool
agent = Agent(
    name="BillingAssistant",
    model=config.DEFAULT_MODEL,
    instructions="You are an accounting assistant. Use calculate_vat for any VAT computation.",
    tools=[calculate_vat],
)

async def main():
    result = await Runner.run(
        agent,
        input="How much do I pay including tax for a $1200 invoice (excl. tax)?"
    )
    print(result.final_output)

asyncio.run(main())
