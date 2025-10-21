"""Script to compare multiple LLM models on the same test set."""
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
from src.llm import get_llm_provider, OpenAIProvider, OllamaProvider
from src.rag_pipeline import RAGPipeline
from src.evaluation import RAGEvaluator, ModelComparison
# isort: on


def evaluate_model(model_name: str,
                   provider_type: str,
                   test_questions_file: str,
                   vector_store: VectorStore,
                   **provider_kwargs) -> RAGEvaluator:
    """
    Evaluate a single model.

    Args:
        model_name: Name of the model for reporting
        provider_type: 'openai' or 'ollama'
        test_questions_file: Path to test questions
        vector_store: VectorStore instance (shared)
        **provider_kwargs: Additional provider arguments

    Returns:
        RAGEvaluator with results
    """
    logger.info(f"Evaluating model: {model_name}")

    # Initialize LLM provider
    if provider_type == "openai":
        llm_provider = OpenAIProvider(**provider_kwargs)
    elif provider_type == "ollama":
        llm_provider = OllamaProvider(**provider_kwargs)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")

    # Initialize RAG pipeline
    retriever = HybridRetriever(vector_store)
    rag_pipeline = RAGPipeline(retriever, llm_provider)

    # Run evaluation
    evaluator = RAGEvaluator(rag_pipeline)
    questions = evaluator.load_test_questions(test_questions_file)
    evaluator.evaluate_questions(questions)

    return evaluator


def main(test_questions_file: str, output_dir: str = "./comparison_results"):
    """
    Compare multiple models on the same test set.

    Args:
        test_questions_file: Path to test questions JSON file
        output_dir: Directory to save comparison results
    """
    logger.info("Starting model comparison...")

    # Initialize shared components
    logger.info("Initializing shared components...")
    embedding_model = get_embedding_model()
    vector_store = VectorStore(embedding_model)

    # Define models to compare
    models = [
        {
            "name": "GPT-4o",
            "provider": "openai",
            "kwargs": {"model": "gpt-4o", "temperature": 0.1}
        },
        {
            "name": "GPT-4o-mini",
            "provider": "openai",
            "kwargs": {"model": "gpt-4o-mini", "temperature": 0.1}
        },
        {
            "name": "Gemini-2.5-Pro",
            "provider": "openai",  # If using OpenAI-compatible endpoint
            "kwargs": {
                "model": "gemini-2.5-pro",
                "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                "temperature": 0.1
            }
        },
        {
            "name": "MedGemma-Ollama",
            "provider": "ollama",
            "kwargs": {"model": "alibayram/medgemma", "temperature": 0.1}
        },
        # Add more models as needed
    ]

    # Run evaluations
    comparison = ModelComparison()

    for model_config in models:
        try:
            evaluator = evaluate_model(
                model_name=model_config["name"],
                provider_type=model_config["provider"],
                test_questions_file=test_questions_file,
                vector_store=vector_store,
                **model_config["kwargs"]
            )

            comparison.add_result(model_config["name"], evaluator)

            # Save individual results
            output_path = Path(output_dir) / model_config["name"]
            output_path.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            evaluator.save_results(
                str(output_path / f"results_{timestamp}.json"))
            evaluator.generate_report(
                str(output_path / f"report_{timestamp}.json"))
            evaluator.export_to_excel(
                str(output_path / f"results_{timestamp}.xlsx"))

        except Exception as e:
            logger.error(f"Error evaluating {model_config['name']}: {e}")
            continue

    # Generate comparison report
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    comparison_file = output_path / f"comparison_{timestamp}.xlsx"

    logger.info("Generating comparison report...")
    comparison.generate_comparison_report(str(comparison_file))

    logger.info("=" * 50)
    logger.info("MODEL COMPARISON COMPLETE")
    logger.info("=" * 50)
    logger.info(f"Comparison report saved to: {comparison_file}")
    logger.info("=" * 50)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compare multiple LLM models")
    parser.add_argument("test_questions", type=str,
                        help="Path to test questions JSON file")
    parser.add_argument("--output-dir", type=str, default="./comparison_results",
                        help="Output directory for results")

    args = parser.parse_args()

    # Note: You may need to modify the models list in the main() function
    # to match your specific setup and available models

    main(args.test_questions, args.output_dir)
