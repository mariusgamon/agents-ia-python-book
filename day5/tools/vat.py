# tools/vat.py
from agents import function_tool


def compute_vat(amount_excl_tax: float, rate: float = 0.20) -> dict:
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


# La même fonction, exposée à l'agent comme outil (même nom qu'au Jour 2)
calculate_vat = function_tool(compute_vat, name_override="calculate_vat")
