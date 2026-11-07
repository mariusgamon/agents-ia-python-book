from mistral_raw import llm
from tools import search_web_snippets, calculate


# ─── Tool (action atomique) ────────────────────────────────────────────────────
# Rien à redéfinir — get_weather, calculate etc. sont déjà des tools.


# ─── Skill (logique composée) ─────────────────────────────────────────────────

def skill_research_and_summarize(query: str) -> str:
    """
    Skill : recherche des actualités ET les résume en 3 points.
    Combine search_web_snippets (tool) + un appel LLM pour synthétiser.
    """
    # Étape 1 : récupérer les données brutes via un tool
    raw = search_web_snippets(query=query, n=5)

    # Étape 2 : demander au LLM de synthétiser
    summary_messages = [
        {
            "role":    "system",
            "content": "Tu es expert en veille. Synthétise en 3 points clés, concis.",
        },
        {
            "role":    "user",
            "content": f"Sujet : {query}\n\nRésultats bruts :\n{raw}",
        },
    ]
    return llm(summary_messages)


def skill_budget_check(amount: float, vat_rate: float = 0.20) -> str:
    """
    Skill : calcule montant HT, TVA, TTC et génère un commentaire.
    Combine calculate (tool) + logique métier + LLM pour le commentaire.
    """
    # Étape 1 : calculs via le tool
    ttc_result   = calculate(f"{amount} * {1 + vat_rate}")
    vat_amount   = calculate(f"{amount} * {vat_rate}")

    # Étape 2 : commentaire contextuel via LLM
    comment_msgs = [
        {"role": "system", "content": "Donne un conseil budget bref (1 phrase)."},
        {
            "role":    "user",
            "content": f"HT: {amount}€  TVA({vat_rate*100:.0f}%): {vat_amount}  {ttc_result}",
        },
    ]
    comment = llm(comment_msgs)

    return f"HT : {amount}€ | {ttc_result} | Conseil : {comment}"


# ─── Registre mis à jour ───────────────────────────────────────────────────────
from dispatcher import TOOLS  # on étend le registre existant

TOOLS.update({
    "research_and_summarize": skill_research_and_summarize,
    "budget_check":           skill_budget_check,
})
