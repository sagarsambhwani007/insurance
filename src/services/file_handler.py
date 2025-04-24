import os
import json
from typing import Dict, Any, List, Optional
from src.config.paths import PATHS

def save_json_data(data: Dict[str, Any], file_path: str) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        data: The data to save
        file_path: The path to save the data to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving data to {file_path}: {e}")
        return False

def load_json_data(file_path: str, default_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Load data from a JSON file.
    
    Args:
        file_path: The path to load the data from
        default_data: Default data to return if the file doesn't exist
        
    Returns:
        The loaded data, or default_data if the file doesn't exist
    """
    if default_data is None:
        default_data = {}
    
    if not os.path.exists(file_path):
        return default_data
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading data from {file_path}: {e}")
        return default_data

def save_uploaded_file(file_name: str, file_content: bytes) -> str:
    """
    Save an uploaded file to the uploads directory.
    
    Args:
        file_name: The name of the file
        file_content: The content of the file
        
    Returns:
        The path to the saved file
    """
    uploads_dir = PATHS["uploads_dir"]
    file_path = os.path.join(uploads_dir, file_name)
    
    try:
        with open(file_path, 'wb') as f:
            f.write(file_content)
        return file_path
    except Exception as e:
        print(f"Error saving uploaded file {file_name}: {e}")
        return ""

def list_uploaded_files() -> List[str]:
    """
    List all files in the uploads directory.
    
    Returns:
        A list of file names
    """
    uploads_dir = PATHS["uploads_dir"]
    
    try:
        return [f for f in os.listdir(uploads_dir) if os.path.isfile(os.path.join(uploads_dir, f))]
    except Exception as e:
        print(f"Error listing uploaded files: {e}")
        return []

def delete_uploaded_file(file_name: str) -> bool:
    """
    Delete an uploaded file.
    
    Args:
        file_name: The name of the file to delete
        
    Returns:
        True if successful, False otherwise
    """
    uploads_dir = PATHS["uploads_dir"]
    file_path = os.path.join(uploads_dir, file_name)
    
    if not os.path.exists(file_path):
        return False
    
    try:
        os.remove(file_path)
        return True
    except Exception as e:
        print(f"Error deleting uploaded file {file_name}: {e}")
        return False