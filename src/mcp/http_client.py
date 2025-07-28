"""Python client SDK for PDF RAG HTTP Server.

This module provides a Python client for easy integration with the
PDF RAG HTTP API server.
"""

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class PDFRAGClient:
    """Client for PDF RAG HTTP API."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        verify_ssl: bool = True,
    ):
        """Initialize the PDF RAG client.

        Args:
            base_url: Base URL of the API server
            api_key: API key for authentication
            username: Username for JWT authentication
            password: Password for JWT authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_key = api_key
        self.jwt_token = None
        self.verify_ssl = verify_ssl
        
        # Setup session with retry strategy
        self.session = requests.Session()
        self.session.verify = verify_ssl
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],
            backoff_factor=1,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        
        # Authenticate if credentials provided
        if username and password:
            self.login(username, password)
        elif api_key:
            self.session.headers["X-API-Key"] = api_key

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login with username and password to get JWT token.

        Args:
            username: Username
            password: Password

        Returns:
            Token response

        Raises:
            requests.HTTPError: If login fails
        """
        response = self.session.post(
            f"{self.base_url}/api/auth/login",
            json={"username": username, "password": password},
            timeout=self.timeout,
        )
        response.raise_for_status()
        
        data = response.json()
        self.jwt_token = data["access_token"]
        self.session.headers["Authorization"] = f"Bearer {self.jwt_token}"
        
        logger.info(f"Successfully authenticated as {username}")
        return data

    def query(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """Query the technical documentation.

        Args:
            question: Question to search for
            top_k: Number of relevant chunks to retrieve

        Returns:
            Query response with answer and sources

        Raises:
            requests.HTTPError: If query fails
        """
        response = self.session.post(
            f"{self.base_url}/api/query",
            json={"question": question, "top_k": top_k},
            timeout=self.timeout,
        )
        response.raise_for_status()
        
        return response.json()

    def add_document(self, pdf_path: Union[str, Path], document_type: str = "unknown") -> Dict[str, Any]:
        """Add a PDF document to the knowledge base.

        Args:
            pdf_path: Path to PDF file
            document_type: Type of document (e.g., 'manual', 'specification')

        Returns:
            Operation response

        Raises:
            requests.HTTPError: If operation fails
            FileNotFoundError: If PDF file not found
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        response = self.session.post(
            f"{self.base_url}/api/documents",
            json={"pdf_path": str(pdf_path.absolute()), "document_type": document_type},
            timeout=self.timeout,
        )
        response.raise_for_status()
        
        return response.json()

    def add_documents_batch(
        self,
        folder_path: Union[str, Path],
        document_type: str = "unknown",
        recursive: bool = False
    ) -> Dict[str, Any]:
        """Add multiple PDF documents from a folder.

        Args:
            folder_path: Path to folder containing PDFs
            document_type: Default type for all documents
            recursive: Whether to search recursively

        Returns:
            Operation response

        Raises:
            requests.HTTPError: If operation fails
            FileNotFoundError: If folder not found
        """
        folder_path = Path(folder_path)
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        response = self.session.post(
            f"{self.base_url}/api/documents/batch",
            json={
                "folder_path": str(folder_path.absolute()),
                "document_type": document_type,
                "recursive": recursive,
            },
            timeout=self.timeout * 10,  # Longer timeout for batch operations
        )
        response.raise_for_status()
        
        return response.json()

    def upload_document(
        self,
        file_path: Union[str, Path],
        document_type: str = "unknown"
    ) -> Dict[str, Any]:
        """Upload a PDF document to the server.

        Args:
            file_path: Path to PDF file to upload
            document_type: Type of document

        Returns:
            Operation response

        Raises:
            requests.HTTPError: If upload fails
            FileNotFoundError: If file not found
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "application/pdf")}
            data = {"document_type": document_type}
            
            # Temporarily remove Content-Type header for multipart
            headers = self.session.headers.copy()
            headers.pop("Content-Type", None)
            
            response = self.session.post(
                f"{self.base_url}/api/documents/upload",
                files=files,
                data=data,
                headers=headers,
                timeout=self.timeout * 5,  # Longer timeout for uploads
            )
        
        response.raise_for_status()
        return response.json()

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the knowledge base.

        Returns:
            List of documents

        Raises:
            requests.HTTPError: If operation fails
        """
        response = self.session.get(
            f"{self.base_url}/api/documents",
            timeout=self.timeout,
        )
        response.raise_for_status()
        
        data = response.json()
        return data["documents"]

    def get_system_info(self) -> Dict[str, Any]:
        """Get system information and component status.

        Returns:
            System information

        Raises:
            requests.HTTPError: If operation fails
        """
        response = self.session.get(
            f"{self.base_url}/api/system/info",
            timeout=self.timeout,
        )
        response.raise_for_status()
        
        return response.json()

    def clear_database(self, confirm: bool = False) -> Dict[str, Any]:
        """Clear the vector database.

        Args:
            confirm: Must be True to confirm operation

        Returns:
            Operation response

        Raises:
            requests.HTTPError: If operation fails
            ValueError: If confirm is not True
        """
        if not confirm:
            raise ValueError("You must set confirm=True to clear the database")
        
        response = self.session.delete(
            f"{self.base_url}/api/database",
            json={"confirm": confirm},
            timeout=self.timeout,
        )
        response.raise_for_status()
        
        return response.json()

    def health_check(self) -> Dict[str, Any]:
        """Check server health.

        Returns:
            Health status

        Raises:
            requests.HTTPError: If server is unhealthy
        """
        response = self.session.get(
            f"{self.base_url}/api/health",
            timeout=5,
        )
        response.raise_for_status()
        
        return response.json()

    def close(self):
        """Close the client session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Example usage
if __name__ == "__main__":
    # Example 1: Using API key from environment
    api_key = os.environ.get("PDF_RAG_API_KEY")
    if api_key:
        with PDFRAGClient(api_key=api_key) as client:
            # Check health
            health = client.health_check()
            print(f"Server status: {health['status']}")
            
            # Query documents
            result = client.query("How do I configure the RAG system?")
            print(f"Answer: {result['answer']}")
            print(f"Confidence: {result['confidence']}")
            
            # List documents
            docs = client.list_documents()
            print(f"Total documents: {len(docs)}")
    
    # Example 2: Using username/password from environment
    username = os.environ.get("PDF_RAG_USERNAME")
    password = os.environ.get("PDF_RAG_PASSWORD")
    if username and password:
        with PDFRAGClient(username=username, password=password) as client:
            # Add a document
            response = client.add_document("/path/to/document.pdf", "manual")
            print(f"Add document: {response['message']}")
            
            # Upload a document
            response = client.upload_document("/path/to/upload.pdf", "specification")
            print(f"Upload document: {response['message']}")
            
            # Get system info
            info = client.get_system_info()
            print(f"Server version: {info['server_version']}")
            print(f"Components: {info['components_status']}")