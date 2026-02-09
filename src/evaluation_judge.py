"""LLM-as-a-Judge for RAG Evaluation using MedGemma via LM Studio."""
from typing import Dict, Any, Optional
import re
import json
from loguru import logger
from langchain_core.messages import HumanMessage
from src.llm import get_langchain_llm

class RAGJudge:
    """Evaluates RAG outputs using an LLM judge (MedGemma)."""

    def __init__(self, model_name: str = None):
        """
        Initialize the judge.

        Args:
            model_name: Optional model name override.
        """
        self.llm = get_langchain_llm(provider="lmstudio", model=model_name)
        logger.info(f"Initialized RAGJudge with LM Studio model: {model_name or 'default'}")

    def _clean_json_response(self, text: str) -> str:
        """Clean potential markdown or extra text from JSON response."""
        # Try to find JSON block
        match = re.search(r'```json\s*({.*?})\s*```', text, re.DOTALL)
        if match:
            return match.group(1)

        # Try to find just braces
        match = re.search(r'({.*})', text, re.DOTALL)
        if match:
            return match.group(1)

        return text

    def evaluate_faithfulness(self, question: str, context: str, answer: str) -> float:
        """
        Evaluate if the answer is derived ONLY from the provided context.
        Returns a score between 0.0 and 1.0.
        """
        prompt = f"""You are an impartial judge evaluating the faithfulness of an AI assistant's answer to the provided context.

        Task:
        1. Compare the ANSWER to the CONTEXT.
        2. Determine if the ANSWER can be fully supported by the CONTEXT.
        3. If the ANSWER contains information NOT in the CONTEXT, score it 0.
        4. If the ANSWER is fully supported, score it 1.

        CONTEXT:
        {context[:8000]}

        ANSWER:
        {answer}

        Respond with ONLY a JSON object:
        {{
            "score": <0 or 1>,
            "reasoning": "<brief explanation>"
        }}
        """

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = self._clean_json_response(response.content)
            result = json.loads(content)
            return float(result.get("score", 0.0))
        except Exception as e:
            logger.warning(f"Faithfulness evaluation failed: {e}")
            logger.debug(f"Raw response: {response.content if 'response' in locals() else 'None'}")
            return 0.0

    def evaluate_relevance(self, question: str, answer: str) -> float:
        """
        Evaluate if the answer directly addresses the user's question.
        Returns a score between 0.0 and 1.0.
        """
        prompt = f"""You are an impartial judge evaluating the relevance of an AI assistant's answer to a user's question.

        Task:
        1. Read the QUESTION and the ANSWER.
        2. Determine if the ANSWER directly helps the user or answers their question.
        3. Ignore whether the answer is true/false (that is faithfulness). Focus only on RELEVANCE.
        4. Score 1 for completely relevant, 0.5 for partially relevant, 0 for irrelevant.

        QUESTION:
        {question}

        ANSWER:
        {answer}

        Respond with ONLY a JSON object:
        {{
            "score": <0, 0.5, or 1>,
            "reasoning": "<brief explanation>"
        }}
        """

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content = self._clean_json_response(response.content)
            result = json.loads(content)
            return float(result.get("score", 0.0))
        except Exception as e:
            logger.warning(f"Relevance evaluation failed: {e}")
            return 0.0

if __name__ == "__main__":
    # Simple test block
    judge = RAGJudge()

    q = "What is the capital of France?"
    c = "Paris is the capital of France and is known for the Eiffel Tower."
    a = "The capital of France is Paris."

    print(f"Testing Faithfulness (Expected ~1.0)...")
    score = judge.evaluate_faithfulness(q, c, a)
    print(f"Score: {score}")

    a_bad = "The capital of France is London."
    print(f"Testing Faithfulness (Expected ~0.0)...")
    score = judge.evaluate_faithfulness(q, c, a_bad)
    print(f"Score: {score}")

