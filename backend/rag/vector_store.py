"""
OLI Vector Store
ChromaDB-based vector store for Canadian legal documents

Uses sentence-transformers for embeddings (no API key required for MVP)
Can be upgraded to Azure OpenAI embeddings for production
"""

import chromadb
from chromadb.config import Settings
from pathlib import Path
from typing import Optional
import json
import re

# Use sentence-transformers for local embeddings (no API key needed)
from chromadb.utils import embedding_functions


class LegalVectorStore:
    """
    Vector store for Canadian legal documents using ChromaDB
    
    Supports:
    - Local persistence
    - Semantic search
    - Metadata filtering
    - Multiple collections (by domain)
    """
    
    # Embedding model - multilingual for FR/EN support
    EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
    
    # Default paths (relative to backend folder)
    DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "chroma_db"
    
    def __init__(self, persist_directory: str = None):
        if persist_directory is None:
            self.persist_directory = self.DEFAULT_DB_PATH
        else:
            self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        
        # Use sentence-transformers embedding function
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.EMBEDDING_MODEL
        )
        
        # Initialize collections
        self.collections = {}
        self._init_collections()
    
    def _init_collections(self):
        """Initialize or load collections"""
        collection_names = [
            "immigration_acts",      # Main immigration acts
            "immigration_regs",      # Immigration regulations (RIPR, etc.)
            "general_legal",         # General legal provisions
        ]
        
        for name in collection_names:
            self.collections[name] = self.client.get_or_create_collection(
                name=name,
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
    
    def get_collection(self, name: str):
        """Get a collection by name"""
        if name not in self.collections:
            self.collections[name] = self.client.get_or_create_collection(
                name=name,
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"}
            )
        return self.collections[name]
    
    def add_documents(self, 
                      collection_name: str,
                      documents: list[dict],
                      batch_size: int = 100) -> int:
        """
        Add documents to a collection
        
        Args:
            collection_name: Name of the collection
            documents: List of dicts with 'id', 'text', 'metadata' keys
            batch_size: Number of documents to add at once
        
        Returns:
            Number of documents added
        """
        collection = self.get_collection(collection_name)
        total_added = 0
        
        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            ids = [d["id"] for d in batch]
            texts = [d["text"] for d in batch]
            metadatas = [d.get("metadata", {}) for d in batch]
            
            # Filter out empty texts
            valid_indices = [j for j, t in enumerate(texts) if t and len(t.strip()) > 10]
            
            if valid_indices:
                collection.add(
                    ids=[ids[j] for j in valid_indices],
                    documents=[texts[j] for j in valid_indices],
                    metadatas=[metadatas[j] for j in valid_indices]
                )
                total_added += len(valid_indices)
        
        return total_added
    
    def search(self,
               query: str,
               collection_name: str = "immigration_regs",
               n_results: int = 5,
               where: Optional[dict] = None,
               where_document: Optional[dict] = None) -> list[dict]:
        """
        Semantic search in a collection
        
        Args:
            query: Search query
            collection_name: Collection to search in
            n_results: Number of results to return
            where: Metadata filter (e.g., {"doc_type": "Regulation"})
            where_document: Document content filter
        
        Returns:
            List of matching documents with scores
        """
        collection = self.get_collection(collection_name)
        
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                formatted.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    "score": 1 - results["distances"][0][i] if results["distances"] else 1
                })
        
        return formatted
    
    def search_all_collections(self,
                               query: str,
                               n_results: int = 5) -> list[dict]:
        """
        Search across all collections and merge results
        """
        all_results = []
        
        for name in self.collections:
            results = self.search(query, name, n_results)
            for r in results:
                r["collection"] = name
            all_results.extend(results)
        
        # Sort by score (descending)
        all_results.sort(key=lambda x: x["score"], reverse=True)
        
        return all_results[:n_results]
    
    def get_stats(self) -> dict:
        """Get statistics about the vector store"""
        stats = {}
        for name, collection in self.collections.items():
            stats[name] = {
                "count": collection.count(),
                "name": name
            }
        return stats
    
    def delete_collection(self, name: str):
        """Delete a collection"""
        if name in self.collections:
            self.client.delete_collection(name)
            del self.collections[name]
    
    def clear_all(self):
        """Clear all collections (dangerous!)"""
        for name in list(self.collections.keys()):
            self.delete_collection(name)
        self._init_collections()


class LegalDocumentChunker:
    """
    Chunks legal documents for vector storage
    
    Preserves:
    - Section references (R179, Article 52, etc.)
    - Context with overlap
    - Metadata
    """
    
    CHUNK_SIZE = 1000  # characters
    CHUNK_OVERLAP = 200
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_document(self, doc_data: dict) -> list[dict]:
        """
        Chunk a legal document into smaller pieces
        
        Args:
            doc_data: Document dict with 'content', 'title', 'unique_id', etc.
        
        Returns:
            List of chunks with metadata
        """
        content = doc_data.get("content", "")
        if not content:
            return []
        
        chunks = []
        
        # Split by paragraphs first
        paragraphs = content.split("\n\n")
        
        current_chunk = ""
        current_section = "General"
        chunk_index = 0
        
        for para in paragraphs:
            # Detect section references
            section_match = re.search(
                r'\[([^\]]+)\]|(?:Section|Article|R)\s*(\d+)',
                para,
                re.IGNORECASE
            )
            if section_match:
                current_section = section_match.group(1) or section_match.group(2)
            
            # Add to current chunk
            if len(current_chunk) + len(para) < self.chunk_size:
                current_chunk += para + "\n\n"
            else:
                # Save current chunk
                if current_chunk.strip():
                    chunks.append(self._create_chunk(
                        doc_data, current_chunk, current_section, chunk_index
                    ))
                    chunk_index += 1
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                current_chunk = overlap_text + para + "\n\n"
        
        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(self._create_chunk(
                doc_data, current_chunk, current_section, chunk_index
            ))
        
        return chunks
    
    def _create_chunk(self, doc_data: dict, text: str, section: str, index: int) -> dict:
        """Create a chunk dict with metadata"""
        doc_id = doc_data.get("unique_id", "unknown")
        
        return {
            "id": f"{doc_id}_chunk_{index}",
            "text": text.strip(),
            "metadata": {
                "doc_id": doc_id,
                "doc_title": doc_data.get("title", ""),
                "doc_type": doc_data.get("doc_type", ""),
                "section": section,
                "chunk_index": index,
                "html_url": doc_data.get("html_url", ""),
                "current_to_date": doc_data.get("current_to_date", "")
            }
        }
    
    def chunk_from_file(self, filepath: Path) -> list[dict]:
        """Load and chunk a document from a JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            doc_data = json.load(f)
        return self.chunk_document(doc_data)


def ingest_laws_to_vectorstore(
    laws_dir: str = "backend/data/laws",
    db_path: str = "backend/data/chroma_db"
) -> dict:
    """
    Ingest all downloaded laws into the vector store
    
    Returns:
        Statistics about ingestion
    """
    import sys
    import io
    
    # Fix Windows console encoding
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    laws_path = Path(laws_dir)
    
    if not laws_path.exists():
        print(f"❌ Laws directory not found: {laws_dir}")
        print("   Run the downloader first: python backend/rag/downloader.py")
        return {"error": "Laws directory not found"}
    
    # Initialize components
    vector_store = LegalVectorStore(persist_directory=db_path)
    chunker = LegalDocumentChunker()
    
    # Find all JSON files (except summary)
    json_files = [f for f in laws_path.glob("*.json") if not f.name.startswith("_")]
    
    print(f"📚 Found {len(json_files)} documents to ingest")
    
    stats = {
        "acts": {"files": 0, "chunks": 0},
        "regulations": {"files": 0, "chunks": 0}
    }
    
    for i, filepath in enumerate(json_files, 1):
        print(f"[{i}/{len(json_files)}] Processing: {filepath.name[:50]}...")
        
        try:
            # Load and chunk document
            chunks = chunker.chunk_from_file(filepath)
            
            if not chunks:
                print(f"  ⚠️ No content to chunk")
                continue
            
            # Determine collection based on doc type
            doc_type = chunks[0]["metadata"].get("doc_type", "").lower()
            if "act" in doc_type:
                collection = "immigration_acts"
                stats["acts"]["files"] += 1
                stats["acts"]["chunks"] += len(chunks)
            else:
                collection = "immigration_regs"
                stats["regulations"]["files"] += 1
                stats["regulations"]["chunks"] += len(chunks)
            
            # Add to vector store
            added = vector_store.add_documents(collection, chunks)
            print(f"  ✅ Added {added} chunks to {collection}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Print stats
    print("\n" + "=" * 50)
    print("📊 Ingestion Complete!")
    print(f"   Acts: {stats['acts']['files']} files, {stats['acts']['chunks']} chunks")
    print(f"   Regulations: {stats['regulations']['files']} files, {stats['regulations']['chunks']} chunks")
    print(f"   Vector store: {db_path}")
    print("=" * 50)
    
    return stats


if __name__ == "__main__":
    # Run ingestion when called directly
    ingest_laws_to_vectorstore()

