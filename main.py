#!/usr/bin/env python3
"""
Insurance Chatbot - A modular conversational agent for insurance inquiries.
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.interfaces.cli import run_cli_interface

def main():
    """
    Main entry point for the insurance chatbot application.
    """
    run_cli_interface()

if __name__ == "__main__":
    main()