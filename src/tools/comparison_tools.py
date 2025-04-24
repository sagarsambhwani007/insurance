import os
import json
import re
from src.config.paths import PATHS
from src.config.constants import VALID_POLICIES

def compare_policies(query: str) -> str:
    """
    Compare multiple insurance policies with tabular format.
    
    Args:
        query: The user query containing policies to compare
        
    Returns:
        Formatted policy comparison
    """
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
    """
    Compare with external market options.
    
    Args:
        query: The user query to extract policy type from
        
    Returns:
        Formatted market comparison
    """
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