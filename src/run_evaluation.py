"""Run full RAG evaluation."""
import os
import sys
import json
import asyncio
from loguru import logger
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agentic_rag import create_agentic_rag_graph
from src.evaluation import RAGEvaluator
from src.vector_store import VectorStore
from src.embeddings import get_embedding_model

def load_test_questions(path: str):
    """Load test questions from JSON."""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def main():
    """Run evaluation."""
    logger.info("Initializing RAG system for evaluation...")

    # Initialize components
    embedding_model = get_embedding_model()
    vector_store = VectorStore(embedding_model=embedding_model)
    rag_graph = create_agentic_rag_graph(vector_store=vector_store)

    # Initialize evaluator
    evaluator = RAGEvaluator(rag_graph)

    # Load questions
    test_data_path = "test_data/sample_questions.json"
    if not os.path.exists(test_data_path):
        logger.error(f"Test data not found: {test_data_path}")
        return

    logger.info(f"Loading questions from {test_data_path}...")
    questions = load_test_questions(test_data_path)

    # Run evaluation
    logger.info(f"Starting evaluation of {len(questions)} questions...")
    results = evaluator.evaluate_questions(questions, rag_graph)

    # Generate report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"evaluation_report_{timestamp}.json"
    excel_path = f"evaluation_results_{timestamp}.xlsx"

    evaluator.generate_report(report_path)
    evaluator.export_to_excel(excel_path)

    logger.info(f"Evaluation complete. Report saved to {report_path}")

if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    main()
