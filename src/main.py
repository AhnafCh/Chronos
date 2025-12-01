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

# Import the routers
from src.api.websocket import router as ws_router

logger = logging.getLogger(__name__)

# 1. Setup Logging First
setup_logger()

# 2. Lifespan Context Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"🚀 {settings.APP_NAME} starting up...")
    
    # Warmup Vector DB
    if settings.PINECONE_API_KEY:
        try:
            logger.info("🔥 Warming up Vector DB (removing cold start)...")
            await retriever.ainvoke("wake up")
            logger.info("✅ Vector DB is Ready and Hot!")
        except Exception as e:
            logger.error(f"❌ Warmup failed: {e}")

    yield
    # Shutdown
    logger.info(f"🛑 {settings.APP_NAME} shutting down...")

# 3. Create App
app = FastAPI(
    title=settings.APP_NAME,
    version="1.6.0",
    description="Voice RAG Orchestrator",
    lifespan=lifespan
)

# 4. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        content={"error": "Internal server error", "message": str(exc)}
    )

# 6. Include Routes
# WebSocket (Voice + Text)
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])

# 7. Health Check
@app.get("/", tags=["Health"])
async def root():
    return {"status": "online", "service": settings.APP_NAME}

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8026, 
        reload=True,
        log_level="info"
    )