import os
from typing import List
from src.config.paths import PATHS
from src.services.vector_store import add_document_to_vector_store

def process_docs_directory() -> List[str]:
    """
    Process all PDF documents in the docs directory and add them to the vector store.
    
    Returns:
        List of processed document names
    """
    # Create docs directory path
    docs_dir = os.path.join(PATHS["root_dir"], "docs")
    os.makedirs(docs_dir, exist_ok=True)
    
    processed_docs = []
    
    # Check if directory exists
    if not os.path.exists(docs_dir):
        print(f"Docs directory not found at {docs_dir}")
        return processed_docs
    
    # Process all PDF files in the directory
    for filename in os.listdir(docs_dir):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(docs_dir, filename)
            print(f"Processing document: {filename}")
            
            # Add document to vector store
            success = add_document_to_vector_store(file_path)
            
            if success:
                processed_docs.append(filename)
                print(f"Successfully processed {filename}")
            else:
                print(f"Failed to process {filename}")
    
    return processed_docs