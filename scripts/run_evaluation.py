"""Script to run evaluation on test questions."""
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path FIRST (before other imports)
sys.path.insert(0, str(Path(__file__).parent.parent))

# isort: off  - Don't reorder imports below this line
from loguru import logger
from config import settings
from src.embeddings import get_embedding_model
from src.vector_store import VectorStore
from src.retriever import HybridRetriever
from src.llm import get_llm_provider
from src.rag_pipeline import RAGPipeline
from src.evaluation import RAGEvaluator
# isort: on


def main(test_questions_file: str, output_dir: str = "./evaluation_results"):
    """
    Run evaluation on test questions.

    Args:
        test_questions_file: Path to JSON file with test questions
        output_dir: Directory to save evaluation results
    """
    logger.info("Starting RAG evaluation...")
    logger.info(f"LLM provider: {settings.llm_provider}")
    logger.info(f"Embedding provider: {settings.embedding_provider}")

    # Initialize components
    logger.info("Initializing RAG system...")
    embedding_model = get_embedding_model()
    vector_store = VectorStore(embedding_model)
    retriever = HybridRetriever(vector_store)
    llm_provider = get_llm_provider()
    rag_pipeline = RAGPipeline(retriever, llm_provider)

    # Initialize evaluator
    evaluator = RAGEvaluator(rag_pipeline)

    # Load test questions
    logger.info(f"Loading test questions from: {test_questions_file}")
    questions = evaluator.load_test_questions(test_questions_file)

    # Run evaluation
    logger.info("Running evaluation...")
    results = evaluator.evaluate_questions(questions)

    # Save results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_name = settings.llm_provider

    results_file = output_path / f"results_{model_name}_{timestamp}.json"
    report_file = output_path / f"report_{model_name}_{timestamp}.json"
    excel_file = output_path / f"results_{model_name}_{timestamp}.xlsx"

    logger.info("Saving results...")
    evaluator.save_results(str(results_file))

    logger.info("Generating report...")
    report = evaluator.generate_report(str(report_file))

    logger.info("Exporting to Excel...")
    evaluator.export_to_excel(str(excel_file))

    # Print summary
    logger.info("=" * 50)
    logger.info("EVALUATION COMPLETE")
    logger.info("=" * 50)
    logger.info(f"Total questions: {report['total_questions']}")
    logger.info(f"Success rate: {report['success_rate']}%")
    logger.info(f"Average latency: {report['average_latency']}s")
    if 'topic_coverage_rate' in report:
        logger.info(f"Topic coverage: {report['topic_coverage_rate']}%")
    logger.info("=" * 50)
    logger.info(f"Results saved to: {results_file}")
    logger.info(f"Report saved to: {report_file}")
    logger.info(f"Excel exported to: {excel_file}")
    logger.info("=" * 50)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run RAG evaluation")
    parser.add_argument("test_questions", type=str,
                        help="Path to test questions JSON file")
    parser.add_argument("--output-dir", type=str, default="./evaluation_results",
                        help="Output directory for results")

    args = parser.parse_args()

    main(args.test_questions, args.output_dir)
