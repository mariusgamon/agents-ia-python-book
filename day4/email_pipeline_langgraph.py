# email_pipeline_langgraph.py — Version LangGraph (overkill ici)
import config

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from typing import TypedDict

class EmailState(TypedDict):
    email_body: str
    intent: str
    draft: str

llm = ChatOpenAI(model="gpt-5.4-mini")

def classify_node(state: EmailState) -> dict:
    """Nœud qui classifie l'intent de l'email."""
    response = llm.invoke(
        f"Classify this support email intent. "
        f"Return exactly one of: billing, technical, feature_request, other.\n\n"
        f"{state['email_body']}"
    )
    return {"intent": response.content.strip()}

def draft_node(state: EmailState) -> dict:
    """Nœud qui rédige une réponse basée sur l'intent classifié."""
    response = llm.invoke(
        f"Draft a professional response to this {state['intent']} support email. "
        f"Be concise and helpful.\n\n{state['email_body']}"
    )
    return {"draft": response.content}

# Construire le graphe
graph = StateGraph(EmailState)
graph.add_node("classify", classify_node)
graph.add_node("draft", draft_node)
graph.set_entry_point("classify")
graph.add_edge("classify", "draft")
graph.add_edge("draft", END)

# Compilation (cette étape seule ajoute de la latence et une dépendance inutile)
email_workflow = graph.compile()

# Usage: result = email_workflow.invoke({"email_body": "..."})
