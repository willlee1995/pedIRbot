"""Entry point for LangGraph Studio - exports the agent graph."""
import sys
from pathlib import Path

# Add project root to Python path so imports work
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.embeddings import get_embedding_model
from src.vector_store import VectorStore
from src.agentic_rag import create_agentic_rag_graph
from loguru import logger

# Initialize the vector store and create the agent graph
# This is the entry point that LangGraph Studio will use
logger.info("Initializing agent for LangGraph Studio...")

# Initialize embedding model
embedding_model = get_embedding_model()

# Initialize vector store
vector_store = VectorStore(embedding_model)

# Create the agent graph
agent = create_agentic_rag_graph(vector_store)

logger.info("Agent graph created successfully for LangGraph Studio")

