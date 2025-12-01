from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from src.core.config import settings
from src.brain.state import AgentState

# 1. Initialize LLM
llm = ChatOpenAI(
    model="gpt-4o-mini", 
    api_key=settings.OPENAI_API_KEY, #type: ignore
    streaming=True
)

# System Prompt to define personality
SYSTEM_PROMPT = SystemMessage(content=(
    "You are Chronos, a helpful voice assistant. "
    "Keep answers concise (under 2 sentences) for voice output."
))

# 2. Define the Node (The Processor)
async def chatbot_node(state: AgentState):
    """
    Receives the state (history), queries the LLM, and returns the new message.
    """
    messages = state["messages"]
    
    # We prepend the system prompt only for the LLM call, 
    # we don't necessarily need to store it in the history every time 
    # if we manage it here, but typically we just prepend it to the context.
    response = await llm.ainvoke([SYSTEM_PROMPT] + messages)
    
    # Return the new message. Because of 'operator.add' in state.py,
    # this will be appended to the existing list.
    return {"messages": [response]}

# 3. Build the Workflow
def build_graph():
    # Initialize Graph with our State schema
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("chatbot", chatbot_node)

    # Define Edges (Simple loop: Start -> Chatbot -> End)
    workflow.add_edge(START, "chatbot")
    workflow.add_edge("chatbot", END)

    # Add Persistence (Memory)
    # MemorySaver keeps the state in RAM. Later we will swap this for Redis.
    memory = MemorySaver()

    # Compile into a Runnable
    return workflow.compile(checkpointer=memory)

# Singleton instance for the app to import
brain_app = build_graph()