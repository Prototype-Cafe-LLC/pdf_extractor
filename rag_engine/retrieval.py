"""RAG retrieval pipeline for technical documentation.

This module provides the main RAG pipeline that combines document chunking,
embedding generation, vector storage, and LLM integration.
"""

import logging
from pathlib import Path
from typing import Any

from .chunking import DocumentChunker
from .embeddings import EmbeddingGenerator
from .llm_integration import LLMIntegration, LLMResponse
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class RAGEngine:
    """Complete RAG pipeline for technical documentation."""

    def __init__(self, config: dict[str, Any]):
        """Initialize the RAG engine.

        Args:
            config: Configuration dictionary
        """
        self.config = config

        # Initialize components
        self.chunker = DocumentChunker(
            max_tokens=config.get("chunk_size", 512), overlap_tokens=config.get("chunk_overlap", 50)
        )

        self.embedder = EmbeddingGenerator(
            model_name=config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
        )

        self.vector_store = VectorStore(
            db_path=config.get("vector_db_path", "./data/vector_db"),
            collection_name=config.get("collection_name", "technical_docs"),
        )

        self.llm = LLMIntegration(
            model_type=config.get("llm_type", "openai"),
            model_name=config.get("llm_model", "gpt-4"),
            lazy_init=True,  # Delay initialization until first query
        )

        logger.info("RAG Engine initialized successfully")

    def process_document(self, markdown_content: str, metadata: dict[str, Any]) -> bool:
        """Process a document through the RAG pipeline.

        Args:
            markdown_content: Markdown content of the document
            metadata: Document metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Processing document: {metadata.get('document', 'unknown')}")

            # Step 1: Chunk the document
            chunks = self.chunker.chunk_by_sections(markdown_content, metadata)
            logger.debug(f"Created {len(chunks)} chunks")

            if not chunks:
                logger.warning("No chunks created from document")
                return False

            # Step 2: Generate embeddings
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = self.embedder.generate_embeddings(chunk_texts)
            logger.debug(f"Generated embeddings: {embeddings.shape}")

            # Step 3: Prepare metadata for vector store
            chunk_metadata = [chunk.metadata for chunk in chunks]

            # Step 4: Store in vector database
            success = self.vector_store.store_embeddings(chunk_texts, embeddings, chunk_metadata)

            if success:
                logger.info(f"Successfully processed document with {len(chunks)} chunks")
            else:
                logger.error("Failed to store embeddings in vector database")

            return success

        except Exception as e:
            logger.error(f"Failed to process document: {e}")
            return False

    def query(
        self, question: str, top_k: int = 5, filter_dict: dict[str, Any] | None = None
    ) -> LLMResponse:
        """Query the knowledge base with a question.

        Args:
            question: User question
            top_k: Number of relevant chunks to retrieve
            filter_dict: Optional metadata filters

        Returns:
            LLMResponse with answer and metadata
        """
        try:
            logger.info(f"Processing query: {question}")

            # Step 1: Retrieve relevant chunks
            relevant_chunks, sources = self.vector_store.search(question, top_k, filter_dict)

            if not relevant_chunks:
                logger.warning("No relevant chunks found for query")
                return LLMResponse(
                    answer="I couldn't find any relevant information in the knowledge base for your question.",
                    sources=[],
                    confidence=0.0,
                    model_used=self.llm.model_name,
                )

            logger.debug(f"Retrieved {len(relevant_chunks)} relevant chunks")

            # Step 2: Generate LLM response
            response = self.llm.generate_response(question, relevant_chunks, sources)

            logger.info(f"Generated response with confidence: {response.confidence:.2f}")
            return response

        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            return LLMResponse(
                answer=f"Error processing your question: {str(e)}",
                sources=[],
                confidence=0.0,
                model_used=self.llm.model_name,
            )

    def add_pdf_document(self, pdf_path: Path, document_type: str = "unknown") -> bool:
        """Add a PDF document to the knowledge base.

        Args:
            pdf_path: Path to the PDF file
            document_type: Type of document

        Returns:
            True if successful, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from pdf_extractor import process_pdf_file

            # Convert PDF to markdown
            output_path = Path("md") / f"{pdf_path.stem}.md"
            success, error = process_pdf_file(pdf_path, output_path)

            if not success:
                logger.error(f"Failed to convert PDF: {error}")
                return False

            # Read markdown content
            markdown_content = output_path.read_text(encoding="utf-8")

            # Prepare metadata
            metadata = {
                "document": pdf_path.name,
                "type": document_type,
                "source": str(pdf_path),
                "file_path": str(output_path),
            }

            # Process through RAG pipeline
            return self.process_document(markdown_content, metadata)

        except Exception as e:
            logger.error(f"Failed to add PDF document: {e}")
            return False

    def list_documents(self) -> list[dict[str, Any]]:
        """List all documents in the knowledge base.

        Returns:
            List of document metadata
        """
        return self.vector_store.list_documents()

    def delete_document(self, document_name: str) -> bool:
        """Delete a document from the knowledge base.

        Args:
            document_name: Name of the document to delete

        Returns:
            True if successful, False otherwise
        """
        return self.vector_store.delete_document(document_name)

    def get_system_info(self) -> dict[str, Any]:
        """Get system information about all components.

        Returns:
            Dictionary with system information
        """
        return {
            "rag_engine": {"version": "1.0.0", "config": self.config},
            "embedding_model": self.embedder.get_model_info(),
            "llm_model": self.llm.get_model_info(),
            "vector_store": self.vector_store.get_collection_info(),
        }

    def test_components(self) -> dict[str, bool]:
        """Test all RAG components.

        Returns:
            Dictionary with test results for each component
        """
        results = {}

        # Test embedding model
        try:
            test_embedding = self.embedder.generate_embedding("test")
            results["embedding_model"] = test_embedding is not None
        except Exception as e:
            logger.error(f"Embedding model test failed: {e}")
            results["embedding_model"] = False

        # Test LLM
        try:
            results["llm"] = self.llm.test_connection()
        except Exception as e:
            logger.error(f"LLM test failed: {e}")
            results["llm"] = False

        # Test vector store
        try:
            info = self.vector_store.get_collection_info()
            results["vector_store"] = "error" not in info
        except Exception as e:
            logger.error(f"Vector store test failed: {e}")
            results["vector_store"] = False

        return results
