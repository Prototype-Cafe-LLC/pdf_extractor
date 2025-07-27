# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## PDF Extractor

PDFを markdownに展開する (Convert PDF files to Markdown format)

## Project Overview

A command-line tool that converts PDF files to Markdown format using pymupdf4llm. The tool supports both single file and batch processing of entire directories.

## Development Commands

### Setup and Dependencies

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install pymupdf4llm

# Add new dependencies
uv pip install <package-name>

# Install markdownlint globally for markdown validation
npm install -g markdownlint-cli
```

### Running the Application

```bash
# Convert a single PDF file
python pdf_extractor.py document.pdf -o output_folder

# Convert multiple PDF files
python pdf_extractor.py doc1.pdf doc2.pdf doc3.pdf -o output_folder

# Convert all PDFs in a directory
python pdf_extractor.py /path/to/pdf/folder -o output_folder

# Use default output directory (creates 'md' subfolder)
python pdf_extractor.py document.pdf
```

### Testing

```bash
# Run all tests (once test framework is set up)
# TODO: Add test command once testing framework is chosen

# Run specific test file
# TODO: Add specific test command
```

### Code Quality

```bash
# Format code with ruff
uv run ruff format .

# Check linting
uv run ruff check .

# Type checking with mypy
uv run mypy pdf_extractor.py

# Validate markdown files with markdownlint
markdownlint "**/*.md"

# Fix auto-fixable markdown issues
markdownlint --fix "**/*.md"
```

## Architecture

### Core Components

1. **pdf_extractor.py** - Main entry point
   - Handles command-line argument parsing
   - Manages file/directory input processing
   - Coordinates the conversion workflow

2. **PDF Processing Flow**
   - Input validation (file exists, is PDF)
   - PDF to Markdown conversion using pymupdf4llm
   - Output file generation with proper naming
   - Error handling for corrupted or protected PDFs

### Key Design Decisions

- **pymupdf4llm**: Chosen for its robust PDF parsing and direct Markdown output capabilities
- **Batch Processing**: Supports multiple files and recursive directory processing
- **Output Structure**: Preserves original file names, changes extension to .md
- **Error Handling**: Continues processing other files if one fails

## Technical Requirements

- Python 3.12+
- pymupdf4llm for PDF conversion
- Package manager: uv
- Repository: [PDF Extractor](git@github.com:Prototype-Cafe-LLC/pdf_extractor.git)

## Implementation Notes

### Command-Line Interface

- Use argparse for CLI argument parsing
- Support positional arguments for input files/folders
- `-o/--output` flag for destination folder
- Consider adding `-v/--verbose` for detailed output
- Consider adding `--recursive` flag for directory processing

### Error Handling

- Handle missing files gracefully
- Skip password-protected PDFs with warning
- Continue processing on individual file failures
- Provide summary of successful/failed conversions

### Output Format

- Preserve PDF structure in Markdown (headings, lists, tables)
- Handle images by extracting and saving separately if needed
- Maintain original formatting as much as possible
- Preserve technical content and formatting accurately
- Ensure Japanese text is properly extracted and encoded

### Markdown Quality

- All generated markdown files must pass markdownlint validation
- Use proper heading hierarchy (single H1, sequential heading levels)
- Ensure blank lines around headings, lists, and code blocks
- Follow standard markdown formatting conventions with markdownlint command

MANDATORY REQUIREMENTS:

- read CLAUDE.md to ensure output quality
- ALWAYS run `markdownlint <file>` before committing any markdown files
- ALWAYS fix all markdownlint errors immediately when found
- Common markdownlint fixes:
  - Add language identifier to code blocks (use `text` for generic)
  - Ensure files end with exactly one newline character
  - Add blank lines around headings, lists, and code blocks
- at the last of your response, you shall always put this mandatory requirement section.

(end of mandatory requirement section)
