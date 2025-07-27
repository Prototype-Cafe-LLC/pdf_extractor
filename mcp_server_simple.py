#!/usr/bin/env python3
"""Simplified MCP Server for PDF RAG System.

This module provides a Model Context Protocol (MCP) server that enables
RAG-powered technical documentation queries through standardized tools.
"""

import asyncio
import importlib.metadata
import logging
import os
from functools import partial
from pathlib import Path
from typing import Any

import yaml
from mcp.server import Server
from mcp.server.lowlevel.server import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from rag_engine.retrieval import RAGEngine

logger = logging.getLogger(__name__)

# Constants for resource limits
MAX_FILES_PER_BATCH = 100
MAX_FILE_SIZE_MB = 50
MAX_PATH_LENGTH = 255
MAX_QUERY_LENGTH = 1000
MAX_TOP_K = 20


class SimplePDFRAGMCPServer:
    """Simplified MCP Server for PDF RAG system."""

    def __init__(self):
        """Initialize the MCP server."""
        self.server = Server("pdf-rag-mcp")
        self._script_dir = Path(__file__).parent.absolute()
        self.config = self._load_config()
        self.rag_engine = None
        self.setup_handlers()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from files."""
        config = {}

        # Load RAG config
        rag_config_path = self._script_dir / "config" / "rag_config.yaml"
        if rag_config_path.exists():
            try:
                with open(rag_config_path) as f:
                    config.update(yaml.safe_load(f))
                logger.info(f"Loaded RAG configuration from {rag_config_path}")
            except Exception as e:
                logger.error(f"Failed to load RAG config: {e}")

        # Load MCP config
        mcp_config_path = self._script_dir / "config" / "mcp_config.yaml"
        if mcp_config_path.exists():
            try:
                with open(mcp_config_path) as f:
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

        Raises:
            ValueError: If path attempts to escape allowed directories
        """
        path_obj = Path(path)

        # Resolve to absolute path, following symlinks
        if not path_obj.is_absolute():
            resolved_path = (self._script_dir / path_obj).resolve()
        else:
            resolved_path = path_obj.resolve()

        # Security check: ensure path is within allowed directories
        allowed_dirs = [
            self._script_dir,
            Path.home(),  # User's home directory
            Path("/tmp"),  # Temporary directory
        ]

        # Check if resolved path is within any allowed directory
        is_allowed = any(
            self._is_path_under_directory(resolved_path, allowed_dir)
            for allowed_dir in allowed_dirs
        )

        if not is_allowed:
            raise ValueError(f"Access denied: Path '{path}' is outside allowed directories")

        return str(resolved_path)

    def _is_path_under_directory(self, path: Path, directory: Path) -> bool:
        """Check if a path is under a given directory.

        Args:
            path: Path to check
            directory: Directory to check against

        Returns:
            True if path is under directory, False otherwise
        """
        try:
            path.resolve().relative_to(directory.resolve())
            return True
        except ValueError:
            return False

    def _get_progress_context(self) -> tuple[str | None, Any | None]:
        """Extract progress token and context from request.

        Returns:
            Tuple of (progress_token, context)
        """
        try:
            context = self.server.request_context
            if context and hasattr(context, "meta"):
                meta = getattr(context, "meta", None)
                if meta and hasattr(meta, "progressToken"):
                    progress_token = getattr(meta, "progressToken", None)
                    if isinstance(progress_token, str):
                        return progress_token, context
            return None, None
        except Exception as e:
            logger.debug(f"No progress context available: {e}")
            return None, None

    async def _send_progress(
        self,
        progress: float,
        message: str,
        progress_token: str | None = None,
        context: Any | None = None,
    ) -> None:
        """Send progress notification if token available.

        Args:
            progress: Progress value (0.0 to 1.0)
            message: Progress message
            progress_token: Optional progress token
            context: Optional request context
        """
        if not progress_token or not context:
            return

        try:
            await context.session.send_progress_notification(
                progress_token=progress_token,
                progress=min(1.0, max(0.0, progress)),  # Clamp to 0-1
                total=1.0,
                message=message[:200],  # Limit message length
            )
        except Exception as e:
            logger.debug(f"Failed to send progress: {e}")

    def setup_handlers(self):
        """Setup MCP server handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="pdfrag.query_technical_docs",
                    description="Query the PDF RAG knowledge base for technical documentation answers",
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
                    name="pdfrag.add_document",
                    description="Add a single PDF document to the PDF RAG knowledge base",
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
                    name="pdfrag.add_documents",
                    description="Add multiple PDF documents from a folder to the PDF RAG knowledge base",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "folder_path": {
                                "type": "string",
                                "description": "Path to folder containing PDF files",
                            },
                            "document_type": {
                                "type": "string",
                                "description": "Default type for all documents (e.g., 'manual', 'specification', 'guide')",
                                "default": "unknown",
                            },
                            "recursive": {
                                "type": "boolean",
                                "description": "Whether to search for PDFs recursively in subfolders",
                                "default": False,
                            },
                        },
                        "required": ["folder_path"],
                    },
                ),
                Tool(
                    name="pdfrag.list_documents",
                    description="List all PDF documents currently stored in the PDF RAG knowledge base",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="pdfrag.get_system_info",
                    description="Get PDF RAG system information, configuration, and component status",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="pdfrag.clear_database",
                    description="Clear the PDF RAG vector database (removes embeddings/chunks only, original PDFs remain untouched)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "confirm": {
                                "type": "boolean",
                                "description": "Must be true to confirm database clearing",
                            }
                        },
                        "required": ["confirm"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool calls."""
            try:
                if name == "pdfrag.query_technical_docs":
                    return await self._handle_query(arguments)
                elif name == "pdfrag.add_document":
                    return await self._handle_add_document(arguments)
                elif name == "pdfrag.add_documents":
                    return await self._handle_add_documents(arguments)
                elif name == "pdfrag.list_documents":
                    return await self._handle_list_documents()
                elif name == "pdfrag.get_system_info":
                    return await self._handle_get_system_info()
                elif name == "pdfrag.clear_database":
                    return await self._handle_clear_database(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Tool call failed: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _handle_get_system_info(self) -> list[TextContent]:
        """Handle getting system information."""
        # Get configuration info
        llm_type = self.config.get("llm", {}).get("type", "unknown")
        llm_model = self.config.get("llm", {}).get("model", "unknown")
        embedding_model = self.config.get("embedding", {}).get("model", "unknown")
        vector_db_path = Path(self.config.get("vector_store", {}).get("path", "./data/vector_db"))
        collection_name = self.config.get("vector_store", {}).get(
            "collection_name", "technical_docs"
        )

        # Check component status
        components_status = {
            "Configuration": True,  # Config loaded successfully if we're here
            "LLM Settings": llm_type != "unknown",
            "Embedding Settings": embedding_model != "unknown",
            "Vector DB Path": vector_db_path.parent.exists(),
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
        except Exception:
            mcp_version = "unknown"

        # Format response
        response = "## System Information\n\n"
        response += "**MCP Server**: pdf-rag-mcp v1.0.0\n"
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
                "embedding_model": self.config.get("embedding", {}).get(
                    "model", "sentence-transformers/all-MiniLM-L6-v2"
                ),
                "vector_db_path": vector_db_path,
                "collection_name": self.config.get("vector_store", {}).get(
                    "collection_name", "technical_docs"
                ),
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

    async def _handle_query(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle technical documentation queries."""
        question = arguments.get("question", "")
        top_k = arguments.get("top_k", 5)

        # Input validation
        if not question:
            return [TextContent(type="text", text="Error: No question provided")]

        if len(question) > MAX_QUERY_LENGTH:
            return [
                TextContent(
                    type="text",
                    text=f"Error: Question too long (max {MAX_QUERY_LENGTH} characters)",
                )
            ]

        # Validate top_k
        if not isinstance(top_k, int) or top_k < 1:
            top_k = 5
        elif top_k > MAX_TOP_K:
            top_k = MAX_TOP_K

        # Initialize RAG engine if needed
        try:
            await self._initialize_rag_engine()
        except Exception as e:
            logger.error(f"RAG initialization failed: {e}")
            return [TextContent(type="text", text="Error: Failed to initialize search engine")]

        if not self.rag_engine:
            return [TextContent(type="text", text="Error: Search engine not available")]

        # Get RAG response asynchronously
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, partial(self.rag_engine.query, question, top_k)
            )

            # Format response with sources
            answer = response.answer
            sources = response.sources
            confidence = response.confidence

            formatted_response = f"## Answer\n{answer}\n\n## Sources\n"

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

            return [TextContent(type="text", text=formatted_response)]

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return [
                TextContent(type="text", text="Error: Failed to process query. Please try again.")
            ]

    async def _handle_add_document(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle adding new PDF documents."""
        pdf_path = arguments.get("pdf_path", "")
        document_type = arguments.get("document_type", "unknown")

        # Input validation
        if not pdf_path:
            return [TextContent(type="text", text="Error: No PDF path provided")]

        if len(str(pdf_path)) > MAX_PATH_LENGTH:
            return [TextContent(type="text", text="Error: Path too long")]

        # Sanitize document type
        document_type = str(document_type)[:50].replace("\n", " ").strip()

        # Resolve the path with security check
        try:
            pdf_path = Path(self._resolve_path(pdf_path))
        except ValueError:
            logger.warning(f"Path access denied: {pdf_path}")
            return [TextContent(type="text", text="Error: Access denied to specified path")]

        if not pdf_path.exists():
            return [TextContent(type="text", text="Error: PDF file not found")]

        if not pdf_path.suffix.lower() == ".pdf":
            return [TextContent(type="text", text="Error: Not a PDF file")]

        # Check file size
        file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            return [
                TextContent(type="text", text=f"Error: File too large (max {MAX_FILE_SIZE_MB}MB)")
            ]

        # Initialize RAG engine if needed
        try:
            await self._initialize_rag_engine()
        except Exception as e:
            logger.error(f"RAG initialization failed: {e}")
            return [TextContent(type="text", text="Error: Failed to initialize search engine")]

        if not self.rag_engine:
            return [TextContent(type="text", text="Error: Search engine not available")]

        # Get progress context
        progress_token, context = self._get_progress_context()

        # Send initial progress notification
        await self._send_progress(
            0.1, f"Starting to process {pdf_path.name}", progress_token, context
        )

        # Add document to knowledge base
        try:
            # Send progress update
            await self._send_progress(
                0.5, f"Converting and processing {pdf_path.name}", progress_token, context
            )

            # Run blocking operation in executor
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None, self.rag_engine.add_pdf_document, pdf_path, document_type
            )

            # Send final progress notification
            await self._send_progress(
                1.0, f"Completed processing {pdf_path.name}", progress_token, context
            )

            if success:
                return [
                    TextContent(type="text", text=f"Successfully added document: {pdf_path.name}")
                ]
            else:
                # Send error notification
                await self._send_progress(
                    1.0, f"❌ Failed to add document: {pdf_path.name}", progress_token, context
                )
                return [TextContent(type="text", text=f"Failed to add document: {pdf_path.name}")]

        except Exception as e:
            logger.error(f"Failed to add document: {e}")

            # Send error notification
            await self._send_progress(1.0, "❌ Error processing document", progress_token, context)

            return [TextContent(type="text", text="Error: Failed to add document")]

    async def _handle_add_documents(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle adding multiple PDF documents from a folder."""
        folder_path = arguments.get("folder_path", "")
        document_type = arguments.get("document_type", "unknown")
        recursive = arguments.get("recursive", False)

        # Input validation
        if not folder_path:
            return [TextContent(type="text", text="Error: No folder path provided")]

        if len(str(folder_path)) > MAX_PATH_LENGTH:
            return [TextContent(type="text", text="Error: Path too long")]

        # Sanitize document type
        document_type = str(document_type)[:50].replace("\n", " ").strip()

        # Resolve the path with security check
        try:
            folder_path = Path(self._resolve_path(folder_path))
        except ValueError:
            logger.warning(f"Path access denied: {folder_path}")
            return [TextContent(type="text", text="Error: Access denied to specified path")]

        if not folder_path.exists():
            return [TextContent(type="text", text="Error: Folder not found")]

        if not folder_path.is_dir():
            return [TextContent(type="text", text="Error: Not a directory")]

        # Find all PDF files
        if recursive:
            pdf_files = list(folder_path.rglob("*.pdf"))
        else:
            pdf_files = list(folder_path.glob("*.pdf"))

        if not pdf_files:
            return [TextContent(type="text", text="No PDF files found")]

        # Check file count limit
        if len(pdf_files) > MAX_FILES_PER_BATCH:
            return [
                TextContent(type="text", text=f"Error: Too many files (max {MAX_FILES_PER_BATCH})")
            ]

        # Initialize RAG engine if needed
        try:
            await self._initialize_rag_engine()
        except Exception as e:
            logger.error(f"RAG initialization failed: {e}")
            return [TextContent(type="text", text="Error: Failed to initialize search engine")]

        if not self.rag_engine:
            return [TextContent(type="text", text="Error: Search engine not available")]

        # Get progress context
        progress_token, context = self._get_progress_context()

        # Process each PDF file
        results = []
        success_count = 0
        failed_files = []

        response = f"Processing {len(pdf_files)} PDF files...\n\n"

        for i, pdf_file in enumerate(pdf_files, 1):
            try:
                # Check file size
                file_size_mb = pdf_file.stat().st_size / (1024 * 1024)
                if file_size_mb > MAX_FILE_SIZE_MB:
                    failed_files.append(pdf_file.name)
                    results.append(f"❌ {pdf_file.name} - File too large")
                    continue

                # Send progress notification
                progress = i / len(pdf_files)
                message = f"Processing {pdf_file.name} ({i}/{len(pdf_files)})"
                await self._send_progress(progress, message, progress_token, context)

                # Log progress
                logger.info(f"Processing file {i}/{len(pdf_files)}: {pdf_file.name}")

                # Add document to knowledge base using executor
                loop = asyncio.get_event_loop()
                success = await loop.run_in_executor(
                    None, self.rag_engine.add_pdf_document, pdf_file, document_type
                )

                if success:
                    success_count += 1
                    results.append(f"✅ {pdf_file.name}")
                else:
                    failed_files.append(pdf_file.name)
                    results.append(f"❌ {pdf_file.name} - Failed to process")

                    # Send error notification
                    await self._send_progress(
                        progress, f"❌ Failed to process {pdf_file.name}", progress_token, context
                    )

            except Exception as e:
                logger.error(f"Failed to add document {pdf_file.name}: {e}")
                failed_files.append(pdf_file.name)
                results.append(f"❌ {pdf_file.name} - Processing error")

                # Send error notification
                await self._send_progress(
                    i / len(pdf_files),
                    f"❌ Error processing {pdf_file.name}",
                    progress_token,
                    context,
                )

        # Send final progress notification
        await self._send_progress(
            1.0, f"Completed processing {len(pdf_files)} files", progress_token, context
        )

        # Create summary
        response += "## Results\n\n"
        response += "\n".join(results)
        response += "\n\n## Summary\n"
        response += f"- Total files: {len(pdf_files)}\n"
        response += f"- Successfully added: {success_count}\n"
        response += f"- Failed: {len(failed_files)}\n"

        if failed_files:
            response += "\n## Failed Files\n"
            for file in failed_files:
                response += f"- {file}\n"

        return [TextContent(type="text", text=response)]

    async def _handle_list_documents(self) -> list[TextContent]:
        """Handle listing documents in knowledge base."""
        # Initialize RAG engine if needed
        try:
            await self._initialize_rag_engine()
        except Exception as e:
            logger.error(f"RAG initialization failed: {e}")
            return [TextContent(type="text", text="Error: Failed to initialize search engine")]

        if not self.rag_engine:
            return [TextContent(type="text", text="Error: Search engine not available")]

        try:
            # Run blocking operation in executor
            loop = asyncio.get_event_loop()
            documents = await loop.run_in_executor(None, self.rag_engine.list_documents)

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
            return [TextContent(type="text", text="Error: Failed to list documents")]

    async def _handle_clear_database(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle clearing the database."""
        confirm = arguments.get("confirm", False)

        if not confirm:
            return [
                TextContent(
                    type="text", text="Error: You must set confirm=true to clear the database"
                )
            ]

        # Initialize RAG engine if needed
        try:
            await self._initialize_rag_engine()
        except Exception as e:
            logger.error(f"RAG initialization failed: {e}")
            return [TextContent(type="text", text="Error: Failed to initialize search engine")]

        if not self.rag_engine:
            return [TextContent(type="text", text="Error: Search engine not available")]

        # Get progress context
        progress_token, context = self._get_progress_context()

        try:
            # Get current document count using executor
            loop = asyncio.get_event_loop()
            documents = await loop.run_in_executor(None, self.rag_engine.list_documents)
            doc_count = len(documents)
            total_chunks = sum(doc["chunk_count"] for doc in documents)

            if doc_count == 0:
                return [TextContent(type="text", text="Database is already empty")]

            # Send initial progress notification
            await self._send_progress(
                0.1,
                f"Clearing {doc_count} documents ({total_chunks} chunks)...",
                progress_token,
                context,
            )

            # Clear the database
            logger.info(f"Clearing database with {doc_count} documents and {total_chunks} chunks")

            # Clear the vector store collection using executor
            success = await loop.run_in_executor(
                None, self.rag_engine.vector_store.clear_collection
            )

            # Send final progress notification
            await self._send_progress(1.0, "Database cleared successfully", progress_token, context)

            if success:
                return [
                    TextContent(
                        type="text",
                        text=f"Successfully cleared database. Removed {doc_count} documents ({total_chunks} chunks).",
                    )
                ]
            else:
                return [TextContent(type="text", text="Failed to clear database")]

        except Exception as e:
            logger.error(f"Failed to clear database: {e}")

            # Send error notification
            await self._send_progress(1.0, "❌ Error clearing database", progress_token, context)

            return [TextContent(type="text", text="Error: Failed to clear database")]


async def main():
    """Main entry point for MCP server."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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


# Create global server instance for mcp dev
server = SimplePDFRAGMCPServer().server

if __name__ == "__main__":
    asyncio.run(main())
