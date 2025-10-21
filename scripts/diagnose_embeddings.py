"""Diagnose embedding model performance and quality."""
import sys
import os
from pathlib import Path

# Add parent directory to path FIRST
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import numpy as np
from loguru import logger
from config import settings
from src.embeddings import get_embedding_model
from src.vector_store import VectorStore


def calculate_similarity(emb1, emb2):
    """Calculate cosine similarity between two embeddings."""
    return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))


def diagnose_embedding_quality():
    """Diagnose embedding model quality for medical queries."""

    logger.info("=" * 70)
    logger.info("EMBEDDING MODEL DIAGNOSIS")
    logger.info("=" * 70)
    logger.info(f"Provider: {settings.embedding_provider}")

    if settings.embedding_provider == "ollama":
        logger.info(f"Model: {settings.ollama_embedding_model}")
    elif settings.embedding_provider == "openai":
        logger.info(f"Model: {settings.openai_embedding_model}")
    else:
        logger.info(f"Model: {settings.sentence_transformer_model}")

    logger.info("=" * 70)

    # Initialize embedding model
    logger.info("\nInitializing embedding model...")
    embedding_model = get_embedding_model()
    logger.info(f"Embedding dimension: {embedding_model.dimension}")

    # Test queries and expected documents
    test_pairs = [
        {
            "query": "What is a PICC line?",
            "relevant_doc": "A PICC (Peripherally Inserted Central Catheter) is a long, soft, thin, flexible tube that is inserted into a vein in your child's arm. The PICC line allows healthcare providers to give medications, fluids, nutrition, or draw blood samples without repeated needle sticks.",
            "irrelevant_doc": "Bulimia nervosa is an eating disorder characterized by episodes of binge eating followed by compensatory behaviors such as vomiting, fasting, or excessive exercise."
        },
        {
            "query": "How is a liver biopsy done?",
            "relevant_doc": "During a liver biopsy, the doctor uses image guidance (usually ultrasound or CT scan) to guide a thin needle into the liver. A small piece of liver tissue is removed and sent to the laboratory for examination. The procedure usually takes 30-45 minutes.",
            "irrelevant_doc": "Guided meditation is a relaxation technique where you imagine yourself in a peaceful place while listening to calming instructions."
        },
        {
            "query": "PICC insertion procedure",
            "relevant_doc": "PICC insertion using image guidance. The procedure is performed in the interventional radiology suite. Using ultrasound guidance, the interventional radiologist locates a suitable vein and inserts the catheter.",
            "irrelevant_doc": "Body image refers to how you perceive your physical appearance and how you think others perceive you."
        },
        {
            "query": "介入放射學是什麼？",  # Chinese: What is interventional radiology?
            "relevant_doc": "Interventional radiology (IR) is a medical specialty that uses image guidance (such as X-rays, ultrasound, CT, or MRI) to perform minimally invasive procedures.",
            "irrelevant_doc": "Mental health refers to emotional, psychological, and social well-being."
        }
    ]

    logger.info("\n" + "=" * 70)
    logger.info("SEMANTIC SIMILARITY TESTS")
    logger.info("=" * 70)

    all_relevant_scores = []
    all_irrelevant_scores = []

    for i, test in enumerate(test_pairs, 1):
        logger.info(f"\n📝 Test {i}/{len(test_pairs)}")
        logger.info(f"Query: '{test['query']}'")

        # Generate embeddings
        query_emb = embedding_model.embed_query(test['query'])
        relevant_emb = embedding_model.embed_query(test['relevant_doc'])
        irrelevant_emb = embedding_model.embed_query(test['irrelevant_doc'])

        # Calculate similarities
        relevant_sim = calculate_similarity(query_emb, relevant_emb)
        irrelevant_sim = calculate_similarity(query_emb, irrelevant_emb)

        all_relevant_scores.append(relevant_sim)
        all_irrelevant_scores.append(irrelevant_sim)

        logger.info(f"  Relevant doc similarity:   {relevant_sim:.3f} {'✅' if relevant_sim > 0.6 else '⚠️' if relevant_sim > 0.4 else '❌'}")
        logger.info(f"  Irrelevant doc similarity: {irrelevant_sim:.3f} {'❌' if irrelevant_sim < 0.4 else '⚠️'}")
        logger.info(f"  Separation:                {relevant_sim - irrelevant_sim:.3f} {'✅' if relevant_sim - irrelevant_sim > 0.2 else '❌'}")

    # Overall statistics
    avg_relevant = np.mean(all_relevant_scores)
    avg_irrelevant = np.mean(all_irrelevant_scores)
    avg_separation = avg_relevant - avg_irrelevant

    logger.info("\n" + "=" * 70)
    logger.info("OVERALL PERFORMANCE")
    logger.info("=" * 70)
    logger.info(f"Average relevant similarity:   {avg_relevant:.3f}")
    logger.info(f"Average irrelevant similarity: {avg_irrelevant:.3f}")
    logger.info(f"Average separation:            {avg_separation:.3f}")
    logger.info("=" * 70)

    # Diagnosis
    logger.info("\n📊 DIAGNOSIS:")

    if avg_relevant < 0.5:
        logger.error("❌ POOR: Relevant documents have low similarity (<0.5)")
        logger.error("   Problem: Model struggles to match queries with relevant content")
        logger.error("   Solution: Consider switching embedding model")
    elif avg_relevant < 0.7:
        logger.warning("⚠️  FAIR: Relevant documents have moderate similarity (0.5-0.7)")
        logger.warning("   Problem: Model provides acceptable but not great matching")
        logger.warning("   Solution: Consider better embedding model or add more context")
    else:
        logger.info("✅ GOOD: Relevant documents have high similarity (>0.7)")

    if avg_separation < 0.15:
        logger.error("❌ POOR DISCRIMINATION: Cannot separate relevant from irrelevant")
        logger.error("   Problem: Model returns similar scores for both types")
        logger.error("   Solution: MUST switch to better embedding model")
    elif avg_separation < 0.3:
        logger.warning("⚠️  WEAK DISCRIMINATION: Marginal separation (0.15-0.3)")
        logger.warning("   Problem: Some irrelevant docs may rank highly")
        logger.warning("   Solution: Consider better model or add score threshold")
    else:
        logger.info("✅ GOOD DISCRIMINATION: Can separate relevant from irrelevant")

    # Recommendations
    logger.info("\n💡 RECOMMENDATIONS:")

    if avg_relevant < 0.6 or avg_separation < 0.2:
        logger.info("\n🔄 Switch to better embedding model:")
        logger.info("   Option 1 (Best quality):")
        logger.info("     EMBEDDING_PROVIDER=openai")
        logger.info("     OPENAI_EMBEDDING_MODEL=text-embedding-3-large")
        logger.info("     MAX_CHUNK_SIZE=512")
        logger.info("")
        logger.info("   Option 2 (Good quality, local):")
        logger.info("     EMBEDDING_PROVIDER=ollama")
        logger.info("     OLLAMA_EMBEDDING_MODEL=mxbai-embed-large")
        logger.info("     MAX_CHUNK_SIZE=512")
        logger.info("")
        logger.info("   Option 3 (Multilingual focus):")
        logger.info("     EMBEDDING_PROVIDER=sentence-transformer")
        logger.info("     SENTENCE_TRANSFORMER_MODEL=BAAI/bge-m3")
        logger.info("     MAX_CHUNK_SIZE=512")
        logger.info("")
        logger.info("   Then: python scripts/ingest_documents.py KB/ --reset")

    if avg_relevant >= 0.6:
        logger.info("\n✅ Current model is acceptable")
        logger.info("   Consider:")
        logger.info("   1. Adding minimum score threshold (MIN_RELEVANCE_SCORE=0.5)")
        logger.info("   2. Increasing chunk size for more context")
        logger.info("   3. Filtering out non-procedure content")


def test_actual_retrieval():
    """Test retrieval with actual vector store."""
    logger.info("\n" + "=" * 70)
    logger.info("ACTUAL RETRIEVAL TEST")
    logger.info("=" * 70)

    embedding_model = get_embedding_model()
    vector_store = VectorStore(embedding_model)

    stats = vector_store.get_stats()
    logger.info(f"Vector store size: {stats['total_documents']} documents")

    if stats['total_documents'] == 0:
        logger.error("❌ Vector store is EMPTY!")
        logger.error("   Run: python scripts/ingest_documents.py KB/ --reset")
        return

    # Test queries
    test_queries = [
        "What is a PICC line?",
        "How is a liver biopsy performed?",
        "Image-guided drainage procedure",
        "Central venous catheter insertion",
        "介入放射學程序"  # Chinese: Interventional radiology procedure
    ]

    for query in test_queries:
        logger.info(f"\n🔍 Query: '{query}'")
        results = vector_store.similarity_search(query, k=5)

        if results:
            top_score = results[0]['score']
            logger.info(f"   Top score: {top_score:.3f} {'✅' if top_score > 0.6 else '⚠️' if top_score > 0.4 else '❌'}")
            logger.info(f"   Top result: {results[0]['metadata']['filename']}")

            # Show score distribution
            scores = [r['score'] for r in results]
            logger.info(f"   Scores: {[f'{s:.3f}' for s in scores]}")
        else:
            logger.warning("   No results found!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Diagnose embedding quality")
    parser.add_argument(
        "--test-retrieval",
        action="store_true",
        help="Test actual retrieval from vector store"
    )

    args = parser.parse_args()

    # Run semantic similarity tests
    diagnose_embedding_quality()

    # Optionally test actual retrieval
    if args.test_retrieval:
        test_actual_retrieval()

