# ======================================================
# ADVANCED MULTI-AGENT LANGGRAPH TOPOLOGY
# ======================================================

import operator
from typing import TypedDict, Annotated, Optional, List, Literal

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
# 1. STATE (SHARED + ISOLATED)
# ======================================================

class Handoff(TypedDict):
    from_agent: str
    to_agent: str
    reason: str


class State(TypedDict):
    # shared
    messages: Annotated[List[BaseMessage], operator.add]
    steps: int

    # explicit routing
    next_agent: Optional[str]
    handoff: Optional[Handoff]

    # planner-only
    plan: Optional[str]

    # executor-only
    execution_log: Optional[str]

    # verifier-only
    verifier_votes: Optional[List[Literal["APPROVED", "REJECTED"]]]
    critique: Optional[str]

    # final
    result: Optional[str]


# ======================================================
# 2. TOOLS
# ======================================================

@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


tool_node = ToolNode([add])


# ======================================================
# 3. MODELS
# ======================================================

planner_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
executor_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", temperature=0
).bind(tools=[add])
verifier_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)


# ======================================================
# 4. ROUTER AGENT (LOG ONLY)
# ======================================================

def router_agent(state: State):
    if state["next_agent"]:
        return {
            "messages": [
                AIMessage(
                    content=f"📍 Handoff → {state['next_agent']} "
                            f"({state['handoff']['reason']})"
                )
            ]
        }
    return {}


# ======================================================
# 5. PLANNER (ISOLATED)
# ======================================================

def planner_agent(state: State):
    response = planner_llm.invoke(
        [
            HumanMessage(
                content="You are a PLANNER. Create a short plan. Do not execute."
            )
        ] + state["messages"]
    )

    return {
        "plan": response.content,
        "handoff": {
            "from_agent": "planner",
            "to_agent": "executor",
            "reason": "plan ready",
        },
        "next_agent": "executor",
        "steps": state["steps"] + 1,
        "messages": [response],
    }


# ======================================================
# 6. EXECUTOR (PEER DELEGATION POSSIBLE)
# ======================================================

def executor_agent(state: State):
    response = executor_llm.invoke(
        [
            HumanMessage(
                content=f"You are an EXECUTOR.\nPlan:\n{state['plan']}"
            )
        ]
    )

    # executor can request replanning
    if "unclear" in response.content.lower():
        return {
            "handoff": {
                "from_agent": "executor",
                "to_agent": "planner",
                "reason": "plan unclear",
            },
            "next_agent": "planner",
            "steps": state["steps"] + 1,
            "messages": [response],
        }

    return {
        "execution_log": response.content,
        "handoff": {
            "from_agent": "executor",
            "to_agent": "verifier_fanout",
            "reason": "execution done",
        },
        "next_agent": "verifier_fanout",
        "steps": state["steps"] + 1,
        "messages": [response],
    }


# ======================================================
# 7. PARALLEL VERIFIERS
# ======================================================

def verifier_agent_A(state: State):
    resp = verifier_llm.invoke(
        [
            HumanMessage(
                content="Verifier A: Check correctness. Reply APPROVED or REJECTED."
            )
        ] + state["messages"]
    )
    return {"verifier_votes": ["APPROVED" if "approved" in resp.content.lower() else "REJECTED"]}


def verifier_agent_B(state: State):
    resp = verifier_llm.invoke(
        [
            HumanMessage(
                content="Verifier B: Check completeness. Reply APPROVED or REJECTED."
            )
        ] + state["messages"]
    )
    return {"verifier_votes": ["APPROVED" if "approved" in resp.content.lower() else "REJECTED"]}


# ======================================================
# 8. AGGREGATOR (VOTING)
# ======================================================

def verifier_aggregator(state: State):
    approvals = state["verifier_votes"].count("APPROVED")

    if approvals >= 2:
        return {
            "result": "APPROVED by majority",
            "handoff": {
                "from_agent": "verifier",
                "to_agent": "END",
                "reason": "majority approval",
            },
            "next_agent": "END",
        }

    return {
        "critique": "Verification failed",
        "handoff": {
            "from_agent": "verifier",
            "to_agent": "planner",
            "reason": "retry with critique",
        },
        "next_agent": "planner",
    }


# ======================================================
# 9. ROUTER LOGIC (CONTROL)
# ======================================================

MAX_STEPS = 10

def router(state: State) -> str:
    if state["steps"] >= MAX_STEPS:
        return END

    return state["next_agent"] or END


# ======================================================
# 10. GRAPH BUILD
# ======================================================

workflow = StateGraph(State)

workflow.add_node("router", router_agent)
workflow.add_node("planner", planner_agent)
workflow.add_node("executor", executor_agent)
workflow.add_node("tools", tool_node)

workflow.add_node("verifier_A", verifier_agent_A)
workflow.add_node("verifier_B", verifier_agent_B)
workflow.add_node("verifier_aggregator", verifier_aggregator)

workflow.add_edge(START, "planner")

workflow.add_edge("planner", "router")
workflow.add_edge("executor", "tools")
workflow.add_edge("tools", "router")

workflow.add_edge("router", "planner")
workflow.add_edge("router", "executor")
workflow.add_edge("router", "verifier_fanout")

workflow.add_edge("verifier_fanout", "verifier_A")
workflow.add_edge("verifier_fanout", "verifier_B")

workflow.add_edge("verifier_A", "verifier_aggregator")
workflow.add_edge("verifier_B", "verifier_aggregator")

workflow.add_edge("verifier_aggregator", "router")

workflow.add_conditional_edges("router", router)

graph = workflow.compile()


# ======================================================
# 11. RUN
# ======================================================

if __name__ == "__main__":
    final = graph.invoke(
        {
            "messages": [HumanMessage(content="What is 12 + 18?")],
            "steps": 0,
            "next_agent": None,
            "handoff": None,
            "plan": None,
            "execution_log": None,
            "verifier_votes": [],
            "critique": None,
            "result": None,
        }
    )

    print("\n=== FINAL TRACE ===\n")
    for m in final["messages"]:
        print(f"{m.type.upper()}: {m.content}")

    print("\nRESULT:", final["result"])
