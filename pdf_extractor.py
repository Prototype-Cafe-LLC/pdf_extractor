#!/usr/bin/env python3
"""Convert PDF files to Markdown format.

This module provides a command-line tool to convert PDF files to Markdown
using pymupdf4llm. It supports single file conversion, batch processing,
and directory traversal.
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

try:
    import pymupdf4llm
except ImportError:
    print("Error: pymupdf4llm is not installed. Please run: uv pip install pymupdf4llm")
    sys.exit(1)

__version__ = "0.1.0"


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity level.
    
    Args:
        verbose: If True, set logging level to DEBUG, otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Convert PDF files to Markdown format",
        epilog="Examples:\n"
        "  %(prog)s document.pdf\n"
        "  %(prog)s doc1.pdf doc2.pdf -o output_folder\n"
        "  %(prog)s /path/to/pdf/folder -o output_folder --recursive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="PDF files or directories to convert",
    )
    
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output directory (default: 'md' subdirectory in current directory)",
    )
    
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Process directories recursively",
    )
    
    parser.add_argument(
        "--no-lint",
        action="store_true",
        help="Skip markdownlint validation/fixing",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    
    return parser.parse_args()


def validate_input(path: Path) -> Tuple[bool, Optional[str]]:
    """Validate input path.
    
    Args:
        path: Path to validate.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    if not path.exists():
        return False, f"Path does not exist: {path}"
    
    if path.is_file() and path.suffix.lower() != ".pdf":
        return False, f"Not a PDF file: {path}"
    
    return True, None


def create_output_path(input_path: Path, output_dir: Path) -> Path:
    """Create output path for converted markdown file.
    
    Args:
        input_path: Input PDF file path.
        output_dir: Output directory.
        
    Returns:
        Output path with .md extension.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{input_path.stem}.md"


def get_pdf_files(path: Path, recursive: bool) -> List[Path]:
    """Get list of PDF files from path.
    
    Args:
        path: File or directory path.
        recursive: If True, search recursively in directories.
        
    Returns:
        List of PDF file paths.
    """
    if path.is_file():
        return [path] if path.suffix.lower() == ".pdf" else []
    
    if recursive:
        return list(path.rglob("*.pdf"))
    else:
        return list(path.glob("*.pdf"))


def run_markdownlint(file_path: Path, fix: bool = True) -> Tuple[bool, Optional[str]]:
    """Run markdownlint on a markdown file.
    
    Args:
        file_path: Path to the markdown file.
        fix: If True, automatically fix issues. If False, only check.
        
    Returns:
        Tuple of (success, error_message).
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Check if markdownlint is available
        subprocess.run(
            ["markdownlint", "--version"],
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("markdownlint not found. Skipping markdown validation.")
        logger.warning("Install it with: npm install -g markdownlint-cli")
        return True, None
    
    try:
        cmd = ["markdownlint"]
        if fix:
            cmd.append("--fix")
        cmd.append(str(file_path))
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        
        if result.returncode == 0:
            if fix:
                logger.debug("Markdown formatting fixed for: %s", file_path.name)
            return True, None
        else:
            error_msg = f"Markdown validation issues: {result.stdout}"
            if not fix:
                logger.warning(error_msg)
            return False, error_msg
            
    except Exception as e:
        error_msg = f"Error running markdownlint: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def process_pdf_file(pdf_path: Path, output_path: Path, no_lint: bool = False) -> Tuple[bool, Optional[str]]:
    """Convert a PDF file to Markdown.
    
    Args:
        pdf_path: Path to the PDF file.
        output_path: Path for the output Markdown file.
        no_lint: If True, skip markdownlint validation.
        
    Returns:
        Tuple of (success, error_message).
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.debug("Converting %s to markdown", pdf_path)
        
        # Convert PDF to markdown using pymupdf4llm
        markdown_content = pymupdf4llm.to_markdown(str(pdf_path))
        
        # Write markdown content to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_content, encoding="utf-8")
        
        logger.info("Successfully converted: %s -> %s", pdf_path.name, output_path.name)
        
        # Run markdownlint to fix formatting issues
        if not no_lint:
            lint_success, lint_error = run_markdownlint(output_path, fix=True)
            if not lint_success:
                logger.warning("Markdown formatting issues: %s", lint_error)
        
        return True, None
        
    except PermissionError:
        error_msg = f"Permission denied accessing file: {pdf_path}"
        logger.error(error_msg)
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Failed to convert {pdf_path}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code (0 for success, 1 for error).
    """
    args = parse_arguments()
    setup_logging(args.verbose)
    
    logger = logging.getLogger(__name__)
    logger.info("PDF Extractor v%s", __version__)
    
    # Set default output directory
    output_dir = args.output or Path("md")
    
    # Collect all PDF files to process
    pdf_files: List[Path] = []
    for input_path in args.inputs:
        is_valid, error_msg = validate_input(input_path)
        if not is_valid:
            logger.error(error_msg)
            continue
            
        pdf_files.extend(get_pdf_files(input_path, args.recursive))
    
    if not pdf_files:
        logger.error("No PDF files found to process")
        return 1
    
    logger.info("Found %d PDF file(s) to process", len(pdf_files))
    
    # Process PDF files
    successful = 0
    failed = 0
    
    for pdf_file in pdf_files:
        output_path = create_output_path(pdf_file, output_dir)
        success, error_msg = process_pdf_file(pdf_file, output_path, args.no_lint)
        
        if success:
            successful += 1
        else:
            failed += 1
    
    # Print summary
    logger.info("\nConversion Summary:")
    logger.info("  Successful: %d", successful)
    logger.info("  Failed: %d", failed)
    logger.info("  Total: %d", len(pdf_files))
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())