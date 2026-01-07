"""
LangGraph Tutorial: Complete Guide with Code Examples
======================================================

This file provides a comprehensive introduction to LangGraph, including:
- Basic syntax and setup
- State management (TypedDict, Annotated)
- Nodes (functions, ToolNode)
- Edges (regular and conditional)
- Tools integration
- Running and debugging graphs

We're using Google's Gemini (via ChatGoogleGenerativeAI) as the LLM.
Make sure to set GOOGLE_API_KEY in your .env file.

Run this file to see examples in action: python langgraph_examples.py
"""

import os
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated
import operator
import sys

# Setup Gemini model
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Please set GOOGLE_API_KEY in .env")
    sys.exit(1)

model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)

# =============================================================================
# 1. BASIC STATE DEFINITION
# =============================================================================

class BasicState(TypedDict):
    """Simple state with a single message list."""
    messages: Annotated[list, operator.add]

class ExtendedState(TypedDict):
    """State with multiple fields for more complex scenarios."""
    messages: Annotated[list, operator.add]
    current_step: str  # Track progress
    tool_results: list  # Accumulate tool outputs

# =============================================================================
# 2. TOOLS DEFINITION
# =============================================================================

@tool
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a + b

@tool
def divide(a: float, b: float) -> float:
    """Divide two numbers. Returns float."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

tools = [add, multiply, divide]

# Bind tools to model for tool-aware responses
model_with_tools = model.bind_tools(tools)

# =============================================================================
# 3. BASIC GRAPH EXAMPLE (No Tools)
# =============================================================================

def basic_agent_node(state: BasicState):
    """A simple node that calls the LLM without tools."""
    response = model.invoke(state["messages"])
    return {"messages": [response]}

def create_basic_graph():
    """Create a basic graph with one node."""
    graph = StateGraph(BasicState)
    graph.add_node("agent", basic_agent_node)
    graph.set_entry_point("agent")
    return graph.compile()

# =============================================================================
# 4. GRAPH WITH TOOLS EXAMPLE
# =============================================================================

def agent_with_tools_node(state: ExtendedState):
    """Agent node that can use tools."""
    response = model_with_tools.invoke(state["messages"])
    return {"messages": [response], "current_step": "agent_responded"}

def tool_execution_node(state: ExtendedState):
    """Node to execute tools (using ToolNode)."""
    # ToolNode handles tool execution automatically
    tool_node = ToolNode(tools)
    result = tool_node.invoke(state)
    return {"messages": result["messages"], "tool_results": [result], "current_step": "tools_executed"}

def should_continue_tools(state: ExtendedState):
    """Decide whether to continue to tools or end."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END

def create_tools_graph():
    """Create a graph with agent and tools."""
    graph = StateGraph(ExtendedState)
    graph.add_node("agent", agent_with_tools_node)
    graph.add_node("tools", tool_execution_node)

    graph.add_edge("tools", "agent")  # After tools, back to agent
    graph.add_conditional_edges("agent", should_continue_tools)

    graph.set_entry_point("agent")
    return graph.compile()

# =============================================================================
# 5. ADVANCED EXAMPLE: Multi-Step Workflow
# =============================================================================

class WorkflowState(TypedDict):
    messages: Annotated[list, operator.add]
    step_count: int
    final_answer: str

def planning_node(state: WorkflowState):
    """Plan the next steps."""
    prompt = f"Plan how to solve: {state['messages'][0].content}"
    response = model.invoke([HumanMessage(content=prompt)])
    return {"messages": [response], "step_count": state.get("step_count", 0) + 1}

def execution_node(state: WorkflowState):
    """Execute using tools if needed."""
    response = model_with_tools.invoke(state["messages"])
    return {"messages": [response], "step_count": state["step_count"] + 1}

def summarization_node(state: WorkflowState):
    """Summarize the final answer."""
    all_content = "\n".join([msg.content for msg in state["messages"]])
    prompt = f"Summarize the solution: {all_content}"
    response = model.invoke([HumanMessage(content=prompt)])
    return {"messages": [response], "final_answer": response.content, "step_count": state["step_count"] + 1}

def workflow_condition(state: WorkflowState):
    """Decide next step in workflow."""
    if state["step_count"] < 2:
        return "execute"
    elif state["step_count"] < 3:
        return "summarize"
    return END

def create_workflow_graph():
    """Multi-step workflow graph."""
    graph = StateGraph(WorkflowState)
    graph.add_node("plan", planning_node)
    graph.add_node("execute", execution_node)
    graph.add_node("summarize", summarization_node)

    graph.add_edge("plan", "execute")
    graph.add_conditional_edges("execute", workflow_condition)
    graph.add_edge("summarize", END)

    graph.set_entry_point("plan")
    return graph.compile()

# =============================================================================
# 6. RUNNING EXAMPLES
# =============================================================================

def run_basic_example():
    """Run the basic graph example."""
    print("\n=== BASIC GRAPH EXAMPLE ===")
    app = create_basic_graph()
    query = "Hello, what is the capital of France?"
    result = app.invoke({"messages": [HumanMessage(content=query)]})
    print(f"Query: {query}")
    print(f"Response: {result['messages'][-1].content}")

def run_tools_example():
    """Run the tools graph example."""
    print("\n=== TOOLS GRAPH EXAMPLE ===")
    app = create_tools_graph()
    query = "What is 15 + 27? Then multiply the result by 2."
    result = app.invoke({
        "messages": [HumanMessage(content=query)],
        "current_step": "started",
        "tool_results": []
    })
    print(f"Query: {query}")
    print(f"Final Response: {result['messages'][-1].content}")
    print(f"Steps: {result['current_step']}")

def run_workflow_example():
    """Run the multi-step workflow example."""
    print("\n=== WORKFLOW GRAPH EXAMPLE ===")
    app = create_workflow_graph()
    query = "Calculate 10 * 5 and then add 20."
    result = app.invoke({
        "messages": [HumanMessage(content=query)],
        "step_count": 0,
        "final_answer": ""
    })
    print(f"Query: {query}")
    print(f"Final Answer: {result['final_answer']}")
    print(f"Total Steps: {result['step_count']}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("LangGraph Examples with Gemini")
    print("=" * 40)

    try:
        run_basic_example()
        run_tools_example()
        run_workflow_example()
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure your GOOGLE_API_KEY is set correctly.")

    print("\n=== EXAMPLES COMPLETED ===")
    print("Explore the code above to understand LangGraph components!")
    print("- States: TypedDict with Annotated fields")
    print("- Nodes: Functions that process state")
    print("- Edges: Connections between nodes")
    print("- Tools: @tool decorated functions, ToolNode for execution")
    print("- Conditional Edges: Dynamic routing based on state")