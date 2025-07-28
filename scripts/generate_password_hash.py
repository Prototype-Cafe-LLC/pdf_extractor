#!/usr/bin/env python3
"""Generate bcrypt password hash for HTTP server authentication.

This script helps generate secure password hashes for use with the
PDF RAG HTTP server authentication system.
"""

import sys
from getpass import getpass
from passlib.context import CryptContext

# Create password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main():
    """Generate password hash."""
    print("PDF RAG HTTP Server - Password Hash Generator")
    print("=" * 45)
    print()
    
    # Get password from user
    password = getpass("Enter password: ")
    confirm = getpass("Confirm password: ")
    
    if password != confirm:
        print("ERROR: Passwords do not match!")
        sys.exit(1)
    
    if len(password) < 8:
        print("ERROR: Password must be at least 8 characters long!")
        sys.exit(1)
    
    # Generate hash
    hash_value = pwd_context.hash(password)
    
    print()
    print("Generated password hash:")
    print("-" * 45)
    print(hash_value)
    print("-" * 45)
    print()
    print("To use this hash, set the following environment variable:")
    print(f'export ADMIN_PASSWORD_HASH="{hash_value}"')
    print()
    print("Make sure to also set:")
    print("- JWT_SECRET_KEY: A secure random string")
    print("- ADMIN_USERNAME: Your admin username")
    print("- API_KEYS: Your API keys (format: api_key:service_name:rate_limit_per_hour)")
    print("  Example: sk-prod-123:production-web:10000,sk-dev-456:development:1000")


if __name__ == "__main__":
    main()