from langchain.tools import Tool
from src.agents.base_agent import create_specialized_agent
from src.tools.policy_tools import recommend_policy

def create_recommender_agent():
    """
    Create a policy recommender agent.
    
    Returns:
        An AgentExecutor instance specialized for policy recommendations
    """
    policy_recommender_tools = [
        Tool(name="recommend_policy", func=recommend_policy, 
             description="Recommend insurance policies based on user profile and needs")
    ]
    
    return create_specialized_agent(
        "Policy Recommender", 
        "You recommend insurance policies based on user profile, needs, and preferences.",
        policy_recommender_tools
    )

def recommender_node(state):
    """
    Process a state through the recommender agent.
    
    Args:
        state: The current agent state
        
    Returns:
        Updated state with agent response
    """
    from langchain_core.messages import AIMessage
    from src.services.profile_manager import ask_missing_info
    
    messages = state["messages"]
    user_profile = state["user_profile"]
    
    # Check if we need more information
    missing_info = ask_missing_info(user_profile)
    if missing_info:
        return {"messages": [AIMessage(content=missing_info)]}
    
    # Format profile information for the agent
    profile_info = ", ".join([f"{k}: {v}" for k, v in user_profile.items() if k != "last_updated"])
    input_with_profile = f"User profile: {profile_info}\n\nQuery: {messages[-1].content}" 
    
    # Create agent on demand to avoid global state issues
    agent = create_recommender_agent()
    response = agent.invoke({
        "input": input_with_profile,
        "chat_history": messages[:-1]  # Pass all previous messages as chat history
    })
    
    return {"messages": [AIMessage(content=response["output"])]}