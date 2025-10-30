import sys
import os

# Get the absolute path of the script's directory (i.e., pedlRbot/scripts)
script_dir = os.path.dirname(os.path.abspath(__file__))

# Get the path of the project root (pedlRbot) by going one level up
project_root = os.path.dirname(script_dir)

# Add the project root to the Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

"""Script to ingest documents from KB folder into vector database."""
from pathlib import Path

from src.vector_store import VectorStore
from src.embeddings import get_embedding_model
from src.document_processor import DocumentProcessor
from config import settings
from loguru import logger


# isort: off  - Don't reorder imports below this line
# isort: on


def _is_picc_related(file_path: Path, content: str = "") -> bool:
    """
    Check if a document is PICC-related based on filename or content.

    Args:
        file_path: Path to the file
        content: Optional content to check (if already loaded)

    Returns:
        True if document appears to be PICC-related
    """
    picc_keywords = [
        'picc', 'PICC', 'peripherally inserted central catheter',
        'peripherally inserted central', 'central venous catheter',
        'picc line', 'picc insertion', 'picc removal'
    ]

    # Check filename
    filename_lower = file_path.name.lower()
    if any(keyword.lower() in filename_lower for keyword in picc_keywords):
        return True

    # Check file path
    path_str = str(file_path).lower()
    if any(keyword.lower() in path_str for keyword in picc_keywords):
        return True

    # Check content if provided
    if content:
        content_lower = content.lower()
        # Check if multiple PICC keywords appear (more reliable)
        matches = sum(1 for keyword in picc_keywords if keyword.lower() in content_lower)
        if matches >= 2:  # At least 2 keyword matches
            return True

    return False


def main(kb_folder: str, reset: bool = False, markdown_only: bool = True, picc_only: bool = False):
    """
    Ingest documents from KB folder into vector database.

    Args:
        kb_folder: Path to KB folder containing documents
        reset: Whether to reset the collection before ingestion
        markdown_only: Only process markdown files (default: True)
        picc_only: Only ingest PICC-related documents (default: False)
    """
    from pathlib import Path

    logger.info("=" * 70)
    logger.info("DOCUMENT INGESTION")
    logger.info("=" * 70)
    logger.info(f"Source: {kb_folder}")
    logger.info(f"Embedding provider: {settings.embedding_provider}")
    logger.info(f"Markdown only: {markdown_only}")
    logger.info(f"PICC-only filter: {picc_only}")
    if picc_only:
        logger.info("⚠️  Only PICC-related documents will be ingested")
    logger.info("=" * 70)

    # Check if this is the markdown directory
    kb_path = Path(kb_folder)
    if markdown_only and not kb_path.name == 'md' and not str(kb_path).endswith('/md'):
        logger.warning("⚠️  Markdown-only mode enabled but not using KB/md/ directory")
        logger.warning(f"   Expected: KB/md/ or */md/")
        logger.warning(f"   Got: {kb_folder}")
        logger.warning("")
        logger.warning("💡 Recommended workflow:")
        logger.warning("   1. Convert documents: python scripts/convert_to_markdown.py KB KB/md")
        logger.warning("   2. Ingest markdown:   python scripts/ingest_documents.py KB/md --reset")
        logger.warning("")
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Ingestion cancelled")
            return

    # Initialize components
    logger.info("\n🔧 Initializing components...")
    embedding_model = get_embedding_model()
    vector_store = VectorStore(embedding_model)

    if reset:
        logger.warning("🗑️  Resetting collection...")
        vector_store.reset_collection()

    # Process documents
    logger.info("\n📄 Processing documents...")
    processor = DocumentProcessor(
        chunk_size=settings.max_chunk_size,
        chunk_overlap=settings.chunk_overlap,
        markdown_only=markdown_only  # Pass markdown_only flag
    )

    # Check for non-markdown files if markdown_only is True
    if markdown_only:
        all_files = list(kb_path.rglob('*'))
        non_md_files = [f for f in all_files if f.is_file() and f.suffix.lower() not in ['.md', '.markdown', '.gitkeep']]

        if non_md_files:
            logger.warning(f"\n⚠️  Found {len(non_md_files)} non-markdown files (will be skipped):")
            for f in non_md_files[:5]:  # Show first 5
                logger.warning(f"   - {f.name}")
            if len(non_md_files) > 5:
                logger.warning(f"   ... and {len(non_md_files) - 5} more")
            logger.warning("\n💡 Convert them first: python scripts/convert_to_markdown.py KB KB/md")

    # Process documents
    all_chunks = processor.process_directory(kb_folder)

    # Filter for PICC-only if requested
    if picc_only:
        logger.info("\n🔍 Filtering for PICC-related documents...")
        filtered_chunks = []
        skipped_count = 0

        for chunk in all_chunks:
            # Get file path from metadata
            source_path = chunk.metadata.get('source', '')
            if source_path:
                file_path = Path(source_path)
                # Check if PICC-related (check filename and content)
                if _is_picc_related(file_path, chunk.content):
                    filtered_chunks.append(chunk)
                else:
                    skipped_count += 1

        chunks = filtered_chunks
        logger.info(f"✅ Kept {len(chunks)} PICC-related chunks")
        logger.info(f"⏭️  Skipped {skipped_count} non-PICC chunks")

        if not chunks:
            logger.error("\n❌ No PICC-related documents found!")
            logger.error("   Check that your KB folder contains PICC-related files")
            return
    else:
        chunks = all_chunks

    if not chunks:
        logger.error("\n❌ No documents processed!")
        logger.error("   Possible reasons:")
        logger.error("   1. No markdown files in directory")
        logger.error("   2. All files failed to process")
        logger.error("   3. Wrong directory specified")
        logger.error("")
        logger.error("💡 Try: python scripts/convert_to_markdown.py KB KB/md")
        return

    # Add to vector store
    logger.info(f"\n🔄 Adding {len(chunks)} chunks to vector store...")
    vector_store.add_documents(chunks)

    # Print statistics
    stats = vector_store.get_stats()
    logger.info("\n" + "=" * 70)
    logger.info("✅ INGESTION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Collection: {stats['collection_name']}")
    logger.info(f"Total documents: {stats['total_documents']}")
    logger.info(f"Persist directory: {stats['persist_directory']}")
    logger.info("=" * 70)
    logger.info("\n💡 Next steps:")
    logger.info("   1. Test retrieval: python scripts/analyze_retrieval.py 'Your query here'")
    logger.info("   2. Test chat:      python test_chat.py")
    logger.info("=" * 70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest documents into vector database (markdown files only by default)"
    )
    parser.add_argument(
        "kb_folder",
        type=str,
        nargs='?',
        default="KB/md",
        help="Path to markdown folder (default: KB/md)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset collection before ingestion"
    )
    parser.add_argument(
        "--allow-all-formats",
        action="store_true",
        help="Allow processing non-markdown files (not recommended)"
    )
    parser.add_argument(
        "--picc-only",
        action="store_true",
        help="Only ingest PICC-related documents (useful for testing with smaller KB)"
    )

    args = parser.parse_args()

    main(args.kb_folder, args.reset, markdown_only=not args.allow_all_formats, picc_only=args.picc_only)
