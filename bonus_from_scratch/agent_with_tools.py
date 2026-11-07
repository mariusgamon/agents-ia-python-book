import json
from mistral_raw import llm, SYSTEM_PROMPT, extract_json
from dispatcher import dispatch_tool


def agent_with_tools(user_input: str, max_turns: int = 10) -> str:
    """
    Agent complet avec tool calling from scratch.

    Flux à chaque tour :
    1. Le LLM répond
    2. Si JSON   → dispatcher → résultat injecté → tour suivant
    3. Si texte  → réponse finale → on retourne
    4. Si max_turns atteint → RuntimeError
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_input},
    ]

    for turn in range(1, max_turns + 1):
        print(f"\n── Tour {turn} ──────────────────────────")

        # Appel LLM
        response = llm(messages)
        messages.append({"role": "assistant", "content": response})

        print(f"LLM : {response[:120]}{'...' if len(response) > 120 else ''}")

        # ─── Tenter de parser comme un appel de tool ────────────────────────
        stripped = extract_json(response)   # tolère ```json ... ```
        if stripped.startswith("{") and stripped.endswith("}"):
            try:
                data = json.loads(stripped)

                tool_name = data.get("tool", "")
                args      = data.get("args", {})

                if not tool_name:
                    # JSON valide mais pas un appel de tool → réponse finale
                    return response

                # Exécuter le tool
                print(f"→ Tool : {tool_name}({args})")
                tool_result = dispatch_tool(tool_name, args)
                print(f"← Résultat : {tool_result[:80]}{'...' if len(tool_result) > 80 else ''}")

                # Injecter le résultat dans le contexte
                messages.append({
                    "role":    "user",
                    "content": (
                        f"Résultat de '{tool_name}' :\n{tool_result}\n\n"
                        "Continue avec ces données."
                    ),
                })
                continue  # prochain tour

            except json.JSONDecodeError:
                # Commence par { mais n'est pas du JSON valide
                # Le LLM a peut-être fait une erreur de format → réponse finale
                print("⚠ JSON invalide — traité comme réponse finale")
                return response

        # ─── Pas de JSON → réponse finale ───────────────────────────────────
        return response

    raise RuntimeError(
        f"Agent bloqué après {max_turns} tours. "
        f"Vérifiez le system prompt ou augmentez max_turns."
    )


# ─── Test ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    questions = [
        "Quel temps fait-il à Nantes en ce moment ?",
        "Combien font 847.50 * 1.20 (avec TVA à 20%) ?",
        "Quel temps fait-il à Tokyo, et combien font 15 * 7 ?",
    ]

    for q in questions:
        print(f"\n{'='*60}")
        print(f"Question : {q}")
        print(f"{'='*60}")
        result = agent_with_tools(q)
        print(f"\nRéponse finale : {result}")
