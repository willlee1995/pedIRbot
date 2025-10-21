"""Configuration management for PedIR RAG Backend."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_api_base: str = "https://api.openai.com/v1"
    openai_embedding_model: str = "text-embedding-3-large"
    openai_chat_model: str = "gpt-4o"

    # Ollama Configuration
    ollama_api_base: str = "http://localhost:11434"
    ollama_chat_model: str = "alibayram/medgemma"

    # Vector Database Configuration
    chroma_persist_directory: str = "./chroma_db"
    collection_name: str = "pedir_knowledge_base"

    # Retrieval Configuration
    top_k_retrieval: int = 5
    hybrid_alpha: float = 0.7  # Weight for semantic search

    # Application Settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    max_chunk_size: int = 400  # Reduced for embeddinggemma compatibility
    chunk_overlap: int = 50
    min_relevance_score: float = 0.4  # Minimum similarity score for retrieval

    # Embedding Model Options
    embedding_provider: Literal["openai",
                                "sentence-transformer", "ollama"] = "openai"
    sentence_transformer_model: str = "BAAI/bge-m3"
    ollama_embedding_model: str = "qwen3-embedding:0.6b"

    # LLM Provider
    llm_provider: Literal["openai", "ollama"] = "openai"


settings = Settings()
