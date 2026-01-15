from typing import TypedDict, Annotated
import operator
from dotenv import load_dotenv

load_dotenv()

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# -------------------------
# 1. Define State
# -------------------------

class State(TypedDict):
    messages: Annotated[list, operator.add]
    response: str


# -------------------------
# 2. LLM setup
# -------------------------

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7
)


# -------------------------
# 3. Agent Node
# -------------------------

def tech_support(state: State) -> State:
    """Generate a response using the LLM"""

    messages = state["messages"]

    result = llm.invoke(messages)

    return {
        "messages": [AIMessage(content=result.content)],
        "response": result.content
    }


# -------------------------
# 4. Quality Check
# -------------------------

def quality_check(state: State) -> str:
    """
    Decide whether to retry or finish.
    This function DOES NOT mutate state.
    It only returns a route label.
    """

    if len(state["response"]) < 10:
        return "retry"
    return "finish"


# -------------------------
# 5. Build the Graph
# -------------------------

workflow = StateGraph(State)

workflow.add_node("tech_support", tech_support)

workflow.set_entry_point("tech_support")

workflow.add_conditional_edges(
    "tech_support",
    quality_check,
    {
        "retry": "tech_support",  # 🔁 LOOP
        "finish": END
    }
)

graph = workflow.compile()


# -------------------------
# 6. Run the Graph
# -------------------------

initial_state = {
    "messages": [
        HumanMessage(content="Explain LangGraph in one sentence.")
    ],
    "response": ""
}

final_state = graph.invoke(initial_state)

print("FINAL RESPONSE:")
print(final_state["response"])
