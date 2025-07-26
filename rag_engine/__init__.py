"""RAG Engine for PDF Extractor.

This package provides Retrieval Augmented Generation (RAG) capabilities
for technical documentation, specifically designed for IoT device manuals
and AT command documentation.
"""

from .chunking import DocumentChunker
from .embeddings import EmbeddingGenerator
from .vector_store import VectorStore
from .llm_integration import LLMIntegration
from .retrieval import RAGEngine

__all__ = [
    "DocumentChunker",
    "EmbeddingGenerator", 
    "VectorStore",
    "LLMIntegration",
    "RAGEngine",
]

__version__ = "1.0.0" 