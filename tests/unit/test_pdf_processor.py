"""
Unit tests for PDF processor.
"""
import pytest
from pathlib import Path
from src.core.pdf_processor import PDFProcessor


class TestPDFProcessor:
    """Test cases for PDFProcessor."""

    def setup_method(self):
        """Setup test fixtures."""
        self.processor = PDFProcessor()

    def test_chunk_text_basic(self):
        """Test basic text chunking functionality."""
        text = "This is a test document. " * 100
        chunks = self.processor.chunk_text(text, chunk_size=50, overlap=10)
        
        assert len(chunks) > 1
        assert all('chunk_index' in chunk for chunk in chunks)
        assert all('text' in chunk for chunk in chunks)
        assert all('estimated_tokens' in chunk for chunk in chunks)

    def test_chunk_text_empty(self):
        """Test chunking empty text."""
        chunks = self.processor.chunk_text("")
        assert chunks == []

    def test_chunk_text_short(self):
        """Test chunking text shorter than chunk size."""
        text = "Short text."
        chunks = self.processor.chunk_text(text, chunk_size=1000)
        
        assert len(chunks) == 1
        assert chunks[0]['text'] == text

    def test_calculate_file_hash_nonexistent(self):
        """Test hash calculation for non-existent file."""
        result = self.processor.calculate_file_hash(Path("/nonexistent/file.pdf"))
        assert result == ""

    def test_validate_pdf_file_nonexistent(self):
        """Test PDF validation for non-existent file."""
        result = self.processor.validate_pdf_file(Path("/nonexistent/file.pdf"))
        assert not result["valid"]
        assert "does not exist" in result["error"]