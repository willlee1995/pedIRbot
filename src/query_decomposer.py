"""Query decomposition for handling multi-part questions."""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
import json

from loguru import logger

from src.llm import LLMProvider


@dataclass
class SubQuery:
    """A decomposed sub-query."""
    query: str
    topic: str
    priority: int = 1  # 1 = high, 2 = medium, 3 = low


@dataclass
class DecompositionResult:
    """Result of query decomposition."""
    original_query: str
    is_complex: bool
    sub_queries: List[SubQuery]
    reasoning: str = ""


class QueryDecomposer:
    """
    Decomposes complex multi-part queries into simpler sub-queries.
    
    This helps handle questions like:
    "What is PICC line insertion and how is it different from port insertion?"
    → Split into two focused queries for better retrieval.
    """

    # Patterns that indicate multi-part questions
    MULTI_QUERY_PATTERNS = [
        r'\band\b.*\?',  # "X and Y?"
        r'\bor\b.*\?',   # "X or Y?"
        r'\balso\b',     # "also"
        r'\bas well\b',  # "as well"
        r'\bdifference\b.*\bbetween\b',  # "difference between X and Y"
        r'\bcompare\b',  # "compare"
        r'\bversus\b|\bvs\.?\b',  # "versus" or "vs"
        r'\?.*\?',       # Multiple question marks
        r'(?:first|second|third|1\.|2\.|3\.)',  # Numbered items
    ]

    DECOMPOSE_PROMPT = """Analyze this query and determine if it asks about multiple distinct topics that should be answered separately.

Query: {query}

If the query asks about multiple procedures, topics, or comparisons, split it into focused sub-queries.
If it's a single focused question, return it as-is.

Respond in JSON only:
{{
    "is_complex": true/false,
    "sub_queries": [
        {{"query": "focused question 1", "topic": "topic name", "priority": 1}},
        {{"query": "focused question 2", "topic": "topic name", "priority": 2}}
    ],
    "reasoning": "brief explanation"
}}

Keep sub-queries simple and focused. Maximum 3 sub-queries."""

    def __init__(self, llm_provider: Optional[LLMProvider] = None, use_llm: bool = True):
        """
        Initialize query decomposer.

        Args:
            llm_provider: LLM for complex decomposition
            use_llm: Whether to use LLM (vs pattern-only)
        """
        self.llm = llm_provider
        self.use_llm = use_llm and llm_provider is not None
        self._compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.MULTI_QUERY_PATTERNS]
        logger.info(f"Initialized QueryDecomposer (LLM: {self.use_llm})")

    def _looks_complex(self, query: str) -> bool:
        """Quick check if query might be complex."""
        for pattern in self._compiled_patterns:
            if pattern.search(query):
                return True
        # Also check query length - very long queries often multi-part
        return len(query.split()) > 25

    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return None

    def _pattern_based_decompose(self, query: str) -> DecompositionResult:
        """Simple pattern-based decomposition (fast, no LLM)."""
        # Check for "difference between X and Y"
        diff_match = re.search(r'difference\s+between\s+(.+?)\s+and\s+(.+?)(?:\?|$)', query, re.IGNORECASE)
        if diff_match:
            topic1, topic2 = diff_match.groups()
            return DecompositionResult(
                original_query=query,
                is_complex=True,
                sub_queries=[
                    SubQuery(f"What is {topic1.strip()}?", topic1.strip(), 1),
                    SubQuery(f"What is {topic2.strip()}?", topic2.strip(), 2),
                ],
                reasoning="Detected comparison question, split into individual topics"
            )

        # Check for "X and Y" pattern
        and_match = re.search(r'(?:what is|tell me about|explain)\s+(.+?)\s+and\s+(.+?)(?:\?|$)', query, re.IGNORECASE)
        if and_match:
            topic1, topic2 = and_match.groups()
            return DecompositionResult(
                original_query=query,
                is_complex=True,
                sub_queries=[
                    SubQuery(f"What is {topic1.strip()}?", topic1.strip(), 1),
                    SubQuery(f"What is {topic2.strip()}?", topic2.strip(), 2),
                ],
                reasoning="Detected multi-topic question with 'and'"
            )

        # Check for multiple question marks
        if query.count('?') > 1:
            parts = [p.strip() + '?' for p in query.split('?') if p.strip()]
            if len(parts) > 1:
                return DecompositionResult(
                    original_query=query,
                    is_complex=True,
                    sub_queries=[SubQuery(p, f"question {i+1}", i+1) for i, p in enumerate(parts[:3])],
                    reasoning="Multiple questions detected"
                )

        # Not complex
        return DecompositionResult(
            original_query=query,
            is_complex=False,
            sub_queries=[SubQuery(query, "main", 1)],
            reasoning="Single focused question"
        )

    def decompose(self, query: str) -> DecompositionResult:
        """
        Decompose a query into sub-queries if needed.

        Args:
            query: User query to analyze

        Returns:
            DecompositionResult with sub-queries
        """
        # Quick check - skip if obviously simple
        if not self._looks_complex(query):
            return DecompositionResult(
                original_query=query,
                is_complex=False,
                sub_queries=[SubQuery(query, "main", 1)],
                reasoning="Simple single-topic query"
            )

        # Try LLM-based decomposition if enabled
        if self.use_llm:
            try:
                prompt = self.DECOMPOSE_PROMPT.format(query=query)
                messages = [{"role": "user", "content": prompt}]
                response = self.llm.generate(messages, temperature=0.1)

                parsed = self._parse_json_response(response)
                if parsed and parsed.get("is_complex"):
                    sub_queries = [
                        SubQuery(
                            sq.get("query", ""),
                            sq.get("topic", ""),
                            sq.get("priority", 1)
                        )
                        for sq in parsed.get("sub_queries", [])
                        if sq.get("query")
                    ]
                    if sub_queries:
                        logger.info(f"LLM decomposed query into {len(sub_queries)} sub-queries")
                        return DecompositionResult(
                            original_query=query,
                            is_complex=True,
                            sub_queries=sub_queries,
                            reasoning=parsed.get("reasoning", "")
                        )
            except Exception as e:
                logger.warning(f"LLM decomposition failed: {e}")

        # Fallback to pattern-based
        return self._pattern_based_decompose(query)

    def merge_responses(self, responses: List[Dict[str, Any]], 
                        decomposition: DecompositionResult) -> Dict[str, Any]:
        """
        Merge responses from multiple sub-queries.

        Args:
            responses: List of response dicts from each sub-query
            decomposition: Original decomposition result

        Returns:
            Merged response dict
        """
        if len(responses) == 1:
            return responses[0]

        # Combine response texts
        merged_parts = []
        all_sources = []
        is_emergency = False
        safety_assessment = None

        for i, (sq, resp) in enumerate(zip(decomposition.sub_queries, responses)):
            if resp.get("is_emergency"):
                is_emergency = True
            
            # Format each sub-response
            topic_header = f"**{sq.topic.title()}:**" if sq.topic != "main" else ""
            if topic_header:
                merged_parts.append(f"\n{topic_header}\n{resp.get('response', '')}")
            else:
                merged_parts.append(resp.get('response', ''))

            # Collect sources (deduplicated)
            for source in resp.get("sources", []):
                if source not in all_sources:
                    all_sources.append(source)

            # Use highest risk safety assessment
            if resp.get("safety_assessment"):
                if safety_assessment is None:
                    safety_assessment = resp["safety_assessment"]

        return {
            "response": "\n".join(merged_parts),
            "sources": all_sources[:10],  # Limit total sources
            "is_emergency": is_emergency,
            "safety_assessment": safety_assessment,
            "was_decomposed": True,
            "sub_query_count": len(responses)
        }
