"""Embedding generation for documents and queries."""
from typing import List, Union
from abc import ABC, abstractmethod

import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import ollama
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings


class EmbeddingModel(ABC):
    """Abstract base class for embedding models."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of the embeddings."""
        pass


class OpenAIEmbeddings(EmbeddingModel):
    """OpenAI embedding model implementation."""

    def __init__(self, model: str = None, api_key: str = None, base_url: str = None):
        """
        Initialize OpenAI embeddings.

        Args:
            model: Model name (default from settings)
            api_key: OpenAI API key (default from settings)
            base_url: API base URL (default from settings)
        """
        self.model = model or settings.openai_embedding_model
        self.client = OpenAI(
            api_key=api_key or settings.openai_api_key,
            base_url=base_url or settings.openai_api_base
        )
        self._dimension = None
        logger.info(f"Initialized OpenAI embeddings with model: {self.model}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents with retry logic.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            embeddings = [item.embedding for item in response.data]

            # Cache dimension
            if self._dimension is None and embeddings:
                self._dimension = len(embeddings[0])

            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        return self.embed_documents([text])[0]

    @property
    def dimension(self) -> int:
        """Return the dimension of embeddings."""
        if self._dimension is None:
            # Generate a test embedding to get dimension
            test_embedding = self.embed_query("test")
            self._dimension = len(test_embedding)
        return self._dimension


class SentenceTransformerEmbeddings(EmbeddingModel):
    """Sentence Transformer (local) embedding model implementation."""

    def __init__(self, model_name: str = None):
        """
        Initialize Sentence Transformer embeddings.

        Args:
            model_name: Model name (default from settings)
        """
        self.model_name = model_name or settings.sentence_transformer_model
        logger.info(f"Loading Sentence Transformer model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        self._dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self._dimension}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    @property
    def dimension(self) -> int:
        """Return the dimension of embeddings."""
        return self._dimension


class OllamaEmbeddings(EmbeddingModel):
    """Ollama embedding model implementation."""

    def __init__(self, model: str = None, base_url: str = None):
        """
        Initialize Ollama embeddings.

        Args:
            model: Model name (default from settings)
            base_url: Ollama API base URL (default from settings)
        """
        self.model = model or settings.ollama_embedding_model
        self.base_url = base_url or settings.ollama_api_base

        # Set the Ollama host
        if self.base_url:
            import os
            os.environ['OLLAMA_HOST'] = self.base_url

        # Test connection and get dimension
        try:
            test_embedding = ollama.embeddings(model=self.model, prompt="test")
            self._dimension = len(test_embedding['embedding'])
            logger.info(
                f"Initialized Ollama embeddings with model: {self.model}")
            logger.info(f"Embedding dimension: {self._dimension}")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama embeddings: {e}")
            logger.error(
                f"Make sure Ollama is running and model '{self.model}' is available")
            logger.error(f"Run: ollama pull {self.model}")
            raise

    def _truncate_text(self, text: str, max_length: int = 512) -> str:
        """
        Truncate text to fit within model's context window.

        This should rarely happen if chunking is configured correctly.

        Args:
            text: Text to truncate
            max_length: Maximum number of characters (approximate tokens)

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text

        # Truncate and add indicator
        truncated = text[:max_length-3] + "..."
        logger.error(f"⚠️ CHUNK TOO LARGE: Text truncated from {len(text)} to {max_length} chars! "
                    f"Consider reducing MAX_CHUNK_SIZE in .env to avoid data loss.")
        return truncated

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of documents.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        embeddings = []

        for text in texts:
            try:
                # Safety check: truncate if needed (should not happen with correct chunking)
                # embeddinggemma has ~512 token limit (~400 chars safe limit)
                if len(text) > 400:
                    truncated_text = self._truncate_text(text, max_length=400)
                else:
                    truncated_text = text

                response = ollama.embeddings(
                    model=self.model,
                    prompt=truncated_text
                )
                embeddings.append(response['embedding'])
            except Exception as e:
                error_msg = str(e).lower()
                if "context length" in error_msg or "input length" in error_msg:
                    logger.error(f"Context length error for text of {len(text)} chars: {e}")
                    # Try with aggressive truncation as last resort
                    try:
                        very_short_text = self._truncate_text(text, max_length=200)
                        response = ollama.embeddings(
                            model=self.model,
                            prompt=very_short_text
                        )
                        embeddings.append(response['embedding'])
                        logger.warning(f"Recovered with aggressive truncation to 200 chars")
                    except Exception as e2:
                        logger.error(f"Failed even with aggressive truncation: {e2}")
                        raise
                else:
                    logger.error(f"Error generating embedding for text (length: {len(text)}): {e}")
                    raise

        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        try:
            # Truncate query if needed
            truncated_text = self._truncate_text(text, max_length=400)

            response = ollama.embeddings(
                model=self.model,
                prompt=truncated_text
            )
            return response['embedding']
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise

    @property
    def dimension(self) -> int:
        """Return the dimension of embeddings."""
        return self._dimension


def get_embedding_model(provider: str = None) -> EmbeddingModel:
    """
    Factory function to get the appropriate embedding model.

    Args:
        provider: 'openai', 'sentence-transformer', or 'ollama' (default from settings)

    Returns:
        EmbeddingModel instance
    """
    provider = provider or settings.embedding_provider

    if provider == "openai":
        return OpenAIEmbeddings()
    elif provider == "sentence-transformer":
        return SentenceTransformerEmbeddings()
    elif provider == "ollama":
        return OllamaEmbeddings()
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")
