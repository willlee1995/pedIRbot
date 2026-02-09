"""Test script for RAG pipeline verification."""
import os
import sys
from loguru import logger
from langchain_core.messages import HumanMessage

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agentic_rag import create_agentic_rag_graph
from src.evaluation_judge import RAGJudge
from src.vector_store import VectorStore
from src.embeddings import get_embedding_model
from config import settings

def test_pipeline():
    """Test the RAG pipeline."""
    logger.info("Initializing Embeddings and Vector Store...")
    embedding_model = get_embedding_model()
    vector_store = VectorStore(embedding_model=embedding_model)

    logger.info("Initializing RAG Graph...")
    app = create_agentic_rag_graph(vector_store=vector_store)

    question = "What are the complications of sclerotherapy?"
    logger.info(f"Testing Question: {question}")

    inputs = {"messages": [HumanMessage(content=question)]}

    try:
        logger.info("Invoking graph...")
        # Stream events to see what nodes are hit
        for event in app.stream(inputs, stream_mode="values"):
            msg = event["messages"][-1]
            logger.info(f"Step: {type(msg).__name__} - {str(msg.content)[:100]}...")

    except Exception as e:
        logger.error(f"Graph invocation failed: {e}")
        # raise e # Don't raise to allow judge test to run

def test_judge():
    """Test the RAG Judge."""
    logger.info("Initializing Judge...")
    # Ensure we use LM Studio setting
    model_name = settings.lmstudio_chat_model
    logger.info(f"Using model: {model_name}")

    try:
        judge = RAGJudge(model_name=model_name)

        q = "What is the capital of France?"
        c = "Paris is the capital of France."
        a = "The capital is Paris."

        logger.info("Testing Faithfulness...")
        score = judge.evaluate_faithfulness(q, c, a)
        logger.info(f"Faithfulness Score: {score}")
    except Exception as e:
        logger.error(f"Judge test failed: {e}")

if __name__ == "__main__":
    logger.add(sys.stderr, format="{time} {level} {message}", level="INFO")
    test_judge()
    test_pipeline()
