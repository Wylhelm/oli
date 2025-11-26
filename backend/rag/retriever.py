"""
OLI Contextual Retriever
Retrieves relevant legal context for compliance analysis
"""

from dataclasses import dataclass, field
from typing import Optional
from .vector_store import LegalVectorStore


@dataclass
class RetrievalResult:
    """Result of a retrieval operation"""
    query: str
    documents: list[dict] = field(default_factory=list)
    context: str = ""
    sources: list[dict] = field(default_factory=list)
    total_score: float = 0.0


class ContextualRetriever:
    """
    Retrieves relevant legal context for OLI analysis
    
    Features:
    - Multi-collection search
    - Context assembly
    - Source tracking for citations
    """
    
    # Query templates for different check types
    QUERY_TEMPLATES = {
        "LICO": [
            "What are the LICO Low Income Cut-Off financial requirements for immigration to Canada?",
            "Minimum funds required for permanent residence application settlement funds",
            "R179 financial requirements proof of funds immigration"
        ],
        "DOCUMENT_VALIDITY": [
            "What is the validity period for immigration documents?",
            "Document expiry requirements for immigration applications",
            "How long are supporting documents valid for visa applications?"
        ],
        "IDENTITY": [
            "Identity verification requirements for immigration applications",
            "What identification documents are required for immigration?",
            "Passport and identity document requirements R52"
        ],
        "PROOF_OF_FUNDS": [
            "What proof of funds documents are accepted for immigration?",
            "Bank statements and financial documents for immigration",
            "R76 proof of funds requirements settlement"
        ],
        "GENERAL": [
            "Immigration and Refugee Protection Regulations requirements",
            "IRCC application processing requirements",
            "Federal skilled worker program eligibility"
        ]
    }
    
    def __init__(self, vector_store: Optional[LegalVectorStore] = None):
        self.vector_store = vector_store or LegalVectorStore()
    
    def retrieve(self,
                 query: str,
                 n_results: int = 5,
                 min_score: float = 0.3,
                 collections: Optional[list[str]] = None) -> RetrievalResult:
        """
        Retrieve relevant legal documents for a query
        
        Args:
            query: The search query
            n_results: Number of results per collection
            min_score: Minimum similarity score (0-1)
            collections: Specific collections to search (None = all)
        
        Returns:
            RetrievalResult with documents and assembled context
        """
        all_docs = []
        
        # Search specified collections or all
        if collections:
            for coll_name in collections:
                results = self.vector_store.search(query, coll_name, n_results)
                for r in results:
                    r["collection"] = coll_name
                all_docs.extend(results)
        else:
            all_docs = self.vector_store.search_all_collections(query, n_results * 2)
        
        # Filter by minimum score
        filtered_docs = [d for d in all_docs if d.get("score", 0) >= min_score]
        
        # Sort by score
        filtered_docs.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # Take top results
        top_docs = filtered_docs[:n_results]
        
        # Build context string
        context = self._build_context(top_docs)
        
        # Extract unique sources
        sources = self._extract_sources(top_docs)
        
        # Calculate total relevance score
        total_score = sum(d.get("score", 0) for d in top_docs) / len(top_docs) if top_docs else 0
        
        return RetrievalResult(
            query=query,
            documents=top_docs,
            context=context,
            sources=sources,
            total_score=total_score
        )
    
    def retrieve_for_check(self, 
                           check_type: str,
                           document_text: str = "",
                           n_results: int = 5) -> RetrievalResult:
        """
        Retrieve context for a specific compliance check type
        
        Args:
            check_type: Type of check (LICO, DOCUMENT_VALIDITY, etc.)
            document_text: The document being analyzed (for additional context)
            n_results: Number of results to return
        
        Returns:
            RetrievalResult with relevant legal context
        """
        # Get query templates for this check type
        queries = self.QUERY_TEMPLATES.get(check_type, self.QUERY_TEMPLATES["GENERAL"])
        
        # Combine results from all queries
        all_docs = []
        seen_ids = set()
        
        for query in queries:
            result = self.retrieve(query, n_results=3, min_score=0.2)
            for doc in result.documents:
                if doc["id"] not in seen_ids:
                    all_docs.append(doc)
                    seen_ids.add(doc["id"])
        
        # If we have document text, also search for specific terms
        if document_text:
            # Extract key terms from document
            key_terms = self._extract_key_terms(document_text)
            if key_terms:
                term_result = self.retrieve(key_terms, n_results=2, min_score=0.3)
                for doc in term_result.documents:
                    if doc["id"] not in seen_ids:
                        all_docs.append(doc)
                        seen_ids.add(doc["id"])
        
        # Sort and limit
        all_docs.sort(key=lambda x: x.get("score", 0), reverse=True)
        top_docs = all_docs[:n_results]
        
        # Build result
        context = self._build_context(top_docs)
        sources = self._extract_sources(top_docs)
        total_score = sum(d.get("score", 0) for d in top_docs) / len(top_docs) if top_docs else 0
        
        return RetrievalResult(
            query=f"[{check_type}] compliance check",
            documents=top_docs,
            context=context,
            sources=sources,
            total_score=total_score
        )
    
    def retrieve_comprehensive(self,
                               document_text: str,
                               check_types: list[str] = None) -> dict[str, RetrievalResult]:
        """
        Retrieve context for multiple check types at once
        
        Args:
            document_text: The document being analyzed
            check_types: List of check types (None = all)
        
        Returns:
            Dict mapping check_type to RetrievalResult
        """
        if check_types is None:
            check_types = ["LICO", "DOCUMENT_VALIDITY", "IDENTITY", "PROOF_OF_FUNDS"]
        
        results = {}
        for check_type in check_types:
            results[check_type] = self.retrieve_for_check(
                check_type, 
                document_text,
                n_results=3
            )
        
        return results
    
    def _build_context(self, docs: list[dict]) -> str:
        """Build a context string from retrieved documents"""
        if not docs:
            return "No relevant legal context found."
        
        context_parts = []
        
        for i, doc in enumerate(docs, 1):
            metadata = doc.get("metadata", {})
            title = metadata.get("doc_title", "Unknown Document")
            section = metadata.get("section", "")
            url = metadata.get("html_url", "")
            
            header = f"[Source {i}: {title}"
            if section:
                header += f" - Section {section}"
            header += "]"
            
            text = doc.get("text", "")
            
            context_parts.append(f"{header}\n{text}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def _extract_sources(self, docs: list[dict]) -> list[dict]:
        """Extract unique source citations from documents with summaries"""
        sources = {}
        
        for doc in docs:
            metadata = doc.get("metadata", {})
            url = metadata.get("html_url", "")
            text = doc.get("text", "")
            
            if url and url not in sources:
                # Create a summary from the text (first 300 chars)
                summary = text[:300].strip()
                if len(text) > 300:
                    # Try to cut at a sentence or word boundary
                    last_period = summary.rfind('.')
                    last_space = summary.rfind(' ')
                    cut_point = max(last_period, last_space)
                    if cut_point > 100:
                        summary = summary[:cut_point + 1]
                    summary += "..."
                
                sources[url] = {
                    "title": metadata.get("doc_title", ""),
                    "url": url,
                    "doc_type": metadata.get("doc_type", ""),
                    "section": metadata.get("section", ""),
                    "summary": summary,
                    "relevance": doc.get("score", 0)
                }
            elif url in sources:
                # Append additional text if same source found multiple times
                existing = sources[url]
                if existing.get("summary", "") and text:
                    # Only add if significantly different
                    if text[:50] not in existing["summary"]:
                        additional = text[:150].strip()
                        if len(additional) > 50:
                            existing["summary"] += f" | {additional}..."
        
        return list(sources.values())
    
    def _extract_key_terms(self, text: str, max_terms: int = 50) -> str:
        """Extract key terms from document text for search"""
        import re
        
        # Keywords that indicate important terms
        important_patterns = [
            r'\b(LICO|R\d+|Article\s+\d+)\b',
            r'\b(proof of funds|settlement funds|financial)\b',
            r'\b(permanent residen\w+|temporary residen\w+)\b',
            r'\b(work permit|study permit|visa)\b',
            r'\b\d{1,3}[,\s]?\d{3}\s?\$\b',  # Money amounts
        ]
        
        terms = []
        for pattern in important_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            terms.extend(matches)
        
        # Deduplicate and limit
        unique_terms = list(dict.fromkeys(terms))[:max_terms]
        
        return " ".join(unique_terms)


# Quick test function
def test_retriever():
    """Test the retriever with sample queries"""
    print("🔍 Testing OLI Contextual Retriever")
    print("=" * 50)
    
    retriever = ContextualRetriever()
    
    # Test queries
    queries = [
        "What are the minimum funds required for immigration?",
        "LICO threshold for single person",
        "Document validity period for immigration",
    ]
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        result = retriever.retrieve(query, n_results=3)
        
        print(f"   Found: {len(result.documents)} documents")
        print(f"   Total score: {result.total_score:.2f}")
        
        for doc in result.documents[:2]:
            title = doc.get("metadata", {}).get("doc_title", "Unknown")[:40]
            score = doc.get("score", 0)
            print(f"   - {title}... (score: {score:.2f})")
    
    # Test check-specific retrieval
    print("\n" + "=" * 50)
    print("📋 Testing check-specific retrieval")
    
    result = retriever.retrieve_for_check("LICO")
    print(f"\nLICO check context preview:")
    print(result.context[:500] + "...")
    print(f"\nSources: {len(result.sources)}")
    for src in result.sources:
        print(f"  - {src['title'][:50]}")


if __name__ == "__main__":
    test_retriever()

