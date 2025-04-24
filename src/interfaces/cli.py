import sys
from typing import Dict, Any
from langchain_core.messages import HumanMessage
from src.core.state import create_initial_state, AgentState
from src.core.graph import create_workflow

def run_cli_interface():
    """
    Run the insurance chatbot with a command-line interface.
    """
    print("🤖 Insurance Chatbot initialized. Type 'exit' to quit.")
    print("---------------------------------------------------")
    
    # Create the workflow
    app = create_workflow()
    
    # Initialize state
    state = create_initial_state()
    
    while True:
        # Get user input
        user_input = input("You: ")
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Agent: 👋 Thank you for using our insurance chatbot. Have a great day!")
            break
        
        # Add user message to state
        state["messages"].append(HumanMessage(content=user_input))
        
        # Process through the workflow
        state = app.invoke(state)
        
        # Print the agent's response
        print(f"Agent: {state['messages'][-1].content}")

def chat_with_insurance_agent(message: str, state: AgentState = None) -> Dict[str, Any]:
    """
    Process a single message through the insurance agent workflow.
    
    Args:
        message: The user message to process
        state: The current state, or None to create a new state
        
    Returns:
        The updated state
    """
    # Create workflow
    app = create_workflow()
    
    # Initialize state if needed
    if state is None:
        state = create_initial_state()
    
    # Add user message to state
    state["messages"].append(HumanMessage(content=message))
    
    # Process through the workflow
    result = app.invoke(state)
    
    return result

if __name__ == "__main__":
    run_cli_interface()