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
from src.vector_store import VectorStore
from src.embeddings import get_embedding_model
from src.document_processor import DocumentProcessor
from config import settings
from loguru import logger


# isort: off  - Don't reorder imports below this line
# isort: on


def main(kb_folder: str, reset: bool = False):
    """
    Ingest documents from KB folder into vector database.

    Args:
        kb_folder: Path to KB folder containing documents
        reset: Whether to reset the collection before ingestion
    """
    logger.info(f"Starting document ingestion from: {kb_folder}")
    logger.info(f"Embedding provider: {settings.embedding_provider}")

    # Initialize components
    logger.info("Initializing embedding model...")
    embedding_model = get_embedding_model()

    logger.info("Initializing vector store...")
    vector_store = VectorStore(embedding_model)

    if reset:
        logger.warning("Resetting collection...")
        vector_store.reset_collection()

    # Process documents
    logger.info("Processing documents...")
    processor = DocumentProcessor(
        chunk_size=settings.max_chunk_size,
        chunk_overlap=settings.chunk_overlap
    )

    chunks = processor.process_directory(kb_folder)

    if not chunks:
        logger.error("No documents processed. Exiting.")
        return

    # Add to vector store
    logger.info(f"Adding {len(chunks)} chunks to vector store...")
    vector_store.add_documents(chunks)

    # Print statistics
    stats = vector_store.get_stats()
    logger.info("=" * 50)
    logger.info("INGESTION COMPLETE")
    logger.info("=" * 50)
    logger.info(f"Collection: {stats['collection_name']}")
    logger.info(f"Total documents: {stats['total_documents']}")
    logger.info(f"Persist directory: {stats['persist_directory']}")
    logger.info("=" * 50)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest documents into vector database")
    parser.add_argument("kb_folder", type=str, help="Path to KB folder")
    parser.add_argument("--reset", action="store_true",
                        help="Reset collection before ingestion")

    args = parser.parse_args()

    main(args.kb_folder, args.reset)
