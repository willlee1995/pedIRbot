"""LangGraph-based Agentic RAG implementation for Ollama."""
from typing import List, Dict, Any, Optional, Literal
import re

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from loguru import logger
from pydantic import BaseModel, Field

from src.llm import get_langchain_llm
from src.tools import get_knowledge_base_tools
from src.vector_store import VectorStore
from src.guardrails import EmergencyGuardrailMiddleware, SafetyCheckGuardrail, EMERGENCY_RESPONSE
from config import settings

import json
from langchain_core.tools import render_text_description

def _extract_json(text: str) -> Optional[Dict]:
    """Extract JSON object from text."""
    try:
        # Try to find JSON block
        match = re.search(r'```json\s*({.*?})\s*```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        
        # Try without code block
        match = re.search(r'({.*})', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
            
        return None
    except Exception:
        return None

def extract_text_from_content(content) -> str:
    """
    Extract text from content that can be a string or list of content blocks.

    Args:
        content: Message content (string or list of dicts)

    Returns:
        Extracted text string
    """
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # Handle structured content blocks (LangChain 1.0+)
        text_parts = []
        for block in content:
            if isinstance(block, dict):
                # Extract text from content blocks
                if block.get('type') == 'text':
                    text_parts.append(block.get('text', ''))
                elif 'text' in block:
                    text_parts.append(str(block['text']))
            elif isinstance(block, str):
                text_parts.append(block)
        return ' '.join(text_parts)
    else:
        # Fallback: convert to string
        return str(content)

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


class GradeDocuments(BaseModel):
    """Grade documents using a binary score for relevance check."""
    binary_score: str = Field(
        description="Relevance score: 'yes' if relevant, or 'no' if not relevant"
    )


# Prompts
GRADE_PROMPT = """Is the Document relevant to the Question?
Answer 'yes' or 'no'.

Document:
{context}

Question: {question}

Relevant (yes/no):"""

REWRITE_PROMPT = """Rewrite the Question to be specific keywords for search.
Original: {question}
Keywords:"""

GENERATE_PROMPT = """You are PediIR-Bot from Hong Kong Children's Hospital Radiology.
Answer the question based ONLY on the Context below.
If you don't know, say "I don't have that information. Please ask a nurse or doctor."
Do NOT give medical advice.
Answer in the SAME LANGUAGE as the Question (English or Traditional Chinese).

Question: {question}

Context: {context}

Ends with: "Please remember, this information is for educational purposes only and is not a substitute for professional medical advice. Always discuss any specific medical questions or concerns with your doctor or nurse."
(Chinese: "請記住，此資訊僅供教育目的，不能代替專業醫療建議。請務必與您的醫生或護士討論任何具體的醫療問題或疑慮。")"""




def create_agentic_rag_graph(
    vector_store: VectorStore,
    llm: Optional[BaseChatModel] = None,
    orchestrator_llm: Optional[BaseChatModel] = None,
    answer_llm: Optional[BaseChatModel] = None,
    grader_llm: Optional[BaseChatModel] = None,
    tools: Optional[List[BaseTool]] = None,
) -> StateGraph:
    """
    Create a LangGraph-based agentic RAG graph following the LangGraph tutorial pattern.

    Args:
        vector_store: VectorStore instance for knowledge base access
        llm: LangChain LLM instance (legacy, for backward compatibility)
        orchestrator_llm: LLM for orchestration (tool calling, query generation, rewriting) - default: qwen2.5:8b
        answer_llm: LLM for final answer generation (medical domain) - default: medgemma
        grader_llm: LLM for document grading (default: same as orchestrator_llm)
        tools: List of tools for the agent (default: knowledge base tools)

    Returns:
        Compiled StateGraph instance
    """
    # Get orchestrator LLM (for tool calling, query generation, rewriting)
    logger.info(f"DEBUG: create_agentic_rag_graph called. Settings provider: {settings.llm_provider}")
    if orchestrator_llm is None:
        # Use configured LLM provider
        orchestrator_llm = get_langchain_llm()
        logger.info(f"Using orchestrator LLM from provider: {settings.llm_provider}")

    # Get answer LLM (for final medical answer generation)
    if answer_llm is None:
        # Use configured LLM provider
        answer_llm = get_langchain_llm()
        logger.info(f"Using answer LLM from provider: {settings.llm_provider}")

    # Use orchestrator_llm for grading if not specified
    if grader_llm is None:
        grader_llm = orchestrator_llm

    # Legacy support: if llm is provided, use it as orchestrator
    if llm is not None and orchestrator_llm is None:
        orchestrator_llm = llm

    # Get tools if not provided
    # Follow LangChain 1.0 agentic RAG pattern: simple retriever tool + SQL tools
    # https://docs.langchain.com/oss/python/langgraph/agentic-rag
    # https://docs.langchain.com/oss/python/langgraph/sql-agent
    if tools is None:
        # Add SQL tools FIRST (higher priority/preference)
        from src.sql_tools import get_sql_tools
        sql_tools = get_sql_tools()

        # Create vector search tools (lower priority, fallback)
        kb_tools = get_knowledge_base_tools(vector_store, retriever=None)

        # Combine: SQL tools first (preferred), then vector search (fallback)
        tools = sql_tools + kb_tools
        logger.info(f"Initialized {len(sql_tools)} SQL tools (PREFERRED) + {len(kb_tools)} vector search tools (fallback) = {len(tools)} total tools")

    # Convert tools to retriever tool format if needed
    retriever_tool = tools[0] if tools else None

    # Initialize guardrails
    emergency_guardrail = EmergencyGuardrailMiddleware()
    safety_check = SafetyCheckGuardrail(llm=grader_llm)  # Use grader_llm for safety checks

    # Node 0: Emergency check (before agent processing)
    @traceable(name="emergency_check", run_type="chain", metadata={"node": "guardrail"})
    def check_emergency_node(state: MessagesState):
        """Check for emergency keywords before processing."""
        try:
            logger.info("=== Node: emergency_check ===")
            messages = state["messages"]

            # Extract user query
            query = ""
            for msg in messages:
                if isinstance(msg, HumanMessage) or (isinstance(msg, dict) and msg.get('role') == 'user'):
                    content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
                    query = extract_text_from_content(content)
                    break

            # Store emergency detection result in a message for routing
            if query:
                emergency_response = emergency_guardrail.check_emergency(query)
                if emergency_response:
                    logger.warning("🚨 Emergency detected, routing to emergency handler")
                    # Add a marker message to indicate emergency
                    # The routing function will check for this
                    return {"messages": messages + [AIMessage(content="__EMERGENCY_DETECTED__")]}

            logger.info("No emergency detected, continuing")
            return {"messages": messages}
        except Exception as e:
            logger.error(f"Error in emergency_check: {e}")
            logger.exception(e)
            # On error, continue processing
            return {"messages": state["messages"]}

    # Conditional routing function for emergency check
    def route_emergency(state: MessagesState) -> Literal["handle_emergency", "generate_query_or_respond"]:
        """Route based on emergency detection."""
        messages = state.get("messages", [])

        # Check if emergency marker is present
        for msg in messages:
            if isinstance(msg, AIMessage) and hasattr(msg, 'content'):
                # Handle both string and structured content
                content = msg.content
                if isinstance(content, str) and content == "__EMERGENCY_DETECTED__":
                    return "handle_emergency"
                elif isinstance(content, list):
                    # Check if any block contains the marker
                    for block in content:
                        if isinstance(block, dict) and block.get('text') == "__EMERGENCY_DETECTED__":
                            return "handle_emergency"

        return "generate_query_or_respond"

    # Node 0.5: Emergency response handler
    @traceable(name="handle_emergency", run_type="chain", metadata={"node": "guardrail"})
    def handle_emergency(state: MessagesState):
        """Return emergency response when emergency keywords detected."""
        messages = state["messages"]

        # Remove the emergency marker message (handle both string and structured content)
        def is_emergency_marker(msg):
            if not (isinstance(msg, AIMessage) and hasattr(msg, 'content')):
                return False
            content = msg.content
            if isinstance(content, str):
                return content == "__EMERGENCY_DETECTED__"
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get('text') == "__EMERGENCY_DETECTED__":
                        return True
            return False

        filtered_messages = [m for m in messages if not is_emergency_marker(m)]

        # Extract user query to detect language
        query = ""
        for msg in filtered_messages:
            if isinstance(msg, HumanMessage) or (isinstance(msg, dict) and msg.get('role') == 'user'):
                content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
                query = extract_text_from_content(content)
                break

        # Use emergency guardrail to get appropriate response
        emergency_response = emergency_guardrail.check_emergency(query)
        if emergency_response:
            logger.info("Returning emergency response")
            return {"messages": [AIMessage(content=emergency_response)]}
        else:
            # Fallback emergency response
            return {"messages": [AIMessage(content=EMERGENCY_RESPONSE)]}

    # Node 1: Generate query or respond (uses orchestrator_llm with tool calling)
    @traceable(name="generate_query_or_respond", run_type="chain", metadata={"node": "orchestrator"})
    def generate_query_or_respond(state: MessagesState):
        """Call the model to generate a response. It will decide to retrieve using tools or respond directly."""
        try:
            logger.info("=== Node: generate_query_or_respond ===")
            logger.info(f"State messages count: {len(state.get('messages', []))}")

            # Add system instruction to prefer SQL tools over semantic search
            messages = state["messages"]
            system_instruction = """TOOLS:
1. search_documents_sql(content='keywords') - SEARCH BY KEYWORD (Preferred)
2. search_kb(query='text') - Semantic Search (Fallback)

Use search_documents_sql first."""

            # Add system instruction as first message if not already present
            has_system_instruction = False
            for msg in messages:
                if isinstance(msg, SystemMessage) or (isinstance(msg, dict) and msg.get('role') == 'system'):
                    has_system_instruction = True
                    break

            if not has_system_instruction:
                messages_with_instruction = [SystemMessage(content=system_instruction)] + messages
            else:
                messages_with_instruction = messages

            # Bind tools to orchestrator LLM if supported
            if hasattr(orchestrator_llm, 'bind_tools'):
                try:
                    response = orchestrator_llm.bind_tools(tools).invoke(messages_with_instruction)
                    logger.info(f"Generated response (with tools): {type(response).__name__}")
                    if hasattr(response, 'content'):
                        logger.info(f"Response content preview: {response.content[:200]}...")
                    if hasattr(response, 'tool_calls') and response.tool_calls:
                        logger.info(f"Tool calls made: {len(response.tool_calls)}")
                        for tc in response.tool_calls:
                            logger.info(f"  - Tool: {tc.get('name', 'unknown')}, Args: {tc.get('args', {})}")
                    return {"messages": [response]}
                except Exception as e:
                    logger.warning(f"bind_tools failed: {e}, falling back to manual tool use")
                    
                    # Render tools description
                    tools_description = render_text_description(tools)
                    
                    tool_system_prompt = f"""Tools available:
{tools_description}

To use a tool, respond with ONLY this JSON format:
```json
{{
    "tool": "search_documents_sql",
    "arguments": {{
        "content": "keywords"
    }}
}}
```"""

                    # Invoke with manual prompt
                    # Add system instruction as last message to ensure it's seen
                    context_messages = messages_with_instruction + [SystemMessage(content=tool_system_prompt)]
                    response = orchestrator_llm.invoke(context_messages)
                    content = extract_text_from_content(response.content)
                    
                    # Parse for JSON
                    tool_call_json = _extract_json(content)
                    if tool_call_json and "tool" in tool_call_json:
                        # Create tool call ID
                        import uuid
                        call_id = f"call_{uuid.uuid4().hex[:8]}"
                        
                        logger.info(f"Manual tool call detected: {tool_call_json['tool']}")
                        
                        # Create AIMessage with tool_calls for LangGraph compatibility
                        ai_msg = AIMessage(
                            content="",
                            tool_calls=[{
                                "name": tool_call_json["tool"],
                                "args": tool_call_json.get("arguments", {}),
                                "id": call_id
                            }]
                        )
                        return {"messages": [ai_msg]}
                    
                    # No tool call found, return as normal response
                    return {"messages": [response]}
            else:
                # For models without bind_tools, use the same manual fallback logic
                logger.warning("Orchestrator LLM doesn't support bind_tools, using manual JSON format")
                
                # Render tools description
                tools_description = render_text_description(tools)
                
                tool_system_prompt = f"""You have access to the following tools:

{tools_description}

If you need to use a tool to fetch information, respond with a JSON object in the following format:
```json
{{
    "tool": "tool_name",
    "arguments": {{
        "arg_name": "value"
    }}
}}
```

If you do not need to use a tool, just respond with your answer text."""

                context_messages = messages_with_instruction + [SystemMessage(content=tool_system_prompt)]
                response = orchestrator_llm.invoke(context_messages)
                content = extract_text_from_content(response.content)
                
                # Parse for JSON
                tool_call_json = _extract_json(content)
                if tool_call_json and "tool" in tool_call_json:
                    import uuid
                    call_id = f"call_{uuid.uuid4().hex[:8]}"
                    logger.info(f"Manual tool call detected: {tool_call_json['tool']}")
                    ai_msg = AIMessage(
                        content="",
                        tool_calls=[{
                            "name": tool_call_json["tool"],
                            "args": tool_call_json.get("arguments", {}),
                            "id": call_id
                        }]
                    )
                    return {"messages": [ai_msg]}
                
                return {"messages": [response]}
        except Exception as e:
            logger.error(f"Error in generate_query_or_respond: {e}")
            logger.exception(e)
            # Fallback: just respond without tools
            messages = state["messages"]
            # Add system instruction if not present
            has_system = any(isinstance(msg, SystemMessage) or (isinstance(msg, dict) and msg.get('role') == 'system') for msg in messages)
            if not has_system:
                system_instruction = "PREFER using SQL tools (search_documents_sql) over semantic search (search_kb) for full document context."
                messages = [SystemMessage(content=system_instruction)] + messages
            response = orchestrator_llm.invoke(messages)
            return {"messages": [response]}

    # Node 2: Grade documents
    @traceable(name="grade_documents", run_type="chain", metadata={"node": "grader"})
    def grade_documents(state: MessagesState) -> Literal["generate_answer", "rewrite_question"]:
        """Determine whether the retrieved documents are relevant to the question."""
        try:
            logger.info("=== Node: grade_documents ===")
            messages = state["messages"]
            logger.info(f"State messages count: {len(messages)}")

            # Extract question from first human message
            question = ""
            for msg in messages:
                if isinstance(msg, HumanMessage) or (isinstance(msg, dict) and msg.get('role') == 'user'):
                    content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
                    question = extract_text_from_content(content)
                    logger.info(f"Extracted question: {question[:100]}...")
                    break

            # Get the last tool message (retrieved content)
            context = ""
            for msg in reversed(messages):
                if isinstance(msg, ToolMessage):
                    context = msg.content if hasattr(msg, 'content') else str(msg)
                    logger.info(f"Found ToolMessage context (length: {len(context)} chars)")
                    logger.info(f"ToolMessage name: {msg.name if hasattr(msg, 'name') else 'unknown'}")
                    logger.info(f"ToolMessage content preview: {context[:300]}...")
                    break
                elif isinstance(msg, dict) and msg.get('role') == 'tool':
                    context = msg.get('content', '')
                    logger.info(f"Found tool dict context (length: {len(context)} chars)")
                    break
                elif hasattr(msg, 'name') and msg.name:
                    context = msg.content if hasattr(msg, 'content') else str(msg)
                    logger.info(f"Found named message context (length: {len(context)} chars)")
                    break

            # Check rewrite count to prevent infinite loops
            rewrite_count = sum(1 for msg in messages if isinstance(msg, HumanMessage)) - 1
            if rewrite_count >= 2:
                logger.warning(f"Maximum rewrite attempts reached ({rewrite_count}), forcing generate_answer")
                return "generate_answer"

            if not context:
                logger.warning("No context found for grading, defaulting to generate_answer")
                return "generate_answer"

            # Enhance context with metadata for better grading
            # Extract filename and source info from context if available
            enhanced_context = context[:1500]  # Limit context length
            # Try to extract document title/filename from context string
            # Context format from tools.py: "[Document X] Source: {org} - {filename}..."
            filename_match = re.search(r'\[Document \d+\] Source: [^-]+ - ([^\n\(]+)', context)
            if filename_match:
                filename = filename_match.group(1).strip()
                enhanced_context = f"Document Title/Filename: {filename}\n\n" + enhanced_context
                logger.info(f"Extracted filename for grading: {filename}")

            prompt = GRADE_PROMPT.format(question=question, context=enhanced_context)
            logger.debug(f"Grading prompt length: {len(prompt)} chars")

            # Use structured output if available, otherwise parse manually
            if hasattr(grader_llm, 'with_structured_output'):
                try:
                    response = grader_llm.with_structured_output(GradeDocuments).invoke(
                        [HumanMessage(content=prompt)]
                    )
                    score = response.binary_score if hasattr(response, 'binary_score') else "yes"
                    logger.info(f"Structured output grade: {score}")
                except Exception as e:
                    logger.warning(f"Structured output failed, using fallback: {e}")
                    # Fallback: simple prompt
                    response = grader_llm.invoke([HumanMessage(content=prompt)])
                    content = response.content if hasattr(response, 'content') else str(response)
                    logger.info(f"Grader response: {content[:200]}...")
                    score = "yes" if "yes" in content.lower() else "no"
            else:
                # For Ollama, use simple prompt and parse
                response = grader_llm.invoke([HumanMessage(content=prompt)])
                content = response.content if hasattr(response, 'content') else str(response)
                logger.info(f"Grader response: {content[:200]}...")
                score = "yes" if "yes" in content.lower()[:50] else "no"

            logger.info(f"Document grade: {score}")
            logger.info(f"Routing to: {'generate_answer' if score == 'yes' else 'rewrite_question'}")
            return "generate_answer" if score == "yes" else "rewrite_question"
        except Exception as e:
            logger.error(f"Error in grade_documents: {e}")
            logger.exception(e)
            # Default to generate_answer on error
            return "generate_answer"

    # Node 3: Rewrite question
    @traceable(name="rewrite_question", run_type="chain", metadata={"node": "rewriter"})
    def rewrite_question(state: MessagesState):
        """Rewrite the original user question for better retrieval."""
        try:
            logger.info("=== Node: rewrite_question ===")
            messages = state["messages"]
            logger.info(f"State messages count: {len(messages)}")

            # Check if we've already rewritten too many times (prevent infinite loops)
            rewrite_count = sum(1 for msg in messages if isinstance(msg, HumanMessage)) - 1  # Subtract original question
            if rewrite_count >= 2:  # Max 2 rewrites
                logger.warning(f"Maximum rewrite attempts reached ({rewrite_count}), proceeding to generate answer")
                # Extract original question and go straight to answer generation
                original_question = ""
                for msg in messages:
                    if isinstance(msg, HumanMessage) or (isinstance(msg, dict) and msg.get('role') == 'user'):
                        content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
                        original_question = extract_text_from_content(content)
                        break
                # Return original question to proceed to answer generation (will be routed to generate_answer)
                return {"messages": [HumanMessage(content=original_question)]}

            # Extract original question
            question = ""
            for msg in messages:
                if isinstance(msg, HumanMessage) or (isinstance(msg, dict) and msg.get('role') == 'user'):
                    content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
                    question = extract_text_from_content(content)
                    logger.info(f"Original question: {question}")
                    break

            prompt = REWRITE_PROMPT.format(question=question)
            logger.debug(f"Rewrite prompt: {prompt[:200]}...")

            response = orchestrator_llm.invoke([HumanMessage(content=prompt)])
            logger.info(f"Rewrite response type: {type(response).__name__}")

            rewritten = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"Raw rewritten response: {rewritten[:200]}...")

            # Clean up the response - extract just the question text
            # Remove markdown formatting, explanations, rationales, etc.

            # Try to extract text in quotes first
            quoted_match = re.search(r'["\']([^"\']+)["\']', rewritten)
            if quoted_match:
                rewritten = quoted_match.group(1)
            else:
                # Remove markdown bold and other formatting
                rewritten = re.sub(r'\*\*([^*]+)\*\*', r'\1', rewritten)
                rewritten = re.sub(r'#+\s*', '', rewritten)
                rewritten = re.sub(r'^\s*[-*]\s*', '', rewritten, flags=re.MULTILINE)

                # Remove common prefixes/suffixes
                rewritten = re.sub(r'^(Improved Question|Question|Rewritten|Rewritten Question):\s*', '', rewritten, flags=re.IGNORECASE)
                rewritten = re.sub(r'\*\*Rationale:\*\*.*$', '', rewritten, flags=re.DOTALL | re.IGNORECASE)
                rewritten = re.sub(r'This version.*$', '', rewritten, flags=re.DOTALL | re.IGNORECASE)

                # Take first line or first sentence
                rewritten = rewritten.split('\n')[0].strip()
                rewritten = rewritten.split('.')[0].strip()

            # If still too long or contains explanations, try to extract just the question part
            if len(rewritten) > 200 or 'rationale' in rewritten.lower() or 'improved' in rewritten.lower():
                # Look for question marks - take the sentence with the question mark
                sentences = re.split(r'[.!?]', rewritten)
                for sent in sentences:
                    if '?' in sent:
                        rewritten = sent.strip()
                        break

            logger.info(f"Rewritten question: {rewritten}")

            # Log the rewritten question prominently
            logger.info("=" * 80)
            logger.info("🔄 QUESTION REWRITTEN:")
            logger.info(f"Original Question: {question}")
            logger.info(f"Rewritten Question: {rewritten}")
            logger.info("=" * 80)

            return {"messages": [HumanMessage(content=rewritten)]}
        except Exception as e:
            logger.error(f"Error in rewrite_question: {e}")
            # Return original question on error
            return {"messages": [m for m in state["messages"] if isinstance(m, HumanMessage)][:1]}

    # Node 4: Generate answer
    @traceable(name="generate_answer", run_type="chain", metadata={"node": "answer_generator"})
    def generate_answer(state: MessagesState):
        """Generate final answer based on retrieved context."""
        try:
            messages = state["messages"]

            # Extract question
            question = ""
            for msg in messages:
                if isinstance(msg, HumanMessage) or (isinstance(msg, dict) and msg.get('role') == 'user'):
                    content = msg.content if hasattr(msg, 'content') else msg.get('content', '')
                    question = extract_text_from_content(content)
                    break

            # Extract context from tool messages
            context_parts = []
            for msg in messages:
                if isinstance(msg, ToolMessage):
                    content = msg.content if hasattr(msg, 'content') else str(msg)
                    context_parts.append(content)
                elif isinstance(msg, dict) and msg.get('role') == 'tool':
                    context_parts.append(msg.get('content', ''))

            context = "\n\n".join(context_parts) if context_parts else ""
            logger.info(f"Total context length: {len(context)} chars")
            logger.info(f"Context preview: {context[:300]}...")
            logger.info(f"Generating answer for question: {question[:50]}...")
            logger.debug(f"Context length: {len(context)} chars")

            if not context:
                logger.warning("No context found, generating answer without context")
                context = "No specific context was retrieved."

            prompt = GENERATE_PROMPT.format(question=question, context=context[:4000])  # Limit context
            logger.debug(f"Generate prompt length: {len(prompt)} chars")

            response = answer_llm.invoke([HumanMessage(content=prompt)])
            logger.info(f"Answer response type: {type(response).__name__}")

            # Extract response content
            response_content = ""
            if isinstance(response, AIMessage):
                response_content = response.content
            elif hasattr(response, 'content'):
                response_content = response.content
            else:
                response_content = str(response)

            logger.info(f"Generated answer (length: {len(response_content)} chars)")
            logger.info(f"Answer preview: {response_content[:200]}...")

            # Post-agent safety check
            logger.info("=== Running post-agent safety check ===")
            is_safe, error_message = safety_check.check_safety(response_content, llm=grader_llm)

            if not is_safe:
                logger.warning("⚠️ Safety check failed, returning safety error message")
                return {"messages": [AIMessage(content=error_message or "I cannot provide that response. Please consult with your doctor or nurse.")]}

            logger.info("✅ Safety check passed")
            return {"messages": [AIMessage(content=response_content)]}
        except Exception as e:
            logger.error(f"Error in generate_answer: {e}")
            logger.exception(e)
            error_msg = "I'm sorry, I encountered an error while generating a response. Please try again."
            return {"messages": [AIMessage(content=error_msg)]}

    # Build the graph
    workflow = StateGraph(MessagesState)

    # Create ToolNode instance once
    tool_node = ToolNode(tools)

    # Node wrapper for tool execution with timing
    def retrieve_with_timing(state: MessagesState):
        """Wrapper around ToolNode that logs tool execution details and timing."""
        import time

        # Get messages that need tool execution
        messages = state.get("messages", [])

        # Find the last AIMessage with tool_calls
        tool_calls_info = []
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get('name', 'unknown')
                    tool_args = tool_call.get('args', {})
                    tool_calls_info.append((tool_name, tool_args))
                break  # Only process the most recent AIMessage with tool_calls

        # Log tool execution details before execution
        if tool_calls_info:
            logger.info("=" * 80)
            for tool_name, tool_args in tool_calls_info:
                logger.info(f"🔧 TOOL CALLED: {tool_name}")
                logger.info(f"📝 Query/Arguments:")
                for key, value in tool_args.items():
                    logger.info(f"   {key}: {value}")
                logger.info("-" * 80)

            # Time the tool execution
            start_time = time.time()

            # Execute the tool using ToolNode
            tool_result_state = tool_node.invoke(state)

            execution_time = time.time() - start_time

            logger.info(f"⏱️  Execution Time: {execution_time:.2f} seconds")
            logger.info("=" * 80)

            return tool_result_state

        # If no tool calls found, use standard ToolNode behavior
        return tool_node.invoke(state)

    # Add nodes
    workflow.add_node("check_emergency", check_emergency_node)
    workflow.add_node("handle_emergency", handle_emergency)
    workflow.add_node("generate_query_or_respond", generate_query_or_respond)
    workflow.add_node("retrieve", retrieve_with_timing)
    workflow.add_node("rewrite_question", rewrite_question)
    workflow.add_node("generate_answer", generate_answer)

    # Add edges - start with emergency check
    workflow.add_edge(START, "check_emergency")

    # Conditional edge: route to emergency handler or continue
    workflow.add_conditional_edges(
        "check_emergency",
        route_emergency,
        {
            "handle_emergency": "handle_emergency",
            "generate_query_or_respond": "generate_query_or_respond",
        },
    )

    # Emergency handler goes to END
    workflow.add_edge("handle_emergency", END)

    # Conditional edge: decide whether to retrieve or respond directly
    workflow.add_conditional_edges(
        "generate_query_or_respond",
        tools_condition,
        {
            "tools": "retrieve",
            END: END,
        },
    )

    # Conditional edge: grade documents and route accordingly
    workflow.add_conditional_edges(
        "retrieve",
        grade_documents,
        {
            "generate_answer": "generate_answer",
            "rewrite_question": "rewrite_question",
        },
    )

    workflow.add_edge("generate_answer", END)

    # Add edge from rewrite_question back to generate_query_or_respond, but limit loops
    workflow.add_edge("rewrite_question", "generate_query_or_respond")

    # Compile without checkpointer (not needed for simple RAG)
    graph = workflow.compile()
    logger.info("Agentic RAG graph compiled successfully")

    return graph

