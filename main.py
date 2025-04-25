#!/usr/bin/env python3
"""
Insurance Chatbot - A modular conversational agent for insurance inquiries.
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.interfaces.cli import run_cli_interface
from src.services.document_processor import process_docs_directory

def main():
    """
    Main entry point for the insurance chatbot application.
    """
    # Process documents in the docs directory
    print("Initializing document processing...")
    processed_docs = process_docs_directory()
    if processed_docs:
        print(f"Processed {len(processed_docs)} documents: {', '.join(processed_docs)}")
    else:
        print("No documents were processed. Add PDF files to the 'docs' directory.")
    
    # Run the CLI interface
    run_cli_interface()

if __name__ == "__main__":
    main()