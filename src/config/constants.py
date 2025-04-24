# Define valid policies
VALID_POLICIES = [
    "Basic Health", "Premium Health", "Family Health",
    "Liability Only", "Comprehensive", "Premium Coverage",
    "Basic Home", "Standard Home", "Premium Home",
    "Term Life", "Whole Life", "Universal Life"
]

# LLM model name
DEFAULT_MODEL = "gpt-4"

# Agent types
AGENT_TYPES = [
    "recommender", 
    "comparison", 
    "web_comparison", 
    "faq", 
    "document", 
    "profile_update", 
    "feedback"
]

# Insurance types
INSURANCE_TYPES = ["health", "auto", "home", "life"]

# Document chunking defaults
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200