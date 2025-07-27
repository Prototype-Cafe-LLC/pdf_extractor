# PDF Extractor

Convert PDF files to Markdown format with ease. This command-line tool uses
`pymupdf4llm` to extract content from PDFs while preserving formatting, tables,
and structure.

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

   For MCP clients (e.g., Claude Desktop), add to your MCP configuration:

   ```json
   {
     "mcpServers": {
       "pdf-rag-mcp": {
         "command": "/path/to/pdf_extractor/.venv/bin/python",
         "args": [
           "/path/to/pdf_extractor/src/mcp/simple_server.py"
         ],
         "cwd": "/path/to/pdf_extractor",
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

#### Environment Variables

The MCP server supports configuration through environment variables, which override settings in the YAML files:

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
  - Claude 3 series: claude-3-opus-20240229, claude-3-sonnet-20240229, claude-3-haiku-20240307, claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022
  - Claude 4 series: claude-4-opus, claude-4-sonnet, claude-4-haiku (when available)
- **OpenAI**: gpt-4, gpt-4-turbo, gpt-3.5-turbo, gpt-4o
- **Ollama**: llama2, llama3, mistral, codellama, o3 (or any locally installed model)

**Note**: The API keys are used by the RAG system to generate intelligent
responses. The basic PDF extraction functionality works without any API keys.

**Important**: The LLM is initialized lazily (only when making queries), so
operations like listing documents or adding PDFs will work even without API keys.

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

   - `query_technical_docs`: Ask questions about technical documentation
   - `add_pdf_document`: Add new PDF documents to knowledge base
   - `list_documents`: List available documents
   - `get_system_info`: Get system status and component health

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
