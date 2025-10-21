"""Vector database management using ChromaDB."""
from typing import List, Dict, Any, Optional
import uuid

import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger

from src.document_processor import DocumentChunk
from src.embeddings import EmbeddingModel
from config import settings


class VectorStore:
    """Manages vector storage and retrieval using ChromaDB."""

    def __init__(self,
                 embedding_model: EmbeddingModel,
                 collection_name: str = None,
                 persist_directory: str = None):
        """
        Initialize the vector store.

        Args:ModuleNotFoundError: No module named 'src'
            embedding_model: Embedding model to use
            collection_name: Name of the collection (default from settings)
            persist_directory: Directory to persist the database (default from settings)
        """
        self.embedding_model = embedding_model
        self.collection_name = collection_name or settings.collection_name
        self.persist_directory = persist_directory or settings.chroma_persist_directory

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        logger.info(
            f"Initialized vector store with collection: {self.collection_name}")
        logger.info(f"Current collection size: {self.collection.count()}")

    def add_documents(self, chunks: List[DocumentChunk], batch_size: int = 100):
        """
        Add document chunks to the vector store.

        Args:
            chunks: List of DocumentChunk objects
            batch_size: Number of documents to process at once
        """
        logger.info(f"Adding {len(chunks)} documents to vector store...")

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            # Extract data from chunks
            ids = [chunk.chunk_id for chunk in batch]
            documents = [chunk.content for chunk in batch]
            metadatas = [chunk.metadata for chunk in batch]

            # Generate embeddings
            logger.info(
                f"Processing batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")
            embeddings = self.embedding_model.embed_documents(documents)

            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )

        logger.info(
            f"Successfully added {len(chunks)} documents. Total count: {self.collection.count()}")

    def similarity_search(self,
                          query: str,
                          k: int = None,
                          filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Perform similarity search on the vector store.

        Args:
            query: Query text
            k: Number of results to return (default from settings)
            filter_dict: Optional metadata filter

        Returns:
            List of results with content, metadata, and scores
        """
        k = k or settings.top_k_retrieval

        # Generate query embedding
        query_embedding = self.embedding_model.embed_query(query)

        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter_dict,
            include=["documents", "metadatas", "distances"]
        )

        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                # Convert distance to similarity
                'score': 1 - results['distances'][0][i],
                'id': results['ids'][0][i]
            })

        return formatted_results

    def delete_collection(self):
        """Delete the current collection."""
        self.client.delete_collection(self.collection_name)
        logger.warning(f"Deleted collection: {self.collection_name}")

    def reset_collection(self):
        """Reset the collection (delete and recreate)."""
        self.delete_collection()
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Reset collection: {self.collection_name}")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        return {
            "collection_name": self.collection_name,
            "total_documents": self.collection.count(),
            "persist_directory": self.persist_directory
        }
