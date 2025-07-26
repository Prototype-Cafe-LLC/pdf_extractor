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

4. **Start the MCP server**:

   ```bash
   python mcp_server.py
   ```

#### Environment Variables

Set these environment variables in your shell or `.env` file:

```bash
# For OpenAI
export OPENAI_API_KEY="sk-your-openai-api-key"

# For Anthropic
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-api-key"

# For Ollama (no API key needed)
# Just ensure Ollama is running: ollama serve
```

**Note**: The API keys are used by the RAG system to generate intelligent
responses. The basic PDF extraction functionality works without any API keys.

**Important**: The LLM is initialized lazily (only when making queries), so
operations like listing documents or adding PDFs will work even without API keys.

## Usage

### Basic PDF Extraction

Convert a single PDF file:

```bash
python pdf_extractor.py document.pdf
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
rag.add_pdf_document("path/to/manual.pdf", "at_commands")

# Query the knowledge base
response = rag.query("What is the AT command for checking signal quality?")
print("Answer:", response.answer)
print("Sources:", response.sources)
print("Confidence:", response.confidence)
```

#### Using MCP Server

1. Start the MCP server:

   ```bash
   python mcp_server.py
   ```

2. In Claude Desktop or other MCP client, use these tools:

   - `query_technical_docs`: Ask questions about technical documentation
   - `add_pdf_document`: Add new PDF documents to knowledge base
   - `list_documents`: List available documents
   - `get_system_info`: Get system status and component health

#### Example MCP Queries

```json
{
  "question": "What is the AT+CSQ command used for?",
  "top_k": 3
}
```

```json
{
  "pdf_path": "/path/to/quectel_manual.pdf",
  "document_type": "at_commands"
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
├── pdf_extractor.py      # Main PDF extraction application
├── mcp_server.py         # MCP server for RAG queries
├── pyproject.toml        # Project configuration
├── rag_engine/           # RAG components
│   ├── __init__.py
│   ├── chunking.py       # Document chunking strategies
│   ├── embeddings.py     # Embedding generation
│   ├── vector_store.py   # Vector database operations
│   ├── llm_integration.py # LLM integration
│   └── retrieval.py      # Complete RAG pipeline
├── config/               # Configuration files
│   ├── rag_config.yaml   # RAG settings
│   └── mcp_config.yaml   # MCP server settings
├── data/                 # Data storage
│   ├── chunks/           # Document chunks
│   ├── embeddings/       # Embedding files
│   └── vector_db/        # Vector database
├── tests/                # Test suite
│   ├── test_pdf_extractor.py
│   └── test_rag_engine.py
├── test_rag_basic.py     # Basic RAG functionality test
├── PLAN.md              # Implementation plan
├── RAG_README.md        # Detailed RAG documentation
├── ANTHROPIC_SETUP.md   # Anthropic API setup guide
├── OPENAI_SETUP.md      # OpenAI API setup guide
├── OLLAMA_SETUP.md      # Ollama local setup guide
├── MODEL_COMPARISON.md  # Opus vs O3 model comparison
├── PRIVACY_POLICY.md    # Data usage and privacy policies
└── README.md            # This file
```

## Error Handling

The tool handles various error scenarios gracefully:

- **Missing files**: Skips and reports
- **Invalid file types**: Only processes PDF files
- **Corrupted PDFs**: Logs error and continues with other files
- **Permission errors**: Reports access issues
- **Password-protected PDFs**: Skips with warning

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
