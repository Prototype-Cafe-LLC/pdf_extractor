"""Vector database operations using ChromaDB.

This module provides vector database functionality for storing and retrieving
document embeddings with metadata.
"""

import hashlib
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any

import chromadb
import numpy as np
from chromadb.config import Settings

logger = logging.getLogger(__name__)

# Constants
CHROMADB_BATCH_LIMIT = 1000  # ChromaDB's documented limit for get/delete operations


class VectorStore:
    """Vector database for storing and retrieving document embeddings."""

    def __init__(self, db_path: str = "./data/vector_db", collection_name: str = "technical_docs"):
        """Initialize the vector store.

        Args:
            db_path: Path to the vector database
            collection_name: Name of the collection to use
        """
        self.db_path = Path(db_path)
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self._initialize_db()

    def _initialize_db(self):
        """Initialize ChromaDB client and collection."""
        try:
            logger.info(f"Initializing ChromaDB at {self.db_path}")
            self.db_path.mkdir(parents=True, exist_ok=True)

            self.client = chromadb.PersistentClient(
                path=str(self.db_path),
                settings=Settings(anonymized_telemetry=False, allow_reset=True),
            )

            # Get or create collection
            try:
                self.collection = self.client.get_collection(self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except Exception:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Technical documentation embeddings"},
                )
                logger.info(f"Created new collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")
            raise

    def store_embeddings(
        self, chunks: list[str], embeddings: np.ndarray, metadata: list[dict[str, Any]]
    ) -> bool:
        """Store document chunks with their embeddings and metadata.

        Args:
            chunks: List of text chunks
            embeddings: Numpy array of embeddings
            metadata: List of metadata dictionaries for each chunk

        Returns:
            True if successful, False otherwise
        """
        try:
            if len(chunks) != len(embeddings) or len(chunks) != len(metadata):
                raise ValueError("Chunks, embeddings, and metadata must have the same length")

            # Convert embeddings to list format for ChromaDB
            if hasattr(embeddings, "tolist"):
                embedding_list = embeddings.tolist()
            else:
                embedding_list = embeddings

            # Use the chunk_id from metadata which already includes document name
            chunk_ids = []
            for i, meta in enumerate(metadata):
                if "chunk_id" in meta and isinstance(meta["chunk_id"], str):
                    # Use the pre-generated chunk_id which includes document name
                    chunk_ids.append(meta["chunk_id"])
                else:
                    # Fallback: generate a unique ID
                    chunk_id = self._generate_chunk_id(
                        document_path=meta.get("source", meta.get("document", "unknown")),
                        chunk_index=i,
                        chunk_content=chunks[i][:100],
                    )
                    chunk_ids.append(chunk_id)

            # Store in ChromaDB
            self.collection.add(
                documents=chunks, embeddings=embedding_list, metadatas=metadata, ids=chunk_ids
            )

            logger.info(f"Stored {len(chunks)} chunks in vector database")
            return True

        except Exception as e:
            logger.error(f"Failed to store embeddings: {e}")
            return False

    def search(
        self, query: str, top_k: int = 5, filter_dict: dict[str, Any] | None = None
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """Search for similar documents.

        Args:
            query: Search query
            top_k: Number of results to return
            filter_dict: Optional metadata filters

        Returns:
            Tuple of (chunks, metadata)
        """
        try:
            # Generate query embedding
            from .embeddings import EmbeddingGenerator

            embedder = EmbeddingGenerator()
            query_embedding = embedder.generate_embedding(query)

            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()], n_results=top_k, where=filter_dict
            )

            chunks = results["documents"][0] if results["documents"] else []
            metadata = results["metadatas"][0] if results["metadatas"] else []

            logger.debug(f"Found {len(chunks)} relevant chunks for query: {query}")
            return chunks, metadata

        except Exception as e:
            logger.error(f"Failed to search vector database: {e}")
            return [], []

    def search_by_embedding(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filter_dict: dict[str, Any] | None = None,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """Search using a pre-computed embedding.

        Args:
            query_embedding: Pre-computed query embedding
            top_k: Number of results to return
            filter_dict: Optional metadata filters

        Returns:
            Tuple of (chunks, metadata)
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()], n_results=top_k, where=filter_dict
            )

            chunks = results["documents"][0] if results["documents"] else []
            metadata = results["metadatas"][0] if results["metadatas"] else []

            return chunks, metadata

        except Exception as e:
            logger.error(f"Failed to search by embedding: {e}")
            return [], []

    def get_collection_info(self) -> dict[str, Any]:
        """Get information about the collection.

        Returns:
            Dictionary with collection information
        """
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "db_path": str(self.db_path),
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {"error": str(e)}

    def list_documents(self, batch_size: int = CHROMADB_BATCH_LIMIT) -> list[dict[str, Any]]:
        """List all unique documents in the collection.

        ChromaDB has a limit of 1000 items per get() call, so we need to paginate
        through the results to get all documents.

        Args:
            batch_size: Number of chunks to retrieve per batch (max 1000)

        Returns:
            List of document metadata
        """
        try:
            # Limit batch_size to ChromaDB's maximum
            batch_size = min(batch_size, CHROMADB_BATCH_LIMIT)

            # Collect all unique documents by paginating through chunks
            documents = {}
            retrieved_count = 0
            offset = 0

            while True:
                # Get a batch of results
                results = self.collection.get(limit=batch_size, offset=offset)

                # Check if we got any results
                batch_ids = results.get("ids", [])
                if not batch_ids:
                    break

                # Process this batch
                batch_size_actual = len(batch_ids)
                retrieved_count += batch_size_actual

                logger.debug(f"Retrieved batch at offset {offset}: {batch_size_actual} chunks")

                # Extract unique documents from this batch
                for metadata in results.get("metadatas", []):
                    doc_name = metadata.get("document", "unknown")
                    if doc_name not in documents:
                        documents[doc_name] = {
                            "document": doc_name,
                            "type": metadata.get("type", "unknown"),
                            "chunk_count": 0,
                            "source": metadata.get("source", "unknown"),
                        }
                    documents[doc_name]["chunk_count"] += 1

                # If we got fewer results than requested, we've reached the end
                if batch_size_actual < batch_size:
                    break

                # Move to next batch
                offset += batch_size_actual

            logger.info(f"Found {len(documents)} unique documents from {retrieved_count} chunks")

            # Log document names for debugging if not too many
            if len(documents) <= 10:
                for doc_name in documents.keys():
                    logger.debug(f"  - Document: {doc_name}")

            return list(documents.values())

        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []

    def clear_collection(self) -> bool:
        """Clear all documents from the collection atomically.

        Uses reset_collection for atomic operation to avoid race conditions.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use the atomic reset_collection method
            return self.reset_collection()
        except chromadb.errors.ChromaError as e:
            logger.error(f"Failed to clear collection: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error clearing collection: {e}")
            return False

    def delete_document(self, document_name: str) -> bool:
        """Delete all chunks for a specific document.

        Args:
            document_name: Name of the document to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all chunks for the document
            results = self.collection.get(where={"document": document_name})

            if results["ids"]:
                # Delete the chunks
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks for document: {document_name}")
                return True
            else:
                logger.warning(f"No chunks found for document: {document_name}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False

    def reset_collection(self) -> bool:
        """Reset the entire collection.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Technical documentation embeddings"},
            )
            logger.info(f"Reset collection: {self.collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            return False

    def _generate_chunk_id(self, document_path: str, chunk_index: int, chunk_content: str) -> str:
        """Generate a stable, unique ID for a chunk.

        Args:
            document_path: Full path or unique identifier of the document
            chunk_index: Index of the chunk within the document
            chunk_content: The actual text content of the chunk (first 100 chars)

        Returns:
            A unique, stable ID for the chunk
        """
        # Create a deterministic ID based on document + position + content
        id_string = f"{document_path}|{chunk_index}|{chunk_content}"
        hash_value = hashlib.sha256(id_string.encode("utf-8")).hexdigest()

        # Use document name slug + hash for readability and uniqueness
        doc_slug = self._slugify(Path(document_path).stem)[:30]  # Limit length
        return f"{doc_slug}_{hash_value[:16]}"

    def _slugify(self, text: str) -> str:
        """Convert text to a safe ID component.

        Args:
            text: Text to slugify

        Returns:
            Safe string for use in IDs
        """
        # Normalize unicode
        text = unicodedata.normalize("NFKD", text)
        # Remove non-ASCII
        text = text.encode("ascii", "ignore").decode("ascii")
        # Replace non-alphanumeric with underscores
        text = re.sub(r"[^\w\s-]", "_", text)
        # Replace multiple underscores/spaces with single underscore
        text = re.sub(r"[_\s]+", "_", text)
        # Strip and lowercase
        return text.strip("_").lower()
