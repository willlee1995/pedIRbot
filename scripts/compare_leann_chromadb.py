"""Comparison script showing LEANN vs ChromaDB performance and storage."""
import sys
import os
import time
from pathlib import Path

# Get the absolute path of the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# Add the project root to the Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.vector_store import VectorStore
from src.vector_store_leann import LEANNVectorStore
from src.embeddings import get_embedding_model
from src.document_processor import DocumentProcessor
from config import settings
from loguru import logger


def get_directory_size(path: str) -> int:
    """Get total size of directory in bytes."""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_directory_size(entry.path)
    except Exception:
        pass
    return total


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def compare_storage():
    """Compare storage usage between ChromaDB and LEANN."""
    logger.info("=" * 70)
    logger.info("STORAGE COMPARISON: ChromaDB vs LEANN")
    logger.info("=" * 70)

    # Check ChromaDB size
    chroma_path = Path(settings.chroma_persist_directory)
    chroma_size = 0
    if chroma_path.exists():
        chroma_size = get_directory_size(str(chroma_path))
        logger.info(f"ChromaDB Storage: {format_size(chroma_size)}")
    else:
        logger.warning("ChromaDB directory not found")

    # Check LEANN size
    leann_path = Path(settings.leann_persist_directory)
    leann_size = 0
    if leann_path.exists():
        leann_size = get_directory_size(str(leann_path))
        logger.info(f"LEANN Storage: {format_size(leann_size)}")
    else:
        logger.warning("LEANN directory not found")

    if chroma_size > 0 and leann_size > 0:
        savings = ((chroma_size - leann_size) / chroma_size) * 100
        logger.info(f"\n💾 Storage Savings: {savings:.1f}%")
        logger.info(f"   ChromaDB: {format_size(chroma_size)}")
        logger.info(f"   LEANN: {format_size(leann_size)}")
        logger.info(f"   Saved: {format_size(chroma_size - leann_size)}")

    logger.info("=" * 70)


def compare_search_performance(test_queries: list[str] = None):
    """Compare search performance between ChromaDB and LEANN."""
    if test_queries is None:
        test_queries = [
            "What is a PICC line?",
            "How do I care for a central venous catheter?",
            "What are the complications of venous access procedures?",
            "How is an angiogram performed?",
            "What is embolization therapy?"
        ]

    logger.info("=" * 70)
    logger.info("SEARCH PERFORMANCE COMPARISON")
    logger.info("=" * 70)

    embedding_model = get_embedding_model()

    # Initialize ChromaDB
    chroma_store = None
    try:
        chroma_store = VectorStore(embedding_model)
        logger.info("✅ ChromaDB initialized")
    except Exception as e:
        logger.warning(f"⚠️  ChromaDB not available: {e}")

    # Initialize LEANN
    leann_store = None
    try:
        leann_store = LEANNVectorStore(embedding_model)
        logger.info("✅ LEANN initialized")
    except Exception as e:
        logger.warning(f"⚠️  LEANN not available: {e}")

    if not chroma_store and not leann_store:
        logger.error("Neither ChromaDB nor LEANN is available for comparison")
        return

    results = {
        "chromadb": {"times": [], "results": []},
        "leann": {"times": [], "results": []}
    }

    for query in test_queries:
        logger.info(f"\n🔍 Query: {query}")

        # Test ChromaDB
        if chroma_store:
            try:
                start = time.time()
                chroma_results = chroma_store.similarity_search(query, k=5)
                chroma_time = time.time() - start
                results["chromadb"]["times"].append(chroma_time)
                results["chromadb"]["results"].append(len(chroma_results))
                logger.info(f"   ChromaDB: {chroma_time*1000:.2f}ms, {len(chroma_results)} results")
            except Exception as e:
                logger.warning(f"   ChromaDB error: {e}")

        # Test LEANN
        if leann_store:
            try:
                start = time.time()
                leann_results = leann_store.similarity_search(query, k=5)
                leann_time = time.time() - start
                results["leann"]["times"].append(leann_time)
                results["leann"]["results"].append(len(leann_results))
                logger.info(f"   LEANN: {leann_time*1000:.2f}ms, {len(leann_results)} results")
            except Exception as e:
                logger.warning(f"   LEANN error: {e}")

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("PERFORMANCE SUMMARY")
    logger.info("=" * 70)

    if results["chromadb"]["times"]:
        avg_chroma = sum(results["chromadb"]["times"]) / len(results["chromadb"]["times"]) * 1000
        logger.info(f"ChromaDB Average: {avg_chroma:.2f}ms")

    if results["leann"]["times"]:
        avg_leann = sum(results["leann"]["times"]) / len(results["leann"]["times"]) * 1000
        logger.info(f"LEANN Average: {avg_leann:.2f}ms")

    if results["chromadb"]["times"] and results["leann"]["times"]:
        speedup = avg_chroma / avg_leann if avg_leann > 0 else 0
        if speedup > 1:
            logger.info(f"⚡ LEANN is {speedup:.2f}x faster")
        else:
            logger.info(f"⚡ ChromaDB is {1/speedup:.2f}x faster")

    logger.info("=" * 70)


def main():
    """Run comparison between ChromaDB and LEANN."""
    logger.info("🚀 Starting ChromaDB vs LEANN Comparison")
    logger.info("")

    # Compare storage
    compare_storage()
    logger.info("")

    # Compare search performance
    compare_search_performance()

    logger.info("\n✅ Comparison complete!")
    logger.info("")
    logger.info("💡 Key Benefits of LEANN:")
    logger.info("   • 97% storage savings")
    logger.info("   • Fast, accurate retrieval")
    logger.info("   • Graph-based selective recomputation")
    logger.info("   • Metadata filtering support")
    logger.info("   • HNSW and DiskANN backends")


if __name__ == "__main__":
    main()



