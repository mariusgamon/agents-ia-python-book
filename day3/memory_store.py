# memory_store.py — async version, solid starting point for a real app
# pip install aiosqlite
import aiosqlite
from datetime import datetime
from pathlib import Path

DB_PATH = Path("agent_memory.db")

async def init_db():
    """Initialise la base de données mémoire (tables + index)."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(user_id, key)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        # Indexes — créés dès le départ, pas en conseil de fin de chapitre
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_memory_user_key "
            "ON user_memory(user_id, key)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_history_user_time "
            "ON conversation_history(user_id, created_at DESC)"
        )
        await db.commit()

async def save_memory(user_id: str, key: str, value: str):
    """Sauvegarde ou met à jour une information en mémoire."""
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO user_memory (user_id, key, value, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
        """, (user_id, key, value, now, now))
        await db.commit()

async def get_memory(user_id: str, key: str) -> str | None:
    """Récupère une information stockée."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT value FROM user_memory WHERE user_id = ? AND key = ?",
            (user_id, key),
        )
        row = await cursor.fetchone()
        return row[0] if row else None

async def get_all_memories(user_id: str) -> dict:
    """Récupère toutes les informations stockées pour un utilisateur."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT key, value FROM user_memory WHERE user_id = ?",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return {row[0]: row[1] for row in rows}

async def add_to_history(user_id: str, role: str, content: str):
    """Ajoute un message à l'historique."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO conversation_history (user_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, role, content, datetime.now().isoformat()))
        await db.commit()

async def get_recent_history(user_id: str, limit: int = 10) -> list[dict]:
    """Récupère les N messages les plus récents."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT role, content FROM conversation_history
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, limit))
        rows = await cursor.fetchall()
        return [{"role": row[0], "content": row[1]} for row in reversed(rows)]
