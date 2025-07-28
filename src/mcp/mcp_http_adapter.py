#!/usr/bin/env python3
"""MCP HTTP Transport Adapter for PDF RAG System.

This module provides MCP (Model Context Protocol) HTTP transport endpoints
that allow MCP clients to connect to the PDF RAG system via HTTP.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MCPRequest(BaseModel):
    """MCP JSON-RPC request."""
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    """MCP JSON-RPC response."""
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class MCPHTTPAdapter:
    """Adapter to handle MCP protocol over HTTP transport."""
    
    def __init__(self, rag_engine):
        """Initialize the MCP HTTP adapter.
        
        Args:
            rag_engine: The RAG engine instance
        """
        self.rag_engine = rag_engine
        self.sessions = {}  # Store session state
        self.tools = self._get_tools()
        
    def _get_tools(self) -> list[dict]:
        """Get available MCP tools."""
        return [
            {
                "name": "pdfrag.query_technical_docs",
                "description": "Query the PDF RAG knowledge base for technical documentation answers",
                "inputSchema": {
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
            },
            {
                "name": "pdfrag.add_document",
                "description": "Add a single PDF document to the PDF RAG knowledge base",
                "inputSchema": {
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
            },
            {
                "name": "pdfrag.add_documents",
                "description": "Add multiple PDF documents from a folder to the PDF RAG knowledge base",
                "inputSchema": {
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
            },
            {
                "name": "pdfrag.list_documents",
                "description": "List all PDF documents currently stored in the PDF RAG knowledge base",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "pdfrag.get_system_info",
                "description": "Get PDF RAG system information, configuration, and component status",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "pdfrag.clear_database",
                "description": "Clear the PDF RAG vector database (removes embeddings/chunks only, original PDFs remain untouched)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "confirm": {
                            "type": "boolean",
                            "description": "Must be true to confirm database clearing",
                        }
                    },
                    "required": ["confirm"],
                },
            },
        ]
    
    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Handle tool calls."""
        try:
            if name == "pdfrag.query_technical_docs":
                question = arguments.get("question")
                top_k = arguments.get("top_k", 5)
                    
                if not question:
                    return {
                        "content": [{"type": "text", "text": "Error: Question is required"}],
                        "isError": True,
                    }
                    
                # Execute query
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, self.rag_engine.query, question, top_k
                )
                    
                # Format response
                answer_text = f"**Answer**: {response.answer}\n\n"
                answer_text += f"**Confidence**: {response.confidence:.2f}\n\n"
                    
                if response.sources:
                    answer_text += "**Sources**:\n"
                    for source in response.sources:
                        answer_text += f"- {source.get('document', 'Unknown')} "
                        if 'page' in source:
                            answer_text += f"(page {source['page']})"
                        answer_text += "\n"
                    
                return {
                    "content": [{"type": "text", "text": answer_text}],
                    "isError": False
                }
            
            elif name == "pdfrag.add_document":
                pdf_path = arguments.get("pdf_path")
                document_type = arguments.get("document_type", "unknown")
                
                if not pdf_path:
                    return {
                        "content": [{"type": "text", "text": "Error: pdf_path is required"}],
                        "isError": True,
                    }
                
                path = Path(pdf_path)
                
                if not path.exists():
                    return {
                        "content": [{"type": "text", "text": f"Error: PDF file not found: {pdf_path}"}],
                        "isError": True,
                    }
                
                if not path.suffix.lower() == ".pdf":
                    return {
                        "content": [{"type": "text", "text": f"Error: Not a PDF file: {pdf_path}"}],
                        "isError": True,
                    }
                
                # Add document
                loop = asyncio.get_event_loop()
                success = await loop.run_in_executor(
                    None, self.rag_engine.add_pdf_document, path, document_type
                )
                
                if success:
                    return {
                        "content": [{"type": "text", "text": f"Successfully added document: {path.name}"}],
                        "isError": False
                    }
                else:
                    return {
                        "content": [{"type": "text", "text": f"Failed to add document: {path.name}"}],
                        "isError": True
                    }
                
            elif name == "pdfrag.add_documents":
                folder_path = arguments.get("folder_path")
                document_type = arguments.get("document_type", "unknown")
                recursive = arguments.get("recursive", False)
                
                if not folder_path:
                    return {
                        "content": [{"type": "text", "text": "Error: folder_path is required"}],
                        "isError": True,
                    }
                
                folder = Path(folder_path)
                
                if not folder.exists():
                    return {
                        "content": [{"type": "text", "text": f"Error: Folder not found: {folder_path}"}],
                        "isError": True,
                    }
                
                if not folder.is_dir():
                    return {
                        "content": [{"type": "text", "text": f"Error: Not a directory: {folder_path}"}],
                        "isError": True,
                    }
                
                # Find all PDF files
                if recursive:
                    pdf_files = list(folder.rglob("*.pdf"))
                else:
                    pdf_files = list(folder.glob("*.pdf"))
                
                if not pdf_files:
                    return {
                        "content": [{"type": "text", "text": f"No PDF files found in {folder_path}"}],
                        "isError": False
                    }
                
                # Add documents
                success_count = 0
                failed_files = []
                
                for pdf_file in pdf_files:
                    try:
                        loop = asyncio.get_event_loop()
                        success = await loop.run_in_executor(
                            None, self.rag_engine.add_pdf_document, pdf_file, document_type
                        )
                        if success:
                            success_count += 1
                        else:
                            failed_files.append(pdf_file.name)
                    except Exception as e:
                        logger.error(f"Failed to add {pdf_file.name}: {e}")
                        failed_files.append(pdf_file.name)
                
                result_text = f"Processed {len(pdf_files)} files.\n"
                result_text += f"Successfully added: {success_count}\n"
                result_text += f"Failed: {len(failed_files)}"
                
                if failed_files:
                    result_text += f"\n\nFailed files:\n"
                    for f in failed_files[:10]:  # Show first 10
                        result_text += f"- {f}\n"
                    if len(failed_files) > 10:
                        result_text += f"... and {len(failed_files) - 10} more"
                
                return {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": len(failed_files) > 0
                }
            
            elif name == "pdfrag.list_documents":
                loop = asyncio.get_event_loop()
                documents = await loop.run_in_executor(
                    None, self.rag_engine.list_documents
                )
                    
                if not documents:
                    return {
                        "content": [{"type": "text", "text": "No documents found in the knowledge base."}],
                        "isError": False
                    }
                    
                doc_list = "**Documents in Knowledge Base**:\n\n"
                for doc in documents:
                    doc_list += f"- **{doc['document']}**\n"
                    doc_list += f"  - Type: {doc.get('type', 'unknown')}\n"
                    doc_list += f"  - Chunks: {doc.get('chunk_count', 0)}\n"
                    doc_list += f"  - Source: {doc.get('source', 'N/A')}\n\n"
                    
                return {
                    "content": [{"type": "text", "text": doc_list}],
                    "isError": False
                }
                
            elif name == "pdfrag.get_system_info":
                system_info = self.rag_engine.get_system_info()
                test_results = self.rag_engine.test_components()
                    
                info_text = "**System Information**:\n\n"
                info_text += "**Component Status**:\n"
                for component, status in test_results.items():
                    status_emoji = "✅" if status else "❌"
                    info_text += f"- {component}: {status_emoji}\n"
                    
                info_text += f"\n**Configuration**:\n"
                info_text += f"- LLM: {system_info.get('llm_type', 'unknown')} ({system_info.get('llm_model', 'unknown')})\n"
                info_text += f"- Embedding Model: {system_info.get('embedding_model', 'unknown')}\n"
                info_text += f"- Collection: {system_info.get('collection_name', 'unknown')}\n"
                    
                return {
                    "content": [{"type": "text", "text": info_text}],
                    "isError": False
                }
            
            elif name == "pdfrag.clear_database":
                confirm = arguments.get("confirm", False)
                
                if not confirm:
                    return {
                        "content": [{"type": "text", "text": "Error: You must set confirm=true to clear the database"}],
                        "isError": True,
                    }
                
                # Get current document count first
                loop = asyncio.get_event_loop()
                documents = await loop.run_in_executor(
                    None, self.rag_engine.list_documents
                )
                doc_count = len(documents)
                total_chunks = sum(doc.get("chunk_count", 0) for doc in documents)
                
                if doc_count == 0:
                    return {
                        "content": [{"type": "text", "text": "Database is already empty"}],
                        "isError": False
                    }
                
                # Clear the database
                success = await loop.run_in_executor(
                    None, self.rag_engine.vector_store.clear_collection
                )
                
                if success:
                    return {
                        "content": [{"type": "text", "text": f"Successfully cleared database. Removed {doc_count} documents ({total_chunks} chunks)."}],
                        "isError": False
                    }
                else:
                    return {
                        "content": [{"type": "text", "text": "Failed to clear database"}],
                        "isError": True
                    }
                
            else:
                return {
                    "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
                    "isError": True,
                }
                    
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True,
            }
    
    async def handle_mcp_request(self, request: Request) -> JSONResponse:
        """Handle MCP JSON-RPC requests.
        
        Args:
            request: FastAPI request object
            
        Returns:
            JSON-RPC response
        """
        try:
            # Parse request body
            body = await request.json()
            mcp_request = MCPRequest(**body)
            
            # Get or create session
            session_id = request.headers.get("X-Session-ID", str(uuid4()))
            
            # Handle different methods
            if mcp_request.method == "initialize":
                # Initialize session
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "pdf-rag-mcp-http",
                        "version": "1.0.0"
                    }
                }
                
            elif mcp_request.method == "tools/list":
                # List available tools
                result = {
                    "tools": self.tools
                }
                
            elif mcp_request.method == "tools/call":
                # Call a tool
                params = mcp_request.params or {}
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if not tool_name:
                    raise ValueError("Tool name is required")
                
                tool_result = await self.call_tool(tool_name, arguments)
                
                # Tool result is already in the right format
                result = tool_result
                
            else:
                # Unknown method
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": mcp_request.id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {mcp_request.method}"
                        }
                    },
                    status_code=200,
                    headers={"X-Session-ID": session_id}
                )
            
            # Return successful response
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": mcp_request.id,
                    "result": result
                },
                status_code=200,
                headers={"X-Session-ID": session_id}
            )
            
        except json.JSONDecodeError:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                },
                status_code=200
            )
        except Exception as e:
            logger.error(f"MCP request error: {e}", exc_info=True)
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": getattr(mcp_request, 'id', None) if 'mcp_request' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                },
                status_code=200
            )
    
    async def handle_sse_request(self, request: Request):
        """Handle Server-Sent Events (SSE) for MCP.
        
        Args:
            request: FastAPI request object
            
        Returns:
            SSE streaming response
        """
        session_id = request.headers.get("X-Session-ID", str(uuid4()))
        
        async def event_generator():
            """Generate SSE events."""
            try:
                # Send initial connection event
                yield f"data: {json.dumps({'type': 'connection', 'status': 'connected'})}\n\n"
                
                # Keep connection alive
                while True:
                    await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    
            except asyncio.CancelledError:
                logger.info(f"SSE connection closed for session {session_id}")
                raise
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Session-ID": session_id
            }
        )