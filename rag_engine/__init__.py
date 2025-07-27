"""RAG Engine for PDF Extractor.

This package provides Retrieval Augmented Generation (RAG) capabilities
for PDF documents, enabling efficient search and retrieval of information
from various types of technical documentation.
"""

from .chunking import DocumentChunker
from .embeddings import EmbeddingGenerator
from .llm_integration import LLMIntegration
from .retrieval import RAGEngine
from .vector_store import VectorStore

__all__ = [
    "DocumentChunker",
    "EmbeddingGenerator",
    "VectorStore",
    "LLMIntegration",
    "RAGEngine",
]

__version__ = "1.0.0"
