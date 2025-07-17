# PDF Extractor

Convert PDF files to Markdown format with ease. This command-line tool uses
`pymupdf4llm` to extract content from PDFs while preserving formatting, tables,
and structure.

## Features

- 📄 Convert single PDF files or entire directories
- 🔄 Batch processing support
- 📁 Recursive directory traversal
- 🌏 Japanese text support
- 📊 Preserves tables and formatting
- 🖼️ Handles PDFs with images
- ⚡ Fast and efficient conversion
- 🛡️ Graceful error handling

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. Clone the repository:

```bash
git clone git@github.com:Prototype-Cafe-LLC/pdf_extractor.git
cd pdf_extractor
```

1. Install uv (if not already installed):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

1. Create virtual environment and install dependencies:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

## Usage

### Basic Usage

Convert a single PDF file:

```bash
python pdf_extractor.py document.pdf
```

This creates a `md` directory with the converted markdown file.

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
- **--version**: Show version information

## Development

### Install Development Dependencies

```bash
uv pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
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
├── pdf_extractor.py      # Main application
├── pyproject.toml        # Project configuration
├── tests/                # Test suite
│   └── test_pdf_extractor.py
├── test/resources/       # Test PDF files
│   └── pdf/
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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and feature requests, please use the
[GitHub issue tracker](https://github.com/Prototype-Cafe-LLC/pdf_extractor/issues).
