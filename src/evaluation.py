"""Evaluation framework for testing RAG system performance."""
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
from datetime import datetime
import time

import pandas as pd
from loguru import logger

from src.rag_pipeline import RAGPipeline


class RAGEvaluator:
    """Evaluate RAG system performance on test questions."""

    def __init__(self, rag_pipeline: RAGPipeline):
        """
        Initialize the evaluator.

        Args:
            rag_pipeline: RAGPipeline instance to evaluate
        """
        self.rag_pipeline = rag_pipeline
        self.results = []

    def load_test_questions(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load test questions from a JSON file.

        Expected format:
        [
            {
                "id": "q1",
                "question": "How long should my child fast before the procedure?",
                "language": "en",
                "category": "preparation",
                "expected_topics": ["fasting", "food", "water"]
            },
            ...
        ]

        Args:
            file_path: Path to JSON file with test questions

        Returns:
            List of question dictionaries
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)

        logger.info(f"Loaded {len(questions)} test questions from {file_path}")
        return questions

    def evaluate_questions(self,
                           questions: List[Dict[str, Any]],
                           temperature: float = 0.1,
                           k: int = None) -> List[Dict[str, Any]]:
        """
        Evaluate the RAG system on a list of questions.

        Args:
            questions: List of question dictionaries
            temperature: LLM temperature
            k: Number of documents to retrieve

        Returns:
            List of evaluation results
        """
        results = []

        for i, q in enumerate(questions, 1):
            logger.info(
                f"Evaluating question {i}/{len(questions)}: {q.get('id', 'unknown')}")

            start_time = time.time()

            try:
                # Generate response
                result = self.rag_pipeline.generate_response(
                    query=q['question'],
                    k=k,
                    temperature=temperature,
                    include_sources=True
                )

                latency = time.time() - start_time

                # Compile evaluation result
                eval_result = {
                    'question_id': q.get('id', f'q_{i}'),
                    'question': q['question'],
                    'language': q.get('language', 'unknown'),
                    'category': q.get('category', 'unknown'),
                    'response': result['response'],
                    'num_sources': len(result.get('sources', [])),
                    'sources': result.get('sources', []),
                    'is_emergency': result.get('is_emergency', False),
                    'latency_seconds': round(latency, 2),
                    'timestamp': datetime.now().isoformat()
                }

                # Add expected topics if provided
                if 'expected_topics' in q:
                    eval_result['expected_topics'] = q['expected_topics']
                    # Check if response contains expected topics
                    response_lower = result['response'].lower()
                    eval_result['topics_covered'] = [
                        topic for topic in q['expected_topics']
                        if topic.lower() in response_lower
                    ]

                results.append(eval_result)

            except Exception as e:
                logger.error(f"Error evaluating question {q.get('id')}: {e}")
                results.append({
                    'question_id': q.get('id', f'q_{i}'),
                    'question': q['question'],
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })

        self.results = results
        logger.info(
            f"Evaluation completed: {len(results)} questions processed")
        return results

    def save_results(self, output_path: str):
        """
        Save evaluation results to a JSON file.

        Args:
            output_path: Path to output JSON file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to {output_path}")

    def generate_report(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a summary report of evaluation results.

        Args:
            output_path: Optional path to save report as JSON

        Returns:
            Report dictionary
        """
        if not self.results:
            logger.warning("No results to generate report from")
            return {}

        # Calculate statistics
        total_questions = len(self.results)
        successful = [r for r in self.results if 'error' not in r]
        errors = [r for r in self.results if 'error' in r]

        latencies = [r['latency_seconds']
                     for r in successful if 'latency_seconds' in r]

        # Count by language and category
        languages = {}
        categories = {}

        for r in successful:
            lang = r.get('language', 'unknown')
            cat = r.get('category', 'unknown')

            languages[lang] = languages.get(lang, 0) + 1
            categories[cat] = categories.get(cat, 0) + 1

        # Build report
        report = {
            'total_questions': total_questions,
            'successful': len(successful),
            'errors': len(errors),
            'success_rate': round(len(successful) / total_questions * 100, 2) if total_questions > 0 else 0,
            'average_latency': round(sum(latencies) / len(latencies), 2) if latencies else 0,
            'min_latency': round(min(latencies), 2) if latencies else 0,
            'max_latency': round(max(latencies), 2) if latencies else 0,
            'languages': languages,
            'categories': categories,
            'timestamp': datetime.now().isoformat()
        }

        # Add topic coverage statistics if available
        questions_with_topics = [
            r for r in successful if 'expected_topics' in r]
        if questions_with_topics:
            total_topics = sum(len(r['expected_topics'])
                               for r in questions_with_topics)
            covered_topics = sum(len(r.get('topics_covered', []))
                                 for r in questions_with_topics)
            report['topic_coverage_rate'] = round(
                covered_topics / total_topics * 100, 2) if total_topics > 0 else 0

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"Report saved to {output_path}")

        return report

    def export_to_excel(self, output_path: str):
        """
        Export results to Excel for manual review and scoring.

        Args:
            output_path: Path to output Excel file
        """
        if not self.results:
            logger.warning("No results to export")
            return

        # Prepare data for Excel
        excel_data = []

        for r in self.results:
            row = {
                'Question ID': r.get('question_id', ''),
                'Question': r.get('question', ''),
                'Language': r.get('language', ''),
                'Category': r.get('category', ''),
                'Response': r.get('response', ''),
                'Num Sources': r.get('num_sources', 0),
                'Latency (s)': r.get('latency_seconds', ''),
                'Is Emergency': r.get('is_emergency', False),
                'Error': r.get('error', ''),
                # Add empty columns for manual scoring
                'Accuracy (1-6)': '',
                'Relevance (1-6)': '',
                'Completeness (1-3)': '',
                'Comments': ''
            }
            excel_data.append(row)

        df = pd.DataFrame(excel_data)
        df.to_excel(output_path, index=False, engine='openpyxl')

        logger.info(f"Results exported to Excel: {output_path}")


class ModelComparison:
    """Compare multiple models/configurations on the same test set."""

    def __init__(self):
        """Initialize the comparison framework."""
        self.comparisons = {}

    def add_result(self, model_name: str, evaluator: RAGEvaluator):
        """
        Add evaluation results for a model.

        Args:
            model_name: Name/identifier for the model
            evaluator: RAGEvaluator with results
        """
        self.comparisons[model_name] = {
            'results': evaluator.results,
            'report': evaluator.generate_report()
        }
        logger.info(f"Added results for model: {model_name}")

    def generate_comparison_report(self, output_path: str):
        """
        Generate a comparison report across all models.

        Args:
            output_path: Path to save comparison report
        """
        comparison_data = []

        for model_name, data in self.comparisons.items():
            report = data['report']
            comparison_data.append({
                'Model': model_name,
                'Success Rate (%)': report.get('success_rate', 0),
                'Avg Latency (s)': report.get('average_latency', 0),
                'Min Latency (s)': report.get('min_latency', 0),
                'Max Latency (s)': report.get('max_latency', 0),
                'Topic Coverage (%)': report.get('topic_coverage_rate', 'N/A'),
                'Total Questions': report.get('total_questions', 0)
            })

        df = pd.DataFrame(comparison_data)
        df.to_excel(output_path, index=False, engine='openpyxl')

        logger.info(f"Comparison report saved to: {output_path}")
