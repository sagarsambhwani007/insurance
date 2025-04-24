import re
from typing import Dict, Any
from datetime import datetime
from src.config.constants import INSURANCE_TYPES

def update_user_profile(message: str, current_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update user profile based on message content using regex patterns.
    
    Args:
        message: The user message to extract information from
        current_profile: The current user profile dictionary
        
    Returns:
        Updated user profile dictionary
    """
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
    for insurance in INSURANCE_TYPES:
        if insurance in message.lower():
            if "interests" not in new_profile:
                new_profile["interests"] = []
            if insurance not in new_profile["interests"]:
                new_profile["interests"].append(insurance)
    
    # Add timestamp for the update
    new_profile["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return new_profile

def ask_missing_info(profile: Dict[str, Any]) -> str:
    """
    Generate prompts for missing user information.
    
    Args:
        profile: The user profile to check for missing information
        
    Returns:
        A prompt asking for missing information, or None if no information is missing
    """
    questions = []
    if "age" not in profile: questions.append("your age")
    if "income" not in profile: questions.append("your income")
    if "goal" not in profile: questions.append("your financial goal")
    
    if questions:
        return "🧠 To provide better recommendations, please share: " + ", ".join(questions)
    return None

def format_profile_summary(profile: Dict[str, Any]) -> str:
    """
    Format the user profile as a readable summary.
    
    Args:
        profile: The user profile to format
        
    Returns:
        A formatted string representation of the profile
    """
    profile_items = []
    for key, value in profile.items():
        if key != "last_updated":
            if isinstance(value, list):
                profile_items.append(f"- **{key.title()}**: {', '.join(value)}")
            else:
                profile_items.append(f"- **{key.title()}**: {value}")
    
    return "\n".join(profile_items)