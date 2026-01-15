# ======================================================
# CUSTOMER FEEDBACK SENTIMENT ANALYZER
# A basic LangGraph implementation for real-world use
# ======================================================
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class FeedbackState(TypedDict):
    customer_feedback: str
    sentiment: str
    response_template: str
    confidence_score: float

def analyze_sentiment(state: FeedbackState):
    '''Analyze customer feedback sentiment using keyword matching'''
    feedback_lower = state["customer_feedback"].lower()
    
    # Define sentiment keywords
    positive_words = ["great", "excellent", "love", "amazing", "happy", "satisfied", "wonderful", "perfect"]
    negative_words = ["bad", "terrible", "hate", "disappointed", "issue", "problem", "awful", "horrible"]
    
    # Count occurrences
    positive_count = sum(word in feedback_lower for word in positive_words)
    negative_count = sum(word in feedback_lower for word in negative_words)
    
    # Determine sentiment and confidence
    total_sentiment_words = positive_count + negative_count
    
    if total_sentiment_words == 0:
        return {"sentiment": "neutral", "confidence_score": 0.5}
    
    if positive_count > negative_count:
        confidence = min(0.99, 0.5 + (positive_count - negative_count) * 0.1)
        return {"sentiment": "positive", "confidence_score": confidence}
    elif negative_count > positive_count:
        confidence = min(0.99, 0.5 + (negative_count - positive_count) * 0.1)
        return {"sentiment": "negative", "confidence_score": confidence}
    else:
        return {"sentiment": "neutral", "confidence_score": 0.5}

def generate_response(state: FeedbackState):
    '''Generate appropriate automated response based on sentiment'''
    templates = {
        "positive": (
            "POSITIVE FEEDBACK (Confidence: {:.0%})\n".format(state["confidence_score"]) +
            "Thank you for your positive feedback! We are delighted you enjoyed our service.\n" +
            "Original: '{}'".format(state["customer_feedback"])
        ),
        "negative": (
            "NEGATIVE FEEDBACK (Confidence: {:.0%})\n".format(state["confidence_score"]) +
            "We sincerely apologize for your experience. Our support team will contact you within 24 hours.\n" +
            "Original: '{}'".format(state["customer_feedback"])
        ),
        "neutral": (
            "NEUTRAL FEEDBACK (Confidence: {:.0%})\n".format(state["confidence_score"]) +
            "Thank you for your feedback. We appreciate all customer input.\n" +
            "Original: '{}'".format(state["customer_feedback"])
        )
    }
    return {"response_template": templates[state["sentiment"]]}

# Build the sentiment analysis graph
graph = StateGraph(FeedbackState)
graph.add_node("sentiment_analyzer", analyze_sentiment)
graph.add_node("response_generator", generate_response)

# Define execution flow
graph.add_edge(START, "sentiment_analyzer")
graph.add_edge("sentiment_analyzer", "response_generator")
graph.add_edge("response_generator", END)

# Compile the graph
agent = graph.compile()

# ======================================================
# TEST THE SYSTEM
# ======================================================

if __name__ == "__main__":
    test_feedbacks = [
        "I absolutely love this product! It's amazing and works perfectly!",
        "Terrible experience. The service was awful and very disappointing.",
        "The product arrived on time.",
        "Great service! Happy with my purchase. Excellent quality.",
        "Bad quality, horrible support. I hate this experience."
    ]

    print("=" * 70)
    print("CUSTOMER FEEDBACK SENTIMENT ANALYSIS SYSTEM")
    print("=" * 70)

    for feedback in test_feedbacks:
        result = agent.invoke({
            "customer_feedback": feedback, 
            "sentiment": "", 
            "response_template": "",
            "confidence_score": 0.0
        })
        print("\n" + result["response_template"])
        print("-" * 70)
