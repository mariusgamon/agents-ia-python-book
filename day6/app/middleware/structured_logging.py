# app/middleware/structured_logging.py — JSON logs with agent-specific fields
import json
import time
import uuid
import logging
import sys
from fastapi import Request

class JSONFormatter(logging.Formatter):
    """Outputs one JSON object per line — parseable by CloudWatch, Datadog, Loki, etc."""
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Merge extra fields passed via logger.info("msg", extra={...})
        for key in ("run_id", "tool_name", "tool_duration_ms", "token_count",
                     "input_tokens", "output_tokens", "user_id", "status_code",
                     "response_empty", "agent_turns"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)
        return json.dumps(log_entry)

def setup_structured_logging():
    """Call once at startup. Replaces default handlers with JSON output to stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    
    # Silence noisy uvicorn access logs — we log requests ourselves
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

async def agent_request_logger(request: Request, call_next):
    """Middleware that logs every request with agent-relevant metrics."""
    run_id = str(uuid.uuid4())[:8]
    request.state.run_id = run_id
    logger = logging.getLogger("agent.request")
    
    start = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)
    
    # Flag suspicious responses — 200 with empty body is the silent killer
    response_empty = (
        response.status_code == 200
        and hasattr(response, "body")
        and len(getattr(response, "body", b"")) < 20
    )
    
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)",
        extra={
            "run_id": run_id,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "user_id": request.headers.get("x-user-id", "anonymous"),
            "response_empty": response_empty,
        }
    )
    
    if response_empty:
        logger.warning(
            f"Empty 200 response on {request.url.path}",
            extra={"run_id": run_id, "response_empty": True}
        )
    
    return response
