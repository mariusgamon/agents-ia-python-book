# app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AgentRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000, description="Message for the agent")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    # NOTE: this is the conversation HISTORY (what the LLM sees), not the SDK 'context'
    # parameter (which is local Python state for tools/hooks, NOT sent to the LLM).
    history: Optional[list[dict]] = Field(None, description="Prior conversation turns to prepend")

class AgentResponse(BaseModel):
    response: str
    tokens_used: Optional[int] = None
    duration_ms: int
    timestamp: datetime = Field(default_factory=datetime.now)

class APIError(BaseModel):
    code: str
    message: str
    details: Optional[str] = None
