"""RAG pipeline implementation with prompt engineering."""
from typing import List, Dict, Any, Optional
from loguru import logger

from src.retriever import HybridRetriever
from src.llm import LLMProvider


class RAGPipeline:
    """RAG pipeline for generating responses based on retrieved context."""

    # Emergency keywords that trigger canned responses
    EMERGENCY_KEYWORDS = [
        'severe bleeding', 'can\'t breathe', 'chest pain', 'allergic reaction',
        'emergency', 'urgent', 'ambulance', '999', 'unconscious',
        '不能呼吸', '嚴重出血', '胸痛', '過敏反應', '緊急'
    ]

    EMERGENCY_RESPONSE = """This sounds like it could be an emergency. Please do not rely on this chatbot.

**Call 999 or go to the nearest Accident & Emergency department immediately.**

If you have urgent questions about your procedure, please contact the HKCH IR nurse coordinator at [phone number].
"""

    EMERGENCY_RESPONSE_ZH = """這聽起來可能是緊急情況。請不要依賴此聊天機器人。

**請立即致電999或前往最近的急症室。**

如果您對手術有緊急疑問，請致電[電話號碼]聯絡香港兒童醫院介入放射科護士協調員。
"""

    # System prompt template
    SYSTEM_PROMPT = """You are 'PediIR-Bot', a helpful and friendly AI assistant from the Hong Kong Children's Hospital Radiology department. Your purpose is to provide clear and simple information to patients and their families about pediatric interventional radiology procedures.

CRITICAL INSTRUCTIONS:
1. You MUST base your answer EXCLUSIVELY on the information provided in the 'CONTEXT' section below.
2. Do not use any of your own internal knowledge or information from outside this context.
3. If the provided context does not contain the information needed to answer the question, you MUST respond with:
   "I'm sorry, I don't have the specific information to answer that question. It's a very good question, and I recommend you ask one of the nurses or your doctor. Would you like me to provide the contact number for the IR nurse coordinator?"
4. You are strictly forbidden from providing any form of medical advice, diagnosis, treatment recommendations, or interpretation of a patient's personal medical situation.
5. Your role is purely educational.
6. Your tone must always be empathetic, reassuring, and easy to understand.
7. Use simple language and avoid complex medical jargon.
8. The user may ask questions in English or Traditional Chinese. You must generate your response in the same language as the user's original query.

CONTEXT:
{context}

IMPORTANT DISCLAIMER:
Every response you provide must end with the following disclaimer:
"Please remember, this information is for educational purposes only and is not a substitute for professional medical advice. Always discuss any specific medical questions or concerns with your doctor or nurse."

(Chinese version: "請記住，此資訊僅供教育目的，不能代替專業醫療建議。請務必與您的醫生或護士討論任何具體的醫療問題或疑慮。")
"""

    def __init__(self, retriever: HybridRetriever, llm_provider: LLMProvider):
        """
        Initialize the RAG pipeline.

        Args:
            retriever: HybridRetriever instance
            llm_provider: LLMProvider instance
        """
        self.retriever = retriever
        self.llm = llm_provider
        logger.info("Initialized RAG pipeline")

    def _check_emergency(self, query: str) -> Optional[str]:
        """
        Check if query contains emergency keywords.

        Args:
            query: User query

        Returns:
            Emergency response if triggered, None otherwise
        """
        query_lower = query.lower()

        for keyword in self.EMERGENCY_KEYWORDS:
            if keyword in query_lower:
                logger.warning(f"Emergency keyword detected: {keyword}")
                # Detect language and return appropriate response
                if any(ord(char) > 127 for char in query):  # Contains non-ASCII (likely Chinese)
                    return self.EMERGENCY_RESPONSE_ZH
                else:
                    return self.EMERGENCY_RESPONSE

        return None

    def _format_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        """
        Format retrieved documents into context string.

        Args:
            retrieved_docs: List of retrieved documents with content and metadata

        Returns:
            Formatted context string
        """
        context_parts = []

        for i, doc in enumerate(retrieved_docs, 1):
            source_org = doc['metadata'].get('source_org', 'Unknown')
            filename = doc['metadata'].get('filename', 'Unknown')

            context_parts.append(
                f"[Document {i}] (Source: {source_org} - {filename})\n{doc['content']}\n"
            )

        return "\n---\n".join(context_parts)

    def generate_response(self,
                          query: str,
                          k: int = None,
                          filter_dict: Optional[Dict[str, Any]] = None,
                          temperature: float = 0.1,
                          include_sources: bool = True) -> Dict[str, Any]:
        """
        Generate a response using the RAG pipeline.

        Args:
            query: User query
            k: Number of documents to retrieve
            filter_dict: Optional metadata filter for retrieval
            temperature: LLM temperature
            include_sources: Whether to include source documents in response

        Returns:
            Dict with 'response', 'sources', and 'is_emergency' keys
        """
        logger.info(f"Processing query: {query[:100]}...")

        # Check for emergency keywords
        emergency_response = self._check_emergency(query)
        if emergency_response:
            return {
                'response': emergency_response,
                'sources': [],
                'is_emergency': True
            }

        # Retrieve relevant documents
        retrieved_docs = self.retriever.retrieve(
            query, k=k, filter_dict=filter_dict)

        if not retrieved_docs:
            logger.warning("No relevant documents retrieved")
            return {
                'response': "I'm sorry, I couldn't find any relevant information to answer your question. Please contact the IR nurse coordinator for assistance.",
                'sources': [],
                'is_emergency': False
            }

        # Format context
        context = self._format_context(retrieved_docs)

        # Build messages
        system_prompt = self.SYSTEM_PROMPT.format(context=context)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

        # Generate response
        logger.info("Generating LLM response...")
        response = self.llm.generate(messages, temperature=temperature)

        # Prepare result
        result = {
            'response': response,
            'is_emergency': False
        }

        if include_sources:
            result['sources'] = [
                {
                    # Truncate for brevity
                    'content': doc['content'][:200] + '...',
                    'source_org': doc['metadata'].get('source_org', 'Unknown'),
                    'filename': doc['metadata'].get('filename', 'Unknown'),
                    'score': doc['score']
                }
                for doc in retrieved_docs
            ]
        else:
            result['sources'] = []

        logger.info("Response generated successfully")
        return result

    def stream_response(self,
                        query: str,
                        k: int = None,
                        filter_dict: Optional[Dict[str, Any]] = None,
                        temperature: float = 0.1):
        """
        Generate a streaming response using the RAG pipeline.

        Args:
            query: User query
            k: Number of documents to retrieve
            filter_dict: Optional metadata filter for retrieval
            temperature: LLM temperature

        Yields:
            Response chunks and metadata
        """
        logger.info(f"Processing streaming query: {query[:100]}...")

        # Check for emergency keywords
        emergency_response = self._check_emergency(query)
        if emergency_response:
            yield {'type': 'emergency', 'content': emergency_response}
            return

        # Retrieve relevant documents
        retrieved_docs = self.retriever.retrieve(
            query, k=k, filter_dict=filter_dict)

        if not retrieved_docs:
            logger.warning("No relevant documents retrieved")
            yield {'type': 'error', 'content': "No relevant information found"}
            return

        # Send sources first
        yield {
            'type': 'sources',
            'content': [
                {
                    'source_org': doc['metadata'].get('source_org', 'Unknown'),
                    'filename': doc['metadata'].get('filename', 'Unknown'),
                    'score': doc['score']
                }
                for doc in retrieved_docs
            ]
        }

        # Format context and build messages
        context = self._format_context(retrieved_docs)
        system_prompt = self.SYSTEM_PROMPT.format(context=context)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

        # Stream response
        logger.info("Streaming LLM response...")
        for chunk in self.llm.stream_generate(messages, temperature=temperature):
            yield {'type': 'response', 'content': chunk}

        logger.info("Streaming completed")
