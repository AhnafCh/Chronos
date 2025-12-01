# src/main.py
import logging
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.core.logger import setup_logger

# For dummy import to initialize the retriever at startup
from src.brain.retriever import retriever

# Import the router (where the actual logic lives)
from src.api.websocket import router as ws_router

logger = logging.getLogger(__name__)

# 1. Setup Logging First
setup_logger()

# 2. Lifespan Context Manager (Startup/Shutdown hooks)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"🚀 {settings.APP_NAME} starting up...")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info(f"OpenAI API: {'✓ Configured' if settings.OPENAI_API_KEY else '✗ Missing'}")
    logger.info(f"Deepgram API: {'✓ Configured' if settings.DEEPGRAM_API_KEY else '✗ Missing'}")
    logger.info(f"Pinecone API: {'✓ Configured' if settings.PINECONE_API_KEY else '✗ Missing'}")

    # Warmup Vector DB if configured
    if settings.PINECONE_API_KEY:
        try:
            logger.info("🔥 Warming up Vector DB (removing cold start)...")
            # We run a fake search. This forces the connection to open.
            await retriever.ainvoke("wake up")
            logger.info("✅ Vector DB is Ready and Hot!")
        except Exception as e:
            logger.error(f"❌ Warmup failed: {e}")


    yield
    # Shutdown
    logger.info(f"🛑 {settings.APP_NAME} shutting down...")

# 3. Create App with Lifespan
app = FastAPI(
    title=settings.APP_NAME,
    version="1.5.0",
    description="Voice RAG Orchestrator with Real-time ASR, LLM, and TTS",
    lifespan=lifespan
)

# 4. Add CORS Middleware (for web clients)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )

# 6. Include Routes
# This registers the route defined in websocket.py
# The route in websocket.py is "/chat", so combined with prefix "/ws", it becomes "/ws/chat"
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])

# 7. Health Check Endpoints
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - System status"""
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "version": "1.5.0",
        "phase": "Phase 1.5 - Full Voice RAG Pipeline"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    health_status = {
        "status": "healthy",
        "services": {
            "openai": bool(settings.OPENAI_API_KEY),
            "deepgram": bool(settings.DEEPGRAM_API_KEY),
            "pinecone": bool(settings.PINECONE_API_KEY),
        },
        "config": {
            "input_sample_rate": settings.INPUT_SAMPLE_RATE,
            "output_sample_rate": settings.OUTPUT_SAMPLE_RATE,
            "debug_mode": settings.DEBUG
        }
    }
    return health_status

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8026,
        reload=True,
        log_level="info"
    )