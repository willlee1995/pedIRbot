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
from src.document_db import DocumentDatabase
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


def main(kb_folder: str, reset: bool = False, markdown_only: bool = True, picc_only: bool = False, whole_document: bool = False, sqlite_only: bool = False):
    """
    Ingest documents from KB folder into vector database.

    Args:
        kb_folder: Path to KB folder containing documents
        reset: Whether to reset the collection before ingestion
        markdown_only: Only process markdown files (default: True)
        picc_only: Only ingest PICC-related documents (default: False)
        whole_document: Embed whole documents without chunking (default: False)
        sqlite_only: Only store in SQLite, skip vector store chunking (default: False)
    """
    from pathlib import Path

    logger.info("=" * 70)
    logger.info("DOCUMENT INGESTION")
    logger.info("=" * 70)
    logger.info(f"Source: {kb_folder}")
    logger.info(f"Embedding provider: {settings.embedding_provider}")
    logger.info(f"Markdown only: {markdown_only}")
    logger.info(f"PICC-only filter: {picc_only}")
    logger.info(f"Whole document mode: {whole_document}")
    logger.info(f"SQLite only mode: {sqlite_only}")
    if picc_only:
        logger.info("⚠️  Only PICC-related documents will be ingested")
    if sqlite_only:
        logger.info("📚 SQLite-only mode: Documents will be stored in SQLite, NO chunking or vector store")
        logger.info("   Agent will use SQL tools to fetch full documents directly")
    elif whole_document:
        logger.info("📄 Whole documents will be embedded (no chunking)")
        logger.warning("⚠️  IMPORTANT: Make sure your embedding model supports long documents!")
        logger.warning("   For whole document mode, consider using a model with larger context window:")
        logger.warning("   - nomic-embed-text (supports up to ~8000 chars)")
        logger.warning("   - mxbai-embed-large (supports up to ~2000 chars)")
        logger.warning("   Current model: " + settings.ollama_embedding_model)
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

    # Initialize document database for storing full documents
    document_db = DocumentDatabase()
    if reset:
        logger.warning("🗑️  Resetting collection and database...")
        vector_store.reset_collection()
        document_db.reset_database()

    # Process documents
    logger.info("\n📄 Processing documents...")
    processor = DocumentProcessor(
        chunk_size=settings.max_chunk_size,
        chunk_overlap=settings.chunk_overlap,
        markdown_only=markdown_only,  # Pass markdown_only flag
        whole_document=whole_document  # Pass whole_document flag
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

    # Process documents and store full documents in SQLite
    # First, collect full documents before chunking
    logger.info("\n📚 Collecting full documents for SQLite storage...")
    kb_path = Path(kb_folder)
    full_documents = {}

    # Collect full documents
    for file_path in kb_path.rglob('*.md'):
        if not file_path.is_file():
            continue

        try:
            text, metadata = processor.load_document(str(file_path))
            procedure_category = processor._classify_procedure_category(text, str(file_path))
            metadata["procedure_category"] = procedure_category

            # Create document ID from filename (without extension)
            document_id = file_path.stem
            full_documents[document_id] = {
                'text': text,
                'metadata': metadata
            }
        except Exception as e:
            logger.warning(f"Error loading document {file_path}: {e}")
            continue

    # Store full documents in SQLite
    logger.info(f"💾 Storing {len(full_documents)} full documents in SQLite...")
    for doc_id, doc_data in full_documents.items():
        document_db.store_document(
            document_id=doc_id,
            filename=doc_data['metadata'].get('filename', doc_id),
            content=doc_data['text'],
            metadata=doc_data['metadata']
        )

    logger.info(f"✅ Stored {len(full_documents)} documents in SQLite database")

    # If sqlite_only mode, skip chunking and vector store entirely
    if sqlite_only:
        logger.info("\n⏭️  Skipping chunking and vector store (SQLite-only mode)")
        logger.info("   Documents are available via SQL tools only")

        # Print SQLite statistics only
        sqlite_stats = document_db.get_stats()
        logger.info("\n" + "=" * 70)
        logger.info("✅ INGESTION COMPLETE (SQLite Only)")
        logger.info("=" * 70)
        logger.info("Document Database (SQLite):")
        logger.info(f"  Total documents: {sqlite_stats['total_documents']}")
        logger.info(f"  Unique organizations: {sqlite_stats['unique_orgs']}")
        logger.info(f"  Unique regions: {sqlite_stats['unique_regions']}")
        logger.info(f"  Unique categories: {sqlite_stats['unique_categories']}")
        logger.info(f"  Database path: {document_db.db_path}")
        logger.info("=" * 70)
        logger.info("\n💡 Next steps:")
        logger.info("   Agent will use SQL tools (search_documents_sql, get_document_by_id) to access documents")
        logger.info("   No vector search available - use SQL queries with metadata filters")
        logger.info("=" * 70)
        return

    # Process documents for chunking (normal mode: SQLite + Vector Store)
    logger.info("\n🔄 Processing documents for vector store...")
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
    vector_stats = vector_store.get_stats()
    sqlite_stats = document_db.get_stats()

    logger.info("\n" + "=" * 70)
    logger.info("✅ INGESTION COMPLETE")
    logger.info("=" * 70)
    logger.info("Vector Store (ChromaDB):")
    logger.info(f"  Collection: {vector_stats['collection_name']}")
    logger.info(f"  Total chunks: {vector_stats['total_documents']}")
    logger.info(f"  Persist directory: {vector_stats['persist_directory']}")
    logger.info("")
    logger.info("Document Database (SQLite):")
    logger.info(f"  Total documents: {sqlite_stats['total_documents']}")
    logger.info(f"  Unique organizations: {sqlite_stats['unique_orgs']}")
    logger.info(f"  Unique regions: {sqlite_stats['unique_regions']}")
    logger.info(f"  Unique categories: {sqlite_stats['unique_categories']}")
    logger.info(f"  Database path: {document_db.db_path}")
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
    parser.add_argument(
        "--whole-document",
        action="store_true",
        help="Embed whole documents without chunking (keeps information together)"
    )
    parser.add_argument(
        "--sqlite-only",
        action="store_true",
        help="Only store in SQLite, skip chunking and vector store (agent uses SQL tools only)"
    )

    args = parser.parse_args()

    main(
        args.kb_folder,
        args.reset,
        markdown_only=not args.allow_all_formats,
        picc_only=args.picc_only,
        whole_document=args.whole_document,
        sqlite_only=args.sqlite_only
    )
