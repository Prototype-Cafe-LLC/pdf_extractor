#!/usr/bin/env python3
"""Tests for MCP server tool functionalities.

This module provides comprehensive tests for all MCP tools including:
- query_technical_docs
- add_pdf_document  
- list_documents
- get_system_info
"""

import asyncio
import json
import pytest
import pytest_asyncio
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, MagicMock, patch, AsyncMock

from mcp.types import (
    CallToolRequest,
    CallToolResult,
    TextContent,
)

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server import PDFRAGMCPServer
from rag_engine.retrieval import RAGEngine
from rag_engine.llm_integration import LLMResponse as RAGResponse


class TestMCPTools:
    """Test suite for MCP server tools."""
    
    @pytest.fixture
    def mock_rag_engine(self):
        """Create a mock RAG engine."""
        mock = MagicMock(spec=RAGEngine)
        
        # Mock query response
        mock.query.return_value = RAGResponse(
            answer="The AT+CSQ command is used to check signal quality.",
            sources=[
                {
                    "document": "at_commands_manual.pdf",
                    "page": "42",
                    "section": "Network Commands"
                }
            ],
            confidence=0.92,
            model_used="gpt-4",
            processing_time=0.5
        )
        
        # Mock add_pdf_document
        mock.add_pdf_document.return_value = True
        
        # Mock list_documents
        mock.list_documents.return_value = [
            {
                "document": "at_commands_manual.pdf",
                "type": "at_commands",
                "chunk_count": 150,
                "source": "/test/path/manual.pdf"
            }
        ]
        
        # Mock get_system_info
        mock.get_system_info.return_value = {
            "rag_engine": {"version": "1.0.0"},
            "embedding_model": {
                "model_name": "all-MiniLM-L6-v2",
                "embedding_dimension": 384
            },
            "llm_model": {
                "model_name": "gpt-4",
                "provider": "openai"
            },
            "vector_store": {
                "collection_name": "technical_docs",
                "document_count": 3
            }
        }
        
        # Mock test_components
        mock.test_components.return_value = {
            "vector_store": True,
            "embedding_model": True,
            "llm_integration": True,
            "chunking": True
        }
        
        return mock
    
    @pytest_asyncio.fixture
    async def server(self, mock_rag_engine):
        """Create server instance with mocked RAG engine."""
        server = PDFRAGMCPServer()
        server.rag_engine = mock_rag_engine
        return server
    
    def create_tool_request(self, name: str, arguments: Dict[str, Any]) -> CallToolRequest:
        """Helper to create a CallToolRequest."""
        request = MagicMock(spec=CallToolRequest)
        request.params = MagicMock()
        request.params.name = name
        request.params.arguments = arguments
        return request
    
    @pytest.mark.asyncio
    async def test_query_technical_docs_success(self, server):
        """Test successful technical documentation query."""
        request = self.create_tool_request(
            "query_technical_docs",
            {
                "question": "What is the AT+CSQ command used for?",
                "top_k": 3
            }
        )
        
        result = await server.handle_call_tool(request)
        
        assert isinstance(result, CallToolResult)
        assert len(result.content) == 1
        assert isinstance(result.content[0], TextContent)
        
        text = result.content[0].text
        assert "AT+CSQ command is used to check signal quality" in text
        assert "Sources" in text
        assert "at_commands_manual.pdf" in text
        assert "Page: 42" in text
        assert "Confidence Score**: 0.92" in text
    
    @pytest.mark.asyncio
    async def test_query_technical_docs_no_rag_engine(self, server):
        """Test query when RAG engine is not initialized."""
        server.rag_engine = None
        
        request = self.create_tool_request(
            "query_technical_docs",
            {"question": "Test question"}
        )
        
        result = await server.handle_call_tool(request)
        
        assert isinstance(result, CallToolResult)
        assert "Failed to initialize RAG engine" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_add_pdf_document_success(self, server, tmp_path):
        """Test successful PDF document addition."""
        # Create a test PDF file
        test_pdf = tmp_path / "test_manual.pdf"
        test_pdf.write_text("dummy pdf content")
        
        request = self.create_tool_request(
            "add_pdf_document",
            {
                "pdf_path": str(test_pdf),
                "document_type": "at_commands"
            }
        )
        
        result = await server.handle_call_tool(request)
        
        assert isinstance(result, CallToolResult)
        assert "Successfully added document: test_manual.pdf" in result.content[0].text
        
        # Verify the mock was called correctly
        server.rag_engine.add_pdf_document.assert_called_once_with(
            test_pdf,
            "at_commands"
        )
    
    @pytest.mark.asyncio
    async def test_add_pdf_document_file_not_found(self, server):
        """Test adding PDF that doesn't exist."""
        request = self.create_tool_request(
            "add_pdf_document",
            {"pdf_path": "/nonexistent/file.pdf"}
        )
        
        result = await server.handle_call_tool(request)
        
        assert isinstance(result, CallToolResult)
        assert "PDF file not found" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_add_pdf_document_failure(self, server, tmp_path):
        """Test failed PDF document addition."""
        # Create a test PDF file
        test_pdf = tmp_path / "test_manual.pdf"
        test_pdf.write_text("dummy pdf content")
        
        # Make the mock return False for failure
        server.rag_engine.add_pdf_document.return_value = False
        
        request = self.create_tool_request(
            "add_pdf_document",
            {"pdf_path": str(test_pdf)}
        )
        
        result = await server.handle_call_tool(request)
        
        assert isinstance(result, CallToolResult)
        assert "Failed to add document" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_list_documents_with_documents(self, server):
        """Test listing documents when documents exist."""
        request = self.create_tool_request("list_documents", {})
        
        result = await server.handle_call_tool(request)
        
        assert isinstance(result, CallToolResult)
        text = result.content[0].text
        
        assert "Documents in Knowledge Base" in text
        assert "at_commands_manual.pdf" in text
        assert "at_commands" in text
        assert "Chunks: 150" in text
        assert "Source: /test/path/manual.pdf" in text
    
    @pytest.mark.asyncio
    async def test_list_documents_empty(self, server):
        """Test listing documents when knowledge base is empty."""
        server.rag_engine.list_documents.return_value = []
        
        request = self.create_tool_request("list_documents", {})
        
        result = await server.handle_call_tool(request)
        
        assert isinstance(result, CallToolResult)
        assert "No documents in knowledge base" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_get_system_info_success(self, server):
        """Test getting system information."""
        request = self.create_tool_request("get_system_info", {})
        
        result = await server.handle_call_tool(request)
        
        assert isinstance(result, CallToolResult)
        text = result.content[0].text
        
        # Check system information sections
        assert "System Information" in text
        assert "RAG Engine Version**: 1.0.0" in text
        
        # Check component status
        assert "Component Status" in text
        assert "✅" in text  # Should have checkmarks for working components
        assert "**Vector Store**: Working" in text
        assert "**Embedding Model**: Working" in text
        
        # Check model information
        assert "Model Information" in text
        assert "**Embedding Model**: all-MiniLM-L6-v2" in text
        assert "**Embedding Dimension**: 384" in text
        assert "**LLM Model**: gpt-4" in text
        assert "**LLM Provider**: openai" in text
        
        # Check vector store info
        assert "**Vector Database**: technical_docs" in text
        assert "**Document Count**: 3" in text
    
    @pytest.mark.asyncio
    async def test_get_system_info_component_failure(self, server):
        """Test system info when some components fail."""
        # Mock some components as failing
        server.rag_engine.test_components.return_value = {
            "vector_store": True,
            "embedding_model": False,
            "llm_integration": False,
            "chunking": True
        }
        
        request = self.create_tool_request("get_system_info", {})
        
        result = await server.handle_call_tool(request)
        
        text = result.content[0].text
        assert "❌" in text  # Should have X marks for failed components
        assert "**Embedding Model**: Failed" in text
        assert "**Llm Integration**: Failed" in text
    
    @pytest.mark.asyncio
    async def test_unknown_tool(self, server):
        """Test handling of unknown tool name."""
        request = self.create_tool_request("unknown_tool", {"arg": "value"})
        
        result = await server.handle_call_tool(request)
        
        assert isinstance(result, CallToolResult)
        assert "Error: Unknown tool: unknown_tool" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_tool_exception_handling(self, server):
        """Test exception handling in tool calls."""
        # Make the query method raise an exception
        server.rag_engine.query.side_effect = Exception("Test error")
        
        request = self.create_tool_request(
            "query_technical_docs",
            {"question": "Test question"}
        )
        
        result = await server.handle_call_tool(request)
        
        assert isinstance(result, CallToolResult)
        assert "Error: Test error" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_initialize_rag_engine(self, server):
        """Test RAG engine initialization."""
        server.rag_engine = None
        
        # Mock the RAGEngine class
        with patch('mcp_server.RAGEngine') as MockRAGEngine:
            mock_instance = MagicMock()
            MockRAGEngine.return_value = mock_instance
            
            await server._initialize_rag_engine()
            
            assert server.rag_engine is mock_instance
            MockRAGEngine.assert_called_once()
            
            # Check the configuration passed
            call_args = MockRAGEngine.call_args[0][0]
            assert "llm_type" in call_args
            assert "embedding_model" in call_args
            assert "vector_db_path" in call_args
    
    @pytest.mark.asyncio
    async def test_initialize_rag_engine_failure(self, server):
        """Test RAG engine initialization failure."""
        server.rag_engine = None
        
        with patch('mcp_server.RAGEngine', side_effect=Exception("Init failed")):
            await server._initialize_rag_engine()
            
            assert server.rag_engine is None
    
    @pytest.mark.asyncio
    async def test_query_with_default_top_k(self, server):
        """Test query with default top_k value."""
        request = self.create_tool_request(
            "query_technical_docs",
            {"question": "Test question"}  # No top_k specified
        )
        
        result = await server.handle_call_tool(request)
        
        # Verify default top_k=5 was used
        server.rag_engine.query.assert_called_with("Test question", 5)
    
    @pytest.mark.asyncio 
    async def test_add_document_with_default_type(self, server, tmp_path):
        """Test adding document with default document type."""
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_text("dummy")
        
        request = self.create_tool_request(
            "add_pdf_document",
            {"pdf_path": str(test_pdf)}  # No document_type specified
        )
        
        result = await server.handle_call_tool(request)
        
        # Verify default type "unknown" was used
        server.rag_engine.add_pdf_document.assert_called_with(
            test_pdf,
            "unknown"
        )


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])