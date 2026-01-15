# ============================= Agent with Tools and routing =====================================================
import operator
from typing import TypedDict, Annotated
from dotenv import load_dotenv

load_dotenv()

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI


# -------------------------
# 1. STATE DEFINITION
# -------------------------

class State(TypedDict):
    # Conversation log (append-only)
    messages: Annotated[list[BaseMessage], operator.add]

    # Guard rail for loops
    steps: int


# -------------------------
# 2. TOOLS
# -------------------------

@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@tool
def subtract(a: int, b: int) -> int:
    """Subtract two numbers."""
    return a - b    

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b    

@tool
def divide(a: int, b: int) -> float | str:
    """Divide two numbers."""
    if b == 0:
        return "Error: Division by zero."
    return a / b


tools = [add, subtract, multiply, divide]
tool_node = ToolNode(tools)


# -------------------------
# 3. MODEL
# -------------------------

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
).bind_tools(tools)


# -------------------------
# 4. AGENT NODE
# -------------------------

def agent_node(state: State):
    """
    The agent only THINKS and EMITS messages.
    It never decides where to go next.
    """
    response = model.invoke(state["messages"])

    return {
        "messages": [response],
        "steps": state["steps"] + 1,
    }
# -------------------------
# 5. FINAL NODE (FALLTHROUGH)
# -------------------------

def final_node(state: State):
    """
    Optional terminal node to show fallthrough routing.
    """
    last = state["messages"][-1]

    if isinstance(last, AIMessage):
        return {
            "messages": [
                AIMessage(content=f"✅ Final Answer:\n{last.content}")
            ]
        }
    return {}
# -------------------------
# 6. ROUTER (CONTROL FLOW BRAIN)
# -------------------------
MAX_STEPS = 5
def router(state: State) -> str:
    """
    Decides what node runs next.
    """
    # ---- Guard rail: max iterations
    if state["steps"] >= MAX_STEPS:
        print("⛔ Max steps reached")
        return END

    last = state["messages"][-1]

    # ---- Tool error handling
    if isinstance(last, ToolMessage):
        if "error" in last.content.lower():
            print("⛔ Tool error detected")
            return END

    # ---- Tool requested → tools
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"

    # ---- Semantic-ish routing
    if isinstance(last, AIMessage):
        content = last.content.lower()
        if "answer" in content or "final" in content:
            return "final"

    # ---- Default termination
    return END

# -------------------------
# 7. BUILD THE GRAPH
# -------------------------
workflow = StateGraph(State)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)
workflow.add_node("final", final_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", router)
workflow.add_edge("tools", "agent")
workflow.add_edge("final", END)

graph = workflow.compile()


# -------------------------
# 8. RUN
# -------------------------

if __name__ == "__main__":
    initial_state: State = {
        "messages": [
            HumanMessage(content="What is 7 + 8?")
        ],
        "steps": 0,
    }

    result = graph.invoke(initial_state)

    print("\n===== EXECUTION TRACE =====\n")
    for msg in result["messages"]:
        role = msg.type.upper()
        print(f"{role}: {msg.content}")

