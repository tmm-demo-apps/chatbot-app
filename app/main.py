"""FastAPI application for the AI Chatbot service."""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from .chat_service import ChatService
from .llm.client import get_llm_client
from .integrations.bookstore import BookstoreClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
chat_requests = Counter('chatbot_requests_total', 'Total chat requests', ['status'])
response_time = Histogram('chatbot_response_seconds', 'Response time in seconds')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Chatbot service...")
    llm_client = get_llm_client()
    bookstore_client = BookstoreClient()
    app.state.chat_service = ChatService(llm_client, bookstore_client)
    
    # Check LLM health
    if await llm_client.health_check():
        logger.info(f"LLM backend healthy: {os.getenv('LLM_BACKEND', 'ollama')}")
    else:
        logger.warning("LLM backend not available, will use canned responses")
    
    # Check Bookstore API health
    if await bookstore_client.health_check():
        logger.info(f"Bookstore API healthy: {bookstore_client.base_url}")
    else:
        logger.warning(f"Bookstore API not available at {bookstore_client.base_url}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Chatbot service...")


app = FastAPI(
    title="Bookstore Chatbot",
    description="AI-powered customer support chatbot",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    session_id: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message and return a response."""
    with response_time.time():
        try:
            response = await app.state.chat_service.get_response(
                message=request.message,
                session_id=request.session_id
            )
            chat_requests.labels(status="success").inc()
            return ChatResponse(
                response=response,
                session_id=request.session_id or "anonymous"
            )
        except Exception as e:
            chat_requests.labels(status="error").inc()
            logger.error(f"Chat error: {e}")
            raise HTTPException(status_code=500, detail="Failed to process message")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/ready")
async def ready():
    """Readiness check endpoint."""
    llm_client = get_llm_client()
    llm_healthy = await llm_client.health_check()
    
    return {
        "status": "ready" if llm_healthy else "degraded",
        "llm_backend": os.getenv("LLM_BACKEND", "ollama"),
        "llm_available": llm_healthy
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
