"""Document processing and chunking utilities."""
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from markitdown import MarkItDown
import markdown
from bs4 import BeautifulSoup
from loguru import logger


@dataclass
class DocumentChunk:
    """Represents a chunk of document text with metadata."""
    content: str
    metadata: Dict[str, Any]
    chunk_id: str


class DocumentProcessor:
    """Process various document formats and chunk them for vectorization."""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Initialize the document processor.

        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.markitdown = MarkItDown()
        logger.info(
            "Initialized MarkItDown converter for unified document processing")

    def load_document(self, file_path: str) -> tuple[str, Dict[str, Any]]:
        """
        Load a document and extract its text content using MarkItDown.

        Args:
            file_path: Path to the document file

        Returns:
            Tuple of (markdown_text_content, metadata)
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Extract metadata
        metadata = {
            "source": str(file_path),
            "filename": file_path.name,
            "file_type": file_path.suffix.lower(),
        }

        # Detect source organization from path or filename
        metadata["source_org"] = self._detect_source_org(str(file_path))

        try:
            # Use MarkItDown for unified conversion to Markdown
            logger.debug(
                f"Converting {file_path.name} to Markdown using MarkItDown...")
            result = self.markitdown.convert(str(file_path))

            # Extract the markdown text
            markdown_text = result.text_content if hasattr(
                result, 'text_content') else str(result)

            # Convert markdown to plain text for better chunking
            text = self._markdown_to_text(markdown_text)

            logger.debug(
                f"Successfully converted {file_path.name} ({len(text)} chars)")

            return text, metadata

        except Exception as e:
            logger.error(f"Error converting {file_path} with MarkItDown: {e}")
            # Fallback to simple text extraction
            logger.warning(
                f"Falling back to simple text extraction for {file_path.name}")
            return self._fallback_load(file_path), metadata

    def _markdown_to_text(self, markdown_text: str) -> str:
        """
        Convert markdown to plain text while preserving structure.

        Args:
            markdown_text: Markdown formatted text

        Returns:
            Plain text with preserved structure
        """
        try:
            # Convert markdown to HTML
            html = markdown.markdown(markdown_text)
            # Extract plain text using BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text(separator='\n')
            return text
        except Exception as e:
            logger.warning(
                f"Error converting markdown to text: {e}, returning raw markdown")
            return markdown_text

    def _fallback_load(self, file_path: Path) -> str:
        """
        Fallback method for simple text extraction when MarkItDown fails.

        Args:
            file_path: Path to the file

        Returns:
            Extracted text content
        """
        try:
            # Try reading as plain text with different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read()
                except UnicodeDecodeError:
                    continue

            # If all encodings fail, read as binary and decode with errors ignored
            with open(file_path, 'rb') as file:
                return file.read().decode('utf-8', errors='ignore')

        except Exception as e:
            logger.error(f"Fallback load failed for {file_path}: {e}")
            raise

    def _detect_source_org(self, file_path: str) -> str:
        """Detect source organization from file path or name."""
        path_lower = file_path.lower()

        if 'hkch' in path_lower or 'hkch' in path_lower:
            return 'HKCH'
        elif 'sickkids' in path_lower or 'sick_kids' in path_lower:
            return 'SickKids'
        elif 'hksir' in path_lower:
            return 'HKSIR'
        elif 'cirse' in path_lower:
            return 'CIRSE'
        elif 'sir' in path_lower and 'hksir' not in path_lower:
            return 'SIR'
        else:
            return 'Unknown'

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
        """
        Split text into overlapping chunks with HARD size limit enforcement.

        Args:
            text: Text content to chunk
            metadata: Document metadata to attach to each chunk

        Returns:
            List of DocumentChunk objects
        """
        # Clean the text
        text = self._clean_text(text)

        chunks = []
        chunk_index = 0
        start = 0
        text_length = len(text)

        while start < text_length:
            # Calculate end position
            end = start + self.chunk_size

            # If this is not the last chunk, try to break at a sentence or word boundary
            if end < text_length:
                # Look for sentence endings within the last 20% of the chunk
                search_start = max(start, end - int(self.chunk_size * 0.2))
                sentence_end = max(
                    text.rfind('. ', search_start, end),
                    text.rfind('.\n', search_start, end),
                    text.rfind('! ', search_start, end),
                    text.rfind('? ', search_start, end),
                    text.rfind('。', search_start, end),  # Chinese period
                    text.rfind('！', search_start, end),  # Chinese exclamation
                    text.rfind('？', search_start, end),  # Chinese question mark
                )

                if sentence_end > search_start:
                    end = sentence_end + 1
                else:
                    # No sentence boundary found, look for word boundary
                    word_end = text.rfind(' ', search_start, end)
                    if word_end > search_start:
                        end = word_end

            # Extract chunk
            chunk_text = text[start:end].strip()

            # Only add non-empty chunks
            if chunk_text:
                chunk_id = f"{metadata['filename']}_chunk_{chunk_index}"
                chunks.append(DocumentChunk(
                    content=chunk_text,
                    metadata={**metadata, "chunk_index": chunk_index, "chunk_size": len(chunk_text)},
                    chunk_id=chunk_id
                ))
                chunk_index += 1

            # Move start position with overlap
            if end < text_length:
                start = end - self.chunk_overlap
            else:
                break

        avg_size = sum(len(c.content) for c in chunks) // len(chunks) if chunks else 0
        max_size = max(len(c.content) for c in chunks) if chunks else 0

        logger.info(f"Created {len(chunks)} chunks from {metadata['filename']} "
                   f"(avg: {avg_size} chars, max: {max_size} chars)")

        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove excessive newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()

    def process_directory(self, directory_path: str,
                          file_patterns: Optional[List[str]] = None) -> List[DocumentChunk]:
        """
        Process all documents in a directory using MarkItDown.

        Args:
            directory_path: Path to directory containing documents
            file_patterns: Optional list of file patterns to match (e.g., ['*.pdf', '*.docx'])

        Returns:
            List of all DocumentChunk objects from all documents
        """
        directory = Path(directory_path)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        all_chunks = []

        # Extended file patterns - MarkItDown supports many formats
        if file_patterns is None:
            file_patterns = [
                '*.pdf', '*.docx', '*.doc', '*.pptx', '*.ppt',  # Office documents
                '*.xlsx', '*.xls', '*.csv',  # Spreadsheets
                '*.md', '*.markdown', '*.txt',  # Text formats
                '*.html', '*.htm',  # Web formats
                '*.jpg', '*.jpeg', '*.png',  # Images (with OCR if available)
                '*.mp3', '*.wav'  # Audio (with transcription if available)
            ]

        # Collect all matching files
        files = []
        for pattern in file_patterns:
            files.extend(directory.rglob(pattern))

        # Remove duplicates
        files = list(set(files))

        logger.info(f"Found {len(files)} files to process in {directory}")
        logger.info(
            f"Using MarkItDown for unified conversion to Markdown format")

        for file_path in files:
            try:
                logger.info(f"Processing: {file_path}")
                text, metadata = self.load_document(str(file_path))
                chunks = self.chunk_text(text, metadata)
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue

        logger.info(f"Total chunks created: {len(all_chunks)}")
        return all_chunks
