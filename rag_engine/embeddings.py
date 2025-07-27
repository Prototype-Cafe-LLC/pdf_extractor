"""Embedding generation for document chunks.

This module provides embedding generation capabilities for technical documentation
chunks using sentence transformers.
"""

import logging
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates embeddings for document chunks using sentence transformers."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize the embedding generator.

        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def generate_embeddings(self, chunks: list[str]) -> np.ndarray:
        """Generate embeddings for a list of text chunks.

        Args:
            chunks: List of text chunks to embed

        Returns:
            Numpy array of embeddings
        """
        if not chunks:
            return np.array([])

        try:
            logger.debug(f"Generating embeddings for {len(chunks)} chunks")
            embeddings = self.model.encode(chunks, show_progress_bar=True)
            logger.debug(f"Generated embeddings shape: {embeddings.shape}")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Numpy array of embedding
        """
        try:
            embedding = self.model.encode([text])
            return embedding[0]
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Cosine similarity score
        """
        try:
            # Normalize embeddings
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            normalized1 = embedding1 / norm1
            normalized2 = embedding2 / norm2

            # Compute cosine similarity
            similarity = np.dot(normalized1, normalized2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Failed to compute similarity: {e}")
            return 0.0

    def batch_similarity(
        self, query_embedding: np.ndarray, chunk_embeddings: np.ndarray
    ) -> np.ndarray:
        """Compute similarity between query and multiple chunk embeddings.

        Args:
            query_embedding: Query embedding
            chunk_embeddings: Array of chunk embeddings

        Returns:
            Array of similarity scores
        """
        try:
            # Normalize query embedding
            query_norm = np.linalg.norm(query_embedding)
            if query_norm == 0:
                return np.zeros(len(chunk_embeddings))

            normalized_query = query_embedding / query_norm

            # Normalize chunk embeddings
            chunk_norms = np.linalg.norm(chunk_embeddings, axis=1)
            chunk_norms[chunk_norms == 0] = 1  # Avoid division by zero
            normalized_chunks = chunk_embeddings / chunk_norms[:, np.newaxis]

            # Compute cosine similarities
            similarities = np.dot(normalized_chunks, normalized_query)
            return similarities
        except Exception as e:
            logger.error(f"Failed to compute batch similarity: {e}")
            return np.zeros(len(chunk_embeddings))

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the loaded model.

        Returns:
            Dictionary with model information
        """
        if self.model is None:
            return {"error": "Model not loaded"}

        try:
            return {
                "model_name": self.model_name,
                "max_seq_length": getattr(self.model, "max_seq_length", "unknown"),
                "embedding_dimension": self.model.get_sentence_embedding_dimension(),
                "device": str(self.model.device),
            }
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {"error": str(e)}
