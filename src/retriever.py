"""Hybrid retrieval combining semantic and keyword search."""
from typing import List, Dict, Any, Optional
import numpy as np
from rank_bm25 import BM25Okapi
from loguru import logger

from src.vector_store import VectorStore
from config import settings


class HybridRetriever:
    """Hybrid retriever combining semantic (vector) and keyword (BM25) search."""

    def __init__(self, vector_store: VectorStore, alpha: float = None):
        """
        Initialize hybrid retriever.

        Args:
            vector_store: VectorStore instance for semantic search
            alpha: Weight for semantic search (1-alpha for BM25). Default from settings.
        """
        self.vector_store = vector_store
        self.alpha = alpha if alpha is not None else settings.hybrid_alpha

        # Initialize BM25 index
        self.bm25_index = None
        self.bm25_documents = []
        self.bm25_metadata = []
        self.bm25_ids = []

        self._build_bm25_index()

        logger.info(f"Initialized hybrid retriever with alpha={self.alpha}")

    def _build_bm25_index(self):
        """Build BM25 index from vector store contents."""
        logger.info("Building BM25 index...")

        # Get all documents from vector store
        # Note: ChromaDB doesn't have a direct "get all" method, so we use peek
        all_data = self.vector_store.collection.get(
            include=["documents", "metadatas"]
        )

        if not all_data['documents']:
            logger.warning(
                "No documents found in vector store. BM25 index is empty.")
            return

        self.bm25_documents = all_data['documents']
        self.bm25_metadata = all_data['metadatas']
        self.bm25_ids = all_data['ids']

        # Tokenize documents for BM25
        tokenized_docs = [doc.lower().split() for doc in self.bm25_documents]
        self.bm25_index = BM25Okapi(tokenized_docs)

        logger.info(
            f"BM25 index built with {len(self.bm25_documents)} documents")

    def rebuild_bm25_index(self):
        """Rebuild the BM25 index (call after adding new documents)."""
        self._build_bm25_index()

    def _bm25_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """
        Perform BM25 keyword search.

        Args:
            query: Query text
            k: Number of results to return

        Returns:
            List of results with content, metadata, and scores
        """
        if self.bm25_index is None:
            logger.warning("BM25 index not initialized")
            return []

        # Tokenize query
        tokenized_query = query.lower().split()

        # Get BM25 scores
        scores = self.bm25_index.get_scores(tokenized_query)

        # Get top-k indices
        top_k_indices = np.argsort(scores)[::-1][:k]

        # Format results
        results = []
        for idx in top_k_indices:
            if scores[idx] > 0:  # Only include non-zero scores
                results.append({
                    'content': self.bm25_documents[idx],
                    'metadata': self.bm25_metadata[idx],
                    'score': float(scores[idx]),
                    'id': self.bm25_ids[idx]
                })

        return results

    def _merge_results(self,
                       semantic_results: List[Dict[str, Any]],
                       bm25_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge and rerank results from semantic and BM25 search.

        Args:
            semantic_results: Results from semantic search
            bm25_results: Results from BM25 search

        Returns:
            Merged and reranked results
        """
        # Normalize scores for each method
        def normalize_scores(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            if not results:
                return []

            scores = [r['score'] for r in results]
            min_score = min(scores)
            max_score = max(scores)

            if max_score == min_score:
                return results

            for r in results:
                r['normalized_score'] = (
                    r['score'] - min_score) / (max_score - min_score)

            return results

        semantic_results = normalize_scores(semantic_results)
        bm25_results = normalize_scores(bm25_results)

        # Combine scores
        combined_scores = {}

        # Add semantic scores
        for result in semantic_results:
            doc_id = result['id']
            combined_scores[doc_id] = {
                'content': result['content'],
                'metadata': result['metadata'],
                'score': self.alpha * result.get('normalized_score', 0),
                'semantic_score': result['score'],
                'bm25_score': 0
            }

        # Add BM25 scores
        for result in bm25_results:
            doc_id = result['id']
            if doc_id in combined_scores:
                combined_scores[doc_id]['score'] += (
                    1 - self.alpha) * result.get('normalized_score', 0)
                combined_scores[doc_id]['bm25_score'] = result['score']
            else:
                combined_scores[doc_id] = {
                    'content': result['content'],
                    'metadata': result['metadata'],
                    'score': (1 - self.alpha) * result.get('normalized_score', 0),
                    'semantic_score': 0,
                    'bm25_score': result['score']
                }

        # Sort by combined score
        merged_results = sorted(
            combined_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )

        return merged_results

    def retrieve(self,
                 query: str,
                 k: int = None,
                 filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Perform hybrid retrieval.

        Args:
            query: Query text
            k: Number of results to return (default from settings)
            filter_dict: Optional metadata filter for semantic search

        Returns:
            List of top-k results with content, metadata, and combined scores
        """
        k = k or settings.top_k_retrieval

        # Perform semantic search
        logger.debug(f"Performing semantic search for: {query[:50]}...")
        semantic_results = self.vector_store.similarity_search(
            query, k=k*2, filter_dict=filter_dict)

        # Perform BM25 search (if index is available)
        bm25_results = []
        if self.bm25_index is not None:
            logger.debug("Performing BM25 search...")
            bm25_results = self._bm25_search(query, k=k*2)

        # Merge results
        merged_results = self._merge_results(semantic_results, bm25_results)

        # Return top-k
        final_results = merged_results[:k]

        logger.info(f"Retrieved {len(final_results)} results for query")
        return final_results
