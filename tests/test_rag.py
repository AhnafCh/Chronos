import asyncio
import sys
import os

sys.path.append(os.getcwd())

from langchain_core.messages import HumanMessage
from src.brain.graph import brain_app

async def run_test():
    config = {"configurable": {"thread_id": "rag_test_1"}}

    # Question specifically about the data we ingested
    question = "How much does the Pro Plan cost?"
    print(f"User: {question}")
    print("Thinking...")

    async for event in brain_app.astream_events(
        {"messages": [HumanMessage(content=question)]},
        config=config, # type: ignore
        version="v2"
    ):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"] # type: ignore
            if chunk.content:
                print(chunk.content, end="", flush=True)
    
    print("\n\n(If it said $99/month, RAG is working!)")

if __name__ == "__main__":
    asyncio.run(run_test())