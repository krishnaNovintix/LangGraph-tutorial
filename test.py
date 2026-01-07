#=========== easy level ==============
# from langgraph.graph import StateGraph, START, END
# from typing import TypedDict

# class AgentState(TypedDict):
#     input_text: str
#     sentiment: str

# def sense_emotion(state: AgentState):
#     if "happy" in state["input_text"]:
#         return {"sentiment": "happy"}
#     return {"sentiment": "sad"}

# def set_emoji(state: AgentState):
#     if state["sentiment"] == "happy":
#         return {"input_text": state["input_text"] + "hehe"}
#     return {"input_text": state["input_text"] + "lame ah"}    

# graph = StateGraph(AgentState)
# graph.add_node("classifier", sense_emotion)
# graph.add_node("emoji", set_emoji)

# graph.add_edge(START, "classifier")
# graph.add_edge("classifier", "emoji")
# graph.add_edge("emoji", END)

# agent = graph.compile()

# result = agent.invoke({"input_text": "i am happy da boi"})
# print(result)

# ============================= conditional edges ========================
# from typing import TypedDict, Literal
# from langgraph.graph import StateGraph, START, END

# # 1. State
# class State(TypedDict):
#     query: str
#     category: str  # "refund" or "tech"
#     response: str

# # 2. Nodes
# def categorizer(state: State):
#     print("---CATEGORIZING---")
#     if "money" in state["query"] or "refund" in state["query"]:
#         return {"category": "refund"}
#     return {"category": "tech"}

# def handle_refund(state: State):
#     print("---HANDLING REFUND---")
#     return {"response": "Refund request sent to the bank."}

# def handle_tech(state: State):
#     print("---HANDLING TECH---")
#     return {"response": "Please try restarting your device."}

# # 3. The Router Function
# # This function decides the "path"
# def route_query(state: State) -> Literal["refund_path", "tech_path"]:
#     if state["category"] == "refund":
#         return "refund_path"
#     return "tech_path"

# # 4. Building the Graph
# workflow = StateGraph(State)

# workflow.add_node("classifier", categorizer)
# workflow.add_node("refund_processor", handle_refund)
# workflow.add_node("tech_support", handle_tech)

# # --- THE EDGES ---
# workflow.add_edge(START, "classifier")

# # Add Conditional Edge: 
# # If 'classifier' finishes, run 'route_query' to decide where to go next.
# workflow.add_conditional_edges(
#     "classifier", 
#     route_query,
#     {
#         "refund_path": "refund_processor",
#         "tech_path": "tech_support"
#     }
# )

# # Both paths lead to the END
# workflow.add_edge("refund_processor", END)
# workflow.add_edge("tech_support", END)

# app = workflow.compile()

# ================ loooping =========================
# def quality_check(state: State):
#     if len(state["response"]) < 10:
#         return "retry"
#     return "finish"

# # In the graph setup:
# workflow.add_conditional_edges(
#     "tech_support",
#     quality_check,
#     {
#         "retry": "tech_support", # <--- THIS IS THE LOOP
#         "finish": END
#     }
# )

#============================ persistent state ==========================
# from typing import TypedDict, Annotated, Literal
# from langgraph.graph import StateGraph, START, END
# from langgraph.checkpoint.memory import MemorySaver

# # 1. Define the State
# # We use 'list' and 'add' so the 'history' builds up over time instead of being overwritten
# from operator import add
# class State(TypedDict):
#     input: str
#     history: Annotated[list, add]
#     needs_research: bool

# # 2. Define the Nodes
# def oracle(state: State):
#     print("--- NODE: ORACLE (Thinking...) ---")
#     user_input = state["input"]
    
#     # Logic: If the user asks about something specific, trigger research
#     if "weather" in user_input.lower() or "price" in user_input.lower():
#         return {"history": ["Oracle: I need to look that up..."], "needs_research": True}
    
#     return {"history": ["Oracle: I can answer that directly!"], "needs_research": False}

# def researcher(state: State):
#     print("--- NODE: RESEARCHER (Searching...) ---")
#     # Simulating a search result
#     return {"history": ["Researcher: Found it! It is 72 degrees and sunny."]}

# # 3. Define the Router (Conditional Logic)
# def router(state: State) -> Literal["to_research", "to_end"]:
#     if state["needs_research"]:
#         return "to_research"
#     return "to_end"

# # 4. Build the Graph
# workflow = StateGraph(State)

# workflow.add_node("oracle", oracle)
# workflow.add_node("researcher", researcher)

# workflow.add_edge(START, "oracle")

# # Logic: From oracle, decide whether to go to researcher or end
# workflow.add_conditional_edges(
#     "oracle",
#     router,
#     {
#         "to_research": "researcher",
#         "to_end": END
#     }
# )

# workflow.add_edge("researcher", END)

# # 5. Add Persistence (Memory)
# memory = MemorySaver()
# app = workflow.compile(checkpointer=memory)

# # --- EXECUTION ---

# # Define a thread (This is like a 'Chat Session ID')
# config = {"configurable": {"thread_id": "session_1"}}

# print("\n--- FIRST RUN ---")
# result1 = app.invoke({"input": "What is the weather?"}, config)
# print(result1["history"])

# print("\n--- SECOND RUN (Same Thread, Memory Active) ---")
# # Because we use the same thread_id, the 'history' list continues to grow
# result2 = app.invoke({"input": "What is the price of Bitcoin?"}, config)
# print(result2["history"])

#========================= TOOLSSSS =========================


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