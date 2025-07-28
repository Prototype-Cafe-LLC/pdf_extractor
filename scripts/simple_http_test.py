#!/usr/bin/env python3
"""Simple test to verify HTTP server starts correctly."""

import os
import sys
from pathlib import Path

# Set required environment variables
os.environ.update({
    "JWT_SECRET_KEY": "test-secret-key",
    "ADMIN_USERNAME": "testadmin",
    "ADMIN_PASSWORD_HASH": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMmfFBJom",
    "API_KEYS": "test-key:test:1000",
})

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    print("Testing HTTP server imports...")
    from src.mcp.http_server import app, server
    print("✓ HTTP server imported successfully")
    
    print("\nTesting authentication module...")
    from src.mcp.auth import get_current_user, create_access_token
    print("✓ Authentication module imported successfully")
    
    print("\nTesting client SDK...")
    from src.mcp.http_client import PDFRAGClient
    print("✓ Client SDK imported successfully")
    
    print("\nCreating test token...")
    token = create_access_token({"sub": "testadmin"})
    print(f"✓ Created JWT token: {token[:20]}...")
    
    print("\n✅ All imports and basic functionality work!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)