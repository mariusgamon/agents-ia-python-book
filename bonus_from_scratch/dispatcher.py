from tools import get_weather, calculate, search_web_snippets

# ─── Registre des tools ───────────────────────────────────────────────────────
# Clé  : le nom exact que le LLM doit mentionner dans son JSON
# Valeur: la fonction Python correspondante
TOOLS: dict[str, callable] = {
    "get_weather":         get_weather,
    "calculate":           calculate,
    "search_web_snippets": search_web_snippets,
}


def dispatch_tool(tool_name: str, args: dict) -> str:
    """
    Exécute un tool par son nom.

    Retourne toujours une chaîne — même en cas d'erreur.
    Cela permet à la boucle de continuer et au LLM de s'adapter.
    """
    if tool_name not in TOOLS:
        known = ", ".join(TOOLS.keys())
        return f"[ERREUR] Tool inconnu : '{tool_name}'. Disponibles : {known}"

    try:
        result = TOOLS[tool_name](**args)
        return str(result)

    except TypeError as e:
        return f"[ERREUR] Arguments invalides pour '{tool_name}' : {e}"

    except Exception as e:
        return f"[ERREUR] '{tool_name}' a échoué : {type(e).__name__}: {e}"
