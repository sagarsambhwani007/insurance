import os

def get_project_paths():
    """
    Get dynamic paths for the insurance chatbot project.
    Creates necessary directories if they don't exist.
    """
    # Get the root directory (2 levels up from this file)
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Define data directory
    data_dir = os.path.join(root_dir, "data", "insurance_chatbot")
    os.makedirs(data_dir, exist_ok=True)
    
    paths = {
        "root_dir": root_dir,
        "data_dir": data_dir,
        "policies_file": os.path.join(data_dir, "policies.json"),
        "comparisons_file": os.path.join(data_dir, "comparisons.json"),
        "competitors_file": os.path.join(data_dir, "competitors.json"),
        "faqs_file": os.path.join(data_dir, "faqs.json"),
        "uploads_dir": os.path.join(data_dir, "uploads"),
        "chroma_dir": os.path.join(data_dir, "insurance_vector_db")
    }
    
    # Create uploads directory if it doesn't exist
    os.makedirs(paths["uploads_dir"], exist_ok=True)
    
    return paths

# Export paths for easy access
PATHS = get_project_paths()