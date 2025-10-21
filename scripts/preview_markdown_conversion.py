"""Preview MarkItDown conversion for documents."""
import sys
import os
from pathlib import Path

# Add parent directory to path FIRST
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from loguru import logger
from markitdown import MarkItDown
import re


def preview_conversion(file_path: str, show_chunks: bool = False, chunk_size: int = 1024):
    """
    Preview MarkItDown conversion for a file.

    Args:
        file_path: Path to file to convert
        show_chunks: Also show how it would be chunked
        chunk_size: Chunk size for preview chunking
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return

    logger.info("=" * 70)
    logger.info(f"MARKITDOWN CONVERSION PREVIEW")
    logger.info("=" * 70)
    logger.info(f"File: {file_path.name}")
    logger.info(f"Path: {file_path}")
    logger.info(f"Size: {file_path.stat().st_size:,} bytes")
    logger.info("=" * 70)

    # Initialize MarkItDown
    md = MarkItDown()

    try:
        # Convert to markdown
        logger.info("\n🔄 Converting to Markdown...")
        result = md.convert(str(file_path))
        markdown_text = result.text_content

        logger.info(f"✅ Conversion successful!")
        logger.info(f"Markdown length: {len(markdown_text):,} characters")
        logger.info(f"Lines: {len(markdown_text.splitlines())}")

        # Show markdown content
        print("\n" + "=" * 70)
        print("CONVERTED MARKDOWN CONTENT")
        print("=" * 70)
        print(markdown_text)
        print("=" * 70)

        # Convert markdown to plain text (as done in document processor)
        logger.info("\n🔄 Converting Markdown to Plain Text...")
        plain_text = _markdown_to_text(markdown_text)

        logger.info(f"Plain text length: {len(plain_text):,} characters")
        logger.info(f"Lines: {len(plain_text.splitlines())}")

        print("\n" + "=" * 70)
        print("PLAIN TEXT (What gets chunked)")
        print("=" * 70)
        print(plain_text)
        print("=" * 70)

        # Show chunks if requested
        if show_chunks:
            logger.info(f"\n🔄 Chunking with size {chunk_size}...")
            chunks = _simple_chunk(plain_text, chunk_size, overlap=50)

            logger.info(f"Total chunks: {len(chunks)}")

            print("\n" + "=" * 70)
            print(f"CHUNKS (size={chunk_size}, overlap=50)")
            print("=" * 70)

            for i, chunk in enumerate(chunks, 1):
                print(f"\n{'─'*70}")
                print(f"Chunk {i}/{len(chunks)} ({len(chunk)} chars)")
                print(f"{'─'*70}")
                print(chunk)

                if i >= 5:  # Limit to first 5 chunks for preview
                    remaining = len(chunks) - 5
                    if remaining > 0:
                        print(f"\n... and {remaining} more chunks")
                    break

            print("=" * 70)

        # Analysis
        print("\n" + "=" * 70)
        print("ANALYSIS")
        print("=" * 70)

        # Check for metadata pollution
        metadata_patterns = [
            r'Source:\s*\w+',
            r'Original URL:\s*https?://',
            r'Page \d+ of \d+',
            r'^\s*#\s*$',  # Empty headers
        ]

        metadata_found = []
        for pattern in metadata_patterns:
            matches = re.findall(pattern, plain_text, re.MULTILINE)
            if matches:
                metadata_found.extend(matches)

        if metadata_found:
            print("\n⚠️  METADATA DETECTED:")
            for item in metadata_found[:10]:  # Show first 10
                print(f"   - {item}")
            if len(metadata_found) > 10:
                print(f"   ... and {len(metadata_found) - 10} more")
        else:
            print("\n✅ No obvious metadata pollution detected")

        # Check for very short content
        if len(plain_text.strip()) < 100:
            print(f"\n⚠️  WARNING: Very short content ({len(plain_text)} chars)")
            print("   This file might be mostly metadata or empty")

        # Check for repeated titles (common issue)
        lines = plain_text.splitlines()
        if len(lines) >= 2 and lines[0] == lines[1]:
            print(f"\n⚠️  WARNING: Duplicate title detected")
            print(f"   Line 1: {lines[0][:80]}")
            print(f"   Line 2: {lines[1][:80]}")

        print("=" * 70)

    except Exception as e:
        logger.error(f"❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()


def _markdown_to_text(markdown_text: str) -> str:
    """Convert markdown to plain text (same logic as DocumentProcessor)."""
    # Remove markdown headers
    text = re.sub(r'^#{1,6}\s+', '', markdown_text, flags=re.MULTILINE)

    # Remove bold/italic markers
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)

    # Remove links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Remove images
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)

    # Remove code blocks
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # Remove horizontal rules
    text = re.sub(r'^[\s]*[-*_]{3,}[\s]*$', '', text, flags=re.MULTILINE)

    # Clean up multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def _simple_chunk(text: str, chunk_size: int, overlap: int = 50):
    """Simple chunking for preview."""
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks


def batch_preview(directory: str, pattern: str = "*", show_chunks: bool = False):
    """Preview conversions for multiple files."""
    directory = Path(directory)

    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return

    # Find matching files
    files = list(directory.rglob(pattern))

    if not files:
        logger.warning(f"No files found matching '{pattern}' in {directory}")
        return

    logger.info(f"Found {len(files)} files matching '{pattern}'")

    for i, file_path in enumerate(files, 1):
        logger.info(f"\n{'#'*70}")
        logger.info(f"File {i}/{len(files)}")
        logger.info(f"{'#'*70}")

        preview_conversion(file_path, show_chunks=show_chunks)

        if i < len(files):
            response = input("\nPress Enter to continue, 's' to skip remaining, 'q' to quit: ").strip().lower()
            if response == 'q':
                break
            elif response == 's':
                logger.info("Skipping remaining files")
                break


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Preview MarkItDown conversion for documents"
    )
    parser.add_argument(
        "file_or_dir",
        type=str,
        help="File or directory to preview"
    )
    parser.add_argument(
        "--chunks",
        action="store_true",
        help="Also show how content would be chunked"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1024,
        help="Chunk size for preview (default: 1024)"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.html",
        help="File pattern for directory mode (default: *.html)"
    )
    parser.add_argument(
        "--export",
        type=str,
        help="Export markdown to file"
    )

    args = parser.parse_args()

    target = Path(args.file_or_dir)

    if target.is_file():
        # Single file mode
        preview_conversion(
            target,
            show_chunks=args.chunks,
            chunk_size=args.chunk_size
        )

        # Export if requested
        if args.export:
            md = MarkItDown()
            result = md.convert(str(target))
            with open(args.export, 'w', encoding='utf-8') as f:
                f.write(result.text_content)
            logger.info(f"💾 Markdown exported to: {args.export}")

    elif target.is_dir():
        # Directory mode
        batch_preview(
            target,
            pattern=args.pattern,
            show_chunks=args.chunks
        )

    else:
        logger.error(f"Not a valid file or directory: {target}")

