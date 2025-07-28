#!/bin/bash

# PDF RAG HTTP Server Startup Script

# Generate JWT secret if not set
if [ -z "$JWT_SECRET_KEY" ]; then
    export JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
    echo "Generated JWT_SECRET_KEY: $JWT_SECRET_KEY"
    echo "Save this key securely for future use!"
fi

# Activate virtual environment
source .venv/bin/activate

# Start the HTTP server
echo "Starting PDF RAG HTTP Server on port 8080..."
python -m src.mcp.http_server