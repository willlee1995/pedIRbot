"""FastAPI server for RAG chatbot testing."""
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from loguru import logger

from config import settings
from src.embeddings import get_embedding_model
from src.vector_store import VectorStore
from src.retriever import HybridRetriever
from src.llm import get_llm_provider
from src.rag_pipeline import RAGPipeline


# Global instances
rag_pipeline: Optional[RAGPipeline] = None
vector_store: Optional[VectorStore] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    global rag_pipeline, vector_store

    logger.info("Initializing RAG system...")

    try:
        # Initialize embedding model
        embedding_model = get_embedding_model()

        # Initialize vector store
        vector_store = VectorStore(embedding_model)

        # Initialize retriever
        retriever = HybridRetriever(vector_store)

        # Initialize LLM provider
        llm_provider = get_llm_provider()

        # Initialize RAG pipeline
        rag_pipeline = RAGPipeline(retriever, llm_provider)

        logger.info("RAG system initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="PedIR RAG Chatbot API",
    description="Testing backend for Pediatric IR Patient Education Chatbot",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class QueryRequest(BaseModel):
    """Request model for chat query."""
    query: str = Field(..., description="User query")
    k: Optional[int] = Field(
        None, description="Number of documents to retrieve")
    temperature: Optional[float] = Field(0.1, description="LLM temperature")
    filter: Optional[Dict[str, Any]] = Field(
        None, description="Metadata filter")
    include_sources: bool = Field(True, description="Include source documents")


class QueryResponse(BaseModel):
    """Response model for chat query."""
    response: str
    sources: list
    is_emergency: bool


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    vector_store_stats: Dict[str, Any]
    settings: Dict[str, Any]


@app.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "message": "PedIR RAG Chatbot API",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    if rag_pipeline is None or vector_store is None:
        raise HTTPException(
            status_code=503, detail="RAG system not initialized")

    return {
        "status": "healthy",
        "vector_store_stats": vector_store.get_stats(),
        "settings": {
            "embedding_provider": settings.embedding_provider,
            "llm_provider": settings.llm_provider,
            "top_k_retrieval": settings.top_k_retrieval,
            "hybrid_alpha": settings.hybrid_alpha
        }
    }


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Process a chat query and return response.

    Args:
        request: QueryRequest with user query and parameters

    Returns:
        QueryResponse with generated response and sources
    """
    if rag_pipeline is None:
        raise HTTPException(
            status_code=503, detail="RAG system not initialized")

    try:
        result = rag_pipeline.generate_response(
            query=request.query,
            k=request.k,
            filter_dict=request.filter,
            temperature=request.temperature,
            include_sources=request.include_sources
        )

        return QueryResponse(**result)

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/stream")
async def query_stream(request: QueryRequest):
    """
    Process a chat query and return streaming response.

    Args:
        request: QueryRequest with user query and parameters

    Returns:
        Streaming response
    """
    if rag_pipeline is None:
        raise HTTPException(
            status_code=503, detail="RAG system not initialized")

    async def generate():
        try:
            for chunk in rag_pipeline.stream_response(
                query=request.query,
                k=request.k,
                filter_dict=request.filter,
                temperature=request.temperature
            ):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            yield f"data: {{'type': 'error', 'content': '{str(e)}'}}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/stats")
async def get_stats():
    """Get vector store statistics."""
    if vector_store is None:
        raise HTTPException(
            status_code=503, detail="Vector store not initialized")

    return vector_store.get_stats()


@app.post("/rebuild-index")
async def rebuild_index():
    """Rebuild the BM25 index (call after adding new documents)."""
    if rag_pipeline is None:
        raise HTTPException(
            status_code=503, detail="RAG system not initialized")

    try:
        rag_pipeline.retriever.rebuild_bm25_index()
        return {"message": "BM25 index rebuilt successfully"}
    except Exception as e:
        logger.error(f"Error rebuilding index: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
