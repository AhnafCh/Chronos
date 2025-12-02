from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.core.config import settings
from src.core import control
from src.brain.state import AgentState
from src.brain.retriever import retriever

# 1. Initialize LLM with control.py settings
llm = ChatOpenAI(
    model=control.LLM_MODEL, 
    api_key=settings.OPENAI_API_KEY, # type: ignore
    streaming=True,
    temperature=control.LLM_TEMPERATURE,
    max_tokens=control.LLM_MAX_TOKENS # type: ignore
)

# 2. Define the Prompt Template (using control settings for response length)
# Note: System prompt can be extended via control.py if needed
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are Chronos, a helpful voice assistant. "
               "Answer questions based on the following context:\n\n{context}\n\n"
               "If user says him/her name, greet them by name and tell them their name's meaning. "
               f"Keep answers concise (under 2 sentences)."),
    MessagesPlaceholder(variable_name="messages"),
])

# 3. Node 1: Retrieval (The Librarian)
async def retrieve_node(state: AgentState):
    # Get the last user message
    last_msg_obj = state["messages"][-1]
    last_message = str(last_msg_obj.content)
    
    # Search Pinecone
    docs = await retriever.ainvoke(last_message)
    
    # Combine found text into a single string
    context_text = "\n\n".join([d.page_content for d in docs])
    
    return {"context": context_text}

# 4. Node 2: Generation (The Chatbot)
async def chatbot_node(state: AgentState):
    context = state.get("context", "")
    messages = state["messages"]
    
    # Format the prompt with context + history
    chain = prompt | llm
    response = await chain.ainvoke({"context": context, "messages": messages})
    
    return {"messages": [response]}

# 5. Build the Workflow
def build_graph():
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("chatbot", chatbot_node)

    # Define Flow: Start -> Retrieve -> Chatbot -> End
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "chatbot")
    workflow.add_edge("chatbot", END)

    memory = MemorySaver()

    return workflow.compile(checkpointer=memory)

brain_app = build_graph()