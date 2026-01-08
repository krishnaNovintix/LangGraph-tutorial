# ======================================================
# SUBGRAPHS & COMPOSITION — FULL REFERENCE
# ======================================================

import operator
from typing import TypedDict, Annotated, Optional, List

from langgraph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool


# ======================================================
# 1. BASE STATE (USED EVERYWHERE)
# ======================================================

class BaseState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    steps: int
    result: Optional[str]


# ======================================================
# 2. TOOL (USED BY MULTIPLE GRAPHS)
# ======================================================

@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


tool_node = ToolNode([add])


# ======================================================
# 3. REUSABLE EXECUTOR SUBGRAPH (PARAMETERIZED)
# ======================================================
# This graph can be reused with ANY instruction

def build_executor_subgraph(task_prompt: str):
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", temperature=0
    ).bind(tools=[add])

    class ExecutorState(BaseState):
        pass

    def executor_agent(state: ExecutorState):
        response = llm.invoke(
            [
                HumanMessage(content=task_prompt)
            ] + state["messages"]
        )
        return {
            "messages": [response],
            "steps": state["steps"] + 1,
        }

    g = StateGraph(ExecutorState)
    g.add_node("executor", executor_agent)
    g.add_node("tools", tool_node)

    g.add_edge(START, "executor")
    g.add_edge("executor", "tools")
    g.add_edge("tools", END)

    return g.compile()


# ======================================================
# 4. VERIFIER SUBGRAPH (REUSABLE MODULE)
# ======================================================

def build_verifier_subgraph():
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

    class VerifierState(BaseState):
        approved: Optional[bool]

    def verifier_agent(state: VerifierState):
        resp = llm.invoke(
            [
                HumanMessage(
                    content="Verify the answer. Reply APPROVED or REJECTED."
                )
            ] + state["messages"]
        )

        approved = "approved" in resp.content.lower()
        return {
            "messages": [resp],
            "approved": approved,
            "steps": state["steps"] + 1,
        }

    g = StateGraph(VerifierState)
    g.add_node("verifier", verifier_agent)
    g.add_edge(START, "verifier")
    g.add_edge("verifier", END)

    return g.compile()


# ======================================================
# 5. RECURSIVE SUPERVISOR GRAPH
# ======================================================
# Calls executor → verifier → retries executor if needed

MAX_RETRIES = 3

class SupervisorState(BaseState):
    retries: int
    approved: Optional[bool]


executor_graph = build_executor_subgraph(
    task_prompt="Compute the answer using tools if needed."
)

verifier_graph = build_verifier_subgraph()


def supervisor_router(state: SupervisorState) -> str:
    if state["retries"] >= MAX_RETRIES:
        return END
    if state.get("approved"):
        return END
    return "executor_subgraph"


def collect_verifier_result(state: SupervisorState):
    last_msg = state["messages"][-1]
    approved = "approved" in last_msg.content.lower()
    return {
        "approved": approved,
        "retries": state["retries"] + (0 if approved else 1),
    }


supervisor = StateGraph(SupervisorState)

# Graphs as nodes (🔥 key concept)
supervisor.add_node("executor_subgraph", executor_graph)
supervisor.add_node("verifier_subgraph", verifier_graph)
supervisor.add_node("collector", collect_verifier_result)

supervisor.add_edge(START, "executor_subgraph")
supervisor.add_edge("executor_subgraph", "verifier_subgraph")
supervisor.add_edge("verifier_subgraph", "collector")
supervisor.add_conditional_edges("collector", supervisor_router)

supervisor_graph = supervisor.compile()


# ======================================================
# 6. TOP-LEVEL SYSTEM GRAPH (COMPOSITION)
# ======================================================
# Supervisor itself is just another node

class SystemState(SupervisorState):
    pass


system = StateGraph(SystemState)

system.add_node("supervisor", supervisor_graph)
system.add_edge(START, "supervisor")
system.add_edge("supervisor", END)

system_graph = system.compile()


# ======================================================
# 7. RUN
# ======================================================

if __name__ == "__main__":
    final = system_graph.invoke(
        {
            "messages": [HumanMessage(content="What is 12 + 18?")],
            "steps": 0,
            "retries": 0,
            "approved": None,
            "result": None,
        }
    )

    print("\n=== FINAL TRACE ===\n")
    for m in final["messages"]:
        print(f"{m.type.upper()}: {m.content}")
