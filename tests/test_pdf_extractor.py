"""Tests for pdf_extractor module."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pdf_extractor import (
    create_output_path,
    get_pdf_files,
    parse_arguments,
    process_pdf_file,
    validate_input,
)


class TestValidateInput:
    """Test input validation."""
    
    def test_valid_pdf_file(self, tmp_path):
        """Test validation of valid PDF file."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.touch()
        
        is_valid, error = validate_input(pdf_file)
        assert is_valid is True
        assert error is None
    
    def test_invalid_file_extension(self, tmp_path):
        """Test validation rejects non-PDF files."""
        txt_file = tmp_path / "test.txt"
        txt_file.touch()
        
        is_valid, error = validate_input(txt_file)
        assert is_valid is False
        assert "Not a PDF file" in error
    
    def test_nonexistent_path(self):
        """Test validation of non-existent path."""
        fake_path = Path("/nonexistent/path.pdf")
        
        is_valid, error = validate_input(fake_path)
        assert is_valid is False
        assert "Path does not exist" in error
    
    def test_valid_directory(self, tmp_path):
        """Test validation of directory."""
        is_valid, error = validate_input(tmp_path)
        assert is_valid is True
        assert error is None


class TestGetPdfFiles:
    """Test PDF file discovery."""
    
    def test_single_pdf_file(self, tmp_path):
        """Test getting single PDF file."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.touch()
        
        files = get_pdf_files(pdf_file, recursive=False)
        assert len(files) == 1
        assert files[0] == pdf_file
    
    def test_non_pdf_file(self, tmp_path):
        """Test that non-PDF files are ignored."""
        txt_file = tmp_path / "test.txt"
        txt_file.touch()
        
        files = get_pdf_files(txt_file, recursive=False)
        assert len(files) == 0
    
    def test_directory_non_recursive(self, tmp_path):
        """Test finding PDFs in directory without recursion."""
        # Create PDFs in root
        (tmp_path / "file1.pdf").touch()
        (tmp_path / "file2.pdf").touch()
        (tmp_path / "file3.txt").touch()
        
        # Create PDFs in subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file4.pdf").touch()
        
        files = get_pdf_files(tmp_path, recursive=False)
        assert len(files) == 2
        assert all(f.suffix == ".pdf" for f in files)
        assert all(f.parent == tmp_path for f in files)
    
    def test_directory_recursive(self, tmp_path):
        """Test finding PDFs in directory with recursion."""
        # Create PDFs in root
        (tmp_path / "file1.pdf").touch()
        (tmp_path / "file2.pdf").touch()
        
        # Create PDFs in subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.pdf").touch()
        
        files = get_pdf_files(tmp_path, recursive=True)
        assert len(files) == 3
        assert all(f.suffix == ".pdf" for f in files)


class TestCreateOutputPath:
    """Test output path creation."""
    
    def test_create_output_path(self, tmp_path):
        """Test creating output path for PDF."""
        input_pdf = Path("/some/path/document.pdf")
        output_dir = tmp_path / "output"
        
        output_path = create_output_path(input_pdf, output_dir)
        
        assert output_path.parent == output_dir
        assert output_path.name == "document.md"
        assert output_dir.exists()
    
    def test_create_nested_output_path(self, tmp_path):
        """Test creating nested output directories."""
        input_pdf = Path("/some/path/document.pdf")
        output_dir = tmp_path / "a" / "b" / "c"
        
        output_path = create_output_path(input_pdf, output_dir)
        
        assert output_dir.exists()
        assert output_path == output_dir / "document.md"


class TestProcessPdfFile:
    """Test PDF processing."""
    
    @patch("pdf_extractor.pymupdf4llm.to_markdown")
    def test_successful_conversion(self, mock_to_markdown, tmp_path):
        """Test successful PDF conversion."""
        # Setup
        pdf_file = tmp_path / "test.pdf"
        pdf_file.touch()
        output_file = tmp_path / "output" / "test.md"
        mock_to_markdown.return_value = "# Test Markdown\n\nContent"
        
        # Execute
        success, error = process_pdf_file(pdf_file, output_file, no_lint=True)
        
        # Verify
        assert success is True
        assert error is None
        assert output_file.exists()
        assert output_file.read_text() == "# Test Markdown\n\nContent"
        mock_to_markdown.assert_called_once_with(str(pdf_file))
    
    @patch("pdf_extractor.pymupdf4llm.to_markdown")
    def test_conversion_failure(self, mock_to_markdown, tmp_path):
        """Test handling of conversion failure."""
        # Setup
        pdf_file = tmp_path / "test.pdf"
        pdf_file.touch()
        output_file = tmp_path / "output" / "test.md"
        mock_to_markdown.side_effect = Exception("Conversion failed")
        
        # Execute
        success, error = process_pdf_file(pdf_file, output_file, no_lint=True)
        
        # Verify
        assert success is False
        assert "Failed to convert" in error
        assert "Conversion failed" in error
        assert not output_file.exists()
    
    @patch("pdf_extractor.pymupdf4llm.to_markdown")
    def test_permission_error(self, mock_to_markdown, tmp_path):
        """Test handling of permission errors."""
        # Setup
        pdf_file = tmp_path / "test.pdf"
        pdf_file.touch()
        output_file = tmp_path / "output" / "test.md"
        mock_to_markdown.side_effect = PermissionError("Access denied")
        
        # Execute
        success, error = process_pdf_file(pdf_file, output_file, no_lint=True)
        
        # Verify
        assert success is False
        assert "Permission denied" in error


class TestParseArguments:
    """Test argument parsing."""
    
    def test_single_input(self):
        """Test parsing single input file."""
        with patch("sys.argv", ["pdf_extractor.py", "test.pdf"]):
            args = parse_arguments()
            assert len(args.inputs) == 1
            assert args.inputs[0] == Path("test.pdf")
            assert args.output is None
            assert args.verbose is False
            assert args.recursive is False
    
    def test_multiple_inputs(self):
        """Test parsing multiple input files."""
        with patch("sys.argv", ["pdf_extractor.py", "file1.pdf", "file2.pdf", "dir1"]):
            args = parse_arguments()
            assert len(args.inputs) == 3
            assert args.inputs[0] == Path("file1.pdf")
            assert args.inputs[1] == Path("file2.pdf")
            assert args.inputs[2] == Path("dir1")
    
    def test_output_directory(self):
        """Test parsing output directory."""
        with patch("sys.argv", ["pdf_extractor.py", "test.pdf", "-o", "output"]):
            args = parse_arguments()
            assert args.output == Path("output")
    
    def test_verbose_flag(self):
        """Test parsing verbose flag."""
        with patch("sys.argv", ["pdf_extractor.py", "test.pdf", "-v"]):
            args = parse_arguments()
            assert args.verbose is True
    
    def test_recursive_flag(self):
        """Test parsing recursive flag."""
        with patch("sys.argv", ["pdf_extractor.py", "dir", "--recursive"]):
            args = parse_arguments()
            assert args.recursive is True


@pytest.fixture
def test_pdf_dir():
    """Get test PDF directory."""
    return Path(__file__).parent.parent / "test" / "resources" / "pdf"


class TestIntegration:
    """Integration tests using real PDF files."""
    
    def test_process_real_pdf(self, test_pdf_dir, tmp_path):
        """Test processing a real PDF file if available."""
        pdf_files = list(test_pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            pytest.skip("No test PDF files found")
        
        # Process first available PDF
        pdf_file = pdf_files[0]
        output_file = tmp_path / f"{pdf_file.stem}.md"
        
        success, error = process_pdf_file(pdf_file, output_file, no_lint=True)
        
        assert success is True
        assert error is None
        assert output_file.exists()
        assert output_file.stat().st_size > 0  # Non-empty file
        
        # Basic validation of markdown content
        content = output_file.read_text()
        assert len(content) > 0  # Has content
        
        # Check for common markdown elements
        # Most PDFs should have at least some text
        assert any(char.isalnum() for char in content)