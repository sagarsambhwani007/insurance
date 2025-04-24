from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from dotenv import load_dotenv
load_dotenv()  # Load first before other imports

from src.core.state import AgentState
from src.config.constants import VALID_POLICIES, DEFAULT_MODEL, AGENT_TYPES
from src.services.profile_manager import update_user_profile, format_profile_summary
from src.agents.recommender import recommender_node
from src.agents.comparator import comparison_node, web_comparison_node
from src.agents.faq_handler import faq_node, document_node

def route_to_agent(state):
    """
    Route the user message to the appropriate specialized agent.
    """
    # Keep existing ChatOpenAI initialization
    llm = ChatOpenAI(model=DEFAULT_MODEL)
    messages = state["messages"]
    user_profile = state["user_profile"]
    last_message = messages[-1].content if messages else ""
    
    # Parse user intent with context-aware prompt
    coordinator_prompt = f"""
    Conversation history: {[msg.content for msg in messages]}
    User profile: {user_profile}
    
    Determine which agent should handle this request:
    1. "recommender" - Policy recommendations
    2. "comparison" - Policy comparisons
    3. "web_comparison" - Competitor comparisons
    4. "faq" - General questions
    5. "document" - Document analysis
    6. "profile_update" - User information updates
    7. "feedback" - Feedback handling
    
    Current message: "{last_message}"
    Respond ONLY with: recommender, comparison, web_comparison, faq, document, profile_update, or feedback.
    """
    
    intent = llm.invoke(coordinator_prompt).content.strip().lower()
    
    # Validate intent against known types
    if intent not in AGENT_TYPES:
        intent = "faq"  # Default to FAQ
    
    # Update state with all necessary fields
    return {
        "current_intent": intent,
        "selected_policy": state.get("selected_policy", ""),
        "user_profile": update_user_profile(last_message, user_profile),
        "messages": messages  # Maintain conversation history
    }

def update_profile_node(state):
    """
    Process a state through the profile update node.
    """
    user_profile = state["user_profile"]
    profile_summary = format_profile_summary(user_profile)
    
    # Preserve all state fields while updating messages
    return {
        **state,  # Carry forward existing state
        "messages": [AIMessage(content=f"### Profile Updated\n\nThank you for providing your information. Here's what I know about you:\n\n{profile_summary}\n\nIs there anything else you'd like to share or update?")]
    }

def process_feedback_node(state):
    """
    Process a state through the feedback node.
    """
    import re
    
    messages = state["messages"]
    llm = ChatOpenAI(model=DEFAULT_MODEL)
    
    # Extract feedback and store for future learning
    feedback_prompt = f"Extract numeric feedback score (1-5) from this message, or return 0 if no score is found: {messages[-1].content}"
    feedback_response = llm.invoke(feedback_prompt).content.strip()
    
    try:
        feedback_score = int(re.search(r'\d+', feedback_response).group())
        if feedback_score < 1 or feedback_score > 5:
            feedback_score = 3  # Default to neutral if outside range
    except (ValueError, AttributeError):
        feedback_score = 3  # Default to neutral if parsing fails
    
    return {
        **state,  # Maintain existing state
        "feedback_score": feedback_score,
        "messages": [AIMessage(content=f"Thank you for your feedback! I've recorded your satisfaction score of {feedback_score}/5. How else can I assist you today?")]
    }

def create_workflow():
    """
    Create the agent workflow graph.
    
    Returns:
        A compiled StateGraph for the insurance agent
    """
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("route", route_to_agent)
    workflow.add_node("recommender", recommender_node)
    workflow.add_node("comparison", comparison_node)
    workflow.add_node("web_comparison", web_comparison_node)
    workflow.add_node("faq", faq_node)
    workflow.add_node("document", document_node)
    workflow.add_node("profile_update", update_profile_node)
    workflow.add_node("feedback", process_feedback_node)
    
    # Set up conditional routing
    workflow.add_conditional_edges(
        "route",
        lambda state: state["current_intent"],
        {
            "recommender": "recommender",
            "comparison": "comparison",
            "web_comparison": "web_comparison",
            "faq": "faq",
            "document": "document",
            "profile_update": "profile_update",
            "feedback": "feedback"
        }
    )
    
    # Connect all agent nodes to END
    for node in ["recommender", "comparison", "web_comparison", "faq", "document", "profile_update", "feedback"]:
        workflow.add_edge(node, END)
    
    # Set the entry point
    workflow.set_entry_point("route")
    
    # Compile the graph
    return workflow.compile()