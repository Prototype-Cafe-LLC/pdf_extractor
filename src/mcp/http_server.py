#!/usr/bin/env python3
"""HTTP Server for PDF RAG System.

This module provides an HTTP-based API server that enables
RAG-powered technical documentation queries through RESTful endpoints.
"""

import asyncio
import logging
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
import yaml
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

try:
    # Try relative import (when run as module)
    from ..rag_engine.retrieval import RAGEngine
    from .auth import get_current_user, User, auth_router
    from .logging_config import configure_mcp_logging, log_system_info
    from .mcp_http_adapter import MCPHTTPAdapter
except ImportError:
    # Fall back to absolute import (when run directly)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.rag_engine.retrieval import RAGEngine
    from src.mcp.auth import get_current_user, User, auth_router
    from src.mcp.logging_config import configure_mcp_logging, log_system_info
    from src.mcp.mcp_http_adapter import MCPHTTPAdapter

# Configure logger with rotation
logger = configure_mcp_logging(server_type="http", enable_console=True)

# Constants for resource limits
MAX_FILES_PER_BATCH = 100
MAX_FILE_SIZE_MB = 50
MAX_QUERY_LENGTH = 1000
MAX_TOP_K = 20


class QueryRequest(BaseModel):
    """Request model for document queries."""
    question: str = Field(..., description="Question to search for in the PDF knowledge base", max_length=MAX_QUERY_LENGTH)
    top_k: int = Field(5, description="Number of relevant chunks to retrieve", ge=1, le=MAX_TOP_K)


class AddDocumentRequest(BaseModel):
    """Request model for adding a single document."""
    pdf_path: str = Field(..., description="Path to PDF file to add")
    document_type: str = Field("unknown", description="Type of document (e.g., 'manual', 'specification', 'guide')", max_length=50)


class AddDocumentsRequest(BaseModel):
    """Request model for adding multiple documents from a folder."""
    folder_path: str = Field(..., description="Path to folder containing PDF files")
    document_type: str = Field("unknown", description="Default type for all documents", max_length=50)
    recursive: bool = Field(False, description="Whether to search for PDFs recursively in subfolders")


class ClearDatabaseRequest(BaseModel):
    """Request model for clearing the database."""
    confirm: bool = Field(..., description="Must be true to confirm database clearing")


class QueryResponse(BaseModel):
    """Response model for document queries."""
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    processing_time: Optional[float] = None


class DocumentResponse(BaseModel):
    """Response model for document operations."""
    message: str
    success: bool


class DocumentListResponse(BaseModel):
    """Response model for listing documents."""
    documents: List[Dict[str, Any]]
    total_count: int


class SystemInfoResponse(BaseModel):
    """Response model for system information."""
    server_version: str
    components_status: Dict[str, bool]
    configuration: Dict[str, Any]
    features: List[str]


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    version: str
    components: Dict[str, bool]


class PDFRAGHTTPServer:
    """HTTP Server for PDF RAG system."""

    def __init__(self):
        """Initialize the HTTP server."""
        # Get project root directory (two levels up from src/mcp/)
        self._project_root = Path(__file__).parent.parent.parent
        self.rag_engine = None
        self.mcp_adapter = None
        self.config = self._load_config()
        
        # SECURITY: Define allowed base directories for file operations
        default_doc_dir = Path.home() / ".pdf_rag" / "documents"
        self._allowed_dirs = [
            Path(os.environ.get("ALLOWED_DOCUMENTS_DIR", str(default_doc_dir))).resolve(),
            Path(tempfile.gettempdir()).resolve(),
        ]
        
        # Create allowed directories if they don't exist
        for dir_path in self._allowed_dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

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

        # Load HTTP server config
        http_config_path = self._project_root / "config" / "http_server_config.yaml"
        if http_config_path.exists():
            try:
                with open(http_config_path) as f:
                    config.update(yaml.safe_load(f))
                logger.info("Loaded HTTP server configuration")
            except Exception as e:
                logger.error(f"Failed to load HTTP server config: {e}")

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

    def _validate_path(self, path: Path) -> Path:
        """Validate that a path is within allowed directories.
        
        Args:
            path: Path to validate
            
        Returns:
            Resolved absolute path
            
        Raises:
            HTTPException: If path is not allowed
        """
        try:
            # Resolve to absolute path
            resolved_path = path.resolve()
            
            # Check if path is within any allowed directory
            for allowed_dir in self._allowed_dirs:
                try:
                    resolved_path.relative_to(allowed_dir)
                    return resolved_path
                except ValueError:
                    continue
                    
            # Path is not in any allowed directory
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to this path is not allowed"
            )
        except Exception as e:
            logger.error(f"Path validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid path"
            )

    async def initialize_rag_engine(self):
        """Initialize the RAG engine."""
        if self.rag_engine:
            return

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
            
            # Initialize MCP adapter
            self.mcp_adapter = MCPHTTPAdapter(self.rag_engine)
            logger.info("MCP HTTP adapter initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {e}")
            self.rag_engine = None
            self.mcp_adapter = None
            raise


# Create server instance
server = PDFRAGHTTPServer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    log_system_info(logger)
    logger.info("Starting PDF RAG HTTP Server...")
    await server.initialize_rag_engine()
    yield
    # Shutdown
    logger.info("Shutting down PDF RAG HTTP Server...")


# Create FastAPI app
app = FastAPI(
    title="PDF RAG HTTP Server",
    description="HTTP API for PDF RAG-powered technical documentation queries",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=server.config.get("http_server", {}).get("cors_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication router
app.include_router(auth_router)


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    components = {
        "rag_engine": server.rag_engine is not None,
        "configuration": bool(server.config),
    }
    
    return HealthResponse(
        status="healthy" if all(components.values()) else "degraded",
        version="1.0.0",
        components=components
    )


# MCP Protocol Endpoints
@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Handle MCP JSON-RPC requests."""
    if not server.mcp_adapter:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MCP adapter not available"
        )
    
    return await server.mcp_adapter.handle_mcp_request(request)


@app.get("/mcp")
async def mcp_sse_endpoint(request: Request):
    """Handle MCP Server-Sent Events (SSE) connections."""
    if not server.mcp_adapter:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MCP adapter not available"
        )
    
    return await server.mcp_adapter.handle_sse_request(request)


@app.post("/api/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    current_user: User = Depends(get_current_user)
):
    """Query technical documentation."""
    logger.info(f"Query request from user {current_user.username} - Question length: {len(request.question)}, top_k: {request.top_k}")

    if not server.rag_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG engine not available"
        )

    try:
        # Get RAG response
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, server.rag_engine.query, request.question, request.top_k
        )
        
        logger.info(f"Query completed - Confidence: {response.confidence:.2f}, Sources: {len(response.sources)}")

        return QueryResponse(
            answer=response.answer,
            sources=response.sources,
            confidence=response.confidence,
            processing_time=response.processing_time
        )

    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process query"
        )


@app.post("/api/documents", response_model=DocumentResponse)
async def add_document(
    request: AddDocumentRequest,
    current_user: User = Depends(get_current_user)
):
    """Add a single PDF document to the knowledge base."""
    logger.info(f"Add document request from user {current_user.username} - Type: {request.document_type}")

    if not server.rag_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG engine not available"
        )

    # SECURITY: Validate and sanitize the path
    try:
        pdf_path = server._validate_path(Path(request.pdf_path))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path"
        )

    if not pdf_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found"
        )

    if not pdf_path.suffix.lower() == ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not a PDF file"
        )

    # Check file size
    file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large (max {MAX_FILE_SIZE_MB}MB)"
        )

    try:
        # Add document using executor
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(
            None, server.rag_engine.add_pdf_document, pdf_path, request.document_type
        )

        if success:
            logger.info(f"Successfully added document: {pdf_path.name}")
            return DocumentResponse(
                message=f"Successfully added document: {pdf_path.name}",
                success=True
            )
        else:
            logger.error(f"Failed to add document: {pdf_path.name}")
            return DocumentResponse(
                message=f"Failed to add document: {pdf_path.name}",
                success=False
            )

    except Exception as e:
        logger.error(f"Failed to add document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add document"
        )


@app.post("/api/documents/batch", response_model=DocumentResponse)
async def add_documents_batch(
    request: AddDocumentsRequest,
    current_user: User = Depends(get_current_user)
):
    """Add multiple PDF documents from a folder to the knowledge base."""
    logger.info(f"Add documents batch request from user {current_user.username}")

    if not server.rag_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG engine not available"
        )

    # SECURITY: Validate and sanitize the path
    try:
        folder_path = server._validate_path(Path(request.folder_path))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid folder path"
        )

    if not folder_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )

    if not folder_path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not a directory"
        )

    # Find all PDF files
    if request.recursive:
        pdf_files = list(folder_path.rglob("*.pdf"))
    else:
        pdf_files = list(folder_path.glob("*.pdf"))

    if not pdf_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No PDF files found"
        )

    if len(pdf_files) > MAX_FILES_PER_BATCH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many files (max {MAX_FILES_PER_BATCH})"
        )

    # Process files
    success_count = 0
    failed_files = []

    for pdf_file in pdf_files:
        try:
            # Check file size
            file_size_mb = pdf_file.stat().st_size / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                failed_files.append(pdf_file.name)
                continue

            # Add document
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                None, server.rag_engine.add_pdf_document, pdf_file, request.document_type
            )

            if success:
                success_count += 1
            else:
                failed_files.append(pdf_file.name)

        except Exception as e:
            logger.error(f"Failed to add document {pdf_file.name}: {e}")
            failed_files.append(pdf_file.name)

    message = f"Processed {len(pdf_files)} files. Successfully added: {success_count}, Failed: {len(failed_files)}"
    if failed_files:
        message += f". Failed files: {', '.join(failed_files[:5])}"
        if len(failed_files) > 5:
            message += f" and {len(failed_files) - 5} more"

    return DocumentResponse(
        message=message,
        success=len(failed_files) == 0
    )


@app.post("/api/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("unknown"),
    current_user: User = Depends(get_current_user)
):
    """Upload and add a PDF document to the knowledge base."""
    logger.info(f"Upload document request from user {current_user.username} - File: {file.filename}, Type: {document_type}")

    if not server.rag_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG engine not available"
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )

    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    file_size_mb = file_size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large (max {MAX_FILE_SIZE_MB}MB)"
        )

    # SECURITY: Create secure temporary file
    try:
        # Use secure temporary file creation
        with tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False,
            dir=server._allowed_dirs[1]  # Use temp directory
        ) as tmp_file:
            temp_path = Path(tmp_file.name)
            content = await file.read()
            tmp_file.write(content)

        # Add document
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(
            None, server.rag_engine.add_pdf_document, temp_path, document_type
        )

        if success:
            logger.info(f"Successfully added uploaded document: {file.filename}")
            return DocumentResponse(
                message=f"Successfully added document: {file.filename}",
                success=True
            )
        else:
            logger.error(f"Failed to add uploaded document: {file.filename}")
            return DocumentResponse(
                message=f"Failed to add document: {file.filename}",
                success=False
            )

    except Exception as e:
        logger.error(f"Failed to process uploaded document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process uploaded document"
        )
    finally:
        # Clean up temporary file
        if temp_path.exists():
            temp_path.unlink()


@app.get("/api/documents", response_model=DocumentListResponse)
async def list_documents(
    current_user: User = Depends(get_current_user)
):
    """List all documents in the knowledge base."""
    logger.info(f"List documents request from user {current_user.username}")

    if not server.rag_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG engine not available"
        )

    try:
        # Get documents list
        loop = asyncio.get_event_loop()
        documents = await loop.run_in_executor(None, server.rag_engine.list_documents)

        return DocumentListResponse(
            documents=documents,
            total_count=len(documents)
        )

    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents"
        )


@app.get("/api/system/info", response_model=SystemInfoResponse)
async def get_system_info(
    current_user: User = Depends(get_current_user)
):
    """Get system information and component status."""
    logger.info(f"System info request from user {current_user.username}")

    if not server.rag_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG engine not available"
        )

    try:
        # Get system info
        system_info = server.rag_engine.get_system_info()
        test_results = server.rag_engine.test_components()

        # Format configuration
        config_info = {
            "llm_type": server.config.get("llm", {}).get("type", "unknown"),
            "llm_model": server.config.get("llm", {}).get("model", "unknown"),
            "embedding_model": server.config.get("embedding", {}).get("model", "unknown"),
            "collection_name": server.config.get("vector_store", {}).get("collection_name", "unknown"),
        }

        return SystemInfoResponse(
            server_version="1.0.0",
            components_status=test_results,
            configuration=config_info,
            features=[
                "Query technical documentation using RAG",
                "Add PDF documents to knowledge base",
                "Upload PDF files via API",
                "List all documents in the system",
                "Get system status and configuration",
                "JWT-based authentication",
                "CORS support for web clients"
            ]
        )

    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system information"
        )


@app.delete("/api/database", response_model=DocumentResponse)
async def clear_database(
    request: ClearDatabaseRequest,
    current_user: User = Depends(get_current_user)
):
    """Clear the vector database."""
    logger.info(f"Clear database request from user {current_user.username}")

    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must set confirm=true to clear the database"
        )

    if not server.rag_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG engine not available"
        )

    try:
        # Get current document count
        loop = asyncio.get_event_loop()
        documents = await loop.run_in_executor(None, server.rag_engine.list_documents)
        doc_count = len(documents)
        total_chunks = sum(doc["chunk_count"] for doc in documents)

        if doc_count == 0:
            return DocumentResponse(
                message="Database is already empty",
                success=True
            )

        # Clear the database
        logger.info(f"Clearing database with {doc_count} documents and {total_chunks} chunks")
        success = await loop.run_in_executor(
            None, server.rag_engine.vector_store.clear_collection
        )

        if success:
            return DocumentResponse(
                message=f"Successfully cleared database. Removed {doc_count} documents ({total_chunks} chunks).",
                success=True
            )
        else:
            return DocumentResponse(
                message="Failed to clear database",
                success=False
            )

    except Exception as e:
        logger.error(f"Failed to clear database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear database"
        )


def main():
    """Main entry point for HTTP server."""
    # Get server configuration
    host = server.config.get("http_server", {}).get("host", "0.0.0.0")
    port = server.config.get("http_server", {}).get("port", 8000)
    workers = server.config.get("http_server", {}).get("workers", 1)
    
    # Run server
    if workers > 1:
        uvicorn.run(
            "src.mcp.http_server:app",
            host=host,
            port=port,
            workers=workers,
            log_config=None  # Use our custom logging
        )
    else:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_config=None  # Use our custom logging
        )


if __name__ == "__main__":
    main()