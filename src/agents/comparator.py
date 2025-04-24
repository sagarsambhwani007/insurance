from langchain.tools import Tool
from langchain_core.messages import AIMessage
from src.agents.base_agent import create_specialized_agent
from src.tools.comparison_tools import compare_policies, web_compare

def create_comparison_agent():
    """
    Create a policy comparison agent.
    
    Returns:
        An AgentExecutor instance specialized for policy comparisons
    """
    policy_comparison_tools = [
        Tool(name="compare_policies", func=compare_policies, 
             description="Compare multiple insurance policies in a tabular format")
    ]
    
    return create_specialized_agent(
        "Policy Comparison",
        "You compare different insurance policies side by side in clear tables.",
        policy_comparison_tools
    )

def create_web_comparison_agent():
    """
    Create a web comparison agent.
    
    Returns:
        An AgentExecutor instance specialized for web comparisons
    """
    web_comparison_tools = [
        Tool(name="web_compare", func=web_compare, 
             description="Compare with external market options and competitors")
    ]
    
    return create_specialized_agent(
        "Web Comparison",
        "You compare our policies with competitors and provide market analysis.",
        web_comparison_tools
    )

def comparison_node(state):
    """
    Process a state through the comparison agent.
    """
    from langchain_core.messages import AIMessage
    messages = state["messages"]

    # Pass chat_history as required by the prompt template
    agent = create_comparison_agent()
    response = agent.invoke({
        "input": messages[-1].content,
        "chat_history": messages[:-1]  # Pass all previous messages as chat_history
    })

    return {"messages": [AIMessage(content=response["output"])]}

def web_comparison_node(state):
    """
    Process a state through the web comparison agent.
    
    Args:
        state: The current agent state
        
    Returns:
        Updated state with agent response
    """
    messages = state["messages"]
    
    # Create agent on demand
    agent = create_web_comparison_agent()
    response = agent.invoke({"input": messages[-1].content})
    
    return {"messages": [AIMessage(content=response["output"])]}