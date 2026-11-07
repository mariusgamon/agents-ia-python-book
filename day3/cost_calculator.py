# cost_calculator.py — version complète (le livre en montre une version condensée au §3.5)
#
# Coût de l'historique injecté dans le prompt, selon trois stratégies mémoire.
# Scénario du livre : chatbot de support SaaS B2B, 500 conversations/jour,
# 15 échanges par conversation, ~500 tokens par échange (100 user + 400 assistant).
#
#     python cost_calculator.py
import math

MODEL_INPUT_COST_PER_1M = 2.50    # $ per 1M input tokens. Update from the official pricing page.
MODEL_OUTPUT_COST_PER_1M = 10.00  # $ per 1M output tokens (output ≈ 4× input)

CONVERSATIONS_PER_DAY = 500
TURNS = 15
TOKENS_PER_TURN = 500
DAYS_PER_MONTH = 30

SUMMARY_EVERY = 5          # on résume l'historique tous les 5 tours
SUMMARY_TOKENS = 350       # taille du résumé qui remplace l'historique brut
EXTERNAL_MEMORY_TOKENS = 350  # faits ciblés injectés depuis SQLite à chaque requête


def monthly_memory_cost(
    conversations_per_day: int,
    turns: int,
    avg_history_tokens: int,
) -> float:
    """Coût mensuel de l'historique injecté dans le prompt."""
    daily = avg_history_tokens * turns * conversations_per_day
    return daily * MODEL_INPUT_COST_PER_1M / 1_000_000 * DAYS_PER_MONTH


def _usd(x: float) -> float:
    """Arrondi commercial au centime (round() arrondit 65.625 à 65.62)."""
    return math.floor(x * 100 + 0.5) / 100


def _report(avg_tokens: float, extra_daily_cost: float = 0.0) -> dict:
    requests_per_day = CONVERSATIONS_PER_DAY * TURNS
    daily_tokens = float(avg_tokens * requests_per_day)
    daily_cost = daily_tokens * MODEL_INPUT_COST_PER_1M / 1_000_000 + extra_daily_cost
    return {
        "daily_history_tokens": round(daily_tokens, 1),
        "daily_cost_usd": _usd(daily_cost),
        "monthly_cost_usd": _usd(daily_cost * DAYS_PER_MONTH),
    }


def naive_full_history() -> dict:
    """Tout l'historique est renvoyé à chaque tour : (t-1) × 500 tokens au tour t."""
    history = [(t - 1) * TOKENS_PER_TURN for t in range(1, TURNS + 1)]
    avg = sum(history) / TURNS
    return {"avg_history_tokens_per_request": round(avg, 1), **_report(avg)}


def summarize_every_n_turns() -> dict:
    """
    Tous les SUMMARY_EVERY tours, l'historique brut est remplacé par un résumé.
    Chaque synthèse est un appel LLM : on paie l'historique résumé en input
    et le résumé généré en output.
    """
    history, summary_calls_input = [], 0
    for t in range(1, TURNS + 1):
        block = (t - 1) // SUMMARY_EVERY            # nombre de synthèses déjà faites
        raw = ((t - 1) % SUMMARY_EVERY) * TOKENS_PER_TURN
        history.append((SUMMARY_TOKENS if block else 0) + raw)

    n_summaries = (TURNS - 1) // SUMMARY_EVERY
    for k in range(n_summaries):
        # entrée = résumé précédent (s'il existe) + les SUMMARY_EVERY derniers tours
        summary_calls_input += (SUMMARY_TOKENS if k else 0) + SUMMARY_EVERY * TOKENS_PER_TURN

    synthesis_daily = CONVERSATIONS_PER_DAY * (
        summary_calls_input * MODEL_INPUT_COST_PER_1M
        + n_summaries * SUMMARY_TOKENS * MODEL_OUTPUT_COST_PER_1M
    ) / 1_000_000

    avg = sum(history) / TURNS
    return {
        "avg_history_tokens_per_request": round(avg, 1),
        **_report(avg),                                   # historique seul, comme les autres stratégies
        "synthesis_monthly_usd": _usd(synthesis_daily * DAYS_PER_MONTH),
        "total_monthly_usd": _report(avg, extra_daily_cost=synthesis_daily)["monthly_cost_usd"],
    }


def external_sqlite_memory() -> dict:
    """Seuls quelques faits ciblés sont injectés (lookup SQLite, pas d'appel LLM)."""
    return {"tokens_per_request": EXTERNAL_MEMORY_TOKENS, **_report(EXTERNAL_MEMORY_TOKENS)}


if __name__ == "__main__":
    scenarios = {
        "naive_full_history": naive_full_history(),
        f"summarize_every_{SUMMARY_EVERY}_turns": summarize_every_n_turns(),
        "external_sqlite_memory": external_sqlite_memory(),
    }
    for name, stats in scenarios.items():
        print(f"\n--- {name} ---")
        for key, value in stats.items():
            print(f"  {key}: {value}")
