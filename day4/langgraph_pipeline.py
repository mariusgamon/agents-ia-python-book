# langgraph_pipeline.py
import config

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated
import operator

# Définir l'état partagé
class AgentState(TypedDict):
    topic: str
    research: str
    analysis: str
    final_report: str

llm = ChatOpenAI(model="gpt-5.4-mini")

# Nœud 1 : Recherche
def research_node(state: AgentState) -> dict:
    topic = state["topic"]
    prompt = f"Research factual information about: {topic}. Be precise and concise."
    response = llm.invoke(prompt)
    return {"research": response.content}

# Nœud 2 : Analyse
def analysis_node(state: AgentState) -> dict:
    research = state["research"]
    prompt = f"""Analyze this information and identify:
    1. Key points (3 max)
    2. What is useful for a developer
    3. What is missing
    
    Information: {research}"""
    response = llm.invoke(prompt)
    return {"analysis": response.content}

# Nœud 3 : Rédaction
def writing_node(state: AgentState) -> dict:
    analysis = state["analysis"]
    research = state["research"]
    prompt = f"""Write a concise technical report based on:
    Analysis: {analysis}
    Raw data: {research}
    
    Format: title -> 3 key points -> actionable conclusion
    Audience: Python developers"""
    response = llm.invoke(prompt)
    return {"final_report": response.content}

# Construire le graphe
graph = StateGraph(AgentState)

graph.add_node("research", research_node)
graph.add_node("analysis", analysis_node)
graph.add_node("writing", writing_node)

# Définir le flux
graph.set_entry_point("research")
graph.add_edge("research", "analysis")
graph.add_edge("analysis", "writing")
graph.add_edge("writing", END)

workflow = graph.compile()

# Exécution
result = workflow.invoke({"topic": "OpenAI Agents SDK vs LangGraph in 2026"})
print(result["final_report"])
