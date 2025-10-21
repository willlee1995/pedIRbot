"""Analyze retrieval quality for specific queries."""
import sys
import os
from pathlib import Path
from typing import List

# Add parent directory to path FIRST
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from loguru import logger
from config import settings
from src.embeddings import get_embedding_model
from src.vector_store import VectorStore
from src.retriever import HybridRetriever


def analyze_query(query: str, k: int = 10, show_full_content: bool = False, export_file: str = None):
    """
    Analyze retrieval results for a query.

    Args:
        query: Query to test
        k: Number of results to retrieve
        show_full_content: Show full chunk content instead of preview
        export_file: Optional file to export detailed results
    """
    logger.info("=" * 70)
    logger.info(f"RETRIEVAL ANALYSIS")
    logger.info("=" * 70)
    logger.info(f"Query: '{query}'")
    logger.info(f"Retrieving top {k} results")
    logger.info(f"Embedding provider: {settings.embedding_provider}")
    logger.info(f"Hybrid alpha: {settings.hybrid_alpha}")
    logger.info("=" * 70)

    # Initialize components
    embedding_model = get_embedding_model()
    vector_store = VectorStore(embedding_model)
    retriever = HybridRetriever(vector_store)

    # Check database size
    stats = vector_store.get_stats()
    logger.info(f"\n📊 Vector Store Stats:")
    logger.info(f"   Total documents: {stats['total_documents']}")

    if stats['total_documents'] == 0:
        logger.error("❌ Vector store is EMPTY!")
        logger.error("   Run: python scripts/ingest_documents.py KB/ --reset")
        return

    # Retrieve documents
    logger.info(f"\n🔍 Retrieving documents for query: '{query}'")
    results = retriever.retrieve(query, k=k)

    if not results:
        logger.warning("❌ NO DOCUMENTS RETRIEVED!")
        logger.warning("   This could mean:")
        logger.warning("   1. No relevant content in knowledge base")
        logger.warning("   2. Embedding model not matching well")
        logger.warning("   3. Query needs rephrasing")
        return

    # Display results
    logger.info(f"\n✅ Retrieved {len(results)} documents:")
    logger.info("=" * 70)

    export_data = []

    for i, doc in enumerate(results, 1):
        source_org = doc['metadata'].get('source_org', 'Unknown')
        filename = doc['metadata'].get('filename', 'Unknown')
        score = doc.get('score', 0)
        content = doc['content']
        chunk_id = doc['metadata'].get('chunk_id', 'N/A')

        # Color coding based on score
        if score >= 0.7:
            score_indicator = "✅"
        elif score >= 0.5:
            score_indicator = "⚠️"
        else:
            score_indicator = "❌"

        print(f"\n{'='*70}")
        print(f"📄 Document {i} of {len(results)} {score_indicator}")
        print(f"{'='*70}")
        print(f"Filename:      {filename}")
        print(f"Source:        {source_org}")
        print(f"Chunk ID:      {chunk_id}")
        print(f"Combined Score: {score:.4f} {score_indicator}")
        print(f"  ├─ Semantic:  {doc.get('semantic_score', 'N/A')}")
        print(f"  └─ BM25:      {doc.get('bm25_score', 'N/A')}")
        print(f"Chunk Length:  {len(content)} characters")

        # Show metadata if available
        metadata = doc['metadata']
        if 'page' in metadata:
            print(f"Page:          {metadata['page']}")
        if 'section' in metadata:
            print(f"Section:       {metadata['section']}")

        print(f"\n{'─'*70}")
        print("CONTENT:")
        print(f"{'─'*70}")

        if show_full_content:
            # Show full content
            print(content)
        else:
            # Show preview
            preview_length = 300
            if len(content) > preview_length:
                print(f"{content[:preview_length]}...")
                print(f"\n[Showing {preview_length} of {len(content)} characters. Use --full to see complete content]")
            else:
                print(content)

        # Store for export
        export_data.append({
            'rank': i,
            'filename': filename,
            'source': source_org,
            'score': score,
            'semantic_score': doc.get('semantic_score', 'N/A'),
            'bm25_score': doc.get('bm25_score', 'N/A'),
            'chunk_id': chunk_id,
            'length': len(content),
            'content': content,
            'metadata': metadata
        })

    # Export to file if requested
    if export_file:
        import json
        try:
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'query': query,
                    'timestamp': str(Path(__file__).stat().st_mtime),
                    'settings': {
                        'embedding_provider': settings.embedding_provider,
                        'hybrid_alpha': settings.hybrid_alpha,
                        'k': k
                    },
                    'results': export_data
                }, f, indent=2, ensure_ascii=False)
            logger.info(f"\n💾 Detailed results exported to: {export_file}")
        except Exception as e:
            logger.error(f"Failed to export results: {e}")

    # Analysis
    logger.info("\n" + "=" * 70)
    logger.info("ANALYSIS")
    logger.info("=" * 70)

    # Check score distribution
    scores = [doc['score'] for doc in results]
    avg_score = sum(scores) / len(scores)
    max_score = max(scores)
    min_score = min(scores)

    logger.info(f"Score range: {min_score:.3f} - {max_score:.3f}")
    logger.info(f"Average score: {avg_score:.3f}")

    if max_score < 0.6:
        logger.warning("⚠️  LOW SCORES: Top result < 0.6")
        logger.warning("   Consider:")
        logger.warning("   1. Adding more relevant content to KB")
        logger.warning("   2. Using different embedding model")
        logger.warning("   3. Rephrasing the query")

    # Check source diversity
    sources = [doc['metadata'].get('source_org', 'Unknown') for doc in results]
    source_counts = {}
    for source in sources:
        source_counts[source] = source_counts.get(source, 0) + 1

    logger.info(f"\nSource distribution:")
    for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        logger.info(f"   {source}: {count} documents")

    # Recommendations
    logger.info("\n📋 RECOMMENDATIONS:")

    if 'SickKids' in source_counts and source_counts['SickKids'] > 3:
        logger.info("   Consider filtering SickKids content:")
        logger.info("   python scripts/filter_sickkids_content.py --execute")

    if avg_score < 0.5:
        logger.info("   Low relevance scores detected:")
        logger.info("   - Check if KB contains relevant content for this query")
        logger.info("   - Try different query phrasing")


def batch_analyze(queries, k: int = 5, show_full_content: bool = False, export_file: str = None):
    """Analyze multiple queries."""
    logger.info(f"\n🔬 BATCH ANALYSIS: {len(queries)} queries\n")

    for i, query in enumerate(queries, 1):
        logger.info(f"\n{'#'*70}")
        logger.info(f"Query {i}/{len(queries)}")
        logger.info(f"{'#'*70}")

        # Create separate export file for each query in batch
        query_export = None
        if export_file:
            base_name = Path(export_file).stem
            ext = Path(export_file).suffix
            query_export = f"{base_name}_query{i}{ext}"

        analyze_query(query, k=k, show_full_content=show_full_content, export_file=query_export)

        if i < len(queries):
            input("\nPress Enter to continue to next query...")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze retrieval quality")
    parser.add_argument(
        "query",
        type=str,
        nargs='?',
        help="Query to analyze (optional)"
    )
    parser.add_argument(
        "--queries",
        type=str,
        nargs='+',
        help="Multiple queries to analyze"
    )
    parser.add_argument(
        "-k",
        type=int,
        default=10,
        help="Number of results to retrieve (default: 10)"
    )
    parser.add_argument(
        "--test-picc",
        action="store_true",
        help="Run pre-defined PICC-related queries"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Show full chunk content instead of preview"
    )
    parser.add_argument(
        "--export",
        type=str,
        help="Export detailed results to JSON file"
    )

    args = parser.parse_args()

    if args.test_picc:
        # Pre-defined PICC queries
        queries = [
            "What is a PICC line?",
            "How is a PICC inserted?",
            "PICC line insertion procedure",
            "Peripherally inserted central catheter",
            "Caring for PICC line at home"
        ]
        batch_analyze(queries, k=args.k, show_full_content=args.full, export_file=args.export)

    elif args.queries:
        batch_analyze(args.queries, k=args.k, show_full_content=args.full, export_file=args.export)

    elif args.query:
        analyze_query(args.query, k=args.k, show_full_content=args.full, export_file=args.export)

    else:
        # Interactive mode
        print("=" * 70)
        print("Retrieval Analysis Tool")
        print("=" * 70)
        print("Enter queries to analyze retrieval quality")
        print("Commands:")
        print("  'full' - Toggle full content display")
        print("  'quit' - Exit")
        print("=" * 70)

        show_full = args.full

        while True:
            query = input("\nQuery to analyze: ").strip()

            if query.lower() in ['quit', 'exit', 'q']:
                break

            if query.lower() == 'full':
                show_full = not show_full
                print(f"Full content display: {'ON' if show_full else 'OFF'}")
                continue

            if query:
                analyze_query(query, k=args.k, show_full_content=show_full)

