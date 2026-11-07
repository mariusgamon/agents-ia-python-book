# conditional_pipeline.py — pas d'appels LLM ici, simulation locale du pattern
from typing import TypedDict
from langgraph.graph import StateGraph, END

class ValidationState(TypedDict):
    code: str
    errors: list[str]
    corrected_code: str
    report: str

def analyze_code(state: ValidationState) -> dict:
    """Analyse le code et détecte les erreurs."""
    code = state["code"]
    # Analyse statique — simplifié pour la démo
    errors = []
    if "except:" in code:
        errors.append("Overly generic exception (bare except)")
    if "eval(" in code:
        errors.append("Use of eval() — security risk")
    if len([line for line in code.split("\n") if line.strip()]) > 50:
        errors.append("Function too long (> 50 lines)")
    return {"errors": errors}

def fix_code(state: ValidationState) -> dict:
    """Corrige automatiquement les erreurs simples."""
    code = state["code"]
    corrected_code = code.replace("except:", "except Exception as e:")
    return {"corrected_code": corrected_code}

def generate_report(state: ValidationState) -> dict:
    """Génère un rapport quand aucune correction n'est nécessaire."""
    return {"report": "Code validated. No errors detected."}

def generate_report_with_fixes(state: ValidationState) -> dict:
    """Génère un rapport avec les corrections appliquées."""
    errors = "\n".join([f"- {e}" for e in state["errors"]])
    return {"report": f"Corrections applied:\n{errors}"}

def router(state: ValidationState) -> str:
    """Décide du chemin selon les erreurs détectées."""
    if state["errors"]:
        return "fix"
    return "clean_report"

graph = StateGraph(ValidationState)
graph.add_node("analyze", analyze_code)
graph.add_node("fix", fix_code)
graph.add_node("clean_report", generate_report)
graph.add_node("fix_report", generate_report_with_fixes)

graph.set_entry_point("analyze")
graph.add_conditional_edges(
    "analyze",
    router,
    {
        "fix": "fix",
        "clean_report": "clean_report",
    }
)
graph.add_edge("fix", "fix_report")
graph.add_edge("clean_report", END)
graph.add_edge("fix_report", END)

workflow = graph.compile()

# --- Lancer le pipeline sur deux exemples pour voir les deux branches ---
if __name__ == "__main__":
    bad_code = """
def parse_user_input(raw):
    try:
        return eval(raw)
    except:
        return None
"""
    print("--- Bad code ---")
    result = workflow.invoke({"code": bad_code, "errors": [], "corrected_code": "", "report": ""})
    print(result["report"])
    print("\nCorrected:\n" + result["corrected_code"])

    good_code = """
def add(a: int, b: int) -> int:
    return a + b
"""
    print("\n--- Good code ---")
    result = workflow.invoke({"code": good_code, "errors": [], "corrected_code": "", "report": ""})
    print(result["report"])
