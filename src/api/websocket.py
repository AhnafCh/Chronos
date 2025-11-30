# src/api/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.transport.connection_mgr import ConnectionManager

# Services are imported HERE, not in main.py
from src.services.asr import DeepgramASR
from src.services.llm import OpenAILLM
from src.services.tts import OpenAITTS

router = APIRouter()

@router.websocket("/chat")  # This becomes /ws/chat because of the prefix in main.py
async def websocket_endpoint(websocket: WebSocket):
    # Dependency Injection: Create fresh services for this specific user connection
    asr_service = DeepgramASR()
    llm_service = OpenAILLM()
    tts_service = OpenAITTS()

    manager = ConnectionManager(
        websocket=websocket,
        asr=asr_service,
        llm=llm_service,
        tts=tts_service
    )

    try:
        await manager.connect()
    except WebSocketDisconnect:
        # Expected when client closes tab/connection
        pass
    except Exception as e:
        print(f"Global Connection Error: {e}")