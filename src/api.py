"""FastAPI server for RAG chatbot testing."""
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from loguru import logger

from config import settings
from src.embeddings import get_embedding_model
from src.vector_store import VectorStore
from src.retriever import AdvancedRetriever
from src.llm import get_langchain_llm
from src.rag_pipeline import RAGPipeline

# Import LangSmith traceable decorator
try:
    from langsmith import traceable
    from langsmith import Client as LangSmithClient
    LANGSMITH_AVAILABLE = True
    langsmith_client = LangSmithClient(api_key=settings.langsmith_api_key) if settings.langsmith_api_key else None
except ImportError:
    LANGSMITH_AVAILABLE = False
    langsmith_client = None
    # Create a no-op decorator if LangSmith is not available
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


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

        # Initialize retriever (optional, for direct retrieval)
        retriever = AdvancedRetriever(vector_store, llm=get_langchain_llm())

        # Initialize RAG pipeline with agent
        rag_pipeline = RAGPipeline(vector_store, retriever=retriever)

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
    run_id: Optional[str] = None  # For feedback tracking


class FeedbackRequest(BaseModel):
    """Request model for feedback."""
    run_id: str = Field(..., description="Run ID from query response")
    score: float = Field(..., ge=0.0, le=1.0, description="Feedback score (0.0-1.0)")
    comment: Optional[str] = Field(None, description="Optional comment")


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


@traceable(name="api_query", metadata={"endpoint": "/query", "component": "api"})
def _process_query(query: str, k: Optional[int], filter_dict: Optional[Dict[str, Any]],
                   temperature: float, include_sources: bool) -> Dict[str, Any]:
    """Internal function to process query with LangSmith tracing."""
    if rag_pipeline is None:
        raise ValueError("RAG system not initialized")

    result = rag_pipeline.generate_response(
        query=query,
        k=k,
        filter_dict=filter_dict,
        temperature=temperature,
        include_sources=include_sources
    )
    return result


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Process a chat query and return response.

    Args:
        request: QueryRequest with user query and parameters

    Returns:
        QueryResponse with generated response and sources
    """
    # Generate run_id for feedback tracking
    run_id = str(uuid.uuid4())

    if rag_pipeline is None:
        raise HTTPException(
            status_code=503, detail="RAG system not initialized")

    try:
        result = _process_query(
            query=request.query,
            k=request.k,
            filter_dict=request.filter,
            temperature=request.temperature,
            include_sources=request.include_sources
        )

        # Add run_id to result for feedback tracking
        result['run_id'] = run_id

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


@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit feedback for a query run.

    Args:
        request: FeedbackRequest with run_id and score

    Returns:
        Success message
    """
    if not LANGSMITH_AVAILABLE or langsmith_client is None:
        raise HTTPException(
            status_code=503, detail="LangSmith is not available")

    try:
        langsmith_client.create_feedback(
            request.run_id,
            key="user-score",
            score=request.score,
            comment=request.comment,
        )
        logger.info(f"Feedback submitted for run_id: {request.run_id}, score: {request.score}")
        return {"message": "Feedback submitted successfully", "run_id": request.run_id}
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
