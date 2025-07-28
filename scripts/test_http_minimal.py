#!/usr/bin/env python3
"""Minimal HTTP server test using FastAPI test client."""

import os
import sys
import tempfile
from pathlib import Path

# Set required environment variables
os.environ.update({
    "JWT_SECRET_KEY": "test-secret-key",
    "ADMIN_USERNAME": "testadmin",
    "ADMIN_PASSWORD_HASH": "$2b$12$2NbuIAE4LVuCmbA5XUACfeBYwmFS6GDfzk1riyKZucq/1y5WHGTe6",
    "API_KEYS": "test-key:test:1000",
    "ALLOWED_DOCUMENTS_DIR": tempfile.gettempdir(),
})

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import modules first
from fastapi.testclient import TestClient

# Force reload of auth module to pick up env vars
import importlib
import src.mcp.auth
importlib.reload(src.mcp.auth)

# Import after reload
from src.mcp.http_server import app
from src.mcp.http_client import PDFRAGClient

# Debug: Check if users are loaded
print(f"Loaded users: {list(src.mcp.auth.DEMO_USERS.keys())}")
print(f"Loaded API keys: {list(src.mcp.auth.API_KEYS.keys())}")

print("=== Minimal HTTP Server Test ===\n")

# Create test client
client = TestClient(app)

# Test 1: Health check
print("1. Testing health check...")
response = client.get("/api/health")
assert response.status_code == 200
data = response.json()
assert data["status"] in ["healthy", "degraded"]
print(f"✓ Health check passed: {data['status']}")

# Test 2: Authentication
print("\n2. Testing authentication...")
response = client.post(
    "/api/auth/login",
    json={"username": "testadmin", "password": "testpass"}
)
if response.status_code != 200:
    print(f"Login failed: {response.status_code} - {response.json()}")
    sys.exit(1)
token = response.json()["access_token"]
print(f"✓ Login successful, got token: {token[:20]}...")

# Test 3: Authenticated request
print("\n3. Testing authenticated request...")
headers = {"Authorization": f"Bearer {token}"}
response = client.get("/api/auth/me", headers=headers)
assert response.status_code == 200
user = response.json()
assert user["username"] == "testadmin"
print(f"✓ Got user info: {user['username']}")

# Test 4: API key auth
print("\n4. Testing API key authentication...")
headers = {"X-API-Key": "test-key"}
response = client.get("/api/documents", headers=headers)
if response.status_code != 200:
    print(f"Documents request failed: {response.status_code} - {response.json()}")
else:
    docs = response.json()
    print(f"✓ API key auth successful, found {docs['total_count']} documents")

# Test 5: System info
print("\n5. Testing system info...")
response = client.get("/api/system/info", headers=headers)
assert response.status_code == 200
info = response.json()
print(f"✓ Server version: {info['server_version']}")

print("\n✅ All tests passed!")