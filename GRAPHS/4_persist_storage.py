#============================ persistent state ======================================================
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# 1. Define the State
# We use 'list' and 'add' so the 'history' builds up over time instead of being overwritten
from operator import add
class State(TypedDict):
    input: str
    history: Annotated[list, add]
    needs_research: bool

# 2. Define the Nodes
def oracle(state: State):
    print("--- NODE: ORACLE (Thinking...) ---")
    user_input = state["input"]
    
    # Logic: If the user asks about something specific, trigger research
    if "weather" in user_input.lower() or "price" in user_input.lower():
        return {"history": ["Oracle: I need to look that up..."], "needs_research": True}
    
    return {"history": ["Oracle: I can answer that directly!"], "needs_research": False}

def researcher(state: State):
    print("--- NODE: RESEARCHER (Searching...) ---")
    # Simulating a search result
    return {"history": ["Researcher: Found it! It is 72 degrees and sunny."]}

# 3. Define the Router (Conditional Logic)
def router(state: State) -> Literal["to_research", "to_end"]:
    if state["needs_research"]:
        return "to_research"
    return "to_end"

# 4. Build the Graph
workflow = StateGraph(State)

workflow.add_node("oracle", oracle)
workflow.add_node("researcher", researcher)

workflow.add_edge(START, "oracle")

# Logic: From oracle, decide whether to go to researcher or end
workflow.add_conditional_edges(
    "oracle",
    router,
    {
        "to_research": "researcher",
        "to_end": END
    }
)

workflow.add_edge("researcher", END)

# 5. Add Persistence (Memory)
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# --- EXECUTION ---

# Define a thread (This is like a 'Chat Session ID')
config = {"configurable": {"thread_id": "session_1"}}

print("\n--- FIRST RUN ---")
result1 = app.invoke({"input": "What is the weather?"}, config)
print(result1["history"])

print("\n--- SECOND RUN (Same Thread, Memory Active) ---")
# Because we use the same thread_id, the 'history' list continues to grow
result2 = app.invoke({"input": "What is the price of Bitcoin?"}, config)
print(result2["history"])
