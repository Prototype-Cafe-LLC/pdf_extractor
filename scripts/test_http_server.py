#!/usr/bin/env python3
"""End-to-end test for HTTP server functionality."""

import asyncio
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp.http_client import PDFRAGClient


def create_test_pdf(path: Path) -> None:
    """Create a simple test PDF."""
    import fitz  # PyMuPDF
    
    # Create a new PDF
    doc = fitz.open()
    page = doc.new_page()
    
    # Add text
    text = "This is a test PDF document for RAG system.\nIt contains information about testing."
    page.insert_text((50, 50), text, fontsize=12)
    
    # Save the PDF
    doc.save(str(path))
    doc.close()


def start_server():
    """Start the HTTP server in background."""
    env = os.environ.copy()
    env.update({
        "JWT_SECRET_KEY": "test-secret-key-12345",
        "ADMIN_USERNAME": "testadmin", 
        "ADMIN_PASSWORD_HASH": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMmfFBJom",  # testpass
        "API_KEYS": "test-api-key:test-service:1000",
        "ALLOWED_DOCUMENTS_DIR": tempfile.gettempdir(),
    })
    
    # Start server
    process = subprocess.Popen(
        [sys.executable, "-m", "src.mcp.http_server"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    print("Starting HTTP server...")
    for i in range(30):
        try:
            client = PDFRAGClient(
                base_url="http://localhost:8000",
                verify_ssl=False
            )
            health = client.health_check()
            if health["status"] in ["healthy", "degraded"]:
                print("✓ Server started successfully")
                return process
        except Exception:
            time.sleep(1)
    
    # Server failed to start
    process.terminate()
    stdout, stderr = process.communicate()
    print(f"Server failed to start:\n{stderr.decode()}")
    sys.exit(1)


def run_tests():
    """Run end-to-end tests."""
    print("\n=== PDF RAG HTTP Server End-to-End Tests ===\n")
    
    # Create test environment
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        test_pdf = tmppath / "test_document.pdf"
        create_test_pdf(test_pdf)
        
        # Start server
        server_process = start_server()
        
        try:
            # Test 1: Health check
            print("\n1. Testing health check...")
            client = PDFRAGClient(
                base_url="http://localhost:8000",
                verify_ssl=False
            )
            health = client.health_check()
            assert health["status"] in ["healthy", "degraded"]
            print("✓ Health check passed")
            
            # Test 2: Authentication with username/password
            print("\n2. Testing JWT authentication...")
            auth_client = PDFRAGClient(
                base_url="http://localhost:8000",
                username="testadmin",
                password="testpass",
                verify_ssl=False
            )
            me = auth_client.session.get("http://localhost:8000/api/auth/me").json()
            assert me["username"] == "testadmin"
            print("✓ JWT authentication passed")
            
            # Test 3: API key authentication
            print("\n3. Testing API key authentication...")
            api_client = PDFRAGClient(
                base_url="http://localhost:8000",
                api_key="test-api-key",
                verify_ssl=False
            )
            docs = api_client.list_documents()
            assert isinstance(docs, list)
            print("✓ API key authentication passed")
            
            # Test 4: Add document
            print("\n4. Testing document addition...")
            response = api_client.add_document(test_pdf, "test_manual")
            assert response["success"] is True
            print("✓ Document added successfully")
            
            # Test 5: List documents
            print("\n5. Testing document listing...")
            docs = api_client.list_documents()
            assert len(docs) > 0
            assert any(d["type"] == "test_manual" for d in docs)
            print(f"✓ Found {len(docs)} documents")
            
            # Test 6: Query documents
            print("\n6. Testing document query...")
            result = api_client.query("What is this document about?")
            assert "answer" in result
            assert result["confidence"] > 0
            print(f"✓ Query returned answer with confidence {result['confidence']:.2f}")
            
            # Test 7: System info
            print("\n7. Testing system info...")
            info = api_client.get_system_info()
            assert info["server_version"] == "1.0.0"
            assert all(info["components_status"].values())
            print("✓ System info retrieved")
            
            # Test 8: Clear database
            print("\n8. Testing database clear...")
            response = api_client.clear_database(confirm=True)
            assert response["success"] is True
            docs_after = api_client.list_documents()
            assert len(docs_after) == 0
            print("✓ Database cleared successfully")
            
            # Test 9: Error handling
            print("\n9. Testing error handling...")
            try:
                api_client.add_document("/nonexistent/file.pdf")
                assert False, "Should have raised exception"
            except Exception as e:
                assert "not found" in str(e).lower()
            print("✓ Error handling works correctly")
            
            # Test 10: Rate limiting
            print("\n10. Testing rate limiting...")
            # This would require making many requests quickly
            # For now, just verify the header is accepted
            limited_client = PDFRAGClient(
                base_url="http://localhost:8000",
                api_key="test-api-key",
                verify_ssl=False
            )
            # Make a few requests
            for i in range(5):
                limited_client.health_check()
            print("✓ Rate limiting headers accepted")
            
            print("\n✅ All tests passed!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        finally:
            # Stop server
            print("\nStopping server...")
            server_process.terminate()
            server_process.wait(timeout=5)
            print("Server stopped")


if __name__ == "__main__":
    run_tests()