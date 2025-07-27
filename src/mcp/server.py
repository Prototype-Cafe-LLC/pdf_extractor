#!/usr/bin/env python3
"""MCP Server for PDF RAG System.

This module provides a Model Context Protocol (MCP) server that enables
RAG-powered technical documentation queries through standardized tools.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

import yaml
from mcp.server import Server
from mcp.server.lowlevel.server import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    TextContent,
    Tool,
)

try:
    # Try relative import (when run as module)
    from ..rag_engine.retrieval import RAGEngine
except ImportError:
    # Fall back to absolute import (when run directly)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.rag_engine.retrieval import RAGEngine

logger = logging.getLogger(__name__)


class PDFRAGMCPServer:
    """MCP Server for PDF RAG system."""

    def __init__(self):
        """Initialize the MCP server."""
        self.server = Server("pdf-rag-mcp")
        # Get project root directory (two levels up from src/mcp/)
        self._project_root = Path(__file__).parent.parent.parent
        self.rag_engine = None
        self.config = self._load_config()
        self.setup_handlers()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from files.

        Returns:
            Configuration dictionary
        """
        config = {}

        # Load RAG config
        rag_config_path = self._project_root / "config" / "rag_config.yaml"
        if rag_config_path.exists():
            try:
                with open(rag_config_path) as f:
                    config.update(yaml.safe_load(f))
                logger.info("Loaded RAG configuration")
            except Exception as e:
                logger.error(f"Failed to load RAG config: {e}")

        # Load MCP config
        mcp_config_path = self._project_root / "config" / "mcp_config.yaml"
        if mcp_config_path.exists():
            try:
                with open(mcp_config_path) as f:
                    config.update(yaml.safe_load(f))
                logger.info("Loaded MCP configuration")
            except Exception as e:
                logger.error(f"Failed to load MCP config: {e}")

        # Override with environment variables if set
        if os.environ.get("LLM_TYPE"):
            config.setdefault("llm", {})["type"] = os.environ["LLM_TYPE"]
            logger.info(f"Using LLM type from env: {os.environ['LLM_TYPE']}")
        
        if os.environ.get("LLM_MODEL"):
            config.setdefault("llm", {})["model"] = os.environ["LLM_MODEL"]
            logger.info(f"Using LLM model from env: {os.environ['LLM_MODEL']}")
        
        if os.environ.get("EMBEDDING_MODEL"):
            config.setdefault("embedding", {})["model"] = os.environ["EMBEDDING_MODEL"]
            logger.info(f"Using embedding model from env: {os.environ['EMBEDDING_MODEL']}")

        return config

    def setup_handlers(self):
        """Setup MCP server handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
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
                                "description": "Question to search for in the PDF knowledge base",
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of relevant chunks to retrieve (default: 5)",
                                "default": 5,
                            },
                        },
                        "required": ["question"],
                    },
                ),
                Tool(
                    name="add_pdf_document",
                    description="Add a PDF document to the knowledge base",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pdf_path": {
                                "type": "string",
                                "description": "Path to PDF file to add",
                            },
                            "document_type": {
                                "type": "string",
                                "description": "Type of document (e.g., 'manual', 'specification', 'guide')",
                                "default": "unknown",
                            },
                        },
                        "required": ["pdf_path"],
                    },
                ),
                Tool(
                    name="list_documents",
                    description="List all documents in the knowledge base",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="get_system_info",
                    description="Get system information and component status",
                    inputSchema={"type": "object", "properties": {}},
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool_wrapper(request: CallToolRequest) -> CallToolResult:
            """Wrapper for handle_call_tool to register with MCP."""
            return await self.handle_call_tool(request)

    async def handle_call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle tool calls."""
        try:
            name = request.params.name
            arguments = request.params.arguments

            if name == "query_technical_docs":
                return await self._handle_query(arguments)
            elif name == "add_pdf_document":
                return await self._handle_add_document(arguments)
            elif name == "list_documents":
                return await self._handle_list_documents(arguments)
            elif name == "get_system_info":
                return await self._handle_get_system_info(arguments)
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: Unknown tool: {name}")]
                )
        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            return CallToolResult(content=[TextContent(type="text", text=f"Error: {str(e)}")])

    async def _handle_query(self, arguments: dict[str, Any]) -> CallToolResult:
        """Handle technical documentation queries."""
        question = arguments["question"]
        top_k = arguments.get("top_k", 5)

        # Initialize RAG engine if not already done
        if not self.rag_engine:
            await self._initialize_rag_engine()

        if not self.rag_engine:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: Failed to initialize RAG engine")]
            )

        # Get RAG response
        response = self.rag_engine.query(question, top_k)

        # Format response with sources
        answer = response.answer
        sources = response.sources
        confidence = response.confidence

        formatted_response = f"""## Answer
{answer}

## Sources
"""
        if sources:
            for source in sources:
                doc_name = source.get("document", "Unknown")
                page_info = source.get("page", "N/A")
                section = source.get("section", "")

                source_line = f"- **{doc_name}**"
                if page_info != "N/A":
                    source_line += f" (Page: {page_info})"
                if section:
                    source_line += f" - {section}"

                formatted_response += source_line + "\n"
        else:
            formatted_response += "No specific sources available\n"

        formatted_response += f"\n**Confidence Score**: {confidence:.2f}"

        if response.processing_time:
            formatted_response += f"\n**Processing Time**: {response.processing_time:.2f}s"

        return CallToolResult(content=[TextContent(type="text", text=formatted_response)])

    async def _handle_add_document(self, arguments: dict[str, Any]) -> CallToolResult:
        """Handle adding new PDF documents."""
        pdf_path = Path(arguments["pdf_path"])
        document_type = arguments.get("document_type", "unknown")

        if not pdf_path.exists():
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: PDF file not found: {pdf_path}")]
            )

        # Initialize RAG engine if not already done
        if not self.rag_engine:
            await self._initialize_rag_engine()

        if not self.rag_engine:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: Failed to initialize RAG engine")]
            )

        # Add document to knowledge base
        success = self.rag_engine.add_pdf_document(pdf_path, document_type)

        if success:
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"Successfully added document: {pdf_path.name}")
                ]
            )
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Failed to add document: {pdf_path.name}")]
            )

    async def _handle_list_documents(self, arguments: dict[str, Any]) -> CallToolResult:
        """Handle listing documents in knowledge base."""
        # Initialize RAG engine if not already done
        if not self.rag_engine:
            await self._initialize_rag_engine()

        if not self.rag_engine:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: Failed to initialize RAG engine")]
            )

        documents = self.rag_engine.list_documents()

        if not documents:
            return CallToolResult(
                content=[TextContent(type="text", text="No documents in knowledge base")]
            )

        response = "## Documents in Knowledge Base\n\n"
        for doc in documents:
            response += f"- **{doc['document']}** ({doc['type']})\n"
            response += f"  - Chunks: {doc['chunk_count']}\n"
            response += f"  - Source: {doc['source']}\n\n"

        return CallToolResult(content=[TextContent(type="text", text=response)])

    async def _handle_get_system_info(self, arguments: dict[str, Any]) -> CallToolResult:
        """Handle getting system information."""
        # Initialize RAG engine if not already done
        if not self.rag_engine:
            await self._initialize_rag_engine()

        if not self.rag_engine:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: Failed to initialize RAG engine")]
            )

        # Get system info
        system_info = self.rag_engine.get_system_info()

        # Test components
        test_results = self.rag_engine.test_components()

        # Format response
        response = "## System Information\n\n"

        # RAG Engine info
        rag_info = system_info.get("rag_engine", {})
        response += f"**RAG Engine Version**: {rag_info.get('version', 'unknown')}\n\n"

        # Component status
        response += "## Component Status\n\n"
        for component, status in test_results.items():
            status_icon = "✅" if status else "❌"
            response += f"{status_icon} **{component.replace('_', ' ').title()}**: {'Working' if status else 'Failed'}\n"

        # Model information
        response += "\n## Model Information\n\n"

        embedding_info = system_info.get("embedding_model", {})
        if "error" not in embedding_info:
            response += f"**Embedding Model**: {embedding_info.get('model_name', 'unknown')}\n"
            response += (
                f"**Embedding Dimension**: {embedding_info.get('embedding_dimension', 'unknown')}\n"
            )

        llm_info = system_info.get("llm_model", {})
        if "error" not in llm_info:
            response += f"**LLM Model**: {llm_info.get('model_name', 'unknown')}\n"
            response += f"**LLM Provider**: {llm_info.get('provider', 'unknown')}\n"

        # Vector store info
        vector_info = system_info.get("vector_store", {})
        if "error" not in vector_info:
            response += f"**Vector Database**: {vector_info.get('collection_name', 'unknown')}\n"
            response += f"**Document Count**: {vector_info.get('document_count', 'unknown')}\n"

        return CallToolResult(content=[TextContent(type="text", text=response)])

    async def _initialize_rag_engine(self):
        """Initialize the RAG engine."""
        try:
            logger.info("Initializing RAG engine...")

            # Prepare configuration
            rag_config = {
                "llm_type": self.config.get("llm", {}).get("type", "openai"),
                "llm_model": self.config.get("llm", {}).get("model", "gpt-4"),
                "embedding_model": self.config.get("embedding", {}).get(
                    "model", "sentence-transformers/all-MiniLM-L6-v2"
                ),
                "vector_db_path": self.config.get("vector_store", {}).get(
                    "path", "./data/vector_db"
                ),
                "collection_name": self.config.get("vector_store", {}).get(
                    "collection_name", "technical_docs"
                ),
                "chunk_size": self.config.get("chunking", {}).get("max_tokens", 512),
                "chunk_overlap": self.config.get("chunking", {}).get("overlap_tokens", 50),
            }

            self.rag_engine = RAGEngine(rag_config)
            logger.info("RAG engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {e}")
            self.rag_engine = None


async def main():
    """Main entry point for MCP server."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    server = PDFRAGMCPServer()

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
