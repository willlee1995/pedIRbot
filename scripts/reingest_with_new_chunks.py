#!/usr/bin/env python
"""
Re-ingest knowledge base with new chunking configuration.

This script re-processes the knowledge base with:
- Larger chunk size (1500 chars) for better context preservation
- More overlap (200 chars) to prevent context fragmentation
- Jina embedding model for improved long-text embeddings

IMPORTANT: This will reset the existing vector database!
"""
import sys
import os

# Get the absolute path of the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# Add the project root to the Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from pathlib import Path
from src.vector_store import VectorStore
from src.embeddings import get_embedding_model
from src.document_processor import DocumentProcessor
from config import settings
from loguru import logger


def main():
    """Re-ingest documents with new chunking configuration."""
    logger.info("=" * 70)
    logger.info("RE-INGESTION WITH NEW CHUNKING PARAMETERS")
    logger.info("=" * 70)
    
    # Show configuration
    logger.info("\n📋 New Configuration:")
    logger.info(f"   Chunk Size:    {settings.max_chunk_size} chars (previously 800)")
    logger.info(f"   Chunk Overlap: {settings.chunk_overlap} chars (previously 50)")
    logger.info(f"   Embedding:     {settings.embedding_provider}")
    if settings.embedding_provider == "sentence-transformer":
        logger.info(f"   Model:         {settings.sentence_transformer_model}")
    logger.info("")
    
    # Default to KB/md folder
    kb_folder = Path(project_root) / "KB" / "md"
    if not kb_folder.exists():
        kb_folder = Path(project_root) / "KB"
    
    logger.info(f"📁 Source: {kb_folder}")
    logger.info("")
    
    # Confirmation
    response = input("⚠️  This will RESET the vector database. Continue? (yes/no): ")
    if response.lower() != 'yes':
        logger.info("Cancelled.")
        return
    
    # Initialize components
    logger.info("\n🔧 Initializing embedding model...")
    try:
        embedding_model = get_embedding_model()
        logger.info(f"   ✅ Loaded {settings.embedding_provider}")
    except Exception as e:
        logger.error(f"   ❌ Failed to load embedding model: {e}")
        if settings.embedding_provider == "sentence-transformer":
            logger.info("   💡 Installing Jina model... (this may take a while)")
            logger.info(f"      pip install sentence-transformers")
            logger.info(f"      Model will auto-download on first use")
        return
    
    vector_store = VectorStore(embedding_model)
    
    # Reset collection
    logger.warning("\n🗑️  Resetting collection...")
    vector_store.reset_collection()
    
    # Process documents with new chunking
    logger.info("\n📄 Processing documents with new chunking...")
    processor = DocumentProcessor(
        chunk_size=settings.max_chunk_size,
        chunk_overlap=settings.chunk_overlap,
        markdown_only=True
    )
    
    chunks = processor.process_directory(str(kb_folder))
    
    if not chunks:
        logger.error("\n❌ No documents processed!")
        return
    
    # Show chunk statistics
    chunk_sizes = [len(c.content) for c in chunks]
    avg_size = sum(chunk_sizes) / len(chunk_sizes)
    max_size = max(chunk_sizes)
    min_size = min(chunk_sizes)
    
    logger.info(f"\n📊 Chunk Statistics:")
    logger.info(f"   Total chunks: {len(chunks)}")
    logger.info(f"   Avg size:     {avg_size:.0f} chars")
    logger.info(f"   Min size:     {min_size} chars")
    logger.info(f"   Max size:     {max_size} chars")
    
    # Add to vector store
    logger.info(f"\n🔄 Generating embeddings and storing...")
    vector_store.add_documents(chunks)
    
    # Final statistics
    stats = vector_store.get_stats()
    logger.info("\n" + "=" * 70)
    logger.info("✅ RE-INGESTION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Collection: {stats['collection_name']}")
    logger.info(f"Total documents: {stats['total_documents']}")
    logger.info("=" * 70)
    logger.info("\n💡 Next steps:")
    logger.info("   1. Test chat: python test_chat.py")
    logger.info("   2. Compare retrieval quality with previous setup")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
