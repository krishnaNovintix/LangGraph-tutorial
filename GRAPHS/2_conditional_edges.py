# ======================================================
# CUSTOMER SUPPORT TICKET ROUTING SYSTEM
# Demonstrates conditional routing in LangGraph
# ======================================================
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
import datetime

class SupportTicket(TypedDict):
    query: str
    category: str
    priority: str
    response: str
    ticket_id: str

def categorize_ticket(state: SupportTicket):
    '''Categorize support ticket based on keywords'''
    print("[SYSTEM] Analyzing ticket...")
    query_lower = state["query"].lower()
    
    # Multi-category classification with priority assignment
    if any(word in query_lower for word in ["refund", "charge", "billing", "payment", "invoice", "money"]):
        return {"category": "billing", "priority": "high"}
    elif any(word in query_lower for word in ["password", "login", "account", "access", "locked"]):
        return {"category": "account", "priority": "medium"}
    else:
        return {"category": "technical", "priority": "medium"}

def handle_billing(state: SupportTicket):
    '''Process billing-related tickets'''
    print(f"[BILLING DEPT] Processing ticket {state['ticket_id']}...")
    return {
        "response": (
            f"TICKET #{state['ticket_id']} - BILLING DEPARTMENT\n"
            f"Priority: {state['priority'].upper()}\n"
            f"Status: ESCALATED\n\n"
            "Your billing inquiry has been forwarded to our finance team.\n"
            "Expected response time: 24 hours\n"
            "You will receive an email confirmation shortly."
        )
    }

def handle_technical(state: SupportTicket):
    '''Process technical support tickets'''
    print(f"[TECH SUPPORT] Processing ticket {state['ticket_id']}...")
    return {
        "response": (
            f"TICKET #{state['ticket_id']} - TECHNICAL SUPPORT\n"
            f"Priority: {state['priority'].upper()}\n"
            f"Status: IN PROGRESS\n\n"
            "Troubleshooting Steps:\n"
            "1. Clear browser cache and cookies\n"
            "2. Try accessing from incognito/private mode\n"
            "3. Disable browser extensions temporarily\n"
            "4. Contact support if issue persists: support@company.com"
        )
    }

def handle_account(state: SupportTicket):
    '''Process account-related tickets'''
    print(f"[ACCOUNT SERVICES] Processing ticket {state['ticket_id']}...")
    return {
        "response": (
            f"TICKET #{state['ticket_id']} - ACCOUNT SERVICES\n"
            f"Priority: {state['priority'].upper()}\n"
            f"Status: PENDING VERIFICATION\n\n"
            "For security, please complete these steps:\n"
            "1. Verify your email address (check spam folder)\n"
            "2. Answer your security questions\n"
            "3. Check your inbox for password reset link\n\n"
            "Need help? Call us at: 1-800-SUPPORT"
        )
    }

# Router function - decides department routing
def route_ticket(state: SupportTicket) -> Literal["billing_path", "technical_path", "account_path"]:
    '''Route ticket to appropriate department'''
    routing_map = {
        "billing": "billing_path",
        "technical": "technical_path",
        "account": "account_path"
    }
    return routing_map[state["category"]]

# Build the support ticket system graph
workflow = StateGraph(SupportTicket)

# Add department nodes
workflow.add_node("categorizer", categorize_ticket)
workflow.add_node("billing_dept", handle_billing)
workflow.add_node("tech_support", handle_technical)
workflow.add_node("account_services", handle_account)

# Define routing
workflow.add_edge(START, "categorizer")

# Conditional routing to appropriate department
workflow.add_conditional_edges(
    "categorizer", 
    route_ticket,
    {
        "billing_path": "billing_dept",
        "technical_path": "tech_support",
        "account_path": "account_services"
    }
)

# All departments lead to END
workflow.add_edge("billing_dept", END)
workflow.add_edge("tech_support", END)
workflow.add_edge("account_services", END)

app = workflow.compile()

# ======================================================
# TEST THE SYSTEM
# ======================================================

if __name__ == "__main__":
    test_tickets = [
        "I was charged twice for my subscription",
        "I cannot log into my account",
        "The application keeps crashing when I try to upload files"
    ]

    print("=" * 70)
    print("CUSTOMER SUPPORT TICKET ROUTING SYSTEM")
    print("=" * 70)

    for idx, ticket_query in enumerate(test_tickets, 1):
        ticket = {
            "query": ticket_query,
            "category": "",
            "priority": "",
            "response": "",
            "ticket_id": f"TKT{datetime.datetime.now().strftime('%Y%m%d')}{idx:03d}"
        }
        
        print(f"\n[NEW TICKET] {ticket_query}")
        result = app.invoke(ticket)
        print(f"\n{result['response']}")
        print("-" * 70)
