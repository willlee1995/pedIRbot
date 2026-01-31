"""Vector database management using LEANN (Low-Storage Vector Index)."""
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
from loguru import logger

try:
    from leann import LeannBuilder, LeannSearcher
    LEANN_AVAILABLE = True
except ImportError as e:
    LEANN_AVAILABLE = False
    import platform
    if platform.system() == "Windows":
        logger.warning(
            "LEANN not available on Windows. leann-backend-hnsw has no Windows wheels.\n"
            "Options: 1) Use WSL (Windows Subsystem for Linux), 2) Build from source, "
            "3) Use Docker/Linux container, or 4) Continue using ChromaDB."
        )
    else:
        logger.warning(f"LEANN not installed. Install with: pip install leann\nError: {e}")

from src.document_processor import DocumentChunk
from src.embeddings import EmbeddingModel
from config import settings


class LEANNVectorStore:
    """Manages vector storage and retrieval using LEANN (Low-Storage Vector Index)."""

    def __init__(self,
                 embedding_model: EmbeddingModel,
                 index_name: str = None,
                 persist_directory: str = None,
                 backend: str = "hnsw",
                 graph_degree: int = 32,
                 complexity: int = 64,
                 compact: bool = True,
                 recompute: bool = True):
        """
        Initialize the LEANN vector store.

        Args:
            embedding_model: Embedding model to use
            index_name: Name of the index (default from settings)
            persist_directory: Directory to persist the index (default: .leann/indexes/)
            backend: Backend to use ("hnsw" or "diskann")
            graph_degree: Graph degree for HNSW (default: 32)
            complexity: Build complexity (default: 64)
            compact: Use compact storage (default: True)
            recompute: Enable recomputation (default: True)
        """
        if not LEANN_AVAILABLE:
            raise ImportError(
                "LEANN is not installed. Install with: pip install leann")

        self.embedding_model = embedding_model
        self.index_name = index_name or settings.collection_name
        self.persist_directory = persist_directory or ".leann/indexes"
        self.backend = backend
        self.graph_degree = graph_degree
        self.complexity = complexity
        self.compact = compact
        self.recompute = recompute

        # Create persist directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)

        # Index path
        self.index_path = os.path.join(
            self.persist_directory, f"{self.index_name}.leann")

        # Initialize builder (for adding documents)
        self.builder = None

        # Initialize searcher if index exists
        self.searcher = None
        if os.path.exists(self.index_path):
            try:
                self.searcher = LeannSearcher(self.index_path)
                logger.info(
                    f"Loaded existing LEANN index: {self.index_path}")
            except Exception as e:
                logger.warning(
                    f"Failed to load existing index: {e}. Will create new index.")
                self.searcher = None

        logger.info(
            f"Initialized LEANN vector store with index: {self.index_name}")
        logger.info(f"Index path: {self.index_path}")
        logger.info(f"Backend: {self.backend}, Compact: {self.compact}, Recompute: {self.recompute}")

    def _get_builder(self) -> LeannBuilder:
        """Get or create a builder instance."""
        if self.builder is None:
            self.builder = LeannBuilder(backend_name=self.backend)
        return self.builder

    def add_documents(self, chunks: List[DocumentChunk], batch_size: int = 100):
        """
        Add document chunks to the LEANN index.

        Args:
            chunks: List of DocumentChunk objects
            batch_size: Number of documents to process at once (for logging)
        """
        logger.info(f"Adding {len(chunks)} documents to LEANN index...")

        builder = self._get_builder()

        # Add chunks to builder
        for i, chunk in enumerate(chunks):
            if (i + 1) % batch_size == 0:
                logger.info(
                    f"Processing chunk {i + 1}/{len(chunks)}...")

            # LEANN supports metadata filtering
            # Add text with metadata
            builder.add_text(
                chunk.content,
                metadata=chunk.metadata
            )

        logger.info(f"Added {len(chunks)} chunks to builder")

    def build_index(self, force: bool = False):
        """
        Build the LEANN index from added documents.

        Args:
            force: Force rebuild if index exists (default: False)
        """
        if self.builder is None:
            logger.warning("No documents added. Cannot build index.")
            return

        if os.path.exists(self.index_path) and not force:
            logger.warning(
                f"Index already exists at {self.index_path}. Use force=True to rebuild.")
            return

        logger.info(f"Building LEANN index at {self.index_path}...")
        logger.info(
            f"Backend: {self.backend}, Graph Degree: {self.graph_degree}, Complexity: {self.complexity}")

        try:
            # Build index with specified parameters
            self.builder.build_index(
                self.index_path,
                graph_degree=self.graph_degree,
                complexity=self.complexity,
                compact=self.compact,
                recompute=self.recompute
            )

            logger.info(f"Successfully built LEANN index: {self.index_path}")

            # Initialize searcher with new index
            self.searcher = LeannSearcher(self.index_path)
            logger.info("LEANN index ready for searching")

        except Exception as e:
            logger.error(f"Failed to build LEANN index: {e}")
            raise

    def similarity_search(self,
                          query: str,
                          k: int = None,
                          filter_dict: Optional[Dict[str, Any]] = None,
                          complexity: int = None,
                          recompute: bool = None) -> List[Dict[str, Any]]:
        """
        Perform similarity search on the LEANN index.

        Args:
            query: Query text
            k: Number of results to return (default from settings)
            filter_dict: Optional metadata filter
            complexity: Search complexity (default: same as build complexity)
            recompute: Enable recomputation during search (default: same as build)

        Returns:
            List of results with content, metadata, and scores
        """
        if self.searcher is None:
            raise ValueError(
                "Index not built or loaded. Call build_index() first or ensure index exists.")

        k = k or settings.top_k_retrieval
        complexity = complexity or self.complexity
        recompute = recompute if recompute is not None else self.recompute

        logger.debug(f"Searching LEANN index with query: {query[:50]}...")

        try:
            # Convert filter_dict to LEANN metadata filter format
            metadata_filters = None
            if filter_dict:
                # LEANN supports operators like ==, !=, <, <=, >, >=, in, not_in, etc.
                # Convert our simple filter_dict to LEANN format
                metadata_filters = {}
                for key, value in filter_dict.items():
                    # Use equality operator by default
                    metadata_filters[key] = {"==": value}

            # Perform search
            if metadata_filters:
                results = self.searcher.search(
                    query,
                    top_k=k,
                    complexity=complexity,
                    recompute=recompute,
                    metadata_filters=metadata_filters
                )
            else:
                results = self.searcher.search(
                    query,
                    top_k=k,
                    complexity=complexity,
                    recompute=recompute
                )

            # Format results to match expected format
            formatted_results = []
            for result in results:
                # LEANN returns results with text, metadata, and score
                # Adjust based on actual LEANN API response structure
                if isinstance(result, dict):
                    content = result.get('text', result.get('content', ''))
                    metadata = result.get('metadata', {})
                    score = result.get('score', result.get('distance', 0))
                else:
                    # If result is a tuple or object, extract accordingly
                    # This may need adjustment based on actual LEANN API
                    content = getattr(result, 'text', getattr(result, 'content', str(result)))
                    metadata = getattr(result, 'metadata', {})
                    score = getattr(result, 'score', getattr(result, 'distance', 0))

                # Convert distance to similarity if needed
                # LEANN may return distance, convert to similarity score
                if score > 1:
                    similarity_score = 1 / (1 + score)
                else:
                    similarity_score = 1 - score if score <= 1 else score

                formatted_results.append({
                    'content': content,
                    'metadata': metadata,
                    'score': similarity_score,
                    'id': metadata.get('chunk_id', metadata.get('id', ''))
                })

            logger.info(f"Found {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Error searching LEANN index: {e}")
            logger.exception(e)
            raise

    def as_retriever(self, **kwargs):
        """
        Get LangChain-compatible retriever from LEANN vector store.

        Note: This creates a simple wrapper retriever since LEANN doesn't
        have direct LangChain integration.
        """
        from langchain_core.retrievers import BaseRetriever
        from langchain_core.documents import Document
        from langchain_core.callbacks import CallbackManagerForRetrieverRun

        # Extract k from kwargs or use default
        k = kwargs.get('k', kwargs.get('search_kwargs', {}).get('k', settings.top_k_retrieval))

        class LEANNRetriever(BaseRetriever):
            """LangChain retriever wrapper for LEANN."""

            def __init__(self, leann_store: 'LEANNVectorStore', k: int = settings.top_k_retrieval):
                super().__init__()
                self.leann_store = leann_store
                self.k = k

            def _get_relevant_documents(
                self,
                query: str,
                *,
                run_manager: CallbackManagerForRetrieverRun,
            ) -> List[Document]:
                """Retrieve relevant documents."""
                results = self.leann_store.similarity_search(
                    query, k=self.k)

                docs = []
                for result in results:
                    doc = Document(
                        page_content=result['content'],
                        metadata=result['metadata']
                    )
                    docs.append(doc)

                return docs

        return LEANNRetriever(self, k=k)

    def delete_index(self):
        """Delete the current index."""
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
            logger.warning(f"Deleted LEANN index: {self.index_path}")
        else:
            logger.info(f"Index does not exist: {self.index_path}")

        # Also try to remove metadata file if it exists
        meta_path = f"{self.index_path}.meta.json"
        if os.path.exists(meta_path):
            os.remove(meta_path)

        self.searcher = None

    def reset_index(self):
        """Reset the index (delete and prepare for rebuild)."""
        self.delete_index()
        self.builder = None
        logger.info(f"Reset LEANN index: {self.index_name}")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the LEANN index."""
        index_exists = os.path.exists(self.index_path)
        index_size = 0
        if index_exists:
            try:
                index_size = os.path.getsize(self.index_path)
            except Exception:
                pass

        return {
            "index_name": self.index_name,
            "index_path": self.index_path,
            "index_exists": index_exists,
            "index_size_mb": round(index_size / (1024 * 1024), 2) if index_size > 0 else 0,
            "backend": self.backend,
            "compact": self.compact,
            "recompute": self.recompute
        }

    @property
    def collection(self):
        """Access underlying LEANN searcher (for backward compatibility)."""
        return self.searcher

