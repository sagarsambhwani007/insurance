import os
import json
from src.config.paths import PATHS
from src.config.constants import INSURANCE_TYPES

def recommend_policy(query: str) -> str:
    """
    Recommend insurance policies based on user profile and query.
    
    Args:
        query: The user query to extract policy type from
        
    Returns:
        Formatted policy recommendations
    """
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

def answer_faq(query: str) -> str:
    """
    Answer FAQs about insurance policies with improved formatting.
    
    Args:
        query: The user query to match against FAQs
        
    Returns:
        Formatted FAQ answer
    """
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