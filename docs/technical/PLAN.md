# RAG + LLM MCP Server Implementation Plan

## Overview

Transform the existing PDF extractor into an intelligent RAG (Retrieval Augmented
Generation) system with LLM integration, packaged as an MCP (Model Context Protocol)
server for seamless integration with AI assistants.

## Goals

1. **Prevent Hallucination**: Ensure all responses are grounded in source documents
2. **Intelligent Responses**: Use LLM to generate coherent, contextual answers
3. **Source Attribution**: Provide clear references to source documents
4. **MCP Integration**: Enable seamless use in Claude Desktop and other MCP clients
5. **Technical Accuracy**: Specialize in IoT device documentation (AT commands,
   hardware specs)

## Architecture

### Current State

- PDF → Markdown conversion using pymupdf4llm
- Basic file processing and validation
- Markdown formatting with markdownlint

### Target State

- PDF → Markdown → Chunks → Embeddings → Vector DB
- RAG retrieval + LLM generation
- MCP server with standardized tools
- Source attribution and confidence scoring

## Implementation Phases

### Phase 1: Core RAG Infrastructure ✅ COMPLETED

- [x] Document chunking strategies
- [x] Embedding generation with sentence-transformers
- [x] Vector database integration (ChromaDB)
- [x] Basic retrieval pipeline

### Phase 2: LLM Integration ✅ COMPLETED

- [x] LLM model integration (OpenAI, Anthropic, Ollama)
- [x] Context-aware prompt engineering
- [x] Response generation with source attribution
- [x] Confidence scoring

### Phase 3: MCP Server ✅ COMPLETED

- [x] MCP server implementation
- [x] Tool definitions and handlers
- [x] Error handling and logging
- [x] Configuration management

### Phase 4: Testing and Optimization ✅ COMPLETED

- [x] Unit tests for each component
- [x] Integration tests
- [x] Performance optimization
- [x] Documentation updates

### Phase 5: Setup and Deployment ✅ COMPLETED

- [x] Setup documentation and guides
- [x] API key configuration instructions
- [x] Environment variable setup
- [x] Quick start guides

## Technical Stack

### Dependencies

```toml
# Core RAG
sentence-transformers>=2.2.2
chromadb>=0.4.0
langchain>=0.1.0
langchain-community>=0.0.10

# LLM Integration
langchain-openai>=0.0.5
langchain-anthropic>=0.1.0
langchain-ollama>=0.1.0

# MCP Server
mcp>=1.0.0
pydantic>=2.0.0

# Utilities
numpy>=1.24.0
tiktoken>=0.5.0
pyyaml>=6.0
```

### Project Structure

```text
pdf_extractor/
├── pdf_extractor.py          # Existing PDF converter
├── mcp_server.py             # New: MCP server
├── rag_engine/
│   ├── __init__.py
│   ├── chunking.py           # Document chunking
│   ├── embeddings.py         # Embedding generation
│   ├── vector_store.py       # Vector database
│   ├── llm_integration.py    # LLM integration
│   └── retrieval.py          # RAG pipeline
├── config/
│   ├── rag_config.yaml       # RAG configuration
│   └── mcp_config.yaml       # MCP configuration
├── data/
│   ├── raw_md/               # Existing markdown
│   ├── chunks/               # New: chunked docs
│   ├── embeddings/           # New: embeddings
│   └── vector_db/            # New: vector DB
└── tests/
    ├── test_rag_engine.py    # New: RAG tests
    └── test_mcp_server.py    # New: MCP tests
```

## Key Components

### 1. Document Chunking

- **Strategy**: Section-based chunking for technical documents
- **Focus**: Preserve AT command context and examples
- **Size**: 512 tokens with 50 token overlap
- **Metadata**: Document source, page numbers, command types

### 2. Embedding Generation

- **Model**: sentence-transformers/all-MiniLM-L6-v2
- **Optimization**: Technical domain fine-tuning
- **Storage**: ChromaDB with metadata filtering

### 3. LLM Integration

- **Models**: OpenAI GPT-4, Anthropic Claude, Ollama local
- **Prompts**: Technical documentation specialized
- **Temperature**: 0.1 for accuracy
- **Context**: RAG-retrieved chunks with source info

### 4. MCP Server Tools

- `query_technical_docs`: Main RAG query interface
- `add_pdf_document`: Add new documents to KB
- `list_documents`: List available documents
- `get_document_info`: Get document metadata

## Testing Strategy

### Unit Tests

- Document chunking accuracy
- Embedding generation quality
- Vector search relevance
- LLM response generation
- MCP tool handlers

### Integration Tests

- End-to-end RAG pipeline
- MCP server communication
- Error handling scenarios
- Performance benchmarks

### Test Data

- Existing Quectel AT command manuals
- Synthetic technical queries
- Edge cases (missing info, ambiguous queries)

## Success Metrics

### Accuracy

- Response relevance to queries
- Source attribution accuracy
- Technical command correctness

### Performance

- Query response time < 2 seconds
- Document processing time < 30 seconds per PDF
- Memory usage < 2GB for typical document set

### Usability

- MCP client integration success
- Error handling robustness
- Configuration flexibility

## Risk Mitigation

### Technical Risks

- **LLM API costs**: Support local models (Ollama)
- **Vector DB performance**: ChromaDB optimization
- **Memory usage**: Streaming processing for large docs

### Quality Risks

- **Hallucination**: Strict context-only responses
- **Source accuracy**: Metadata validation
- **Response quality**: Prompt engineering iteration

## Implementation Timeline

### ✅ COMPLETED: All Phases (Accelerated Timeline)

**Phase 1: Core RAG Infrastructure** ✅

- Document chunking with multiple strategies
- Embedding generation using sentence-transformers
- Vector database integration with ChromaDB
- Basic retrieval pipeline

**Phase 2: LLM Integration** ✅

- Multi-provider LLM integration (OpenAI, Anthropic, Ollama)
- Context-aware prompt engineering
- Response generation with source attribution
- Confidence scoring and validation

**Phase 3: MCP Server** ✅

- Complete MCP server implementation
- Tool definitions and handlers
- Error handling and logging
- Configuration management

**Phase 4: Testing and Optimization** ✅

- Comprehensive unit tests
- Integration tests for all components
- Performance optimization
- Documentation updates

**Phase 5: Setup and Deployment** ✅

- Setup documentation and guides
- API key configuration instructions
- Environment variable setup
- Quick start guides

### Actual Implementation Time: ~1 Day

- All core functionality implemented and tested
- Comprehensive documentation created
- Setup guides and examples provided
- Ready for immediate use

## Implementation Status ✅ COMPLETED

All planned features have been successfully implemented and tested.
The RAG + LLM MCP server system is now fully functional.

### Completed Components

1. ✅ **RAG Engine** (`rag_engine/`)
   - Document chunking with multiple strategies
   - Embedding generation using sentence-transformers
   - Vector database operations with ChromaDB
   - LLM integration (OpenAI, Anthropic, Ollama)
   - Complete RAG pipeline with source attribution

2. ✅ **MCP Server** (`mcp_server.py`)
   - Standardized tools for technical document queries
   - Document management (add, list, query)
   - System information and health checks
   - Error handling and logging

3. ✅ **Configuration** (`config/`)
   - RAG system configuration (`rag_config.yaml`)
   - MCP server metadata (`mcp_config.yaml`)
   - Flexible settings for different use cases

4. ✅ **Testing** (`tests/`, `test_rag_basic.py`)
   - Unit tests for all components
   - Integration tests for RAG pipeline
   - Basic functionality verification

5. ✅ **Documentation**
   - Updated README.md with setup instructions
   - Detailed RAG documentation (`RAG_README.md`)
   - Anthropic API setup guide (`ANTHROPIC_SETUP.md`)
   - Implementation plan (`PLAN.md`)

## Setup Instructions

### Quick Start

1. **Install dependencies**:

   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e .
   ```

2. **Set API key** (choose one):

   ```bash
   # For Anthropic
   export ANTHROPIC_API_KEY="sk-ant-your-key-here"

   # For OpenAI
   export OPENAI_API_KEY="sk-your-key-here"

   # For Ollama (no key needed)
   # Just ensure Ollama is running: ollama serve
   ```

3. **Test the system**:

   ```bash
   python test_rag_basic.py
   ```

4. **Start MCP server**:

   ```bash
   python mcp_server.py
   ```

### Configuration

- Edit `config/rag_config.yaml` to customize LLM settings
- Edit `config/mcp_config.yaml` to modify server metadata
- API keys can be set via environment variables or `.env` file

### Usage Examples

**Python API**:

```python
from rag_engine.retrieval import RAGEngine
import yaml

with open("config/rag_config.yaml", 'r') as f:
    config = yaml.safe_load(f)

rag = RAGEngine(config)
rag.add_pdf_document("manual.pdf", "at_commands")
response = rag.query("What is AT+CSQ?")
print(response.answer)
```

**MCP Tools**:

- `query_technical_docs`: Ask questions about documentation
- `add_pdf_document`: Add new PDFs to knowledge base
- `list_documents`: List available documents
- `get_system_info`: Get system status

## Next Steps (Future Enhancements)

1. **Performance Optimization**
   - Implement caching for embeddings
   - Optimize vector search algorithms
   - Add batch processing for large document sets

2. **Advanced Features**
   - Multi-modal support (images, diagrams)
   - Real-time document updates
   - Advanced filtering and search options

3. **Integration Enhancements**
   - Web interface for document management
   - API endpoints for external applications
   - Plugin system for custom document types

4. **Monitoring and Analytics**
   - Query performance metrics
   - Usage analytics and insights
   - System health monitoring

## Notes

- ✅ Maintains backward compatibility with existing PDF extractor
- ✅ Follows existing coding standards and markdownlint requirements
- ✅ Ensures Japanese text support in all components
- ✅ Prioritizes technical accuracy over response length
- ✅ Designed for extensibility to other document types
- ✅ Comprehensive error handling and logging
- ✅ Source attribution prevents hallucination
- ✅ Configurable for different use cases and environments
