import os
from langchain.tools import Tool
from langchain_core.messages import AIMessage
from src.agents.base_agent import create_specialized_agent
from src.tools.policy_tools import recommend_policy
from src.tools.document_tools import analyze_document
from src.config.paths import PATHS

def create_recommender_agent():
    """
    Create a policy recommender agent.
    
    Returns:
        An AgentExecutor instance specialized for policy recommendations
    """
    policy_recommender_tools = [
        Tool(name="recommend_policy", func=recommend_policy, 
             description="Recommend insurance policies based on user profile and needs"),
        Tool(name="analyze_document", func=analyze_document,
             description="Extract and analyze information from documents to enhance recommendations")
    ]
    
    return create_specialized_agent(
        "Policy Recommender", 
        "You recommend insurance policies based on user profile, needs, preferences, and document analysis.",
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
    from src.services.profile_manager import ask_missing_info
    
    messages = state["messages"]
    user_profile = state["user_profile"]
    uploaded_files = state.get("uploaded_files", [])
    
    # Check if we need more information
    missing_info = ask_missing_info(user_profile)
    if missing_info:
        return {"messages": [AIMessage(content=missing_info)]}
    
    # Format profile information for the agent
    profile_info = ", ".join([f"{k}: {v}" for k, v in user_profile.items() if k != "last_updated"])
    
    # Add document context if available
    doc_context = ""
    if uploaded_files:
        doc_context = f"\nUploaded documents: {', '.join(uploaded_files)}"
    
    input_with_context = f"User profile: {profile_info}{doc_context}\n\nQuery: {messages[-1].content}"
    
    # Create agent on demand to avoid global state issues
    agent = create_recommender_agent()
    response = agent.invoke({
        "input": input_with_context,
        "chat_history": messages[:-1]  # Pass all previous messages as chat history
    })
    
    # If documents are available, enhance recommendations with document analysis
    if uploaded_files or any(os.path.exists(os.path.join(PATHS["root_dir"], "docs", f)) for f in os.listdir(os.path.join(PATHS["root_dir"], "docs"))):
        # Query the vector store for relevant information
        document_analysis = analyze_document(messages[-1].content, use_uploaded=bool(uploaded_files))
        
        # Combine responses
        combined_response = f"{response['output']}\n\n**Additional insights from your documents:**\n{document_analysis}"
        return {"messages": [AIMessage(content=combined_response)]}
    
    return {"messages": [AIMessage(content=response["output"])]}