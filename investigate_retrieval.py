import sys
import os
from loguru import logger

sys.path.append(os.getcwd())

from src.vector_store import VectorStore
from src.embeddings import get_embedding_model

def investigate():
    logger.info("Initializing embedding model...")
    embedding_model = get_embedding_model()

    logger.info("Initializing vector store...")
    vector_store = VectorStore(embedding_model)

    query = "what is picc"
    logger.info(f"Query: {query}")

    # 1. Check collection stats
    stats = vector_store.get_stats()
    logger.info(f"Vector Store Stats: {stats}")

    # 2. Perform direct search
    logger.info("Performing similarity search...")
    results = vector_store.similarity_search(query, k=5)

    if not results:
        logger.warning("No results found!")
    else:
        logger.info(f"Found {len(results)} results:")
        for i, result in enumerate(results):
            # VectorStore.similarity_search returns dicts with keys: content, metadata, score, id
            if isinstance(result, dict):
                score = result.get('score', 'N/A')
                content = result.get('content', '')
                metadata = result.get('metadata', {})
                filename = metadata.get('filename', 'unknown')
            else:
                # Fallback for unexpected types
                logger.warning(f"Unexpected result type: {type(result)}")
                score = 'N/A'
                content = str(result)
                metadata = {}
                filename = 'unknown'

            content_preview = content[:100].replace('\n', ' ')
            logger.info(f"  {i+1}. [Score: {score}] {filename}: {content_preview}...")
            logger.info(f"     Metadata: {metadata}")

    # 3. Check for specific PICC content in embedding model (optional, just printing stats for now)

if __name__ == "__main__":
    investigate()
