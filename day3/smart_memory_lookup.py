# smart_memory_lookup.py — fetch only relevant memories, not the full profile
import aiosqlite
from pathlib import Path

DB_PATH = Path("agent_memory.db")

async def get_relevant_memories(
    user_id: str,
    categories: list[str],
    limit: int = 5,
) -> list[dict]:
    """
    Pull only memories matching requested categories.
    3-5 targeted facts instead of 50 dumped into the prompt.
    """
    if not categories:
        return []

    placeholders = ",".join("?" for _ in categories)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            f"""
            SELECT key, value FROM user_memory
            WHERE user_id = ?
            AND key IN ({placeholders})
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            [user_id, *categories, limit],
        )
        rows = await cursor.fetchall()
    return [{"key": r[0], "value": r[1]} for r in rows]

async def build_memory_context(user_id: str, query_categories: list[str]) -> str:
    """
    Build a compact context string from relevant memories only.
    Result: ~150 tokens instead of ~2500.
    """
    memories = await get_relevant_memories(user_id, query_categories)
    if not memories:
        return ""

    lines = [f"- {m['key']}: {m['value']}" for m in memories]
    return "User profile:\n" + "\n".join(lines)
