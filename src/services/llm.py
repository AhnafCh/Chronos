import uuid
import logging
from typing import AsyncGenerator
from langchain_core.messages import HumanMessage
from src.core.interfaces import LLMInterface
from src.brain.graph import brain_app

logger = logging.getLogger(__name__)

class OpenAILLM(LLMInterface):
    def __init__(self):
        self.thread_id = str(uuid.uuid4())
        self.config = {"configurable": {"thread_id": self.thread_id}}
        logger.info(f"Brain initialized for session: {self.thread_id}")

    async def generate_response(self, query: str) -> AsyncGenerator[str, None]:
        if not query:
            return

        try:
            # Stream events from the Graph (LangGraph)
            # detailed events including token streaming
            async for event in brain_app.astream_events(
                {"messages": [HumanMessage(content=query)]},
                config=self.config, # type: ignore
                version="v2"
            ):
                # 3. Filter for LLM Token Events
                # We look for "on_chat_model_stream" which represents a chunk of text from GPT
                kind = event["event"]
                
                if kind == "on_chat_model_stream":
                    # Extract the chunk data
                    data = event["data"]
                    chunk = data.get("chunk")
                    
                    # Yield content if it exists
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        yield chunk.content

        except Exception as e:
            logger.error(f"LLM/Graph Error: {e}")
            yield "I'm sorry, I'm having trouble thinking right now."