"""Script to verify chunk sizes are within limits."""
import sys
from pathlib import Path

# Add parent directory to path FIRST
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from config import settings
from src.document_processor import DocumentProcessor


def main(kb_folder: str, sample_files: int = 5):
    """
    Verify document chunking without actually ingesting.

    Args:
        kb_folder: Path to KB folder
        sample_files: Number of sample files to test
    """
    logger.info("=" * 60)
    logger.info("CHUNK SIZE VERIFICATION")
    logger.info("=" * 60)
    logger.info(f"Configuration:")
    logger.info(f"  MAX_CHUNK_SIZE: {settings.max_chunk_size}")
    logger.info(f"  CHUNK_OVERLAP: {settings.chunk_overlap}")
    logger.info("=" * 60)

    # Initialize processor
    processor = DocumentProcessor(
        chunk_size=settings.max_chunk_size,
        chunk_overlap=settings.chunk_overlap
    )

    # Process a sample
    logger.info(f"\nProcessing sample from: {kb_folder}")
    chunks = processor.process_directory(kb_folder)

    if not chunks:
        logger.error("No chunks created!")
        return

    # Analyze chunk sizes
    chunk_sizes = [len(c.content) for c in chunks]

    print("\n" + "=" * 60)
    print("CHUNK SIZE ANALYSIS")
    print("=" * 60)
    print(f"Total chunks: {len(chunks)}")
    print(f"Average size: {sum(chunk_sizes) / len(chunk_sizes):.1f} chars")
    print(f"Minimum size: {min(chunk_sizes)} chars")
    print(f"Maximum size: {max(chunk_sizes)} chars")
    print(f"Target max: {settings.max_chunk_size} chars")
    print("=" * 60)

    # Check for oversized chunks
    oversized = [c for c in chunks if len(c.content) > settings.max_chunk_size]

    if oversized:
        print(f"\n⚠️  WARNING: {len(oversized)} chunks exceed MAX_CHUNK_SIZE!")
        print("\nOversized chunks:")
        for chunk in oversized[:10]:  # Show first 10
            print(f"  - {chunk.chunk_id}: {len(chunk.content)} chars "
                  f"(exceeds by {len(chunk.content) - settings.max_chunk_size})")

        if len(oversized) > 10:
            print(f"  ... and {len(oversized) - 10} more")

        print(f"\n💡 Recommendation: These will be truncated during embedding!")
        print(f"   Consider reducing MAX_CHUNK_SIZE to avoid data loss.")
    else:
        print(f"\n✅ SUCCESS: All chunks are within the size limit!")
        print(f"   Safe to proceed with embedding.")

    # Show distribution
    print("\n" + "=" * 60)
    print("SIZE DISTRIBUTION")
    print("=" * 60)
    ranges = [
        (0, 100, "0-100"),
        (100, 200, "100-200"),
        (200, 300, "200-300"),
        (300, 400, "300-400"),
        (400, 500, "400-500"),
        (500, float('inf'), "500+")
    ]

    for min_size, max_size, label in ranges:
        count = sum(1 for s in chunk_sizes if min_size <= s < max_size)
        if count > 0:
            percentage = count / len(chunk_sizes) * 100
            bar = "█" * int(percentage / 2)
            print(f"{label:>10} chars: {count:>4} ({percentage:>5.1f}%) {bar}")

    print("=" * 60)

    # Sample some chunks
    print("\nSample chunks:")
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"\n--- Chunk {i} ({len(chunk.content)} chars) ---")
        print(f"Source: {chunk.metadata.get('source_org', 'Unknown')}")
        print(f"File: {chunk.metadata.get('filename', 'Unknown')}")
        print(f"Content preview: {chunk.content[:200]}...")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Verify chunk sizes")
    parser.add_argument("kb_folder", type=str, help="Path to KB folder")
    parser.add_argument("--sample", type=int, default=5,
                       help="Number of sample files to process")

    args = parser.parse_args()

    main(args.kb_folder, args.sample)

