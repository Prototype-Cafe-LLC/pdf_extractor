#!/usr/bin/env python3
"""Simplified MCP Server for PDF RAG System.

This module provides a Model Context Protocol (MCP) server that enables
RAG-powered technical documentation queries through standardized tools.
"""

import asyncio
import json
import logging
import os
import yaml
import importlib.metadata
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.server.lowlevel.server import NotificationOptions
from mcp.types import Tool, TextContent

from rag_engine.retrieval import RAGEngine

logger = logging.getLogger(__name__)


class SimplePDFRAGMCPServer:
    """Simplified MCP Server for PDF RAG system."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.server = Server("pdf-rag-mcp")
        self._script_dir = Path(__file__).parent.absolute()
        self.config = self._load_config()
        self.rag_engine = None
        self.setup_handlers()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from files."""
        config = {}
        
        # Load RAG config
        rag_config_path = self._script_dir / "config" / "rag_config.yaml"
        if rag_config_path.exists():
            try:
                with open(rag_config_path, 'r') as f:
                    config.update(yaml.safe_load(f))
                logger.info(f"Loaded RAG configuration from {rag_config_path}")
            except Exception as e:
                logger.error(f"Failed to load RAG config: {e}")
        
        # Load MCP config
        mcp_config_path = self._script_dir / "config" / "mcp_config.yaml"
        if mcp_config_path.exists():
            try:
                with open(mcp_config_path, 'r') as f:
                    config.update(yaml.safe_load(f))
                logger.info(f"Loaded MCP configuration from {mcp_config_path}")
            except Exception as e:
                logger.error(f"Failed to load MCP config: {e}")
        
        return config
    
    def _resolve_path(self, path: str) -> str:
        """Resolve a path relative to script directory if it's relative.
        
        Args:
            path: Path to resolve (can be relative or absolute)
            
        Returns:
            Resolved absolute path as string
        """
        path_obj = Path(path)
        if not path_obj.is_absolute():
            return str(self._script_dir / path_obj)
        return str(path_obj)
    
    def setup_handlers(self):
        """Setup MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="query_technical_docs",
                    description="Query technical documentation using RAG",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "Technical question about AT commands, hardware, etc."
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of relevant chunks to retrieve (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["question"]
                    }
                ),
                Tool(
                    name="add_pdf_document",
                    description="Add a PDF document to the knowledge base",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pdf_path": {
                                "type": "string",
                                "description": "Path to PDF file to add"
                            },
                            "document_type": {
                                "type": "string",
                                "description": "Type of document (e.g., 'at_commands', 'hardware_design')",
                                "default": "unknown"
                            }
                        },
                        "required": ["pdf_path"]
                    }
                ),
                Tool(
                    name="list_documents",
                    description="List all documents in the knowledge base",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_system_info",
                    description="Get system information and component status",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            try:
                if name == "query_technical_docs":
                    return await self._handle_query(arguments)
                elif name == "add_pdf_document":
                    return await self._handle_add_document(arguments)
                elif name == "list_documents":
                    return await self._handle_list_documents()
                elif name == "get_system_info":
                    return await self._handle_get_system_info()
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Tool call failed: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _handle_get_system_info(self) -> List[TextContent]:
        """Handle getting system information."""
        # Get configuration info
        llm_type = self.config.get("llm", {}).get("type", "unknown")
        llm_model = self.config.get("llm", {}).get("model", "unknown")
        embedding_model = self.config.get("embedding", {}).get("model", "unknown")
        vector_db_path = Path(self.config.get("vector_store", {}).get("path", "./data/vector_db"))
        collection_name = self.config.get("vector_store", {}).get("collection_name", "technical_docs")
        
        # Check component status
        components_status = {
            "Configuration": True,  # Config loaded successfully if we're here
            "LLM Settings": llm_type != "unknown",
            "Embedding Settings": embedding_model != "unknown",
            "Vector DB Path": vector_db_path.parent.exists()
        }
        
        # Count documents in vector DB
        doc_count = 0
        if vector_db_path.exists():
            # Simple check for chroma DB files
            sqlite_file = vector_db_path / "chroma.sqlite3"
            if sqlite_file.exists():
                doc_count = "Unknown (DB exists)"
            else:
                doc_count = 0
        
        # Get package versions
        try:
            mcp_version = importlib.metadata.version("mcp")
        except:
            mcp_version = "unknown"
        
        # Format response
        response = "## System Information\n\n"
        response += f"**MCP Server**: pdf-rag-mcp v1.0.0\n"
        response += f"**MCP Framework**: v{mcp_version}\n\n"
        
        response += "## Component Status\n\n"
        for component, status in components_status.items():
            status_icon = "✅" if status else "❌"
            status_text = "Working" if status else "Not Configured"
            response += f"{status_icon} **{component}**: {status_text}\n"
        
        response += "\n## Configuration\n\n"
        response += f"**LLM Provider**: {llm_type}\n"
        response += f"**LLM Model**: {llm_model}\n"
        response += f"**Embedding Model**: {embedding_model}\n"
        response += f"**Vector Database**: {collection_name}\n"
        response += f"**Vector DB Path**: {vector_db_path}\n"
        response += f"**Document Count**: {doc_count}\n"
        
        response += "\n## Features\n\n"
        response += "- Query technical documentation using RAG\n"
        response += "- Add PDF documents to knowledge base\n"
        response += "- List all documents in the system\n"
        response += "- Get system status and configuration\n"
        
        return [TextContent(type="text", text=response)]
    
    async def _initialize_rag_engine(self):
        """Initialize the RAG engine if not already done."""
        if self.rag_engine:
            return
        
        try:
            logger.info("Initializing RAG engine...")
            
            # Get vector_db_path from config and resolve it
            vector_db_path = self.config.get("vector_store", {}).get("path", "./data/vector_db")
            vector_db_path = self._resolve_path(vector_db_path)
            
            # Prepare configuration
            rag_config = {
                "llm_type": self.config.get("llm", {}).get("type", "openai"),
                "llm_model": self.config.get("llm", {}).get("model", "gpt-4"),
                "embedding_model": self.config.get("embedding", {}).get("model", "sentence-transformers/all-MiniLM-L6-v2"),
                "vector_db_path": vector_db_path,
                "collection_name": self.config.get("vector_store", {}).get("collection_name", "technical_docs"),
                "chunk_size": self.config.get("chunking", {}).get("max_tokens", 512),
                "chunk_overlap": self.config.get("chunking", {}).get("overlap_tokens", 50),
            }
            
            # Log the actual path being used
            logger.info(f"Script directory: {self._script_dir}")
            logger.info(f"Vector DB path: {rag_config['vector_db_path']}")
            logger.info(f"Current working directory: {os.getcwd()}")
            
            self.rag_engine = RAGEngine(rag_config)
            logger.info("RAG engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {e}")
            self.rag_engine = None
            raise
    
    async def _handle_query(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle technical documentation queries."""
        question = arguments.get("question", "")
        top_k = arguments.get("top_k", 5)
        
        if not question:
            return [TextContent(type="text", text="Error: No question provided")]
        
        # Initialize RAG engine if needed
        try:
            await self._initialize_rag_engine()
        except Exception as e:
            return [TextContent(type="text", text=f"Error: Failed to initialize RAG engine - {str(e)}")]
        
        if not self.rag_engine:
            return [TextContent(type="text", text="Error: RAG engine not available")]
        
        # Get RAG response
        try:
            response = self.rag_engine.query(question, top_k)
            
            # Format response with sources
            answer = response.answer
            sources = response.sources
            confidence = response.confidence
            
            formatted_response = f"## Answer\n{answer}\n\n## Sources\n"
            
            if sources:
                for source in sources:
                    doc_name = source.get('document', 'Unknown')
                    page_info = source.get('page', 'N/A')
                    section = source.get('section', '')
                    
                    source_line = f"- **{doc_name}**"
                    if page_info != 'N/A':
                        source_line += f" (Page: {page_info})"
                    if section:
                        source_line += f" - {section}"
                    
                    formatted_response += source_line + "\n"
            else:
                formatted_response += "No specific sources available\n"
            
            formatted_response += f"\n**Confidence Score**: {confidence:.2f}"
            
            if response.processing_time:
                formatted_response += f"\n**Processing Time**: {response.processing_time:.2f}s"
            
            return [TextContent(type="text", text=formatted_response)]
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return [TextContent(type="text", text=f"Error: Query failed - {str(e)}")]
    
    async def _handle_add_document(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle adding new PDF documents."""
        pdf_path = arguments.get("pdf_path", "")
        document_type = arguments.get("document_type", "unknown")
        
        if not pdf_path:
            return [TextContent(type="text", text="Error: No PDF path provided")]
        
        # Resolve the path
        pdf_path = Path(self._resolve_path(pdf_path))
        
        if not pdf_path.exists():
            return [TextContent(type="text", text=f"Error: PDF file not found: {pdf_path}")]
        
        if not pdf_path.suffix.lower() == '.pdf':
            return [TextContent(type="text", text=f"Error: Not a PDF file: {pdf_path}")]
        
        # Initialize RAG engine if needed
        try:
            await self._initialize_rag_engine()
        except Exception as e:
            return [TextContent(type="text", text=f"Error: Failed to initialize RAG engine - {str(e)}")]
        
        if not self.rag_engine:
            return [TextContent(type="text", text="Error: RAG engine not available")]
        
        # Add document to knowledge base
        try:
            success = self.rag_engine.add_pdf_document(pdf_path, document_type)
            
            if success:
                return [TextContent(type="text", text=f"Successfully added document: {pdf_path.name}")]
            else:
                return [TextContent(type="text", text=f"Failed to add document: {pdf_path.name}")]
                
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return [TextContent(type="text", text=f"Error: Failed to add document - {str(e)}")]
    
    async def _handle_list_documents(self) -> List[TextContent]:
        """Handle listing documents in knowledge base."""
        # Initialize RAG engine if needed
        try:
            await self._initialize_rag_engine()
        except Exception as e:
            return [TextContent(type="text", text=f"Error: Failed to initialize RAG engine - {str(e)}")]
        
        if not self.rag_engine:
            return [TextContent(type="text", text="Error: RAG engine not available")]
        
        try:
            documents = self.rag_engine.list_documents()
            
            # Add debug logging
            logger.info(f"Found {len(documents)} documents in knowledge base")
            
            if not documents:
                return [TextContent(type="text", text="No documents in knowledge base")]
            
            response = "## Documents in Knowledge Base\n\n"
            for doc in documents:
                response += f"- **{doc['document']}** ({doc['type']})\n"
                response += f"  - Chunks: {doc['chunk_count']}\n"
                response += f"  - Source: {doc['source']}\n\n"
            
            return [TextContent(type="text", text=response)]
            
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return [TextContent(type="text", text=f"Error: Failed to list documents - {str(e)}")]


async def main():
    """Main entry point for MCP server."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    server = SimplePDFRAGMCPServer()
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="pdf-rag-mcp",
                server_version="1.0.0",
                capabilities=server.server.get_capabilities(
                    notification_options=NotificationOptions(tools_changed=False),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main()) 