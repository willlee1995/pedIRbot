"""RAG pipeline implementation using LangGraph Agentic RAG."""
from typing import List, Dict, Any, Optional

from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from loguru import logger

<<<<<<< HEAD
from src.retriever import HybridRetriever
from src.llm import LLMProvider
from src.query_grader import QueryGrader, QueryType, SuggestedAction
from src.safety_guard import SafetyGuard, RiskLevel
=======
from src.agentic_rag import create_agentic_rag_graph
from src.vector_store import VectorStore
from src.retriever import AdvancedRetriever
from config import settings

# Import LangSmith traceable decorator
try:
    from langsmith import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    # Create a no-op decorator if LangSmith is not available
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
>>>>>>> 1aad27fcdfa1290f77fcf297c7601ea5fed7f3f2


class RAGPipeline:
    """RAG pipeline using LangGraph Agentic RAG for generating responses."""

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

<<<<<<< HEAD
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

    def __init__(self, retriever: HybridRetriever, llm_provider: LLMProvider, 
                 use_grader: bool = True, use_safety_guard: bool = True):
=======
    def __init__(
        self,
        vector_store: VectorStore,
        retriever: Optional[AdvancedRetriever] = None,
        graph: Optional[StateGraph] = None,
    ):
>>>>>>> 1aad27fcdfa1290f77fcf297c7601ea5fed7f3f2
        """
        Initialize the RAG pipeline using LangGraph.

        Args:
<<<<<<< HEAD
            retriever: HybridRetriever instance
            llm_provider: LLMProvider instance
            use_grader: Whether to use the query grader agent
            use_safety_guard: Whether to use the safety guardrail agent
=======
            vector_store: VectorStore instance
            retriever: AdvancedRetriever instance (optional, kept for compatibility)
            graph: Compiled LangGraph StateGraph (optional, will be created if not provided)
>>>>>>> 1aad27fcdfa1290f77fcf297c7601ea5fed7f3f2
        """
        self.vector_store = vector_store
        self.retriever = retriever
<<<<<<< HEAD
        self.llm = llm_provider
        self.use_grader = use_grader
        self.use_safety_guard = use_safety_guard
        
        # Initialize query grader if enabled
        if use_grader:
            self.query_grader = QueryGrader(llm_provider)
            logger.info("Initialized RAG pipeline with QueryGrader")
        else:
            self.query_grader = None
            logger.info("Initialized RAG pipeline without QueryGrader")
        
        # Initialize safety guard if enabled
        if use_safety_guard:
            self.safety_guard = SafetyGuard(llm_provider, use_llm_check=True)
            logger.info("Initialized RAG pipeline with SafetyGuard")
        else:
            self.safety_guard = None
            logger.info("Initialized RAG pipeline without SafetyGuard")
=======

        # Create LangGraph if not provided
        if graph is None:
            self.graph = create_agentic_rag_graph(vector_store)
        else:
            self.graph = graph

        logger.info("Initialized RAG pipeline with LangGraph Agentic RAG")
>>>>>>> 1aad27fcdfa1290f77fcf297c7601ea5fed7f3f2

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

    @traceable(name="rag_generate_response", metadata={"component": "rag_pipeline"})
    def generate_response(
        self,
        query: str,
        k: int = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        temperature: float = 0.1,
        include_sources: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a response using LangGraph Agentic RAG.

        Args:
            query: User query
            k: Number of documents to retrieve (not used, kept for compatibility)
            filter_dict: Optional metadata filter (not directly used, kept for compatibility)
            temperature: LLM temperature (not directly used, kept for compatibility)
            include_sources: Whether to include source documents in response

        Returns:
            Dict with 'response', 'sources', 'is_emergency', and 'total_time' keys
        """
        import time
        start_time = time.time()
        logger.info("=" * 80)
        logger.info(f"🔄 STARTING QUERY PROCESSING")
        logger.info(f"📝 Query: {query}")
        logger.info(f"⏰ Start Time: {time.strftime('%H:%M:%S', time.localtime(start_time))}")
        logger.info("=" * 80)

        # Safety Guard: Pre-query assessment
        safety_assessment = None
        if self.use_safety_guard and self.safety_guard:
            safety_assessment = self.safety_guard.assess_query(query)
            logger.info(f"Safety assessment: {safety_assessment.risk_level.value} (emergency: {safety_assessment.is_emergency})")
            
            # Handle critical emergencies from SafetyGuard
            if safety_assessment.is_emergency or safety_assessment.risk_level == RiskLevel.CRITICAL:
                logger.warning(f"SafetyGuard detected emergency: {safety_assessment.clinical_concerns}")
                return {
                    'response': self.safety_guard.get_emergency_response(query),
                    'sources': [],
                    'is_emergency': True,
                    'safety_assessment': {
                        'risk_level': safety_assessment.risk_level.value,
                        'concerns': safety_assessment.clinical_concerns
                    }
                }

        # Check for emergency keywords (fallback if SafetyGuard disabled)
        emergency_response = self._check_emergency(query)
        if emergency_response:
            end_time = time.time()
            total_time = end_time - start_time
            logger.info("=" * 80)
            logger.info(f"✅ QUERY COMPLETED (Emergency Response)")
            logger.info(f"⏱️  Total Time: {total_time:.2f} seconds")
            logger.info("=" * 80)
            return {
                'response': emergency_response,
                'sources': [],
                'is_emergency': True,
                'total_time': total_time,
            }

        # Use LangGraph to generate response
        try:
            logger.info("Invoking LangGraph agentic RAG...")

            # Run the graph
            result = self.graph.invoke({
                "messages": [HumanMessage(content=query)]
            })

            # Extract final response from messages
            messages = result.get("messages", [])
            response_text = ""
            sources = []

            # Log all messages in full detail for human observers
            logger.info("=" * 80)
            logger.info(f"📨 CONVERSATION MESSAGES ({len(messages)} total)")
            logger.info("=" * 80)

            for i, msg in enumerate(messages):
                logger.info(f"\n--- Message {i+1} ---")
                msg_type = type(msg).__name__

                if isinstance(msg, AIMessage):
                    logger.info(f"Type: {msg_type} (AI Response)")
                    # Show full content
                    if hasattr(msg, 'content') and msg.content:
                        logger.info(f"Content:\n{msg.content}")
                    else:
                        logger.info(f"Content: (empty)")

                    # Show tool calls with full details
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        logger.info(f"\nTool Calls ({len(msg.tool_calls)}):")
                        for j, tc in enumerate(msg.tool_calls, 1):
                            tool_name = tc.get('name', 'unknown')
                            tool_args = tc.get('args', {})
                            logger.info(f"  {j}. Tool: {tool_name}")
                            logger.info(f"     Arguments:")
                            for key, value in tool_args.items():
                                logger.info(f"       - {key}: {value}")

                elif isinstance(msg, ToolMessage):
                    tool_name = msg.name if hasattr(msg, 'name') else 'Unknown'
                    logger.info(f"Type: {msg_type} (Tool Result)")
                    logger.info(f"Tool: {tool_name}")
                    # Show full content
                    if hasattr(msg, 'content') and msg.content:
                        content = msg.content
                        # Show first 1000 chars if very long, otherwise full
                        if len(content) > 1000:
                            logger.info(f"Content (first 1000 chars):\n{content[:1000]}...")
                            logger.info(f"... ({len(content) - 1000} more characters)")
                        else:
                            logger.info(f"Content:\n{content}")
                    else:
                        logger.info(f"Content: (empty)")

                elif isinstance(msg, HumanMessage):
                    logger.info(f"Type: {msg_type} (User Query)")
                    # Show full content
                    if hasattr(msg, 'content') and msg.content:
                        logger.info(f"Content:\n{msg.content}")
                    else:
                        logger.info(f"Content: (empty)")

                elif isinstance(msg, dict):
                    msg_role = msg.get('role', 'unknown')
                    msg_type_name = msg.get('type', 'unknown')
                    logger.info(f"Type: dict (role={msg_role}, type={msg_type_name})")
                    content = str(msg.get('content', ''))
                    if len(content) > 1000:
                        logger.info(f"Content (first 1000 chars):\n{content[:1000]}...")
                    else:
                        logger.info(f"Content:\n{content}")
                else:
                    logger.info(f"Type: {msg_type}")
                    msg_str = str(msg)
                    if len(msg_str) > 500:
                        logger.info(f"Content (first 500 chars):\n{msg_str[:500]}...")
                    else:
                        logger.info(f"Content:\n{msg_str}")

            logger.info("=" * 80)

            # Find the final assistant message (AIMessage from LangChain)
            logger.debug(f"Total messages in result: {len(messages)}")
            for msg in reversed(messages):
                # Check for AIMessage instance (LangChain message object)
                if isinstance(msg, AIMessage):
                    response_text = msg.content if hasattr(msg, 'content') else str(msg)
                    logger.debug(f"Found AIMessage with content length: {len(response_text) if response_text else 0}")
                    break
                # Fallback: check for dict format
                elif isinstance(msg, dict):
                    if msg.get('role') == 'assistant' or 'type' in msg and msg.get('type') == 'ai':
                        response_text = msg.get('content', '')
                        logger.debug(f"Found assistant message in dict format")
                        break
                # Fallback: check for content attribute
                elif hasattr(msg, 'content'):
                    # Make sure it's not a HumanMessage or ToolMessage
                    if not isinstance(msg, (HumanMessage, ToolMessage)):
                        response_text = msg.content if hasattr(msg, 'content') else str(msg)
                        logger.debug(f"Found message with content attribute")
                        break

            # Extract sources from tool messages
            if include_sources:
                for msg in messages:
                    if isinstance(msg, ToolMessage):
                        tool_name = msg.name if hasattr(msg, 'name') else 'Unknown'
                        content = msg.content if hasattr(msg, 'content') else str(msg)
                        sources.append({
                            'tool': tool_name,
                            'content': content[:200] + '...' if len(content) > 200 else content
                        })
                    elif isinstance(msg, dict) and msg.get('role') == 'tool':
                        sources.append({
                            'tool': msg.get('name', 'Unknown'),
                            'content': msg.get('content', '')[:200] + '...' if len(msg.get('content', '')) > 200 else msg.get('content', '')
                        })
                    elif hasattr(msg, 'name') and msg.name:  # Tool message
                        sources.append({
                            'tool': msg.name,
                            'content': msg.content[:200] + '...' if len(msg.content) > 200 else msg.content
                        })

            if not response_text:
                logger.warning(f"Could not extract response from {len(messages)} messages")
                logger.debug(f"Message types: {[type(msg).__name__ for msg in messages]}")
                response_text = "I'm sorry, I couldn't generate a response."

            # Calculate total time
            end_time = time.time()
            total_time = end_time - start_time

            logger.info("=" * 80)
            logger.info(f"✅ QUERY COMPLETED")
            logger.info(f"📝 Original Query: {query}")
            logger.info(f"📤 Response Length: {len(response_text)} characters")
            logger.info(f"📚 Sources Used: {len(sources)}")
            logger.info(f"⏱️  Total Round Trip Time: {total_time:.2f} seconds")
            logger.info(f"⏰ End Time: {time.strftime('%H:%M:%S', time.localtime(end_time))}")
            logger.info("=" * 80)

            return {
                'response': response_text,
                'sources': sources,
                'is_emergency': False,
                'total_time': total_time,
            }

<<<<<<< HEAD
        # Use query grader if enabled
        if self.use_grader and self.query_grader:
            # Grade the query
            query_classification = self.query_grader.grade_query(query, use_llm=False)  # Fast path for now
            logger.info(f"Query classified as: {query_classification.query_type.value} (confidence: {query_classification.confidence:.2f})")
            
            # Grade retrieved documents
            grading_result = self.query_grader.grade_documents(query, retrieved_docs, use_llm=False)
            logger.info(f"Document grading: can_answer={grading_result.can_answer}, action={grading_result.suggested_action.value}")
            
            # Handle grading results
            if grading_result.suggested_action == SuggestedAction.EXPAND_SEARCH and not grading_result.can_answer:
                # Try expanding the search
                logger.info("Expanding search due to insufficient relevant documents")
                expanded_docs = self.retriever.retrieve(query, k=k*2, filter_dict=filter_dict)
                grading_result = self.query_grader.grade_documents(query, expanded_docs, use_llm=False)
                
                if grading_result.filtered_docs:
                    retrieved_docs = grading_result.filtered_docs
                    logger.info(f"Expanded search found {len(retrieved_docs)} useful documents")
            elif grading_result.filtered_docs:
                # Use filtered docs if we have them
                retrieved_docs = grading_result.filtered_docs
                logger.info(f"Using {len(retrieved_docs)} graded documents")
            
            if not grading_result.can_answer and not grading_result.filtered_docs:
                logger.warning("Query grader determined we cannot answer this query")
                return {
                    'response': "I'm sorry, I couldn't find sufficiently relevant information to answer that question confidently. It's a very good question, and I recommend you ask one of the nurses or your doctor. Would you like me to provide the contact number for the IR nurse coordinator?",
                    'sources': [],
                    'is_emergency': False
                }
        else:
            # Original filtering logic (fallback)
            MIN_RELEVANCE_SCORE = 0.4
            high_quality_docs = [doc for doc in retrieved_docs if doc.get('score', 0) >= MIN_RELEVANCE_SCORE]

            if not high_quality_docs:
                logger.warning(f"All retrieved documents below quality threshold ({MIN_RELEVANCE_SCORE})")
                logger.warning(f"Top score: {retrieved_docs[0].get('score', 0):.3f}")
                return {
                    'response': "I'm sorry, I couldn't find sufficiently relevant information to answer that question confidently. It's a very good question, and I recommend you ask one of the nurses or your doctor. Would you like me to provide the contact number for the IR nurse coordinator?",
                    'sources': [],
                    'is_emergency': False
                }

            retrieved_docs = high_quality_docs
            logger.info(f"Using {len(retrieved_docs)} high-quality documents (score >= {MIN_RELEVANCE_SCORE})")

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

        # Safety Guard: Post-response validation and warning injection
        if self.use_safety_guard and self.safety_guard and safety_assessment:
            # Validate the response (only check if it should be blocked)
            is_safe, _ = self.safety_guard.validate_response(query, response)
            
            if not is_safe:
                logger.warning("SafetyGuard blocked unsafe response")
                response = "I apologize, but I'm not able to provide specific advice for your situation. Please contact your medical team directly for guidance on this matter."
            
            # Add safety warnings based on risk level (from pre-query assessment)
            response = self.safety_guard.add_safety_wrapper(response, safety_assessment)

        # Prepare result
        result = {
            'response': response,
            'is_emergency': False
        }
        
        # Add safety info if available
        if safety_assessment:
            result['safety_assessment'] = {
                'risk_level': safety_assessment.risk_level.value,
                'concerns': safety_assessment.clinical_concerns
            }

        if include_sources:
            result['sources'] = [
                {
                    'content': doc['content'],  # Full content, not truncated
                    'source_org': doc['metadata'].get('source_org', 'Unknown'),
                    'filename': doc['metadata'].get('filename', 'Unknown'),
                    'procedure': doc['metadata'].get('procedure', 'Unknown'),
                    'question_category': doc['metadata'].get('question_category', 'Unknown'),
                    'answer_part': doc['metadata'].get('answer_part', 'Unknown'),
                    'is_qna': doc['metadata'].get('is_qna', False),
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
=======
        except Exception as e:
            end_time = time.time()
            total_time = end_time - start_time if 'start_time' in locals() else 0
            logger.error(f"Error generating response: {e}")
            logger.exception(e)
            logger.info("=" * 80)
            logger.info(f"❌ QUERY FAILED")
            logger.info(f"⏱️  Time Before Error: {total_time:.2f} seconds")
            logger.info("=" * 80)
            return {
                'response': "I'm sorry, I encountered an error while processing your question. Please try again or contact the IR nurse coordinator for assistance.",
                'sources': [],
                'is_emergency': False,
                'total_time': total_time,
            }

    def stream_response(
        self,
        query: str,
        k: int = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        temperature: float = 0.1,
    ):
>>>>>>> 1aad27fcdfa1290f77fcf297c7601ea5fed7f3f2
        """
        Generate a streaming response using LangGraph Agentic RAG.

        Args:
            query: User query
            k: Number of documents to retrieve (not used)
            filter_dict: Optional metadata filter
            temperature: LLM temperature (not directly used)

        Yields:
            Response chunks and metadata
        """
        logger.info(f"Processing streaming query: {query[:100]}...")

        # Check for emergency keywords
        emergency_response = self._check_emergency(query)
        if emergency_response:
            yield {'type': 'emergency', 'content': emergency_response}
            return

        # Use LangGraph streaming
        try:
            logger.info("Streaming LangGraph response...")
            for chunk in self.graph.stream({
                "messages": [HumanMessage(content=query)]
            }):
                # LangGraph returns chunks per node
                for node_name, node_output in chunk.items():
                    if node_name == "generate_answer":
                        # Final answer node
                        messages = node_output.get("messages", [])
                        for msg in messages:
                            if hasattr(msg, 'content'):
                                yield {'type': 'response', 'content': msg.content}
                    elif node_name == "retrieve":
                        # Retrieval node
                        yield {'type': 'tool_execution', 'content': f"Retrieving documents from {node_name}..."}
                    elif node_name == "generate_query_or_respond":
                        # Query generation node
                        yield {'type': 'agent_thinking', 'content': f"Thinking about query: {query[:50]}..."}
                    elif node_name == "rewrite_question":
                        # Question rewriting node
                        yield {'type': 'agent_thinking', 'content': "Rewriting question for better retrieval..."}

<<<<<<< HEAD
        if not retrieved_docs:
            logger.warning("No relevant documents retrieved")
            yield {'type': 'error', 'content': "No relevant information found"}
            return

        # Send sources first
        yield {
            'type': 'sources',
            'content': [
                {
                    'content': doc['content'],  # Full content
                    'source_org': doc['metadata'].get('source_org', 'Unknown'),
                    'filename': doc['metadata'].get('filename', 'Unknown'),
                    'procedure': doc['metadata'].get('procedure', 'Unknown'),
                    'question_category': doc['metadata'].get('question_category', 'Unknown'),
                    'answer_part': doc['metadata'].get('answer_part', 'Unknown'),
                    'is_qna': doc['metadata'].get('is_qna', False),
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
=======
        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            yield {'type': 'error', 'content': f"Error: {str(e)}"}
>>>>>>> 1aad27fcdfa1290f77fcf297c7601ea5fed7f3f2

        logger.info("Streaming completed")
