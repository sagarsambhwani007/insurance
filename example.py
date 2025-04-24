from langgraph.graph import StateGraph, END
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from typing import TypedDict, Annotated, Sequence, Dict, Any, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator

# Define state
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_profile: Dict[str, Any]
    selected_policy: str
    current_intent: str
    feedback_score: int
    uploaded_files: List[str]

# Initialize models
llm = ChatOpenAI(model="gpt-4")

# Define specialized agents
def create_specialized_agent(name, description, tools):
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"You are a specialized {name} agent. {description}"),
        ("human", "{{input}}"),
    ])
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools)

# Policy recommender agent
policy_recommender_tools = [
    Tool(name="recommend_policy", func=recommend_policy, 
         description="Recommend insurance policies based on user profile")
]
policy_recommender = create_specialized_agent(
    "Policy Recommender", 
    "You recommend insurance policies based on user profile and needs.",
    policy_recommender_tools
)

# Policy comparison agent
policy_comparison_tools = [
    Tool(name="compare_policies", func=compare_policies, 
         description="Compare multiple insurance policies")
]
policy_comparison = create_specialized_agent(
    "Policy Comparison",
    "You compare different insurance policies side by side.",
    policy_comparison_tools
)

# Web comparison agent
web_comparison_tools = [
    Tool(name="web_compare", func=web_compare, 
         description="Compare with external market options")
]
web_comparison = create_specialized_agent(
    "Web Comparison",
    "You compare our policies with competitors using web search.",
    web_comparison_tools
)

# FAQ agent
faq_tools = [
    Tool(name="answer_faq", func=answer_faq, 
         description="Answer FAQs about insurance policies")
]
faq_agent = create_specialized_agent(
    "FAQ Specialist",
    "You answer specific questions about insurance policies.",
    faq_tools
)

# Document analysis agent
doc_tools = [
    Tool(name="analyze_document", func=analyze_document, 
         description="Extract and analyze information from uploaded documents")
]
document_agent = create_specialized_agent(
    "Document Analyzer",
    "You analyze uploaded insurance documents and answer questions about them.",
    doc_tools
)

# Define the coordinator agent - this is the main router
def route_to_agent(state):
    messages = state["messages"]
    user_profile = state["user_profile"]
    last_message = messages[-1].content if messages else ""
    
    # Parse user intent with a more sophisticated model
    coordinator_prompt = f"""
    Analyze this user message: {last_message}
    
    User profile: {user_profile}
    
    Determine which specialized agent should handle this request:
    1. "recommender" - If user wants policy recommendations
    2. "comparison" - If user wants to compare specific policies
    3. "web_comparison" - If user wants to compare with competitors
    4. "faq" - If user is asking questions about a policy
    5. "document" - If user wants analysis of uploaded documents
    6. "profile_update" - If user is sharing personal information
    7. "feedback" - If user is providing feedback about responses
    
    Return just the agent name with no additional text.
    """
    
    intent = llm.invoke(coordinator_prompt).content.strip().lower()
    return intent

# Define nodes for each agent
def recommender_node(state):
    messages = state["messages"]
    response = policy_recommender.invoke({"input": messages[-1].content})
    return {"messages": [AIMessage(content=response["output"])]}

def comparison_node(state):
    messages = state["messages"]
    response = policy_comparison.invoke({"input": messages[-1].content})
    return {"messages": [AIMessage(content=response["output"])]}

def web_comparison_node(state):
    messages = state["messages"]
    response = web_comparison.invoke({"input": messages[-1].content})
    return {"messages": [AIMessage(content=response["output"])]}

def faq_node(state):
    messages = state["messages"]
    response = faq_agent.invoke({"input": messages[-1].content})
    return {"messages": [AIMessage(content=response["output"])]}

def document_node(state):
    messages = state["messages"]
    response = document_agent.invoke({"input": messages[-1].content})
    return {"messages": [AIMessage(content=response["output"])]}

def update_profile_node(state):
    messages = state["messages"]
    user_profile = state["user_profile"]
    
    # Update user profile based on the latest message
    new_profile = update_user_profile(messages[-1].content, user_profile)
    
    return {
        "user_profile": new_profile,
        "messages": [AIMessage(content=f"Thank you for providing your information. I've updated your profile.")]
    }

def process_feedback_node(state):
    messages = state["messages"]
    
    # Extract feedback and store for future learning
    feedback_prompt = f"Extract feedback score (1-5) from: {messages[-1].content}"
    feedback_score = int(llm.invoke(feedback_prompt).content.strip()[0])
    
    return {
        "feedback_score": feedback_score,
        "messages": [AIMessage(content="Thank you for your feedback! I'll use this to improve.")]
    }

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

# Add edges
workflow.add_edge("route", "recommender", condition=lambda x: x == "recommender")
workflow.add_edge("route", "comparison", condition=lambda x: x == "comparison")
workflow.add_edge("route", "web_comparison", condition=lambda x: x == "web_comparison")
workflow.add_edge("route", "faq", condition=lambda x: x == "faq")
workflow.add_edge("route", "document", condition=lambda x: x == "document")
workflow.add_edge("route", "profile_update", condition=lambda x: x == "profile_update")
workflow.add_edge("route", "feedback", condition=lambda x: x == "feedback")

# Connect all agent nodes back to END
for node in ["recommender", "comparison", "web_comparison", "faq", "document", "profile_update", "feedback"]:
    workflow.add_edge(node, END)

# Compile the graph
app = workflow.compile()

# Function to run the chatbot
def chat_with_insurance_agent(message: str, state: AgentState = None):
    if state is None:
        state = {
            "messages": [],
            "user_profile": {},
            "selected_policy": "",
            "current_intent": "",
            "feedback_score": 0,
            "uploaded_files": []
        }
    
    # Add user message to state
    state["messages"].append(HumanMessage(content=message))
    
    # Run through the graph
    result = app.invoke(state)
    
    # Return the updated state and the response
    return result

PATHS = get_project_paths()

def recommend_policy(query: str) -> str:
    """Recommend insurance policies based on user profile and query"""
    policy_data_path = PATHS["policies_file"]
    
    # Sample policy data - in production this would load from the file
    policies = {
        "health": ["Basic Health", "Premium Health", "Family Health"],
        "auto": ["Liability Only", "Comprehensive", "Premium Coverage"],
        "home": ["Basic Home", "Standard Home", "Premium Home"],
        "life": ["Term Life", "Whole Life", "Universal Life"]
    }
    
    # Save sample data if file doesn't exist
    if not os.path.exists(policy_data_path):
        with open(policy_data_path, 'w') as f:
            json.dump(policies, f)
    
    # Extract policy type from query
    policy_type = "health"  # Default
    if "car" in query.lower() or "auto" in query.lower():
        policy_type = "auto"
    elif "home" in query.lower() or "house" in query.lower():
        policy_type = "home"
    elif "life" in query.lower():
        policy_type = "life"
    
    recommended = policies.get(policy_type, policies["health"])
    return f"Based on your needs, I recommend these {policy_type} insurance policies:\n" + "\n".join(f"- {p}" for p in recommended)

def compare_policies(query: str) -> str:
    """Compare multiple insurance policies"""
    comparison_data_path = PATHS["comparisons_file"]
    
    # Sample comparison data structure
    comparisons = {
        "Basic Health vs Premium Health": {
            "Monthly Premium": ["$200", "$350"],
            "Deductible": ["$2,000", "$1,000"],
            "Coverage Limit": ["$500,000", "$1,000,000"],
            "Network Size": ["Limited", "Extensive"]
        },
        "Liability Only vs Comprehensive Auto": {
            "Monthly Premium": ["$75", "$150"],
            "Deductible": ["$500", "$250"],
            "Covers Your Car": ["No", "Yes"],
            "Liability Coverage": ["$25,000", "$50,000"]
        }
    }
    
    # Extract policy pair from query
    policy_pair = "Basic Health vs Premium Health"  # Default
    if "auto" in query.lower() or "car" in query.lower():
        policy_pair = "Liability Only vs Comprehensive Auto"
    
    comparison = comparisons.get(policy_pair, comparisons["Basic Health vs Premium Health"])
    
    # Format the comparison as a table
    result = f"Comparison of {policy_pair}:\n\n"
    for feature, values in comparison.items():
        result += f"{feature}: {values[0]} vs {values[1]}\n"
    
    return result

def web_compare(query: str) -> str:
    """Compare with external market options"""
    competitor_data_path = PATHS["competitors_file"]
    
    # Sample competitor data
    competitors = {
        "health": {
            "CompetitorA": {"price": "$300", "rating": "4.2/5", "unique": "24/7 telemedicine"},
            "CompetitorB": {"price": "$250", "rating": "3.8/5", "unique": "No waiting period"},
            "Our Premium Health": {"price": "$350", "rating": "4.5/5", "unique": "Global coverage"}
        },
        "auto": {
            "CompetitorC": {"price": "$120", "rating": "4.0/5", "unique": "Accident forgiveness"},
            "CompetitorD": {"price": "$140", "rating": "4.3/5", "unique": "Roadside assistance"},
            "Our Comprehensive": {"price": "$150", "rating": "4.7/5", "unique": "New car replacement"}
        }
    }
    
    # Save sample data if file doesn't exist
    if not os.path.exists(competitor_data_path):
        with open(competitor_data_path, 'w') as f:
            json.dump(competitors, f)
    
    # Extract policy type from query
    policy_type = "health"  # Default
    if "auto" in query.lower() or "car" in query.lower():
        policy_type = "auto"
    
    market_data = competitors.get(policy_type, competitors["health"])
    
    # Format the comparison
    result = f"Market comparison for {policy_type} insurance:\n\n"
    for company, details in market_data.items():
        result += f"{company}:\n"
        result += f"- Price: {details['price']}\n"
        result += f"- Customer Rating: {details['rating']}\n"
        result += f"- Unique Feature: {details['unique']}\n\n"
    
    return result

def answer_faq(query: str) -> str:
    """Answer FAQs about insurance policies"""
    faq_data_path = PATHS["faqs_file"]
    
    # Sample FAQ data
    faqs = {
        "waiting period": "The standard waiting period for most policies is 30 days from the effective date.",
        "deductible": "A deductible is the amount you pay out of pocket before your insurance coverage kicks in.",
        "premium": "The premium is your regular payment (monthly, quarterly, or annually) to maintain your insurance coverage.",
        "claim": "To file a claim, log into your account portal or call our 24/7 claims hotline at 1-800-555-CLAIM.",
        "coverage limits": "Coverage limits are the maximum amounts your policy will pay for covered losses."
    }
    
    # Save sample data if file doesn't exist
    if not os.path.exists(faq_data_path):
        with open(faq_data_path, 'w') as f:
            json.dump(faqs, f)
    
    # Find the most relevant FAQ
    for keyword, answer in faqs.items():
        if keyword.lower() in query.lower():
            return f"Q: What is the {keyword}?\nA: {answer}"
    
    return "I don't have specific information about that in my FAQ database. Please contact customer service for more details."

def analyze_document(document_name: str) -> str:
    """Extract and analyze information from uploaded documents"""
    uploads_dir = PATHS["uploads_dir"]
    
    # Simulate document analysis
    document_types = {
        "policy": "This appears to be a standard policy document. Key coverage: $500,000 with a $1,000 deductible.",
        "claim": "This is a claim form. Status: In Processing. Estimated completion: 5-7 business days.",
        "id": "This is an identification document. Verified and added to your profile.",
        "medical": "This is a medical report. Relevant conditions noted for underwriting."
    }
    
    # Determine document type from name
    doc_type = "policy"  # Default
    for key in document_types:
        if key in document_name.lower():
            doc_type = key
            break
    
    return f"Analysis of document '{document_name}':\n{document_types[doc_type]}"

def update_user_profile(message: str, current_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Update user profile based on message content"""
    new_profile = dict(current_profile)
    
    # Extract potential profile information
    if "age" in message.lower():
        # Extract age using simple pattern matching
        words = message.split()
        for i, word in enumerate(words):
            if word.lower() == "age" or word.lower() == "aged":
                if i+1 < len(words) and words[i+1].isdigit():
                    new_profile["age"] = int(words[i+1])
    
    if "name" in message.lower():
        # Extract name using simple pattern matching
        words = message.split()
        for i, word in enumerate(words):
            if word.lower() == "name" or word.lower() == "called":
                if i+1 < len(words):
                    new_profile["name"] = words[i+1]
    
    # Check for insurance types
    insurance_types = ["health", "auto", "home", "life"]
    for insurance in insurance_types:
        if insurance in message.lower():
            if "interests" not in new_profile:
                new_profile["interests"] = []
            if insurance not in new_profile["interests"]:
                new_profile["interests"].append(insurance)
    
    # Add timestamp for the update
    new_profile["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return new_profile