"""Script to ingest documents from KB folder into LEANN vector index."""
import sys
import os

# Get the absolute path of the script's directory (i.e., pedIRbot/scripts)
script_dir = os.path.dirname(os.path.abspath(__file__))

# Get the path of the project root (pedIRbot) by going one level up
project_root = os.path.dirname(script_dir)

# Add the project root to the Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from pathlib import Path
import argparse

from src.vector_store_leann import LEANNVectorStore
from src.embeddings import get_embedding_model
from src.document_processor import DocumentProcessor
from src.document_db import DocumentDatabase
from config import settings
from loguru import logger


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
        matches = sum(1 for keyword in picc_keywords if keyword.lower() in content_lower)
        if matches >= 2:
            return True

    return False


def main(
    kb_folder: str,
    reset: bool = False,
    markdown_only: bool = True,
    picc_only: bool = False,
    whole_document: bool = False,
    backend: str = "hnsw",
    graph_degree: int = 32,
    complexity: int = 64,
    compact: bool = True,
    recompute: bool = True
):
    """
    Ingest documents from KB folder into LEANN vector index.

    Args:
        kb_folder: Path to KB folder containing documents
        reset: Whether to reset the index before ingestion
        markdown_only: Only process markdown files (default: True)
        picc_only: Only ingest PICC-related documents (default: False)
        whole_document: Embed whole documents without chunking (default: False)
        backend: LEANN backend ("hnsw" or "diskann")
        graph_degree: Graph degree for HNSW (default: 32)
        complexity: Build complexity (default: 64)
        compact: Use compact storage (default: True)
        recompute: Enable recomputation (default: True)
    """
    from pathlib import Path

    logger.info("=" * 70)
    logger.info("LEANN DOCUMENT INGESTION")
    logger.info("=" * 70)
    logger.info(f"Source: {kb_folder}")
    logger.info(f"Embedding provider: {settings.embedding_provider}")
    logger.info(f"Backend: {backend}")
    logger.info(f"Graph Degree: {graph_degree}, Complexity: {complexity}")
    logger.info(f"Compact: {compact}, Recompute: {recompute}")
    logger.info(f"Markdown only: {markdown_only}")
    logger.info(f"PICC-only filter: {picc_only}")
    logger.info(f"Whole document mode: {whole_document}")
    if picc_only:
        logger.info("⚠️  Only PICC-related documents will be ingested")
    if whole_document:
        logger.info("📄 Whole documents will be embedded (no chunking)")
        logger.warning("⚠️  IMPORTANT: Make sure your embedding model supports long documents!")
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
        logger.warning("   2. Ingest markdown:   python scripts/ingest_documents_leann.py KB/md --reset")
        logger.warning("")
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Ingestion cancelled")
            return

    # Initialize components
    logger.info("\n🔧 Initializing components...")
    embedding_model = get_embedding_model()
    vector_store = LEANNVectorStore(
        embedding_model,
        backend=backend,
        graph_degree=graph_degree,
        complexity=complexity,
        compact=compact,
        recompute=recompute
    )

    # Initialize document database for storing full documents
    document_db = DocumentDatabase()
    if reset:
        logger.warning("🗑️  Resetting LEANN index and database...")
        vector_store.reset_index()
        document_db.reset_database()

    # Process documents
    logger.info("\n📄 Processing documents...")
    processor = DocumentProcessor(
        chunk_size=settings.max_chunk_size,
        chunk_overlap=settings.chunk_overlap,
        markdown_only=markdown_only,
        whole_document=whole_document
    )

    # Check for non-markdown files if markdown_only is True
    if markdown_only:
        all_files = list(kb_path.rglob('*'))
        non_md_files = [f for f in all_files if f.is_file() and f.suffix.lower() not in ['.md', '.markdown', '.gitkeep']]

        if non_md_files:
            logger.warning(f"\n⚠️  Found {len(non_md_files)} non-markdown files (will be skipped):")
            for f in non_md_files[:5]:
                logger.warning(f"   - {f.name}")
            if len(non_md_files) > 5:
                logger.warning(f"   ... and {len(non_md_files) - 5} more")

    # Collect all documents
    all_chunks = []
    total_documents = 0
    skipped_documents = 0

    # Find all markdown files
    if markdown_only:
        files = list(kb_path.rglob('*.md')) + list(kb_path.rglob('*.markdown'))
    else:
        # Support various file types
        extensions = ['.md', '.markdown', '.pdf', '.docx', '.pptx', '.txt', '.html']
        files = []
        for ext in extensions:
            files.extend(kb_path.rglob(f'*{ext}'))

    logger.info(f"\n📚 Found {len(files)} files to process")

    # Process each file
    for file_path in files:
        try:
            # Skip hidden files and directories
            if file_path.name.startswith('.'):
                continue

            # PICC filter
            if picc_only:
                if not _is_picc_related(file_path):
                    skipped_documents += 1
                    continue

            # Load and process document
            text, metadata = processor.load_document(str(file_path))
            if not text:
                logger.warning(f"⚠️  Skipping empty document: {file_path.name}")
                skipped_documents += 1
                continue

            # Store full document in SQLite
            document_id = document_db.add_document(
                filename=metadata.get('filename', file_path.name),
                content=text,
                source=metadata.get('source', str(file_path)),
                metadata=metadata
            )
            logger.debug(f"Stored full document in SQLite: {file_path.name} (ID: {document_id})")

            # Chunk document
            chunks = processor.chunk_document(text, metadata)
            logger.debug(f"Created {len(chunks)} chunks from {file_path.name}")

            # Add document_id to chunk metadata
            for chunk in chunks:
                chunk.metadata['document_id'] = document_id

            all_chunks.extend(chunks)
            total_documents += 1

            if total_documents % 10 == 0:
                logger.info(f"Processed {total_documents} documents, {len(all_chunks)} chunks so far...")

        except Exception as e:
            logger.error(f"❌ Error processing {file_path.name}: {e}")
            logger.exception(e)
            skipped_documents += 1
            continue

    logger.info(f"\n✅ Processing complete!")
    logger.info(f"   Total documents: {total_documents}")
    logger.info(f"   Skipped documents: {skipped_documents}")
    logger.info(f"   Total chunks: {len(all_chunks)}")

    if not all_chunks:
        logger.warning("⚠️  No chunks to add. Exiting.")
        return

    # Add chunks to LEANN index
    logger.info(f"\n🔨 Building LEANN index with {len(all_chunks)} chunks...")
    logger.info("   This may take a while depending on the number of documents...")

    vector_store.add_documents(all_chunks)
    vector_store.build_index(force=reset)

    # Get stats
    stats = vector_store.get_stats()
    logger.info("\n" + "=" * 70)
    logger.info("LEANN INDEX STATISTICS")
    logger.info("=" * 70)
    logger.info(f"Index Name: {stats['index_name']}")
    logger.info(f"Index Path: {stats['index_path']}")
    logger.info(f"Index Size: {stats['index_size_mb']} MB")
    logger.info(f"Backend: {stats['backend']}")
    logger.info(f"Compact Storage: {stats['compact']}")
    logger.info(f"Recompute Enabled: {stats['recompute']}")
    logger.info(f"Total Chunks: {len(all_chunks)}")
    logger.info("=" * 70)
    logger.info("✅ LEANN index built successfully!")
    logger.info(f"💾 Storage saved: LEANN uses ~97% less storage than traditional vector DBs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest documents into LEANN vector index"
    )
    parser.add_argument(
        "kb_folder",
        type=str,
        help="Path to KB folder containing documents"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the index before ingestion"
    )
    parser.add_argument(
        "--no-markdown-only",
        action="store_true",
        help="Process all file types (default: markdown only)"
    )
    parser.add_argument(
        "--picc-only",
        action="store_true",
        help="Only ingest PICC-related documents"
    )
    parser.add_argument(
        "--whole-document",
        action="store_true",
        help="Embed whole documents without chunking"
    )
    parser.add_argument(
        "--backend",
        type=str,
        choices=["hnsw", "diskann"],
        default="hnsw",
        help="LEANN backend (default: hnsw)"
    )
    parser.add_argument(
        "--graph-degree",
        type=int,
        default=32,
        help="Graph degree for HNSW (default: 32)"
    )
    parser.add_argument(
        "--complexity",
        type=int,
        default=64,
        help="Build complexity (default: 64)"
    )
    parser.add_argument(
        "--no-compact",
        action="store_true",
        help="Disable compact storage"
    )
    parser.add_argument(
        "--no-recompute",
        action="store_true",
        help="Disable recomputation (requires no-compact)"
    )

    args = parser.parse_args()

    main(
        kb_folder=args.kb_folder,
        reset=args.reset,
        markdown_only=not args.no_markdown_only,
        picc_only=args.picc_only,
        whole_document=args.whole_document,
        backend=args.backend,
        graph_degree=args.graph_degree,
        complexity=args.complexity,
        compact=not args.no_compact,
        recompute=not args.no_recompute
    )



