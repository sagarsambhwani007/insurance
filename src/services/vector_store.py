import os
from typing import List, Dict, Any, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from src.config.paths import PATHS
from src.config.constants import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP

def get_file_loader(file_path: str):
    """
    Get the appropriate document loader based on file extension.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        A document loader instance
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == '.pdf':
        return PyPDFLoader(file_path)
    elif file_extension in ['.txt', '.md', '.json']:
        return TextLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

def chunk_document(file_path: str, chunk_size: int = DEFAULT_CHUNK_SIZE, 
                  chunk_overlap: int = DEFAULT_CHUNK_OVERLAP) -> List[Dict[str, Any]]:
    """
    Load and chunk a document into smaller pieces.
    
    Args:
        file_path: Path to the document file
        chunk_size: Size of each chunk in characters
        chunk_overlap: Overlap between chunks in characters
        
    Returns:
        List of document chunks
    """
    try:
        # Get appropriate loader
        loader = get_file_loader(file_path)
        
        # Load the document
        documents = loader.load()
        
        # Create text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        
        # Split the documents
        chunks = text_splitter.split_documents(documents)
        
        # Add source filename metadata if not present
        for chunk in chunks:
            if 'source' not in chunk.metadata:
                chunk.metadata['source'] = os.path.basename(file_path)
        
        return chunks
    
    except Exception as e:
        print(f"Error chunking document {file_path}: {e}")
        return []

def get_vector_store(collection_name: Optional[str] = None):
    """
    Get or create a Chroma vector store.
    
    Args:
        collection_name: Optional name for the collection
        
    Returns:
        A Chroma vector store instance
    """
    chroma_dir = PATHS["chroma_dir"]
    embeddings = OpenAIEmbeddings()
    
    # Use default collection name if none provided
    if collection_name is None:
        collection_name = "insurance_documents"
    
    # Create or get the vector store
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=chroma_dir
    )

def add_document_to_vector_store(file_path: str, collection_name: Optional[str] = None) -> bool:
    """
    Process a document and add it to the vector store.
    
    Args:
        file_path: Path to the document file
        collection_name: Optional name for the collection
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Chunk the document
        chunks = chunk_document(file_path)
        
        if not chunks:
            return False
        
        # Get the vector store
        vector_store = get_vector_store(collection_name)
        
        # Add the chunks to the vector store
        vector_store.add_documents(chunks)
        
        # Persist the vector store
        vector_store.persist()
        
        return True
    
    except Exception as e:
        print(f"Error adding document to vector store: {e}")
        return False

def search_vector_store(query: str, collection_name: Optional[str] = None, 
                       k: int = 5) -> List[Dict[str, Any]]:
    """
    Search the vector store for relevant documents.
    
    Args:
        query: The search query
        collection_name: Optional name for the collection
        k: Number of results to return
        
    Returns:
        List of relevant document chunks with scores
    """
    try:
        # Get the vector store
        vector_store = get_vector_store(collection_name)
        
        # Search the vector store
        results = vector_store.similarity_search_with_relevance_scores(query, k=k)
        
        # Format the results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            })
        
        return formatted_results
    
    except Exception as e:
        print(f"Error searching vector store: {e}")
        return []