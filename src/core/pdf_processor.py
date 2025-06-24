"""
PDF document processing utilities.
"""
import hashlib
from pathlib import Path
from typing import List, Dict, Any
import pypdf
from pypdf import PdfReader


class PDFProcessor:
    """PDF document processor for text extraction and metadata."""

    @staticmethod
    def extract_text_from_pdf(file_path: Path) -> Dict[str, Any]:
        """
        Extract text content and metadata from PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted text, metadata, and page information
        """
        try:
            reader = PdfReader(file_path)
            
            # Extract metadata
            metadata = reader.metadata
            total_pages = len(reader.pages)
            
            # Extract text from all pages
            pages_text = []
            full_text = ""
            
            for page_num, page in enumerate(reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    pages_text.append({
                        "page_number": page_num,
                        "text": page_text,
                        "char_count": len(page_text)
                    })
                    full_text += f"\n--- Page {page_num} ---\n{page_text}"
                except Exception as e:
                    print(f"Error extracting text from page {page_num}: {e}")
                    pages_text.append({
                        "page_number": page_num,
                        "text": "",
                        "char_count": 0,
                        "error": str(e)
                    })
            
            return {
                "full_text": full_text.strip(),
                "pages": pages_text,
                "total_pages": total_pages,
                "metadata": {
                    "title": metadata.title if metadata and metadata.title else None,
                    "author": metadata.author if metadata and metadata.author else None,
                    "subject": metadata.subject if metadata and metadata.subject else None,
                    "creator": metadata.creator if metadata and metadata.creator else None,
                    "producer": metadata.producer if metadata and metadata.producer else None,
                    "creation_date": str(metadata.creation_date) if metadata and metadata.creation_date else None,
                    "modification_date": str(metadata.modification_date) if metadata and metadata.modification_date else None,
                },
                "total_characters": len(full_text),
                "success": True
            }
            
        except Exception as e:
            return {
                "full_text": "",
                "pages": [],
                "total_pages": 0,
                "metadata": {},
                "total_characters": 0,
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def calculate_file_hash(file_path: Path) -> str:
        """
        Calculate SHA-256 hash of the file content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA-256 hash string
        """
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            print(f"Error calculating file hash: {e}")
            return ""

    @staticmethod
    def validate_pdf_file(file_path: Path) -> Dict[str, Any]:
        """
        Validate PDF file and return validation results.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing validation results
        """
        try:
            # Check if file exists
            if not file_path.exists():
                return {"valid": False, "error": "File does not exist"}
            
            # Check file size
            file_size = file_path.stat().st_size
            max_size_bytes = 50 * 1024 * 1024  # 50MB
            
            if file_size > max_size_bytes:
                return {
                    "valid": False, 
                    "error": f"File too large: {file_size / (1024*1024):.2f}MB (max: 50MB)"
                }
            
            # Try to open PDF
            reader = PdfReader(file_path)
            page_count = len(reader.pages)
            
            if page_count == 0:
                return {"valid": False, "error": "PDF has no pages"}
            
            # Try to extract text from first page to check readability
            try:
                first_page_text = reader.pages[0].extract_text()
                has_text = bool(first_page_text.strip())
            except:
                has_text = False
            
            return {
                "valid": True,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024*1024), 2),
                "page_count": page_count,
                "has_extractable_text": has_text,
                "error": None
            }
            
        except Exception as e:
            return {"valid": False, "error": f"PDF validation error: {str(e)}"}

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1024, overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Split text into chunks with overlap.
        
        Args:
            text: Input text to chunk
            chunk_size: Maximum tokens per chunk
            overlap: Number of overlapping tokens between chunks
            
        Returns:
            List of text chunks with metadata
        """
        if not text.strip():
            return []
        
        # Simple token approximation: 1 token ≈ 4 characters
        chars_per_token = 4
        chunk_chars = chunk_size * chars_per_token
        overlap_chars = overlap * chars_per_token
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + chunk_chars
            
            # If not the last chunk, try to end at a sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 200 characters
                search_start = max(end - 200, start)
                sentence_end = -1
                
                for punct in ['. ', '! ', '? ', '\n\n']:
                    pos = text.rfind(punct, search_start, end)
                    if pos > sentence_end:
                        sentence_end = pos + len(punct) - 1
                
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "start_char": start,
                    "end_char": end,
                    "char_count": len(chunk_text),
                    "estimated_tokens": len(chunk_text) // chars_per_token
                })
                chunk_index += 1
            
            # Move start position considering overlap
            start = max(start + 1, end - overlap_chars)
            
            # Prevent infinite loop
            if start >= end:
                break
        
        return chunks