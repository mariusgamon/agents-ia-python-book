# semantic_memory.py
import sqlite3
import numpy as np
from openai import OpenAI

import config  # charge OPENAI_API_KEY

DB_PATH = "memory.db"
client = OpenAI()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            embedding BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def embed(text: str) -> np.ndarray:
    """Renvoie un vecteur 1536-dim pour text-embedding-3-small."""
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return np.array(resp.data[0].embedding, dtype=np.float32)

def add_fact(text: str) -> int:
    vec = embed(text)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "INSERT INTO facts (text, embedding) VALUES (?, ?)",
        (text, vec.tobytes()),
    )
    conn.commit()
    fact_id = cur.lastrowid
    conn.close()
    return fact_id

def search_facts(query: str, top_k: int = 3) -> list[tuple[str, float]]:
    """Renvoie les top_k faits les plus proches de query (cosine similarity)."""
    q_vec = embed(query)

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT text, embedding FROM facts").fetchall()
    conn.close()

    if not rows:
        return []

    texts = [r[0] for r in rows]
    embeddings = np.vstack([np.frombuffer(r[1], dtype=np.float32) for r in rows])

    # text-embedding-3-small renvoie des vecteurs normalisés → le produit
    # scalaire suffit. On garde la division par les normes pour que ça
    # marche aussi avec d'autres modèles non normalisés.
    norms = np.linalg.norm(embeddings, axis=1) * np.linalg.norm(q_vec) + 1e-10
    scores = (embeddings @ q_vec) / norms

    top_indices = np.argsort(-scores)[:top_k]
    return [(texts[i], float(scores[i])) for i in top_indices]


from agents import Agent, Runner, function_tool
import asyncio

@function_tool
def recall_fact(query: str) -> str:
    """Search relevant facts from memory using semantic similarity."""
    results = search_facts(query, top_k=3)
    if not results:
        return "No relevant facts found."
    return "\n".join(f"- {text} (score: {score:.2f})" for text, score in results)

agent = Agent(
    name="MemoryAgent",
    model="gpt-5.4-mini",
    instructions=(
        "Use recall_fact to look up relevant context before answering. "
        "If the search returns nothing relevant, say so explicitly."
    ),
    tools=[recall_fact],
)

# --- Demo ---
init_db()
add_fact("Le client Acme préfère les rapports en PDF")
add_fact("Le projet Bravo utilise Python 3.12 et FastAPI")
add_fact("L'équipe se réunit chaque mardi matin à 10h")

result = asyncio.run(Runner.run(agent, "Quel format pour Acme ?"))
print(result.final_output)
# → "Les rapports pour Acme doivent être en PDF (préférence client)."
