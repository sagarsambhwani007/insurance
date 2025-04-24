import os
from typing import List, Dict, Any
from src.config.paths import PATHS
from src.services.vector_store import add_document_to_vector_store, search_vector_store
from src.services.file_handler import list_uploaded_files

def analyze_document(query: str) -> str:
    """
    Extract and analyze information from uploaded documents.
    
    Args:
        query: The user query containing document name or analysis request
        
    Returns:
        Formatted document analysis
    """
    uploads_dir = PATHS["uploads_dir"]
    
    # Check if this is a request to analyze a specific document
    if "analyze" in query.lower() and any(doc_type in query.lower() for doc_type in ["policy", "claim", "id", "medical"]):
        # Extract document name from query if provided
        document_name = None
        uploaded_files = list_uploaded_files()
        
        for file in uploaded_files:
            if file.lower() in query.lower():
                document_name = file
                break
        
        if not document_name and uploaded_files:
            # Use the most recent file if no specific file mentioned
            document_name = uploaded_files[-1]
        
        if not document_name:
            return "❌ No documents found to analyze. Please upload a document first."
        
        # Simulate document analysis with predefined responses
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
    
    # Check if this is a request to search across documents
    elif any(term in query.lower() for term in ["search", "find", "look for", "where"]):
        # Search the vector store for relevant information
        results = search_vector_store(query)
        
        if not results:
            return "❌ No relevant information found in your documents. Try a different search query or upload more documents."
        
        # Format the search results
        result = "### Document Search Results\n\n"
        for i, item in enumerate(results, 1):
            source = item["metadata"].get("source", "Unknown document")
            result += f"**Result {i} from {source}**\n\n"
            result += f"{item['content'][:300]}...\n\n"
            result += f"*Relevance score: {item['score']:.2f}*\n\n---\n\n"
        
        return result
    
    # Otherwise, this is a request to process a new document
    else:
        # Extract document name from query
        document_name = query.strip()
        if not document_name:
            # List available documents if no specific document mentioned
            files = list_uploaded_files()
            if not files:
                return "❌ No documents found in your uploads folder. Please upload a document first."
            
            result = "### Your Uploaded Documents\n\n"
            for i, file in enumerate(files, 1):
                result += f"{i}. {file}\n"
            
            result += "\nTo analyze a document, specify its name or number."
            return result
        
        # Check if the document exists
        file_path = os.path.join(uploads_dir, document_name)
        if not os.path.exists(file_path):
            return f"❌ Document '{document_name}' not found. Please check the name or upload the document."
        
        # Process the document and add to vector store
        success = add_document_to_vector_store(file_path)
        
        if success:
            # Enhanced RAG processing
            if "analyze" in query.lower() or "search" in query.lower():
                # Search vector store with full conversation context
                results = search_vector_store(
                    query + "\n\nRelevant Documents: " + ", ".join(uploaded_files)
                )
                
                if results:
                    return format_search_results(results)
            
            # Add document to vector store when uploaded
            doc_path = os.path.join(uploads_dir, document_name)
            if os.path.exists(doc_path):
                add_document_to_vector_store(doc_path)
                return f"✅ Document '{document_name}' uploaded and indexed!"
            
            return "❌ Document processing failed"