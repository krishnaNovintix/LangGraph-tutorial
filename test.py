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





