import operator
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    # The 'add' operator is critical here. 
    # It tells the graph: "When a node returns 'messages', append them to this list."
    messages: Annotated[list[BaseMessage], operator.add]

    context: str