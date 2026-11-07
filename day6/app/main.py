# app/main.py
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
import os
import logging
from dotenv import load_dotenv

from app.models.schemas import AgentRequest, AgentResponse, APIError
from app.agents.assistant import run_agent

load_dotenv()
logger = logging.getLogger("api")

API_SECRET_KEY = os.getenv("API_SECRET_KEY")
if not API_SECRET_KEY:
    raise RuntimeError(
        "API_SECRET_KEY is required. Set it in your .env file or environment "
        "before starting the API. Never ship a default insecure value to prod."
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage : pré-chauffer l'agent
    print("Starting API...")
    from app.agents.assistant import get_agent
    get_agent()  # Initialiser le singleton
    print("Agent ready.")
    yield
    # Arrêt : nettoyage si nécessaire
    print("Shutting down API.")

app = FastAPI(
    title="AI Agent API",
    description="REST interface for your Python AI agent",
    version="1.0.0",
    lifespan=lifespan
)

# CORS pour une app frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],  # Restreindre en production
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Authentification simple par header
async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.get("/health")
async def health_check():
    """Endpoint de santé pour les load balancers et le monitoring."""
    return {"status": "ok", "version": "1.0.0"}

@app.post(
    "/api/chat",
    response_model=AgentResponse,
    responses={
        401: {"model": APIError},
        422: {"model": APIError},
        503: {"model": APIError},
    }
)
async def chat_with_agent(
    request: AgentRequest,
    _: str = Depends(verify_api_key)
):
    """Envoie un message à l'agent et retourne sa réponse."""
    
    start = time.time()
    
    try:
        response, tokens = await run_agent(
            message=request.message,
            history=request.history,
        )
        
        duration_ms = int((time.time() - start) * 1000)
        
        return AgentResponse(
            response=response,
            tokens_used=tokens,
            duration_ms=duration_ms
        )
    
    except TimeoutError:
        # The agent timed out — log the detail server-side, return a generic message
        logger.warning("Agent timeout", extra={"user_id": request.user_id})
        raise HTTPException(status_code=503, detail="Agent timed out — please retry")
    except Exception:
        # Never expose str(e) to clients in production: it can leak
        # internal URLs, partial keys, server paths, or stack hints.
        logger.exception("Unexpected agent error")
        raise HTTPException(
            status_code=503,
            detail="Agent temporarily unavailable",
        )

@app.get("/")
async def root():
    return {"message": "AI Agent API — see /docs for documentation"}
