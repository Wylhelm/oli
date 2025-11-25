"""
Test script for OLI RAG System
Tests the vector store and retriever with sample queries
"""

import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from pathlib import Path

# Get the backend directory
BACKEND_DIR = Path(__file__).parent.absolute()
CHROMA_DB_PATH = BACKEND_DIR / "data" / "chroma_db"

from rag.vector_store import LegalVectorStore
from rag.retriever import ContextualRetriever


def test_vector_store():
    """Test basic vector store operations"""
    print("=" * 60)
    print("🔍 Testing OLI Vector Store")
    print("=" * 60)
    
    print(f"\n📂 Using ChromaDB path: {CHROMA_DB_PATH}")
    store = LegalVectorStore(persist_directory=str(CHROMA_DB_PATH))
    stats = store.get_stats()
    
    print("\n📊 Vector Store Statistics:")
    for collection, data in stats.items():
        print(f"   {collection}: {data['count']} documents")
    
    return store


def test_retriever(store: LegalVectorStore):
    """Test the retriever with various queries"""
    print("\n" + "=" * 60)
    print("🔎 Testing OLI Contextual Retriever")
    print("=" * 60)
    
    retriever = ContextualRetriever(vector_store=store)
    
    # Test queries related to LICO and financial requirements
    test_queries = [
        "What are the minimum funds required for permanent residence?",
        "LICO low income cut off financial requirements",
        "proof of funds settlement funds immigration",
        "R179 financial requirement",
        "document validity period immigration application",
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        result = retriever.retrieve(query, n_results=3, min_score=0.2)
        
        print(f"   Found: {len(result.documents)} documents")
        print(f"   Avg score: {result.total_score:.3f}")
        
        for doc in result.documents[:2]:
            title = doc.get("metadata", {}).get("doc_title", "Unknown")[:50]
            section = doc.get("metadata", {}).get("section", "")
            score = doc.get("score", 0)
            print(f"   ├─ {title}...")
            print(f"   │  Section: {section}, Score: {score:.3f}")
    
    # Test check-specific retrieval
    print("\n" + "=" * 60)
    print("📋 Testing Check-Specific Retrieval")
    print("=" * 60)
    
    check_types = ["LICO", "DOCUMENT_VALIDITY", "IDENTITY", "PROOF_OF_FUNDS"]
    
    for check_type in check_types:
        result = retriever.retrieve_for_check(check_type)
        print(f"\n🏷️ {check_type}:")
        print(f"   Documents: {len(result.documents)}")
        print(f"   Sources: {len(result.sources)}")
        if result.sources:
            print(f"   First source: {result.sources[0].get('title', 'N/A')[:60]}...")
        
        # Show a snippet of the context
        context_preview = result.context[:200].replace('\n', ' ')
        print(f"   Context preview: {context_preview}...")


def test_specific_lico_query(store: LegalVectorStore):
    """Test a specific query about LICO to see actual content"""
    print("\n" + "=" * 60)
    print("💰 Testing LICO-Specific Search")
    print("=" * 60)
    
    retriever = ContextualRetriever(vector_store=store)
    
    # Search for LICO/funds requirements
    result = retriever.retrieve(
        "minimum necessary income funds settlement permanent resident", 
        n_results=5,
        min_score=0.25
    )
    
    print(f"\n📄 Found {len(result.documents)} relevant chunks\n")
    
    for i, doc in enumerate(result.documents, 1):
        metadata = doc.get("metadata", {})
        print(f"--- Result {i} (Score: {doc.get('score', 0):.3f}) ---")
        print(f"Document: {metadata.get('doc_title', 'N/A')}")
        print(f"Section: {metadata.get('section', 'N/A')}")
        print(f"URL: {metadata.get('html_url', 'N/A')}")
        print(f"Content preview:")
        content = doc.get("text", "")[:500]
        print(f"  {content}...")
        print()


if __name__ == "__main__":
    print("\n" + "🍁" * 30)
    print("  OLI RAG System Test Suite")
    print("🍁" * 30 + "\n")
    
    # Run tests
    store = test_vector_store()
    test_retriever(store)
    test_specific_lico_query(store)
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

