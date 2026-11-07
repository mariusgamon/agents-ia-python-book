# app/middleware/memory_guard.py — sliding window + periodic flush
import os
import psutil
import logging
from collections import deque

logger = logging.getLogger("memory_guard")

# Maximum conversation entries kept in memory per session
MAX_HISTORY_ENTRIES = 50
# Hard memory ceiling — trigger emergency flush above this
MEMORY_CEILING_MB = 400

class ConversationBuffer:
    """Bounded conversation history that auto-evicts oldest entries.
    Uses deque with maxlen — O(1) append, automatic eviction, no manual cleanup."""
    
    def __init__(self, max_entries: int = MAX_HISTORY_ENTRIES):
        self._buffer = deque(maxlen=max_entries)
        self._total_processed = 0
    
    def add(self, role: str, content: str, tool_results: list = None):
        # Truncate tool results — raw HTML/JSON can be 50KB+ per call
        truncated_tools = None
        if tool_results:
            truncated_tools = [
                {"tool": t.get("tool", "unknown"), "result": str(t.get("result", ""))[:500]}
                for t in tool_results
            ]
        
        self._buffer.append({
            "role": role,
            "content": content[:2000],  # cap individual message size
            "tool_results": truncated_tools
        })
        self._total_processed += 1
    
    def get_history(self) -> list:
        return list(self._buffer)
    
    @property
    def stats(self) -> dict:
        return {"buffered": len(self._buffer), "total_processed": self._total_processed}

def check_memory_pressure() -> dict:
    """Returns current memory state. Call this in your /health/detailed endpoint."""
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / 1024 / 1024
    status = "ok" if mem_mb < MEMORY_CEILING_MB else "critical"
    
    if status == "critical":
        logger.error(f"Memory pressure critical: {mem_mb:.0f}MB (ceiling: {MEMORY_CEILING_MB}MB)")
    
    return {"rss_mb": round(mem_mb, 1), "ceiling_mb": MEMORY_CEILING_MB, "status": status}
