# multi_provider_langgraph.py — même graphe, deux providers
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from typing import TypedDict
import os
from dotenv import load_dotenv

load_dotenv()  # lit OPENAI_API_KEY / ANTHROPIC_API_KEY dans .env

# Choose provider at startup via env variable
PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # "openai" or "anthropic"

if PROVIDER == "openai":
    llm = ChatOpenAI(model="gpt-5.4", temperature=0)
else:
    llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)

class State(TypedDict):
    question: str
    answer: str

def answer_node(state: State) -> dict:
    response = llm.invoke(state["question"])
    return {"answer": response.content}

graph = StateGraph(State)
graph.add_node("answer", answer_node)
graph.set_entry_point("answer")
graph.add_edge("answer", END)

workflow = graph.compile()

# Le reste du code est identique quel que soit le provider
result = workflow.invoke({"question": "Liste vs tuple in Python ?"})
print(result["answer"])
