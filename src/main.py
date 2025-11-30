# src/main.py
import uvicorn
from fastapi import FastAPI
from src.core.config import settings
from src.core.logger import setup_logger

# Import the router (where the actual logic lives)
from src.api.websocket import router as ws_router

# 1. Setup Logging
setup_logger()

# 2. Create App
app = FastAPI(title=settings.APP_NAME)

# 3. Include Routes
# This registers the route defined in websocket.py
# The route in websocket.py is "/chat", so combined with prefix "/ws", it becomes "/ws/chat"
app.include_router(ws_router, prefix="/ws")

# 4. Health Check
@app.get("/")
async def root():
    return {"status": "Chronos Voice is Online", "version": "Phase 1.5"}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)