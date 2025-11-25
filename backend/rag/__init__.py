# OLI RAG Module
# Retrieval-Augmented Generation for Canadian Legal Documents

from .vector_store import LegalVectorStore
from .retriever import ContextualRetriever

__all__ = ["LegalVectorStore", "ContextualRetriever"]

