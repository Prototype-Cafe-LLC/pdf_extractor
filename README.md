# PDF Extractor

Convert PDF files to Markdown format with ease. This command-line tool uses
`pymupdf4llm` to extract content from PDFs while preserving formatting, tables,
and structure.

## 🚀 Quick Start (5-minute setup)

Choose your preferred setup:

### Option A: MCP Server for Claude Desktop

For busy users who want to get the MCP server running quickly:

#### 1. Clone and Install (2 minutes)

```bash
git clone git@github.com:Prototype-Cafe-LLC/pdf_extractor.git
cd pdf_extractor
./install.sh
```

That's it! The install script handles everything including uv installation.

#### 2. Configure MCP Server (1 minute)

Add to your Claude Desktop config file:
`~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pdf-rag": {
      "command": "/path/to/pdf_extractor/.venv/bin/python",
      "args": ["/path/to/pdf_extractor/src/mcp/simple_server.py"],
      "env": {
        "ANTHROPIC_API_KEY": "your-api-key"
        // Optional overrides (defaults shown):
        // "LLM_TYPE": "anthropic",
        // "LLM_MODEL": "claude-3-5-sonnet-20241022",
        // "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2"
      }
    }
  }
}
```

**Note**: Only `ANTHROPIC_API_KEY` is required. The server uses sensible defaults
for other settings. For OpenAI, use `OPENAI_API_KEY` and set `LLM_TYPE` to "openai".

#### 3. Start Using (1 minute)

Restart Claude Desktop and start chatting:

- **Add PDFs**: "Add the PDF at /path/to/manual.pdf to the knowledge base"
- **Add folders**: "Add all PDFs from /Users/me/Documents/manuals"
- **Ask questions**: "What does the manual say about network configuration?"
- **List documents**: "Show me all documents in the knowledge base"

That's it! You're ready to query your PDF documents with AI.

### Option B: HTTP API Server for Team Access

For teams who want a shared API server:

#### 1. Install (same as above)

Use the same installation steps from Option A.

#### 2. Configure HTTP Server (2 minutes)

```bash
# Generate secure credentials
export JWT_SECRET_KEY="$(openssl rand -base64 32)"
export ADMIN_USERNAME="admin"

# Generate password hash (you'll be prompted for password)
python scripts/generate_password_hash.py
# Copy the generated hash and export it:
export ADMIN_PASSWORD_HASH="$2b$12$..."

# Set API keys (format: key:name:rate_limit)
export API_KEYS="prod-key-1:production:5000,dev-key-1:development:1000"

# Set LLM API key (choose one)
export ANTHROPIC_API_KEY="your-anthropic-key"  # For Claude
# OR
export OPENAI_API_KEY="your-openai-key"  # For GPT-4
```

#### 3. Start Server (1 minute)

```bash
# Start the HTTP server
python -m src.mcp.http_server

# Server is now running at http://localhost:8000
# API docs available at http://localhost:8000/docs
```

#### 4. Quick Test

```bash
# Test with curl
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# Or use the Python client
python -c "
from src.mcp.http_client import PDFRAGClient
client = PDFRAGClient(username='admin', password='your-password')
print(client.health_check())
"
```

That's it! Your HTTP API server is ready for team use.

## Features

### PDF Extraction

- 📄 Convert single PDF files or entire directories
- 🔄 Batch processing support
- 📁 Recursive directory traversal
- 🌏 Japanese text support
- 📊 Preserves tables and formatting
- 🖼️ Handles PDFs with images
- ⚡ Fast and efficient conversion
- 🛡️ Graceful error handling
- ✨ Automatic markdown formatting with markdownlint

### RAG + LLM Capabilities (New!)

- 🤖 **Intelligent Querying**: Ask questions about technical documentation
- 🔍 **Semantic Search**: Find relevant content using embeddings
- 📚 **Source Attribution**: Every response cites specific document sections
- 🎯 **Hallucination Prevention**: LLM only uses retrieved context
- 📊 **Confidence Scoring**: Indicates reliability of responses
- 🔧 **MCP Server**: Standardized tools for Claude Desktop and other clients
- 🌐 **Multi-LLM Support**: OpenAI (GPT-4, GPT-4o), Anthropic (Claude 4 Opus,
  Claude 3), and Ollama (O3, Llama 3.1) integration
- 📈 **Vector Database**: Persistent storage with ChromaDB
- 📝 **Rotating Logs**: Server logs with automatic rotation for debugging and monitoring
- 🚀 **HTTP API Server**: RESTful API with JWT/API key authentication for team collaboration
- 📦 **Python SDK**: Client library for easy integration with the HTTP API

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral.sh/uv) package manager
- [markdownlint-cli](https://github.com/igorshubovych/markdownlint-cli)
  (recommended for markdown validation)

### Basic Setup (PDF Extractor Only)

1. Clone the repository:

   ```bash
   git clone git@github.com:Prototype-Cafe-LLC/pdf_extractor.git
   cd pdf_extractor
   ```

2. Install uv (if not already installed):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. Create virtual environment and install dependencies:

   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

4. Install markdownlint (recommended):

   ```bash
   npm install -g markdownlint-cli
   ```

### RAG + LLM MCP Server Setup

The PDF Extractor now includes advanced RAG (Retrieval Augmented Generation)
capabilities with MCP (Model Context Protocol) server integration. This allows
you to query technical documentation intelligently with source attribution.

#### Additional Prerequisites for RAG

- LLM API key (OpenAI, Anthropic, or Ollama)
- Internet connection for embedding model download (first time only)

#### Setup Guides

For detailed setup instructions, see:

- [Anthropic Setup Guide](ANTHROPIC_SETUP.md) - For Claude models
- [OpenAI Setup Guide](OPENAI_SETUP.md) - For GPT models
- [Ollama Setup Guide](OLLAMA_SETUP.md) - For local models
- [Model Comparison](MODEL_COMPARISON.md) - Opus vs O3 detailed comparison
- [Privacy Policy](PRIVACY_POLICY.md) - Data usage and privacy policies

#### RAG Setup Steps

1. **Set up API keys** (choose one provider):

   **Option A: OpenAI**

   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

   **Option B: Anthropic**

   ```bash
   export ANTHROPIC_API_KEY="your-anthropic-api-key-here"
   ```

   **Option C: Ollama (Local)**

   ```bash
   # No API key needed, but ensure Ollama is running locally
   # Install Ollama from https://ollama.ai/
   ```

2. **Configure RAG settings** (optional):

   Edit `config/rag_config.yaml` to customize:
   - LLM provider and model
   - Embedding model
   - Chunk size and overlap
   - Vector database settings

3. **Test the RAG system**:

   ```bash
   python test_rag_basic.py
   ```

4. **Configure and start the MCP server**:

   For standalone testing:

   ```bash
   python src/mcp/simple_server.py
   ```

   For MCP clients (e.g., Claude Desktop, Cursor), add to your MCP configuration:

   ```json
   {
     "mcpServers": {
       "pdf-rag-mcp": {
         "command": "/path/to/pdf_extractor/.venv/bin/python",
         "args": [
           "/path/to/pdf_extractor/src/mcp/simple_server.py"
         ],
         "env": {
           "FASTMCP_LOG_LEVEL": "ERROR",
           "ANTHROPIC_API_KEY": "your-api-key",
           "LLM_TYPE": "anthropic",
           "LLM_MODEL": "claude-3-opus-20240229",
           "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2"
         }
       }
     }
   }
   ```

   **Note**: The current MCP servers use stdio (standard input/output) transport.
   For HTTP-based access, use the HTTP API server (see HTTP API Server section below).

   **Troubleshooting MCP Configuration**:
   - If you get "ModuleNotFoundError", use the direct file path in args instead of `-m`
   - Ensure the Python path points to your virtual environment's Python
   - The `cwd` parameter is optional but can help with module resolution

#### Environment Variables

The MCP server supports configuration through environment variables, which
override settings in the YAML files:

**Required API Keys (choose one):**

```bash
# For OpenAI
export OPENAI_API_KEY="sk-your-openai-api-key"

# For Anthropic
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-api-key"

# For Ollama (no API key needed)
# Just ensure Ollama is running: ollama serve
```

**Optional Model Configuration:**

```bash
# Override LLM provider (anthropic, openai, ollama)
export LLM_TYPE="anthropic"

# Override LLM model
export LLM_MODEL="claude-3-opus-20240229"

# Override embedding model
export EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
```

**Logging Configuration:**

```bash
# Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export MCP_LOG_LEVEL="INFO"

# Override log directory (defaults to ./logs)
export MCP_LOG_DIR="/path/to/logs"

# Set log rotation size (in bytes, default: 10MB)
export MCP_LOG_MAX_BYTES="10485760"

# Set number of backup files to keep (default: 5)
export MCP_LOG_BACKUP_COUNT="5"
```

**Available Models:**

- **Anthropic**:
  - Claude 3 series: claude-3-opus-20240229, claude-3-sonnet-20240229,
    claude-3-haiku-20240307, claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022
  - Claude 4 series: claude-4-opus, claude-4-sonnet, claude-4-haiku (when available)
- **OpenAI**: gpt-4, gpt-4-turbo, gpt-3.5-turbo, gpt-4o
- **Ollama**: llama2, llama3, mistral, codellama, o3 (or any locally installed model)

**Note**: The API keys are used by the RAG system to generate intelligent
responses. The basic PDF extraction functionality works without any API keys.

**Important**: The LLM is initialized lazily (only when making queries), so
operations like listing documents or adding PDFs will work even without API keys.

### Understanding MCP vs HTTP Servers

This project includes two different server types:

1. **MCP Server** (`src.mcp.simple_server`) - For AI assistants like Claude Desktop, Cursor
   - Uses stdio (standard input/output) transport
   - Direct integration with AI tools
   - No authentication needed (handled by the client)

2. **HTTP API Server** (`src.mcp.http_server`) - For web applications and APIs
   - Uses HTTP/HTTPS transport
   - JWT and API key authentication
   - RESTful API endpoints
   - Team collaboration features

### HTTP API Server (New!)

The PDF RAG system now includes a RESTful HTTP API server for team collaboration
and remote access:

**Features**:

- 🔐 JWT and API key authentication
- 🌐 RESTful API endpoints
- 🚀 Async FastAPI implementation
- 📦 Python client SDK included
- 🛡️ Enhanced security with path validation
- 📊 Rate limiting and CORS support

**Quick Start**:

1. **Set environment variables**:

   ```bash
   export JWT_SECRET_KEY="your-secure-secret-key"
   export ADMIN_USERNAME="admin"
   export ADMIN_PASSWORD_HASH="$(python scripts/generate_password_hash.py)"
   export API_KEYS="key1:service1:1000,key2:service2:5000"
   ```

2. **Start the HTTP server**:

   ```bash
   python -m src.mcp.http_server
   # Or with custom settings
   uvicorn src.mcp.http_server:app --host 0.0.0.0 --port 8000 --workers 4
   ```

3. **Use the Python client**:

   ```python
   from src.mcp.http_client import PDFRAGClient
   
   # Using API key
   client = PDFRAGClient(api_key="your-api-key")
   
   # Query documents
   result = client.query("How does the system work?")
   print(result['answer'])
   
   # Add documents
   client.add_document("/path/to/document.pdf", "manual")
   ```

**API Endpoints**:

- `POST /api/auth/login` - Get JWT token
- `GET /api/health` - Health check
- `POST /api/query` - Query documents
- `POST /api/documents` - Add single document
- `POST /api/documents/batch` - Add multiple documents
- `GET /api/documents` - List all documents
- `GET /api/system/info` - Get system info
- `DELETE /api/database` - Clear database

See [docs/HTTP_SERVER_README.md](docs/HTTP_SERVER_README.md) for complete documentation.

## Usage

### Basic PDF Extraction

Convert a single PDF file:

```bash
python -m src.pdf_extractor document.pdf
# Or if installed via pip:
pdf-extractor document.pdf
```

This creates a `md` directory with the converted markdown file.

### RAG + LLM Query System

After setting up the RAG system, you can query technical documentation
intelligently:

#### Using Python API

```python
from rag_engine.retrieval import RAGEngine
import yaml

# Load configuration
with open("config/rag_config.yaml", 'r') as f:
    config = yaml.safe_load(f)

# Initialize RAG engine
rag = RAGEngine(config)

# Add PDF document to knowledge base
rag.add_pdf_document("path/to/document.pdf", "manual")

# Query the knowledge base
response = rag.query("How do I configure the network settings?")
print("Answer:", response.answer)
print("Sources:", response.sources)
print("Confidence:", response.confidence)
```

#### Using MCP Server

1. Start the MCP server:

   ```bash
   python src/mcp/simple_server.py
   ```

2. In Claude Desktop or other MCP client, use these tools:

   - `pdfrag.query_technical_docs`: Ask questions about technical documentation
   - `pdfrag.add_document`: Add a single PDF document to knowledge base
   - `pdfrag.add_documents`: Add multiple PDF documents from a folder
   - `pdfrag.list_documents`: List all documents in the knowledge base
   - `pdfrag.get_system_info`: Get system status and component health
   - `pdfrag.clear_database`: Clear the vector database (removes
     embeddings/chunks only)

#### Example MCP Queries

```json
{
  "question": "How do I set up the device configuration?",
  "top_k": 3
}
```

```json
{
  "pdf_path": "/path/to/technical_manual.pdf",
  "document_type": "manual"
}
```

### Specify Output Directory

```bash
python pdf_extractor.py document.pdf -o output_folder
```

### Convert Multiple Files

```bash
python pdf_extractor.py doc1.pdf doc2.pdf doc3.pdf -o output_folder
```

### Process Entire Directory

```bash
python pdf_extractor.py /path/to/pdf/folder -o output_folder
```

### Recursive Directory Processing

```bash
python pdf_extractor.py /path/to/pdf/folder -o output_folder --recursive
```

### Verbose Output

```bash
python pdf_extractor.py document.pdf -v
```

## Command-Line Options

- **inputs**: PDF files or directories to convert (required)
- **-o, --output**: Output directory (default: 'md' in current directory)
- **-v, --verbose**: Enable verbose logging
- **--recursive**: Process directories recursively
- **--no-lint**: Skip markdownlint validation/fixing
- **--version**: Show version information

## Development

### Install Development Dependencies

```bash
uv pip install -e ".[dev]"
```

### Run Tests

```bash
# Basic PDF extraction tests
pytest

# RAG functionality tests
python test_rag_basic.py

# Individual RAG component tests
pytest tests/test_rag_engine.py
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Check linting
uv run ruff check .

# Type checking
uv run mypy pdf_extractor.py

# Validate markdown output
markdownlint "**/*.md"
```

## Project Structure

```text
pdf_extractor/
├── src/                  # Source code
│   ├── pdf_extractor/    # PDF extraction module
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── cli.py        # Command-line interface
│   │   └── converter.py  # PDF conversion logic
│   ├── rag_engine/       # RAG components
│   │   ├── __init__.py
│   │   ├── chunking.py   # Document chunking strategies
│   │   ├── embeddings.py # Embedding generation
│   │   ├── vector_store.py # Vector database operations
│   │   ├── llm_integration.py # LLM integration
│   │   └── retrieval.py  # Complete RAG pipeline
│   └── mcp/              # MCP server implementations
│       ├── __init__.py
│       ├── server.py     # Full MCP server
│       └── simple_server.py # Simplified MCP server
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── scripts/              # Utility scripts
├── docs/                 # Documentation
│   ├── setup/            # Setup guides
│   ├── guides/           # User guides
│   └── technical/        # Technical docs
├── config/               # Configuration files
│   ├── rag_config.yaml   # RAG settings
│   ├── mcp_config.yaml   # MCP server settings
│   └── logging_config.yaml # Logging configuration
├── data/                 # Data storage
│   ├── chunks/           # Document chunks
│   ├── embeddings/       # Embedding files
│   └── vector_db/        # Vector database
├── logs/                 # Server logs (auto-created)
├── pyproject.toml        # Project configuration
├── README.md             # This file
├── CLAUDE.md             # Claude-specific guidance
├── LICENSE               # MIT License
└── PRIVACY_POLICY.md     # Data usage and privacy
```

## Error Handling

The tool handles various error scenarios gracefully:

- **Missing files**: Skips and reports
- **Invalid file types**: Only processes PDF files
- **Corrupted PDFs**: Logs error and continues with other files
- **Permission errors**: Reports access issues
- **Password-protected PDFs**: Skips with warning

## Monitoring and Debugging

### Server Logs

The MCP servers maintain rotating log files for debugging and monitoring:

- **Log location**: `./logs/` directory (configurable via `MCP_LOG_DIR`)
- **Log files**:
  - `mcp_server.log` - Main MCP server logs
  - `simple_server.log` - Simple MCP server logs
- **Rotation policy**:
  - Default: 10MB per file, keeping 5 backups
  - Configurable via environment variables or `config/logging_config.yaml`

### Viewing Logs

```bash
# View recent logs
tail -f logs/mcp_server.log

# Search for errors
grep ERROR logs/mcp_server.log

# View all log files
ls -la logs/
```

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General informational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical failures requiring immediate attention

## Output Format

The tool preserves:

- Document structure and headings
- Lists and bullet points
- Tables with proper formatting
- Code blocks and technical content
- Unicode text (including Japanese)

Generated markdown files are automatically validated and fixed using markdownlint
to ensure consistent formatting and compliance with markdown standards.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE)
file for details.

## Support

For issues and feature requests, please use the
[GitHub issue tracker](https://github.com/Prototype-Cafe-LLC/pdf_extractor/issues).
