"""Vector database operations using ChromaDB.

This module provides vector database functionality for storing and retrieving
document embeddings with metadata.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


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
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except Exception:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Technical documentation embeddings"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")
            raise
    
    def store_embeddings(self, chunks: List[str], embeddings: np.ndarray, 
                        metadata: List[Dict[str, Any]]) -> bool:
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
            if hasattr(embeddings, 'tolist'):
                embedding_list = embeddings.tolist()
            else:
                embedding_list = embeddings
            
            # Generate IDs for chunks
            chunk_ids = [f"chunk_{i}_{metadata[i].get('chunk_id', i)}" 
                        for i in range(len(chunks))]
            
            # Store in ChromaDB
            self.collection.add(
                documents=chunks,
                embeddings=embedding_list,
                metadatas=metadata,
                ids=chunk_ids
            )
            
            logger.info(f"Stored {len(chunks)} chunks in vector database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store embeddings: {e}")
            return False
    
    def search(self, query: str, top_k: int = 5, 
               filter_dict: Optional[Dict[str, Any]] = None) -> Tuple[List[str], List[Dict[str, Any]]]:
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
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                where=filter_dict
            )
            
            chunks = results['documents'][0] if results['documents'] else []
            metadata = results['metadatas'][0] if results['metadatas'] else []
            
            logger.debug(f"Found {len(chunks)} relevant chunks for query: {query}")
            return chunks, metadata
            
        except Exception as e:
            logger.error(f"Failed to search vector database: {e}")
            return [], []
    
    def search_by_embedding(self, query_embedding: np.ndarray, top_k: int = 5,
                           filter_dict: Optional[Dict[str, Any]] = None) -> Tuple[List[str], List[Dict[str, Any]]]:
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
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k,
                where=filter_dict
            )
            
            chunks = results['documents'][0] if results['documents'] else []
            metadata = results['metadatas'][0] if results['metadatas'] else []
            
            return chunks, metadata
            
        except Exception as e:
            logger.error(f"Failed to search by embedding: {e}")
            return [], []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection.
        
        Returns:
            Dictionary with collection information
        """
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "db_path": str(self.db_path)
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {"error": str(e)}
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all unique documents in the collection.
        
        Returns:
            List of document metadata
        """
        try:
            # Get count first
            count = self.collection.count()
            
            # Get all documents with explicit limit
            results = self.collection.get(limit=count if count > 0 else 1000)
            
            # Extract unique documents
            documents = {}
            for i, metadata in enumerate(results['metadatas']):
                doc_name = metadata.get('document', 'unknown')
                if doc_name not in documents:
                    documents[doc_name] = {
                        'document': doc_name,
                        'type': metadata.get('type', 'unknown'),
                        'chunk_count': 0,
                        'source': metadata.get('source', 'unknown')
                    }
                documents[doc_name]['chunk_count'] += 1
            
            logger.info(f"Found {len(documents)} unique documents from {count} total chunks")
            
            return list(documents.values())
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []
    
    def clear_collection(self) -> bool:
        """Clear all documents from the collection.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all document IDs
            results = self.collection.get()
            all_ids = results['ids']
            
            if all_ids:
                # Delete all documents
                self.collection.delete(ids=all_ids)
                logger.info(f"Cleared {len(all_ids)} chunks from collection")
            else:
                logger.info("Collection was already empty")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
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
            results = self.collection.get(
                where={"document": document_name}
            )
            
            if results['ids']:
                # Delete the chunks
                self.collection.delete(ids=results['ids'])
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
                metadata={"description": "Technical documentation embeddings"}
            )
            logger.info(f"Reset collection: {self.collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            return False 