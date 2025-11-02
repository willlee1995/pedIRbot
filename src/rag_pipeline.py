"""RAG pipeline implementation using LangGraph Agentic RAG."""
from typing import List, Dict, Any, Optional

from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from loguru import logger

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

        # Check for emergency keywords
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
