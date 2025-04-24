from langgraph.graph import StateGraph, END
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from typing import TypedDict, Annotated, Sequence, Dict, Any, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator
import re
import os
import json
from datetime import datetime

# Define state
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_profile: Dict[str, Any]
    selected_policy: str
    current_intent: str
    feedback_score: int
    uploaded_files: List[str]

# Initialize paths
def get_project_paths():
    base_dir = "./data/insurance_chatbot"
    os.makedirs(base_dir, exist_ok=True)
    
    paths = {
        "policies_file": os.path.join(base_dir, "policies.json"),
        "comparisons_file": os.path.join(base_dir, "comparisons.json"),
        "competitors_file": os.path.join(base_dir, "competitors.json"),
        "faqs_file": os.path.join(base_dir, "faqs.json"),
        "uploads_dir": os.path.join(base_dir, "uploads"),
        "chroma_dir": os.path.join(base_dir, "insurance_vector_db")
    }
    
    # Create uploads directory if it doesn't exist
    os.makedirs(paths["uploads_dir"], exist_ok=True)
    
    return paths

PATHS = get_project_paths()

# Define valid policies
VALID_POLICIES = [
    "Basic Health", "Premium Health", "Family Health",
    "Liability Only", "Comprehensive", "Premium Coverage",
    "Basic Home", "Standard Home", "Premium Home",
    "Term Life", "Whole Life", "Universal Life"
]

# Initialize models
llm = ChatOpenAI(model="gpt-4")

# Enhanced user profile updating with regex pattern matching
def update_user_profile(message: str, current_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Update user profile based on message content using regex patterns"""
    new_profile = dict(current_profile)
    
    # Extract age using regex
    if age_match := re.search(r"(?:i'?m|i am|age|aged) (\d{1,2})", message.lower()):
        new_profile["age"] = int(age_match.group(1))
    
    # Extract income using regex
    if income_match := re.search(r"(?:income|salary|earn|my income is).{0,10}?[$₹]?(\d[\d,.]+)", message.lower()):
        new_profile["income"] = income_match.group(1)
    
    # Extract financial goals
    if goal_match := re.search(r"(savings|retirement|protection|education|investment)", message.lower()):
        new_profile["goal"] = goal_match.group(1)
    
    # Extract name with improved pattern
    if name_match := re.search(r"(?:my name is|i'?m called|i am) ([A-Z][a-z]+ [A-Z][a-z]+|[A-Z][a-z]+)", message.lower()):
        new_profile["name"] = name_match.group(1)
    
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

def ask_missing_info(profile):
    """Generate prompts for missing user information"""
    questions = []
    if "age" not in profile: questions.append("your age")
    if "income" not in profile: questions.append("your income")
    if "goal" not in profile: questions.append("your financial goal")
    
    if questions:
        return "🧠 To provide better recommendations, please share: " + ", ".join(questions)
    return None

# Tool functions with improved implementations
def recommend_policy(query: str) -> str:
    """Recommend insurance policies based on user profile and query"""
    policy_data_path = PATHS["policies_file"]
    
    # Load or create policy data
    if os.path.exists(policy_data_path):
        with open(policy_data_path, 'r') as f:
            policies = json.load(f)
    else:
        # Sample policy data
        policies = {
            "health": ["Basic Health", "Premium Health", "Family Health"],
            "auto": ["Liability Only", "Comprehensive", "Premium Coverage"],
            "home": ["Basic Home", "Standard Home", "Premium Home"],
            "life": ["Term Life", "Whole Life", "Universal Life"]
        }
        
        # Save sample data
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
    
    # Format response in markdown
    result = f"### Recommended {policy_type.title()} Insurance Policies\n\n"
    for policy in recommended:
        result += f"#### {policy}\n"
        if policy.startswith("Basic"):
            result += "- ✅ Affordable monthly premiums\n"
            result += "- ✅ Essential coverage for most needs\n"
            result += "- ✅ No waiting period for basic services\n"
        elif policy.startswith("Premium"):
            result += "- ✅ Comprehensive coverage with lower deductibles\n"
            result += "- ✅ Additional benefits like global coverage\n"
            result += "- ✅ 24/7 priority customer service\n"
        else:
            result += "- ✅ Balanced coverage options\n"
            result += "- ✅ Flexible payment terms\n"
            result += "- ✅ Customizable add-ons available\n"
    
    return result

def compare_policies(query: str) -> str:
    """Compare multiple insurance policies with tabular format"""
    comparison_data_path = PATHS["comparisons_file"]
    
    # Load or create comparison data
    if os.path.exists(comparison_data_path):
        with open(comparison_data_path, 'r') as f:
            comparisons = json.load(f)
    else:
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
        
        # Save sample data
        with open(comparison_data_path, 'w') as f:
            json.dump(comparisons, f)
    
    # Extract policies from query
    policies = [p.strip() for p in re.split(r"and|,", query.lower()) 
               if any(pn.lower() in p.lower() for pn in VALID_POLICIES)]
    
    if len(policies) < 2:
        return "❌ Please specify at least 2 valid policies to compare."
    
    # Determine the comparison key based on matched policies
    policy_pair = None
    for key in comparisons.keys():
        if all(p.lower() in key.lower() for p in policies):
            policy_pair = key
            break
    
    if not policy_pair:
        policy_pair = "Basic Health vs Premium Health"  # Default if no match
    
    comparison = comparisons.get(policy_pair, comparisons["Basic Health vs Premium Health"])
    
    # Format the comparison as a markdown table
    result = f"### Comparison of {policy_pair}\n\n"
    result += "| Feature | " + " | ".join(policy_pair.split(" vs ")) + " |\n"
    result += "|" + "-" * 10 + "|" + "-" * 15 + "|" + "-" * 15 + "|\n"
    
    for feature, values in comparison.items():
        result += f"| {feature} | {values[0]} | {values[1]} |\n"
    
    return result

def web_compare(query: str) -> str:
    """Compare with external market options"""
    competitor_data_path = PATHS["competitors_file"]
    
    # Load or create competitor data
    if os.path.exists(competitor_data_path):
        with open(competitor_data_path, 'r') as f:
            competitors = json.load(f)
    else:
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
        
        # Save sample data
        with open(competitor_data_path, 'w') as f:
            json.dump(competitors, f)
    
    # Extract policy type from query
    policy_type = "health"  # Default
    if "auto" in query.lower() or "car" in query.lower():
        policy_type = "auto"
    
    market_data = competitors.get(policy_type, competitors["health"])
    
    # Format the comparison in markdown
    result = f"### Market Comparison for {policy_type.title()} Insurance\n\n"
    result += "| Company | Price | Rating | Unique Feature |\n"
    result += "|---------|-------|--------|---------------|\n"
    
    for company, details in market_data.items():
        result += f"| {company} | {details['price']} | {details['rating']} | {details['unique']} |\n"
    
    result += "\n### Summary\n\n"
    our_product = next((c for c in market_data.keys() if c.startswith("Our")), None)
    if our_product:
        result += f"While competitors offer lower prices, {our_product} stands out with its {market_data[our_product]['rating']} rating and unique {market_data[our_product]['unique']} feature, making it an excellent value despite the slightly higher premium."
    
    return result

def answer_faq(query: str) -> str:
    """Answer FAQs about insurance policies with improved formatting"""
    faq_data_path = PATHS["faqs_file"]
    
    # Load or create FAQ data
    if os.path.exists(faq_data_path):
        with open(faq_data_path, 'r') as f:
            faqs = json.load(f)
    else:
        # Sample FAQ data
        faqs = {
            "waiting period": "The standard waiting period for most policies is 30 days from the effective date.",
            "deductible": "A deductible is the amount you pay out of pocket before your insurance coverage kicks in.",
            "premium": "The premium is your regular payment (monthly, quarterly, or annually) to maintain your insurance coverage.",
            "claim": "To file a claim, log into your account portal or call our 24/7 claims hotline at 1-800-555-CLAIM.",
            "coverage limits": "Coverage limits are the maximum amounts your policy will pay for covered losses."
        }
        
        # Save sample data
        with open(faq_data_path, 'w') as f:
            json.dump(faqs, f)
    
    # Find the most relevant FAQ
    for keyword, answer in faqs.items():
        if keyword.lower() in query.lower():
            return f"### FAQ: {keyword.title()}\n\n**Q: What is the {keyword}?**\n\n**A:** {answer}"
    
    return "❌ I don't have specific information about that in my FAQ database. Please contact customer service for more details."

def analyze_document(query: str) -> str:
    """Extract and analyze information from uploaded documents"""
    uploads_dir = PATHS["uploads_dir"]
    
    # Extract document name from query
    document_name = query.strip()
    if not document_name:
        return "❌ Please specify a document name to analyze."
    
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
    
    return f"### Document Analysis: '{document_name}'\n\n📄 {document_types[doc_type]}"

# Define specialized agents with improved prompts
def create_specialized_agent(name, description, tools):
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a specialized {name} agent in the insurance domain.
{description}

IMPORTANT GUIDELINES:
1. Use markdown formatting for all responses
2. Always be helpful, concise, and focused on insurance information
3. Use bullet points and tables when appropriate
4. Begin important sections with emoji indicators: 🧠 for insights, ❌ for warnings, ✅ for benefits
5. If you can't answer confidently, say so rather than providing uncertain information"""),
        ("human", "{{input}}"),
    ])
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools)

# Policy recommender agent
policy_recommender_tools = [
    Tool(name="recommend_policy", func=recommend_policy, 
         description="Recommend insurance policies based on user profile and needs")
]
policy_recommender = create_specialized_agent(
    "Policy Recommender", 
    "You recommend insurance policies based on user profile, needs, and preferences.",
    policy_recommender_tools
)

# Policy comparison agent
policy_comparison_tools = [
    Tool(name="compare_policies", func=compare_policies, 
         description="Compare multiple insurance policies in a tabular format")
]
policy_comparison = create_specialized_agent(
    "Policy Comparison",
    "You compare different insurance policies side by side in clear tables.",
    policy_comparison_tools
)

# Web comparison agent
web_comparison_tools = [
    Tool(name="web_compare", func=web_compare, 
         description="Compare with external market options and competitors")
]
web_comparison = create_specialized_agent(
    "Web Comparison",
    "You compare our policies with competitors and provide market analysis.",
    web_comparison_tools
)

# FAQ agent
faq_tools = [
    Tool(name="answer_faq", func=answer_faq, 
         description="Answer frequently asked questions about insurance policies")
]
faq_agent = create_specialized_agent(
    "FAQ Specialist",
    "You answer specific questions about insurance policies and terms.",
    faq_tools
)

# Document analysis agent
doc_tools = [
    Tool(name="analyze_document", func=analyze_document, 
         description="Extract and analyze information from uploaded documents")
]
document_agent = create_specialized_agent(
    "Document Analyzer",
    "You analyze uploaded insurance documents and extract relevant information.",
    doc_tools
)

# Define the coordinator agent - this is the main router
def route_to_agent(state):
    messages = state["messages"]
    user_profile = state["user_profile"]
    last_message = messages[-1].content if messages else ""
    
    # Parse user intent with a more sophisticated prompt
    coordinator_prompt = f"""
    Analyze this user message: "{last_message}"
    
    User profile: {user_profile}
    
    Determine which specialized insurance agent should handle this request:
    1. "recommender" - If user wants policy recommendations or suggestions
    2. "comparison" - If user wants to compare specific policies side by side
    3. "web_comparison" - If user wants to compare with competitors or market options
    4. "faq" - If user is asking questions about policy terms or insurance concepts
    5. "document" - If user wants analysis of uploaded documents
    6. "profile_update" - If user is sharing personal information about themselves
    7. "feedback" - If user is providing feedback about responses
    
    Respond with ONLY ONE of these exact terms: recommender, comparison, web_comparison, faq, document, profile_update, or feedback.
    """
    
    intent = llm.invoke(coordinator_prompt).content.strip().lower()
    
    # Update selected policy if mentioned in the message
    for policy in VALID_POLICIES:
        if policy.lower() in last_message.lower():
            state["selected_policy"] = policy
    
    # Also update user profile with any detected information
    state["user_profile"] = update_user_profile(last_message, user_profile)
    
    return intent

# Define nodes for each agent
def recommender_node(state):
    messages = state["messages"]
    user_profile = state["user_profile"]
    
    # Check if we need more information
    missing_info = ask_missing_info(user_profile)
    if missing_info:
        return {"messages": [AIMessage(content=missing_info)]}
    
    # Format profile information for the agent
    profile_info = ", ".join([f"{k}: {v}" for k, v in user_profile.items() if k != "last_updated"])
    input_with_profile = f"User profile: {profile_info}\n\nQuery: {messages[-1].content}" 
    
    response = policy_recommender.invoke({"input": input_with_profile})
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
    selected_policy = state.get("selected_policy", "")
    
    # Include selected policy context if available
    input_with_context = messages[-1].content
    if selected_policy:
        input_with_context = f"Policy context: {selected_policy}\n\n{messages[-1].content}"
    
    response = faq_agent.invoke({"input": input_with_context})
    return {"messages": [AIMessage(content=response["output"])]}

def document_node(state):
    messages = state["messages"]
    uploaded_files = state.get("uploaded_files", [])
    
    # Include file list context
    file_context = "No files uploaded."
    if uploaded_files:
        file_context = f"Uploaded files: {', '.join(uploaded_files)}"
    
    input_with_context = f"{file_context}\n\n{messages[-1].content}"
    response = document_agent.invoke({"input": input_with_context})
    
    return {"messages": [AIMessage(content=response["output"])]}

def update_profile_node(state):
    messages = state["messages"]
    user_profile = state["user_profile"]
    
    # Generate profile summary
    profile_items = []
    for key, value in user_profile.items():
        if key != "last_updated":
            if isinstance(value, list):
                profile_items.append(f"- **{key.title()}**: {', '.join(value)}")
            else:
                profile_items.append(f"- **{key.title()}**: {value}")
    
    profile_summary = "\n".join(profile_items)
    
    return {
        "messages": [AIMessage(content=f"### Profile Updated\n\nThank you for providing your information. Here's what I know about you:\n\n{profile_summary}\n\nIs there anything else you'd like to share or update?")]
    }

def process_feedback_node(state):
    messages = state["messages"]
    
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
        "feedback_score": feedback_score,
        "messages": [AIMessage(content=f"Thank you for your feedback! I've recorded your satisfaction score of {feedback_score}/5. How else can I assist you today?")]
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
    
    # Return the updated state and the last response
    return result

# Example usage
if __name__ == "__main__":
    print("Insurance Chatbot initialized. Type 'exit' to quit.")
    state = None
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
            
        state = chat_with_insurance_agent(user_input, state)
        print(f"Agent: {state['messages'][-1].content}")