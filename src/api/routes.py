from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from src.brain.graph import brain_app

router = APIRouter()

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

@router.post("/text-chat", response_model=ChatResponse)
async def text_chat(request: ChatRequest):
    """
    Handle standard text-based chat.
    Uses the SAME LangGraph brain as the Voice agent.
    """
    config = {"configurable": {"thread_id": request.session_id}}
    
    try:
        # FIX: We include "context": "" to satisfy the AgentState TypedDict definition
        result = await brain_app.ainvoke(
            {
                "messages": [HumanMessage(content=request.message)],
                "context": "" 
            }, 
            config=config # type: ignore
        )
        
        # Get the last message (Bot's answer)
        bot_response = result["messages"][-1].content
        return ChatResponse(response=str(bot_response))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))