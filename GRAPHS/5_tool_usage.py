#========================= TOOLSSSS ===============================================================


import operator
from typing import Annotated, TypedDict
# 1. CHANGED: Import for Gemini
from langchain_google_genai import ChatGoogleGenerativeAI 
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

# --- STEP 1: Define the Tools (Same as before) ---
@tool
def add(a: float, b: float) -> float:
    """Adds a and b."""
    return a + b

@tool
def subtract(a: float, b: float) -> float:
    """Subtracts b from a."""
    return a - b

@tool
def multiply(a: float, b: float) -> float:
    """Multiplies a and b."""
    return a * b

@tool
def divide(a: float, b: float) -> float:
    """Divides a by b."""
    if b == 0:
        return "Error: Division by zero."
    return a / b

tools = [add, subtract, multiply, divide]

# --- STEP 2: Define the State ---
class State(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]

# --- STEP 3: Setup Gemini ---
# Ensure you have GOOGLE_API_KEY in your environment variables
model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0).bind_tools(tools)

def call_model(state: State):
    response = model.invoke(state["messages"])
    return {"messages": [response]}

# --- STEP 4: Build the Graph ---
workflow = StateGraph(State)

workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

# --- STEP 5: Persistence & Compilation ---
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# --- STEP 6: Run ---
config = {"configurable": {"thread_id": "gemini_math_session"}}

print("--- Round 1: Gemini Thinking ---")
user_input = "Hi! My name is Gemini. Multiply 12 by 4."
# Using stream_mode="values" gives us the full state at each step
for chunk in app.stream({"messages": [("user", user_input)]}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()

print("\n--- Round 2: Gemini Remembering ---")
user_input = "Now subtract 10 from that result and tell me my name."
for chunk in app.stream({"messages": [("user", user_input)]}, config, stream_mode="values"):
    chunk["messages"][-1].pretty_print()
