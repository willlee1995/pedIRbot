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
    ollama_chat_model: str = "alibayram/medgemma"  # Default LLM (used for final answer generation)
    ollama_orchestrator_model: str = "qwen3:8b"  # Model for orchestration (tool calling)

    # Vector Database Configuration
    chroma_persist_directory: str = "./chroma_db"
    collection_name: str = "pedir_knowledge_base"

    # Document Database Configuration (SQLite for full document storage)
    document_db_path: str = "./document_db.sqlite"

    # Retrieval Configuration
    top_k_retrieval: int = 5
    top_k_reranker: int = 3  # Number of documents to return after reranking
    hybrid_alpha: float = 0.7  # Weight for semantic search (legacy, may be deprecated)

    # LangChain Agent Configuration
    agent_max_iterations: int = 5
    agent_verbose: bool = False
    agent_temperature: float = 0.1

    # LangChain Reranker Configuration
    use_reranker: bool = True
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"  # Default reranker model
    reranker_top_k: int = 10  # Number of documents to rerank (before selecting top_k_reranker)

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

    # LangSmith Configuration
    langsmith_tracing: bool = False  # Set to True to enable tracing
    langsmith_api_key: str = ""
    langsmith_project: str = "pedir-bot"  # Project name in LangSmith
    langsmith_endpoint: str = "https://api.smith.langchain.com"  # LangSmith API endpoint


settings = Settings()
