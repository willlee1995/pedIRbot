"""Query grading and routing agent for intelligent RAG orchestration."""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
import re

from loguru import logger

from src.llm import LLMProvider


class QueryType(Enum):
    """Classification of query types."""
    PROCEDURAL = "procedural"  # About specific IR procedures
    GENERAL = "general"  # General medical/IR information
    EMERGENCY = "emergency"  # Emergency situation
    OFF_TOPIC = "off_topic"  # Not related to pediatric IR
    CLARIFICATION = "clarification"  # User asking for more details


class SuggestedAction(Enum):
    """Actions the grader suggests."""
    ANSWER = "answer"  # Proceed with answer generation
    EXPAND_SEARCH = "expand_search"  # Retrieve more documents
    REJECT = "reject"  # Politely reject off-topic query
    ESCALATE = "escalate"  # Emergency or complex case
    CLARIFY = "clarify"  # Ask user for clarification


@dataclass
class QueryClassification:
    """Result of query classification."""
    query_type: QueryType
    confidence: float
    detected_procedure: Optional[str] = None
    reasoning: str = ""


@dataclass
class DocumentGrade:
    """Grade for a single retrieved document."""
    doc_index: int
    relevance_score: float  # 0-10
    reason: str
    is_useful: bool


@dataclass
class GradingResult:
    """Result of document grading."""
    document_grades: List[DocumentGrade]
    can_answer: bool
    suggested_action: SuggestedAction
    reasoning: str
    filtered_docs: List[Dict[str, Any]]  # Docs filtered by grade


class QueryGrader:
    """Agentic query grading and routing for improved RAG."""

    # Known procedures for classification
    KNOWN_PROCEDURES = [
        "picc", "picc line", "peripherally inserted central catheter",
        "central line", "cvc", "central venous catheter",
        "port", "port-a-cath", "portacath",
        "biopsy", "liver biopsy", "kidney biopsy", "renal biopsy",
        "drain", "drainage", "abscess drainage",
        "embolization", "embolisation",
        "angiography", "angiogram",
        "venogram", "venography",
        "fluoroscopy",
        "nephrostomy", "pcn",
        "gastrostomy", "g-tube", "peg",
        "jejunostomy", "j-tube",
        "tunneled catheter", "hickman", "broviac",
        "sclerotherapy",
        "stent", "stenting",
        "thrombolysis",
        "transfusion",
        "injection", "joint injection",
    ]

    QUERY_CLASSIFICATION_PROMPT = """You are a query classifier for a pediatric interventional radiology chatbot.

Classify this query into one of these types:
- "procedural": About specific IR procedures (PICC lines, biopsies, drains, etc.)
- "general": General medical questions or IR department info
- "emergency": Signs of emergency (breathing problems, severe bleeding, chest pain)  
- "off_topic": Not related to pediatric IR or medical care
- "clarification": User asking for more details about previous answer

Query: {query}

Respond in JSON only:
{{
    "query_type": "procedural|general|emergency|off_topic|clarification",
    "confidence": 0.0-1.0,
    "detected_procedure": "procedure name or null",
    "reasoning": "brief explanation"
}}"""

    DOCUMENT_GRADING_PROMPT = """You are evaluating retrieved documents for answering a user query about pediatric interventional radiology.

Query: {query}

Retrieved Documents:
{documents}

For each document, rate its relevance (0-10) where:
- 0-3: Not relevant or contains wrong information
- 4-6: Partially relevant, some useful information
- 7-10: Highly relevant, directly answers the query

Respond in JSON only:
{{
    "document_grades": [
        {{"doc_index": 0, "relevance_score": 8, "reason": "Directly discusses PICC procedure steps", "is_useful": true}},
        ...
    ],
    "can_answer": true or false,
    "suggested_action": "answer|expand_search|reject|escalate|clarify",
    "reasoning": "Brief explanation of overall assessment"
}}"""

    def __init__(self, llm_provider: LLMProvider, min_relevance_score: float = 5.0):
        """
        Initialize the query grader.

        Args:
            llm_provider: LLM for grading decisions
            min_relevance_score: Minimum score (0-10) to consider document useful
        """
        self.llm = llm_provider
        self.min_relevance_score = min_relevance_score
        logger.info(f"Initialized QueryGrader with min_relevance_score={min_relevance_score}")

    def _extract_procedure_keywords(self, query: str) -> Optional[str]:
        """
        Extract procedure keywords from query using simple matching.

        Args:
            query: User query

        Returns:
            Detected procedure name or None
        """
        query_lower = query.lower()
        for procedure in self.KNOWN_PROCEDURES:
            if procedure in query_lower:
                return procedure
        return None

    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from LLM response, handling markdown code blocks.

        Args:
            response: LLM response string

        Returns:
            Parsed JSON dict or None
        """
        try:
            # Try direct parse first
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try finding JSON object in response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        logger.warning(f"Failed to parse JSON from response: {response[:200]}...")
        return None

    def grade_query(self, query: str, use_llm: bool = True) -> QueryClassification:
        """
        Classify the type of query and determine routing.

        Args:
            query: User query
            use_llm: Whether to use LLM for classification (False for fast path)

        Returns:
            QueryClassification with type and confidence
        """
        # Fast path: Check for keywords
        detected_procedure = self._extract_procedure_keywords(query)

        # Check for emergency keywords (always fast path)
        emergency_keywords = [
            'severe bleeding', "can't breathe", 'chest pain', 'allergic reaction',
            'emergency', 'ambulance', '999', 'unconscious',
            '不能呼吸', '嚴重出血', '胸痛', '過敏反應', '緊急'
        ]
        query_lower = query.lower()
        for keyword in emergency_keywords:
            if keyword in query_lower:
                return QueryClassification(
                    query_type=QueryType.EMERGENCY,
                    confidence=1.0,
                    reasoning=f"Emergency keyword detected: {keyword}"
                )

        if not use_llm:
            # Simple classification without LLM
            if detected_procedure:
                return QueryClassification(
                    query_type=QueryType.PROCEDURAL,
                    confidence=0.8,
                    detected_procedure=detected_procedure,
                    reasoning=f"Procedure keyword detected: {detected_procedure}"
                )
            else:
                return QueryClassification(
                    query_type=QueryType.GENERAL,
                    confidence=0.6,
                    reasoning="No specific procedure detected, treating as general"
                )

        # LLM classification
        try:
            prompt = self.QUERY_CLASSIFICATION_PROMPT.format(query=query)
            messages = [{"role": "user", "content": prompt}]
            response = self.llm.generate(messages, temperature=0.1)

            parsed = self._parse_json_response(response)
            if parsed:
                query_type = QueryType(parsed.get("query_type", "general"))
                return QueryClassification(
                    query_type=query_type,
                    confidence=float(parsed.get("confidence", 0.7)),
                    detected_procedure=parsed.get("detected_procedure") or detected_procedure,
                    reasoning=parsed.get("reasoning", "")
                )
        except Exception as e:
            logger.warning(f"LLM classification failed, using fallback: {e}")

        # Fallback to simple classification
        if detected_procedure:
            return QueryClassification(
                query_type=QueryType.PROCEDURAL,
                confidence=0.7,
                detected_procedure=detected_procedure,
                reasoning="Procedure detected via keyword matching"
            )
        return QueryClassification(
            query_type=QueryType.GENERAL,
            confidence=0.5,
            reasoning="Fallback to general classification"
        )

    def grade_documents(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        use_llm: bool = True
    ) -> GradingResult:
        """
        Grade retrieved documents for relevance and decide if we can answer.

        Args:
            query: User query
            documents: List of retrieved documents with 'content' and 'metadata'
            use_llm: Whether to use LLM for grading

        Returns:
            GradingResult with grades and recommended action
        """
        if not documents:
            return GradingResult(
                document_grades=[],
                can_answer=False,
                suggested_action=SuggestedAction.EXPAND_SEARCH,
                reasoning="No documents retrieved",
                filtered_docs=[]
            )

        if not use_llm:
            # Use existing scores from retrieval
            grades = []
            filtered_docs = []
            for i, doc in enumerate(documents):
                score = doc.get('score', 0.5)
                # Convert 0-1 score to 0-10 scale
                relevance_score = score * 10
                is_useful = relevance_score >= self.min_relevance_score

                grades.append(DocumentGrade(
                    doc_index=i,
                    relevance_score=relevance_score,
                    reason=f"Retrieval score: {score:.3f}",
                    is_useful=is_useful
                ))

                if is_useful:
                    filtered_docs.append(doc)

            can_answer = len(filtered_docs) >= 1
            return GradingResult(
                document_grades=grades,
                can_answer=can_answer,
                suggested_action=SuggestedAction.ANSWER if can_answer else SuggestedAction.EXPAND_SEARCH,
                reasoning=f"Found {len(filtered_docs)} useful documents based on retrieval scores",
                filtered_docs=filtered_docs
            )

        # LLM grading
        try:
            # Format documents for prompt
            docs_text = ""
            for i, doc in enumerate(documents):
                content = doc.get('content', '')[:500]  # Truncate for prompt
                source = doc.get('metadata', {}).get('filename', 'Unknown')
                docs_text += f"\n[Doc {i}] (Source: {source})\n{content}\n"

            prompt = self.DOCUMENT_GRADING_PROMPT.format(
                query=query,
                documents=docs_text
            )
            messages = [{"role": "user", "content": prompt}]
            response = self.llm.generate(messages, temperature=0.1)

            parsed = self._parse_json_response(response)
            if parsed:
                grades = []
                filtered_docs = []

                for grade_data in parsed.get("document_grades", []):
                    idx = grade_data.get("doc_index", 0)
                    relevance = float(grade_data.get("relevance_score", 0))
                    is_useful = grade_data.get("is_useful", relevance >= self.min_relevance_score)

                    grades.append(DocumentGrade(
                        doc_index=idx,
                        relevance_score=relevance,
                        reason=grade_data.get("reason", ""),
                        is_useful=is_useful
                    ))

                    if is_useful and idx < len(documents):
                        filtered_docs.append(documents[idx])

                action_str = parsed.get("suggested_action", "answer")
                try:
                    action = SuggestedAction(action_str)
                except ValueError:
                    action = SuggestedAction.ANSWER

                return GradingResult(
                    document_grades=grades,
                    can_answer=parsed.get("can_answer", len(filtered_docs) > 0),
                    suggested_action=action,
                    reasoning=parsed.get("reasoning", ""),
                    filtered_docs=filtered_docs
                )

        except Exception as e:
            logger.warning(f"LLM grading failed, using fallback: {e}")

        # Fallback to score-based grading
        return self.grade_documents(query, documents, use_llm=False)

    def get_filter_for_query(self, classification: QueryClassification) -> Optional[Dict[str, Any]]:
        """
        Generate metadata filter based on query classification.

        Args:
            classification: Query classification result

        Returns:
            Filter dict for retrieval or None
        """
        if classification.detected_procedure:
            # Could filter by procedure type if metadata supports it
            # For now, return None as the current metadata doesn't have procedure field
            logger.debug(f"Detected procedure: {classification.detected_procedure}")
        return None
