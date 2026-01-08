# ====================================================== multi agent graph =================================================

import operator
from typing import TypedDict, Annotated, Optional

from langgraph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
)
from langchain_core.tools import tool


# ======================================================
# 1. STATE DEFINITION (SHARED STATE)
# ======================================================

class State(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    plan: Optional[str]
    result: Optional[str]
    steps: int


# ======================================================
# 2. TOOLS (EXECUTOR ONLY)
# ======================================================

@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


tools = [add]
tool_node = ToolNode(tools)


# ======================================================
# 3. MODELS (ROLE-SPECIFIC)
# ======================================================

planner_model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
)

executor_model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
).bind(tools=tools)   # 🔑 tools bound ONLY here

verifier_model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
)


# ======================================================
# 4. ROUTER AGENT (DISPATCH ONLY)
# ======================================================

def router_agent(state: State):
    """
    Router agent does NOT solve.
    It only emits trace messages.
    """
    if state["plan"] is None:
        return {"messages": [AIMessage(content="📍 Routing → Planner")]}
    if state["result"] is None:
        return {"messages": [AIMessage(content="📍 Routing → Executor")]}
    return {"messages": [AIMessage(content="📍 Routing → Verifier")]}


# ======================================================
# 5. PLANNER AGENT (WHAT TO DO)
# ======================================================

def planner_agent(state: State):
    prompt = [
        HumanMessage(
            content=(
                "You are a PLANNER.\n"
                "Create a clear step-by-step plan.\n"
                "Do NOT execute tools.\n"
                "Do NOT give the final answer."
            )
        )
    ] + state["messages"]

    response = planner_model.invoke(prompt)

    return {
        "messages": [response],
        "plan": response.content,
        "steps": state["steps"] + 1,
    }


# ======================================================
# 6. EXECUTOR AGENT (DO THE WORK)
# ======================================================

def executor_agent(state: State):
    prompt = [
        HumanMessage(
            content=(
                "You are an EXECUTOR.\n"
                f"Plan:\n{state['plan']}\n\n"
                "Execute the plan using tools if needed.\n"
                "Do NOT verify correctness."
            )
        )
    ]

    response = executor_model.invoke(prompt)

    return {
        "messages": [response],
        "steps": state["steps"] + 1,
    }


# ======================================================
# 7. VERIFIER AGENT (IS THIS CORRECT?)
# ======================================================

def verifier_agent(state: State):
    prompt = [
        HumanMessage(
            content=(
                "You are a VERIFIER.\n"
                "Check if the answer is correct and complete.\n"
                "Reply with:\n"
                "APPROVED: <short reason>\n"
                "or\n"
                "REJECTED: <short reason>"
            )
        )
    ] + state["messages"]

    response = verifier_model.invoke(prompt)

    approved = "approved" in response.content.lower()

    return {
        "messages": [response],
        "result": response.content if approved else None,
        "steps": state["steps"] + 1,
    }


# ======================================================
# 8. ROUTER LOGIC (CONTROL FLOW)
# ======================================================

MAX_STEPS = 6

def router(state: State) -> str:
    """
    THIS decides what node runs next.
    """
    if state["steps"] >= MAX_STEPS:
        print("⛔ Max steps reached")
        return END

    if state["plan"] is None:
        return "planner"

    if state["result"] is None:
        return "executor"

    return "verifier"


# ======================================================
# 9. BUILD THE GRAPH
# ======================================================

workflow = StateGraph(State)

workflow.add_node("router", router_agent)
workflow.add_node("planner", planner_agent)
workflow.add_node("executor", executor_agent)
workflow.add_node("tools", tool_node)
workflow.add_node("verifier", verifier_agent)

workflow.add_edge(START, "router")
workflow.add_conditional_edges("router", router)

workflow.add_edge("planner", "router")
workflow.add_edge("executor", "tools")
workflow.add_edge("tools", "router")
workflow.add_edge("verifier", END)

graph = workflow.compile()


# ======================================================
# 10. RUN
# ======================================================

if __name__ == "__main__":
    initial_state: State = {
        "messages": [
            HumanMessage(content="What is 12 + 18?")
        ],
        "plan": None,
        "result": None,
        "steps": 0,
    }

    final_state = graph.invoke(initial_state)

    print("\n=========== FINAL TRACE ===========\n")
    for msg in final_state["messages"]:
        print(f"{msg.type.upper()}: {msg.content}")
