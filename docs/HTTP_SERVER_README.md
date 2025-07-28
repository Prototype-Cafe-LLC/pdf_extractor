# PDF RAG HTTP Server Documentation

This document provides comprehensive documentation for the PDF RAG HTTP Server,
including API endpoints, authentication, deployment, and usage examples.

**Important**: This HTTP server now supports both REST API and MCP protocol:

- **REST API** (`/api/*` endpoints): For web applications, team collaboration,
  and service-to-service communication
- **MCP Protocol** (`/mcp` endpoint): For MCP clients like Claude Desktop
  using HTTP transport

For local MCP client integration using stdio transport, see the main README.md
and use `src.mcp.simple_server` instead.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
- [Python Client SDK](#python-client-sdk)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The PDF RAG HTTP Server provides a RESTful API interface for the PDF RAG
system, enabling:

- Multi-user access with authentication
- Remote access to RAG functionality
- Easy integration with web applications
- Scalable deployment options
- Rate limiting and security features

## Quick Start

### Installation

```bash
# Install dependencies
uv pip install -r pyproject.toml

# Or install with HTTP server extras
uv pip install -e ".[http]"
```

### Running the Server

```bash
# Start the HTTP server
python -m src.mcp.http_server

# Or with custom configuration
HTTP_SERVER_PORT=8080 python -m src.mcp.http_server

# Production deployment with multiple workers
uvicorn src.mcp.http_server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Testing the Server

```bash
# Health check
curl http://localhost:8000/api/health

# Login and get JWT token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

## Authentication

The server supports two authentication methods:

### 1. JWT Authentication

For interactive users and web applications:

```bash
# Login to get JWT token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Use token in requests
curl http://localhost:8000/api/documents \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 2. API Key Authentication

For service-to-service communication:

```bash
# Use API key in header
curl http://localhost:8000/api/documents \
  -H "X-API-Key: demo-api-key-12345"
```

### Setting Up Credentials

**⚠️ IMPORTANT: No default credentials are provided for security reasons!**

You must set up authentication credentials via environment variables:

#### Required Settings

```bash
# REQUIRED: JWT secret key for token signing
export JWT_SECRET_KEY="your-secret-key-here"
```

#### Optional Authentication Methods

Choose one or both authentication methods based on your needs:

##### Option 1: Username/Password Authentication

Best for: Web applications, admin dashboards, interactive use

```bash
# Set admin username
export ADMIN_USERNAME="admin"

# Generate password hash (you'll be prompted for password)
python scripts/generate_password_hash.py

# Export the generated hash
export ADMIN_PASSWORD_HASH="$2b$12$..."  # Copy from script output
```

##### Option 2: API Key Authentication

Best for: Automated scripts, CI/CD pipelines, service-to-service communication

```bash
# Set API keys (format: api_key:service_name:rate_limit_per_hour)
# - api_key: The actual API key string
# - service_name: Descriptive name for the service
# - rate_limit_per_hour: Number of requests allowed per hour
export API_KEYS="key1:service1:1000,key2:service2:5000"

# Real-world examples:
# export API_KEYS="sk-prod-abc123:production-web:10000,sk-dev-xyz789:development:1000"
# export API_KEYS="secure-key-mobile:mobile-app:5000,secure-key-analytics:analytics-service:2000"
```

**Note**:

- Without any authentication method configured, all API endpoints (except
  /api/health) will return 401 Unauthorized
- You can enable both methods simultaneously for maximum flexibility
- The server checks JWT authentication first, then falls back to API key
  authentication

## API Endpoints

### MCP Protocol Endpoints

The server now includes MCP (Model Context Protocol) support for AI clients:

#### POST /mcp

Handle MCP JSON-RPC requests.

**No authentication required** - MCP clients handle their own authentication.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "pdfrag.query_technical_docs",
        "description": "Query the PDF RAG knowledge base for technical documentation answers",
        "inputSchema": {...}
      }
    ]
  }
}
```

#### GET /mcp

Server-Sent Events (SSE) endpoint for MCP streaming connections.

**Headers:**

- `X-Session-ID`: Optional session identifier

**Response:** Event stream with heartbeat messages

### Authentication Endpoints

#### POST /api/auth/login

Login with username and password.

**Request:**

```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

#### GET /api/auth/me

Get current user information.

**Headers:** Authorization: Bearer TOKEN

**Response:**

```json
{
  "username": "admin",
  "is_active": true,
  "is_admin": true
}
```

### Document Management Endpoints

#### POST /api/query

Query the technical documentation.

**Request:**

```json
{
  "question": "How do I configure the RAG system?",
  "top_k": 5
}
```

**Response:**

```json
{
  "answer": "To configure the RAG system...",
  "sources": [
    {
      "document": "configuration.pdf",
      "page": 12,
      "section": "Configuration"
    }
  ],
  "confidence": 0.95,
  "processing_time": 1.23
}
```

#### POST /api/documents

Add a single PDF document.

**Request:**

```json
{
  "pdf_path": "/path/to/document.pdf",
  "document_type": "manual"
}
```

**Response:**

```json
{
  "message": "Successfully added document: document.pdf",
  "success": true
}
```

#### POST /api/documents/batch

Add multiple PDF documents from a folder.

**Request:**

```json
{
  "folder_path": "/path/to/pdf/folder",
  "document_type": "documentation",
  "recursive": true
}
```

**Response:**

```json
{
  "message": "Processed 10 files. Successfully added: 9, Failed: 1",
  "success": false
}
```

#### POST /api/documents/upload

Upload a PDF document directly.

**Request:** Multipart form data with file

```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@document.pdf" \
  -F "document_type=manual"
```

**Response:**

```json
{
  "message": "Successfully added document: document.pdf",
  "success": true
}
```

#### GET /api/documents

List all documents in the knowledge base.

**Response:**

```json
{
  "documents": [
    {
      "document": "manual.pdf",
      "type": "manual",
      "chunk_count": 42,
      "source": "/docs/manual.pdf"
    }
  ],
  "total_count": 1
}
```

### System Management Endpoints

#### GET /api/system/info

Get system information and component status.

**Response:**

```json
{
  "server_version": "1.0.0",
  "components_status": {
    "vector_store": true,
    "embedding_model": true,
    "llm_model": true
  },
  "configuration": {
    "llm_type": "openai",
    "llm_model": "gpt-4",
    "embedding_model": "all-MiniLM-L6-v2",
    "collection_name": "technical_docs"
  },
  "features": [
    "Query technical documentation using RAG",
    "Add PDF documents to knowledge base",
    "Upload PDF files via API",
    "List all documents in the system",
    "Get system status and configuration",
    "JWT-based authentication",
    "CORS support for web clients"
  ]
}
```

#### DELETE /api/database

Clear the vector database.

**Request:**

```json
{
  "confirm": true
}
```

**Response:**

```json
{
  "message": "Successfully cleared database. Removed 10 documents (420 chunks).",
  "success": true
}
```

#### GET /api/health

Health check endpoint (no authentication required).

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "rag_engine": true,
    "configuration": true
  }
}
```

## Python Client SDK

### SDK Installation

The client SDK is included with the main package:

```python
from src.mcp.http_client import PDFRAGClient
```

### Basic Usage

```python
# Using API key
client = PDFRAGClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# Using username/password
client = PDFRAGClient(
    base_url="http://localhost:8000",
    username="admin",
    password="admin123"
)

# Query documents
result = client.query("How does the system work?")
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']}")

# Add document
response = client.add_document("/path/to/doc.pdf", "manual")
print(response['message'])

# List documents
docs = client.list_documents()
for doc in docs:
    print(f"- {doc['document']} ({doc['chunk_count']} chunks)")
```

### Context Manager

```python
with PDFRAGClient(api_key="your-api-key") as client:
    # Client session is automatically managed
    health = client.health_check()
    print(f"Server status: {health['status']}")
```

### Error Handling

```python
try:
    client.add_document("/path/to/doc.pdf")
except FileNotFoundError:
    print("PDF file not found")
except requests.HTTPError as e:
    if e.response.status_code == 401:
        print("Authentication failed")
    elif e.response.status_code == 429:
        print("Rate limit exceeded")
```

## Configuration

### Environment Variables

```bash
# Server configuration
HTTP_SERVER_HOST=0.0.0.0
HTTP_SERVER_PORT=8000

# Authentication
JWT_SECRET_KEY=your-secret-key-here
DEFAULT_API_KEY=your-api-key-here

# LLM Configuration
LLM_TYPE=openai
LLM_MODEL=gpt-4
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Configuration File

Edit `config/http_server_config.yaml`:

```yaml
http_server:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  cors_origins:
    - "https://yourdomain.com"

auth:
  jwt_algorithm: "HS256"
  access_token_expire_minutes: 1440

rate_limits:
  default: 100
  authenticated: 1000
  api_key: 5000
```

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install -e .

EXPOSE 8000

CMD ["uvicorn", "src.mcp.http_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  pdf-rag-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - LLM_TYPE=openai
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - pdf-rag-api
```

### Production Deployment

1. **Use HTTPS**: Always use TLS/SSL in production
2. **Change default credentials**: Update all default passwords and API keys
3. **Set secure JWT secret**: Use a strong, random secret key
4. **Configure rate limiting**: Adjust limits based on your needs
5. **Enable monitoring**: Use the metrics endpoint for monitoring
6. **Set up logging**: Configure proper log rotation and monitoring

### Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;

    location / {
        proxy_pass http://pdf-rag-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Security Best Practices

### Authentication & Authorization

1. **Change default credentials immediately**
2. **Use strong passwords and API keys**
3. **Rotate JWT secrets regularly**
4. **Implement proper user roles and permissions**
5. **Use HTTPS for all communications**

### Input Validation

1. **File size limits are enforced (50MB default)**
2. **Path traversal protection is implemented**
3. **Input sanitization for all user inputs**
4. **Rate limiting prevents abuse**

### Security Headers (Planned)

**Note**: Security headers are configured in `config/http_server_config.yaml`
but not yet automatically applied by the server. For production deployments,
configure these headers in your reverse proxy (nginx/Apache) or load balancer:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`

### API Key Management

1. **Generate strong API keys**: Use cryptographically secure random generators
2. **Store keys securely**: Never commit keys to version control
3. **Rotate keys regularly**: Implement key rotation policy
4. **Monitor key usage**: Track and audit API key usage

#### API Key Format Details

When setting the `API_KEYS` environment variable, use the following format:

```bash
# Format: api_key:service_name:rate_limit_per_hour
export API_KEYS="key1:name1:limit1,key2:name2:limit2,..."
```

**Components:**

- **api_key**: The actual API key string (e.g., "sk-1234567890abcdef")
  - Should be at least 32 characters long for security
  - Use only alphanumeric characters and hyphens
  - Generate using secure random methods

- **service_name**: Descriptive identifier for the service
  (e.g., "web-app", "mobile-ios", "analytics")
  - Used for logging and monitoring
  - Should be unique per API key
  - Helps identify which service is making requests

- **rate_limit_per_hour**: Maximum requests allowed per hour
  (e.g., 1000, 5000, 10000)
  - Enforced per API key
  - Prevents abuse and ensures fair usage
  - Set based on expected service load

**Example configurations:**

```bash
# Development environment
export API_KEYS="dev-key-123:local-testing:1000"

# Production with multiple services (split for readability)
export API_KEYS="sk-prod-web-abc123:production-website:10000,\
sk-prod-mobile-xyz789:mobile-app:5000,\
sk-prod-analytics-qrs456:analytics-service:2000"

# Mixed environment
export API_KEYS="prod-key-1:web-frontend:10000,\
staging-key-1:staging-api:5000,\
test-key-1:integration-tests:1000"
```

## Troubleshooting

### Common Issues

#### Server won't start

```bash
# Check if port is already in use
lsof -i :8000

# Use a different port
HTTP_SERVER_PORT=8080 python -m src.mcp.http_server
```

#### Authentication fails

```bash
# Verify JWT secret is set
echo $JWT_SECRET_KEY

# Check user credentials in logs
tail -f logs/http_server.log
```

#### Rate limit errors

```python
# Increase rate limit for specific API key
# Edit config/http_server_config.yaml
rate_limits:
  api_key: 10000  # Increase limit
```

#### File upload fails

```bash
# Check file size
ls -lh document.pdf

# Verify file is a valid PDF
file document.pdf
```

### Debug Mode

Enable debug logging:

```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG
python -m src.mcp.http_server
```

### Performance Tuning

1. **Increase workers**: For production, use multiple workers
2. **Enable caching**: Implement Redis for caching frequent queries
3. **Database optimization**: Ensure vector database is properly indexed
4. **Load balancing**: Use multiple server instances behind a load balancer

## API Client Examples

### cURL Examples

```bash
# Query with API key
curl -X POST http://localhost:8000/api/query \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is RAG?"}'

# Upload file with JWT
curl -X POST http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "document_type=manual"
```

### JavaScript/TypeScript

```typescript
// Using fetch API
const response = await fetch('http://localhost:8000/api/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-api-key'
  },
  body: JSON.stringify({
    question: 'How does it work?',
    top_k: 5
  })
});

const data = await response.json();
console.log(data.answer);
```

### Python Requests

```python
import requests

# Simple query
response = requests.post(
    'http://localhost:8000/api/query',
    json={'question': 'What is the configuration?'},
    headers={'X-API-Key': 'your-api-key'}
)

print(response.json()['answer'])
```

## Monitoring and Metrics

### Health Checks

```bash
# Kubernetes liveness probe
curl -f http://localhost:8000/api/health || exit 1
```

### Prometheus Metrics (Planned)

**Note**: Prometheus metrics endpoint is planned but not yet implemented.
This feature is on the roadmap for production monitoring capabilities.

### Logging

Logs are written to:

- Console (stdout)
- File: `logs/http_server.log`
- Rotating logs with configurable size and retention

## Migration from MCP Server

To migrate from the existing MCP stdio server:

1. **Keep both servers running**: The HTTP server is an additional interface
2. **Update client code**: Replace MCP client with HTTP client
3. **Migrate authentication**: Set up users and API keys
4. **Test thoroughly**: Ensure all functionality works correctly
5. **Gradual rollout**: Migrate services one at a time

## Support and Contributing

For issues, feature requests, or contributions:

1. Check the [GitHub repository](https://github.com/your-org/pdf-rag-system)
2. Review existing issues before creating new ones
3. Follow the contribution guidelines
4. Submit pull requests with tests

## License

This project is licensed under the terms specified in the LICENSE file.
