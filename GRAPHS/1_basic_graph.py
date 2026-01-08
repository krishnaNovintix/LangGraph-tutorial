#=========== easy level ==============
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class AgentState(TypedDict):
    input_text: str
    sentiment: str

def sense_emotion(state: AgentState):
    if "happy" in state["input_text"]:
        return {"sentiment": "happy"}
    return {"sentiment": "sad"}

def set_emoji(state: AgentState):
    if state["sentiment"] == "happy":
        return {"input_text": state["input_text"] + "hehe"}
    return {"input_text": state["input_text"] + "lame ah"}    

graph = StateGraph(AgentState)
graph.add_node("classifier", sense_emotion)
graph.add_node("emoji", set_emoji)

graph.add_edge(START, "classifier")
graph.add_edge("classifier", "emoji")
graph.add_edge("emoji", END)

agent = graph.compile()

result = agent.invoke({"input_text": "i am happy da boi"})
print(result)