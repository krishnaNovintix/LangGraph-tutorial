import os
from dotenv import load_dotenv

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated
import operator
import sys

@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

tools = [add, multiply]

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Please set GOOGLE_API_KEY in .env")
    sys.exit(1)

model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]

graph = StateGraph(AgentState)

def agent_node(state):
    response = model.invoke(state["messages"])
    return {"messages": [response]}

graph.add_node("agent", agent_node)

tool_node = ToolNode(tools)
graph.add_node("tools", tool_node)

graph.add_edge("tools", "agent")

def should_continue(state):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END

graph.add_conditional_edges("agent", should_continue)

graph.set_entry_point("agent")

app = graph.compile()

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "What is 2 + 3?"
    result = app.invoke({"messages": [HumanMessage(content=query)]})
    print(result["messages"][-1].content)