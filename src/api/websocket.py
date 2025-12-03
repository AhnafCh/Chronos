# src/api/websocket.py
import logging
from uuid import UUID
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, Depends
from src.transport.connection_mgr import ConnectionManager
from src.core.security import decode_token
from src.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

# Services are imported HERE, not in main.py
from src.services.asr import DeepgramASR
from src.services.llm import OpenAILLM
from src.services.tts import OpenAITTS

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/chat")  # This becomes /ws/chat because of the prefix in main.py
async def websocket_endpoint(
    websocket: WebSocket, 
    session_id: str = Query(..., description="Client generated ID"),
    token: str | None = Query(None, description="Optional JWT token for authentication"),
    db: AsyncSession = Depends(get_db)
):
    # Optional Authentication
    user_id: UUID | None = None
    if token:
        payload = decode_token(token)
        if payload:
            try:
                user_id = UUID(payload.get("sub"))
                logger.info(f"Authenticated user {user_id} connected to session {session_id}")
            except (ValueError, TypeError):
                logger.warning(f"Invalid token for session {session_id}")
        else:
            logger.warning(f"Failed to decode token for session {session_id}")
    else:
        logger.warning(f"Anonymous connection for session {session_id}")
    
    # Dependency Injection: Create fresh services for this specific user connection
    asr_service = DeepgramASR()
    # Pass user_id as string to LLM for user-specific document retrieval
    llm_service = OpenAILLM(thread_id=session_id, user_uuid=str(user_id) if user_id else None)
    tts_service = OpenAITTS()

    manager = ConnectionManager(
        websocket=websocket,
        asr=asr_service,
        llm=llm_service,
        tts=tts_service,
        user_id=user_id,
        session_id=session_id
    )

    try:
        await manager.connect(db)
    except WebSocketDisconnect:
        # Expected when client closes tab/connection
        pass
    except Exception as e:
        logger.error(f"Global Connection Error: {e}")