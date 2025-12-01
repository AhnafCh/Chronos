import asyncio
import sys
import os

# Fix path to allow importing from src
sys.path.append(os.getcwd())

from langchain_core.messages import HumanMessage
from src.brain.graph import brain_app

async def run_chat():
    # Config with a specific thread_id simulates a persistent user session
    config = {"configurable": {"thread_id": "user_session_001"}}

    print("--- TURN 1 (Introduction) ---")
    input_1 = "Hi, my name is Asif."
    print(f"User: {input_1}")
    
    # We stream the graph execution
    async for event in brain_app.astream(
        {"messages": [HumanMessage(content=input_1)]}, 
        config=config # type: ignore
    ):
        # The event contains the output of the nodes that just ran
        for value in event.values():
            print(f"Bot:  {value['messages'][-1].content}")

    print("\n--- TURN 2 (Memory Recall) ---")
    input_2 = "What is my name?"
    print(f"User: {input_2}")
    
    # We invoke the graph again with the SAME thread_id
    async for event in brain_app.astream(
        {"messages": [HumanMessage(content=input_2)]}, 
        config=config # type: ignore
    ):
        for value in event.values():
            print(f"Bot:  {value['messages'][-1].content}")

if __name__ == "__main__":
    asyncio.run(run_chat())