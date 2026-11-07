# agent_loop.py
from mistral_raw import llm


def agent_loop(user_input: str, max_turns: int = 8) -> str:
    """
    Boucle agent minimale avec protection max_turns.

    Cette version simple n'utilise pas encore d'outils : chaque tour
    appelle le LLM avec l'historique courant, et on s'arrête dès que le
    LLM répond "FIN:" suivi de la réponse finale (signal explicite).

    Logique de sortie :
    - Le LLM préfixe sa réponse par "FIN:" → on retourne ce qui suit
    - Sinon, on relance jusqu'à max_turns
    - max_turns atteint → on lève une exception explicite

    En B.4, on remplacera le sentinel "FIN:" par un parsing JSON pour
    distinguer "appel de tool" et "réponse finale" — beaucoup plus robuste.
    """
    messages = [
        {
            "role":    "system",
            "content": (
                "Tu es un assistant. Quand tu as la réponse finale, préfixe-la "
                "par exactement \"FIN:\" suivi de ta réponse, sans rien d'autre. "
                "Si tu as besoin de plus d'informations, pose une seule question "
                "(sans le préfixe \"FIN:\")."
            ),
        },
        {"role": "user", "content": user_input},
    ]

    for turn in range(1, max_turns + 1):
        print(f"[Tour {turn}/{max_turns}]")

        response = llm(messages)
        messages.append({"role": "assistant", "content": response})

        # Vraie condition de sortie : le LLM signale-t-il la fin ?
        if response.strip().startswith("FIN:"):
            return response.strip()[4:].strip()

        # Sinon, on continue : le LLM a posé une question — on lui demande
        # de continuer (dans un vrai usage, on injecterait ici la réponse user
        # ou un résultat de tool — voir B.4).
        messages.append({
            "role": "user",
            "content": "Continue. Si tu as la réponse, préfixe-la par \"FIN:\".",
        })

    # Si on arrive ici, on a épuisé les tours
    raise RuntimeError(
        f"Agent bloqué après {max_turns} tours. "
        f"Dernier message : {messages[-1]['content'][:200]}"
    )


def agent_loop_naive(user_input: str) -> str:
    """
    Boucle vraiment infinie — la condition de sortie dépend d'un signal
    fragile que le LLM peut oublier d'envoyer.
    """
    messages = [{"role": "user", "content": user_input}]

    while True:                     # boucle non bornée — aucun garde-fou
        response = llm(messages)
        messages.append({"role": "assistant", "content": response})

        # Condition de sortie fragile : on dépend d'un mot-clef généré par le LLM.
        # Si le modèle ne dit jamais "DONE", on tourne indéfiniment.
        if "DONE" in response:
            return response

        messages.append({
            "role":    "user",
            "content": "Continue jusqu'à avoir terminé.",
        })
