import json
from mistral_raw import llm, extract_json
from dispatcher import dispatch_tool


# ─── Agents spécialisés ────────────────────────────────────────────────────────

def research_agent(query: str) -> str:
    """
    Agent spécialisé : recherche factuelle.
    Context court, instructions précises = meilleure précision.
    """
    messages = [
        {
            "role":    "system",
            "content": (
                "Tu es un expert en recherche factuelle. "
                "Réponds uniquement avec des faits vérifiables. "
                "Sois concis (3-5 lignes max). "
                "Si tu n'es pas certain, dis-le explicitement."
            ),
        },
        {"role": "user", "content": query},
    ]
    return llm(messages)


def writer_agent(brief: str) -> str:
    """
    Agent spécialisé : rédaction et reformulation.
    Transforme des données brutes en texte lisible.
    """
    messages = [
        {
            "role":    "system",
            "content": (
                "Tu es expert en rédaction claire et concise. "
                "Transforme le brief fourni en texte structuré et professionnel. "
                "Utilise des paragraphes courts. Pas de jargon inutile."
            ),
        },
        {"role": "user", "content": brief},
    ]
    return llm(messages)


def analyst_agent(data: str) -> str:
    """
    Agent spécialisé : analyse et recommandations.
    """
    messages = [
        {
            "role":    "system",
            "content": (
                "Tu es analyste senior. À partir des données fournies, "
                "identifie 2-3 insights clés et formule une recommandation actionnable. "
                "Format : Insights (liste) + Recommandation (1 phrase)."
            ),
        },
        {"role": "user", "content": data},
    ]
    return llm(messages)


# ─── Registre des agents ───────────────────────────────────────────────────────
AGENTS: dict[str, callable] = {
    "research":  research_agent,
    "writer":    writer_agent,
    "analyst":   analyst_agent,
}


# ─── System prompt de l'orchestrateur ─────────────────────────────────────────
ORCHESTRATOR_SYSTEM = f"""Tu es un orchestrateur. Tu coordonnes des agents spécialisés
et des tools pour accomplir des tâches complexes.

Pour déléguer à un agent, réponds UNIQUEMENT avec ce JSON :
{{"delegate": "nom_agent", "input": "ce que l'agent doit accomplir"}}

Pour appeler un tool, réponds UNIQUEMENT avec ce JSON :
{{"tool": "nom_tool", "args": {{...}}}}

Agents disponibles : {', '.join(AGENTS.keys())}
Tools disponibles  : get_weather(city: str), calculate(expression: str),
                     search_web_snippets(query: str, n: int)

Quand la tâche est entièrement accomplie, écris ta réponse finale normalement (sans JSON).

Stratégie recommandée pour une tâche complexe :
1. research  → collecter les faits
2. analyst   → extraire les insights
3. writer    → rédiger la synthèse finale
"""


# ─── Orchestrateur principal ───────────────────────────────────────────────────

def orchestrator(user_request: str, max_turns: int = 12) -> str:
    """
    Orchestrateur multi-agents from scratch.

    Gère deux types de délégation :
    - {"delegate": "agent_name", "input": "..."} → sous-agent
    - {"tool": "tool_name", "args": {...}}        → tool Python
    """
    messages = [
        {"role": "system", "content": ORCHESTRATOR_SYSTEM},
        {"role": "user",   "content": user_request},
    ]
    delegation_log = []  # trace des délégations pour debug

    for turn in range(1, max_turns + 1):
        print(f"\n── Tour {turn}/{max_turns} ──────────────────────────────")

        response = llm(messages)
        messages.append({"role": "assistant", "content": response})

        stripped = extract_json(response)   # tolère ```json ... ```

        # ── Tentative de parsing JSON ────────────────────────────────────────
        if stripped.startswith("{") and stripped.endswith("}"):
            try:
                data = json.loads(stripped)

                # Cas 1 : délégation à un agent
                if "delegate" in data:
                    agent_name  = data["delegate"]
                    agent_input = data.get("input", user_request)

                    if agent_name not in AGENTS:
                        result = f"[ERREUR] Agent inconnu : '{agent_name}'"
                    else:
                        print(f"→ Délègue à : {agent_name}")
                        result = AGENTS[agent_name](agent_input)
                        delegation_log.append({"agent": agent_name, "turns": turn})

                    print(f"← Résultat ({agent_name}) : {result[:80]}...")
                    messages.append({
                        "role":    "user",
                        "content": f"Résultat de l'agent '{agent_name}' :\n{result}\n\nContinue.",
                    })
                    continue

                # Cas 2 : appel de tool
                if "tool" in data:
                    tool_name = data["tool"]
                    args      = data.get("args", {})
                    print(f"→ Tool : {tool_name}({args})")
                    result = dispatch_tool(tool_name, args)
                    print(f"← Résultat : {result[:80]}")
                    messages.append({
                        "role":    "user",
                        "content": f"Résultat du tool '{tool_name}' :\n{result}\n\nContinue.",
                    })
                    continue

            except json.JSONDecodeError:
                pass  # JSON malformé → traiter comme réponse finale

        # ── Réponse finale ────────────────────────────────────────────────────
        print(f"\nDélégations effectuées : {delegation_log}")
        return response

    raise RuntimeError(f"Orchestrateur bloqué après {max_turns} tours.")


# ─── Test ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = orchestrator(
        "Fais une synthèse professionnelle de l'actualité "
        "autour de l'IA en France cette semaine."
    )
    print(f"\n{'='*60}\nSynthèse finale :\n{result}")
