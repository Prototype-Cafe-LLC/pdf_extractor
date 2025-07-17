# Test Resources

This directory contains test resources for the PDF Extractor project.

## Directory Structure

```
test/resources/
├── pdf/          # Place test PDF files here
└── expected/     # Expected markdown output files (optional)
```

## Adding Test PDFs

Place your test PDF files in the `pdf/` subdirectory. Consider including:

- Simple single-page PDFs
- Multi-page documents
- PDFs with various formatting (tables, lists, headers)
- PDFs with images
- PDFs with different encodings
- Password-protected PDFs (for error handling tests)

## Naming Convention

For consistency, consider naming test files descriptively:

- `simple_text.pdf` - Basic text-only PDF
- `multi_page.pdf` - Multi-page document
- `with_tables.pdf` - PDF containing tables
- `with_images.pdf` - PDF containing images
- `japanese_text.pdf` - PDF with Japanese characters
- `protected.pdf` - Password-protected PDF