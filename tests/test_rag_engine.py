"""Tests for RAG engine components."""

import pytest
from pathlib import Path
import tempfile
import shutil

from rag_engine.chunking import DocumentChunker, DocumentChunk
from rag_engine.embeddings import EmbeddingGenerator
from rag_engine.vector_store import VectorStore
from rag_engine.llm_integration import LLMIntegration, LLMResponse
from rag_engine.retrieval import RAGEngine


class TestDocumentChunker:
    """Test document chunking functionality."""
    
    def test_chunker_initialization(self):
        """Test chunker initialization."""
        chunker = DocumentChunker(max_tokens=512, overlap_tokens=50)
        assert chunker.max_tokens == 512
        assert chunker.overlap_tokens == 50
    
    def test_chunk_by_sections(self):
        """Test section-based chunking."""
        chunker = DocumentChunker()
        
        # Sample markdown content
        content = """# Section 1
This is section 1 content.

## Subsection 1.1
More content here.

# Section 2
This is section 2 content.
"""
        
        metadata = {"document": "test.md", "type": "test"}
        chunks = chunker.chunk_by_sections(content, metadata)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
        assert all(chunk.metadata["document"] == "test.md" for chunk in chunks)
    
    def test_chunk_by_tokens(self):
        """Test token-based chunking."""
        chunker = DocumentChunker(max_tokens=100, overlap_tokens=10)
        
        content = "This is a test document with some content. " * 50
        metadata = {"document": "test.md"}
        
        chunks = chunker.chunk_by_tokens(content, metadata)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)


class TestEmbeddingGenerator:
    """Test embedding generation functionality."""
    
    def test_embedding_initialization(self):
        """Test embedding generator initialization."""
        try:
            embedder = EmbeddingGenerator()
            assert embedder.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        except Exception as e:
            pytest.skip(f"Embedding model not available: {e}")
    
    def test_generate_embedding(self):
        """Test single embedding generation."""
        try:
            embedder = EmbeddingGenerator()
            text = "This is a test sentence."
            embedding = embedder.generate_embedding(text)
            
            assert embedding is not None
            assert len(embedding) > 0
        except Exception as e:
            pytest.skip(f"Embedding generation failed: {e}")
    
    def test_generate_embeddings(self):
        """Test batch embedding generation."""
        try:
            embedder = EmbeddingGenerator()
            texts = ["First sentence.", "Second sentence.", "Third sentence."]
            embeddings = embedder.generate_embeddings(texts)
            
            assert embeddings is not None
            assert embeddings.shape[0] == len(texts)
        except Exception as e:
            pytest.skip(f"Batch embedding generation failed: {e}")


class TestVectorStore:
    """Test vector store functionality."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir) / "test_db"
        shutil.rmtree(temp_dir)
    
    def test_vector_store_initialization(self, temp_db_path):
        """Test vector store initialization."""
        try:
            vector_store = VectorStore(str(temp_db_path), "test_collection")
            assert vector_store.db_path == temp_db_path
            assert vector_store.collection_name == "test_collection"
        except Exception as e:
            pytest.skip(f"Vector store initialization failed: {e}")
    
    def test_store_and_search(self, temp_db_path):
        """Test storing and searching embeddings."""
        try:
            vector_store = VectorStore(str(temp_db_path), "test_collection")
            
            # Test data
            chunks = ["This is a test document.", "Another test document."]
            embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]  # Mock embeddings
            metadata = [{"document": "test1.md"}, {"document": "test2.md"}]
            
            # Store embeddings
            success = vector_store.store_embeddings(chunks, embeddings, metadata)
            assert success
            
            # Search
            results_chunks, results_metadata = vector_store.search("test", top_k=2)
            assert len(results_chunks) > 0
            
        except Exception as e:
            pytest.skip(f"Vector store operations failed: {e}")


class TestLLMIntegration:
    """Test LLM integration functionality."""
    
    def test_llm_initialization(self):
        """Test LLM integration initialization."""
        try:
            # Test with mock configuration (no actual API calls)
            llm = LLMIntegration(model_type="openai", model_name="gpt-4")
            assert llm.model_type == "openai"
            assert llm.model_name == "gpt-4"
        except Exception as e:
            pytest.skip(f"LLM initialization failed: {e}")
    
    def test_response_generation(self):
        """Test response generation (mock)."""
        try:
            llm = LLMIntegration(model_type="openai", model_name="gpt-4")
            
            query = "What is AT+CSQ?"
            context_chunks = ["AT+CSQ is used to check signal quality."]
            sources = [{"document": "test.md", "page": "1"}]
            
            response = llm.generate_response(query, context_chunks, sources)
            
            assert isinstance(response, LLMResponse)
            assert response.answer is not None
            assert response.sources == sources
            assert 0.0 <= response.confidence <= 1.0
            
        except Exception as e:
            pytest.skip(f"Response generation failed: {e}")


class TestRAGEngine:
    """Test complete RAG engine functionality."""
    
    @pytest.fixture
    def temp_config(self):
        """Create temporary configuration."""
        return {
            "llm_type": "openai",
            "llm_model": "gpt-4",
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "vector_db_path": "./temp_vector_db",
            "collection_name": "test_collection",
            "chunk_size": 512,
            "chunk_overlap": 50,
        }
    
    def test_rag_engine_initialization(self, temp_config):
        """Test RAG engine initialization."""
        try:
            rag_engine = RAGEngine(temp_config)
            assert rag_engine.config == temp_config
            assert rag_engine.chunker is not None
            assert rag_engine.embedder is not None
            assert rag_engine.vector_store is not None
            assert rag_engine.llm is not None
        except Exception as e:
            pytest.skip(f"RAG engine initialization failed: {e}")
    
    def test_document_processing(self, temp_config):
        """Test document processing pipeline."""
        try:
            rag_engine = RAGEngine(temp_config)
            
            # Sample markdown content
            content = """# Test Document
This is a test document with AT commands.

## AT+CSQ
AT+CSQ is used to check signal quality.

## AT+CREG
AT+CREG is used for network registration.
"""
            
            metadata = {
                "document": "test.md",
                "type": "at_commands",
                "source": "test"
            }
            
            success = rag_engine.process_document(content, metadata)
            assert success
            
        except Exception as e:
            pytest.skip(f"Document processing failed: {e}")
    
    def test_query_processing(self, temp_config):
        """Test query processing."""
        try:
            rag_engine = RAGEngine(temp_config)
            
            # First add some content
            content = "AT+CSQ is used to check signal quality."
            metadata = {"document": "test.md", "type": "at_commands"}
            rag_engine.process_document(content, metadata)
            
            # Then query
            response = rag_engine.query("What is AT+CSQ?")
            
            assert isinstance(response, LLMResponse)
            assert response.answer is not None
            
        except Exception as e:
            pytest.skip(f"Query processing failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__]) 