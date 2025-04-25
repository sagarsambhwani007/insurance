from langchain.tools import Tool
from langchain_core.messages import AIMessage
from src.agents.base_agent import create_specialized_agent
from src.tools.policy_tools import answer_faq
from src.tools.document_tools import analyze_document

def create_faq_agent():
    """
    Create an FAQ specialist agent.
    
    Returns:
        An AgentExecutor instance specialized for answering FAQs
    """
    faq_tools = [
        Tool(name="answer_faq", func=answer_faq, 
             description="Answer frequently asked questions about insurance policies")
    ]
    
    return create_specialized_agent(
        "FAQ Specialist",
        "You answer specific questions about insurance policies and terms.",
        faq_tools
    )

def create_document_agent():
    """
    Create a document analyzer agent.
    
    Returns:
        An AgentExecutor instance specialized for document analysis
    """
    doc_tools = [
        Tool(name="analyze_document", func=analyze_document, 
             description="Extract and analyze information from uploaded documents")
    ]
    
    return create_specialized_agent(
        "Document Analyzer",
        "You analyze uploaded insurance documents and extract relevant information.",
        doc_tools
    )

def faq_node(state):
    """
    Process a state through the FAQ agent.
    
    Args:
        state: The current agent state
        
    Returns:
        Updated state with agent response
    """
    messages = state["messages"]
    selected_policy = state.get("selected_policy", "")
    
    # Include selected policy context if available
    input_with_context = messages[-1].content
    if selected_policy:
        input_with_context = f"Policy context: {selected_policy}\n\n{messages[-1].content}"
    
    # Create agent on demand
    agent = create_faq_agent()
    response = agent.invoke({
        "input": input_with_context,
        "chat_history": messages[:-1]  # Pass all previous messages as chat history
    })
    
    return {"messages": [AIMessage(content=response["output"])]}

def document_node(state):
    """
    Process a state through the document analysis agent.
    Intelligently handles both uploaded documents and documents in the docs folder.
    """
    messages = state["messages"]
    uploaded_files = state.get("uploaded_files", [])
    
    # Add document processing context
    input_with_context = f"Uploaded documents: {uploaded_files}\n\n{messages[-1].content}"
    
    # Create agent on demand with full chat history
    agent = create_document_agent()
    response = agent.invoke({
        "input": input_with_context,
        "chat_history": messages[:-1]  # Pass all previous messages as chat history
    })
    
    # Query the vector store for relevant information
    # The analyze_document function will search across all available documents
    document_analysis = analyze_document(messages[-1].content, use_uploaded=bool(uploaded_files))
    
    # Combine responses
    combined_response = f"{response['output']}\n\nDocument Analysis:\n{document_analysis}"
    
    # Update state with new files if uploaded
    if "uploaded" in response["output"].lower():
        new_files = [f for f in response["output"].split(":")[-1].split(",")]
        uploaded_files.extend(new_files)
    
    return {
        "messages": [AIMessage(content=combined_response)],
        "uploaded_files": uploaded_files
    }
