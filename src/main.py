# src/main.py
import os
import warnings

# Suppress TensorFlow warnings before any TF imports
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress all TF logs except errors
os.environ['TF_ENABLE_DEPRECATION_WARNINGS'] = '0'

# Suppress Python warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', module='tensorflow')
warnings.filterwarnings('ignore', module='tf_keras')

import logging
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.core.logger import setup_logger
from src.core import control

# For dummy import to initialize the retriever at startup
from src.brain.retriever import retriever

# Database initialization
from src.db.database import init_db

# Import the routers
from src.api.websocket import router as ws_router
from src.api.upload import router as upload_router
from src.api.auth import router as auth_router

logger = logging.getLogger(__name__)

# 1. Setup Logging First
setup_logger()

# 2. Lifespan Context Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"🚀 {settings.APP_NAME} starting up...")
    
    # Initialize Database
    try:
        logger.info("🗄️ Initializing database tables...")
        await init_db()
        logger.info("✅ Database is ready!")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
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
# Authentication
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
# WebSocket (Voice + Text)
app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])
# File Upload & Ingestion
app.include_router(upload_router, prefix="/api", tags=["Upload"])

# 7. Health Check
@app.get("/", tags=["Health"])
async def root():
    return {"status": "online", "service": settings.APP_NAME}

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=control.SERVER_HOST,
        port=control.SERVER_PORT, 
        reload=True,
        reload_excludes=["**/__pycache__/**", "**/*.pyc", "**/tests/**", "**/*.md"],
        log_level="info"
    )