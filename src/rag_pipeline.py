"""RAG pipeline implementation using LangGraph Agentic RAG."""
from typing import List, Dict, Any, Optional

from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from loguru import logger

from src.agentic_rag import create_agentic_rag_graph
from src.vector_store import VectorStore
from src.retriever import AdvancedRetriever


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

    def __init__(
        self,
        vector_store: VectorStore,
        retriever: Optional[AdvancedRetriever] = None,
        graph: Optional[StateGraph] = None,
    ):
        """
        Initialize the RAG pipeline using LangGraph.

        Args:
            vector_store: VectorStore instance
            retriever: AdvancedRetriever instance (optional, kept for compatibility)
            graph: Compiled LangGraph StateGraph (optional, will be created if not provided)
        """
        self.vector_store = vector_store
        self.retriever = retriever

        # Create LangGraph if not provided
        if graph is None:
            self.graph = create_agentic_rag_graph(vector_store)
        else:
            self.graph = graph

        logger.info("Initialized RAG pipeline with LangGraph Agentic RAG")

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
            Dict with 'response', 'sources', and 'is_emergency' keys
        """
        logger.info(f"Processing query: {query[:100]}...")

        # Check for emergency keywords
        emergency_response = self._check_emergency(query)
        if emergency_response:
            return {
                'response': emergency_response,
                'sources': [],
                'is_emergency': True,
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

            # Log all messages for debugging
            logger.info(f"Total messages in result: {len(messages)}")
            for i, msg in enumerate(messages):
                msg_type = type(msg).__name__
                if isinstance(msg, AIMessage):
                    content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                    logger.info(f"Message {i}: {msg_type} - Content: {content_preview}")
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        logger.info(f"  Tool calls: {[tc.get('name', 'unknown') for tc in msg.tool_calls]}")
                elif isinstance(msg, ToolMessage):
                    content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                    tool_name = msg.name if hasattr(msg, 'name') else 'Unknown'
                    logger.info(f"Message {i}: {msg_type} (Tool: {tool_name}) - Content: {content_preview}")
                elif isinstance(msg, HumanMessage):
                    content_preview = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                    logger.info(f"Message {i}: {msg_type} - Content: {content_preview}")
                elif isinstance(msg, dict):
                    msg_role = msg.get('role', 'unknown')
                    msg_type_name = msg.get('type', 'unknown')
                    content_preview = str(msg.get('content', ''))[:100]
                    logger.info(f"Message {i}: dict (role={msg_role}, type={msg_type_name}) - Content: {content_preview}")
                else:
                    logger.debug(f"Message {i}: {msg_type} - {str(msg)[:100]}")

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

            return {
                'response': response_text,
                'sources': sources,
                'is_emergency': False,
            }

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            logger.exception(e)
            return {
                'response': "I'm sorry, I encountered an error while processing your question. Please try again or contact the IR nurse coordinator for assistance.",
                'sources': [],
                'is_emergency': False,
            }

    def stream_response(
        self,
        query: str,
        k: int = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        temperature: float = 0.1,
    ):
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

        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            yield {'type': 'error', 'content': f"Error: {str(e)}"}

        logger.info("Streaming completed")
