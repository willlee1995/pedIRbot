"""LangGraph-based Agentic RAG implementation for Ollama."""
from typing import List, Dict, Any, Optional, Literal
import re

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from loguru import logger
from pydantic import BaseModel, Field

from src.llm import get_langchain_llm
from src.tools import get_knowledge_base_tools
from src.vector_store import VectorStore
from config import settings


class GradeDocuments(BaseModel):
    """Grade documents using a binary score for relevance check."""
    binary_score: str = Field(
        description="Relevance score: 'yes' if relevant, or 'no' if not relevant"
    )


# Prompts
GRADE_PROMPT = """You are a grader assessing relevance of a retrieved document to a user question.

CRITICAL: You must consider the QUESTION INTENT and TOPIC TYPE:
- Questions asking "what is", "explain", "tell me about", "describe" → Prefer OVERVIEW, INTRODUCTION, or GENERAL GUIDANCE documents
- Questions asking "how to", "procedure", "steps", "process" → Prefer PROCEDURE-SPECIFIC or INSTRUCTION documents
- Questions about insertion, placement, installation → Prefer INSERTION/PLACEMENT documents
- Questions about removal, withdrawal, extraction → Prefer REMOVAL/WITHDRAWAL documents
- Questions about complications, problems, issues → Prefer COMPLICATION or PROBLEM-SOLVING documents

Here is the retrieved document:

{context}

Here is the user question: {question}

ANALYSIS STEPS:
1. Identify the question type and intent (what is/explain vs how to/procedure vs specific action)
2. Identify the main topic/entity mentioned in the question (e.g., "PICC", "stent", "angioplasty")
3. Check if the document title/content matches the question intent:
   - If question asks "what is X" → Prefer documents about X insertion, X overview, X introduction, X basics
   - If question asks "how to remove X" → Prefer documents about X removal, X withdrawal
   - If question asks about X complications → Prefer documents about X complications, X problems
4. Check if the document contains information that directly answers the question type

Give a binary score 'yes' or 'no' to indicate whether the document is relevant to the question.
- Score 'yes' if the document matches the question intent AND topic
- Score 'no' if the document is about a different procedure type (e.g., removal when question asks about insertion/overview) or irrelevant topic

Examples:
- Question: "what is PICC" → Document about "PICC insertion" → YES (matches overview/introduction intent)
- Question: "what is PICC" → Document about "PICC removal" → NO (wrong procedure type for overview question)
- Question: "how to remove PICC" → Document about "PICC removal" → YES (matches procedure intent)
- Question: "what is angioplasty" → Document about "angioplasty procedure" → YES (matches overview intent)"""

REWRITE_PROMPT = """You are a question rewriter. Given the following user question, rewrite it to be more specific and clear for better retrieval.

Original question: {question}

IMPORTANT: Return ONLY the rewritten question text. Do not include any explanations, rationale, or formatting. Just return the improved question."""

GENERATE_PROMPT = """You are 'PediIR-Bot', a helpful and friendly AI assistant from the Hong Kong Children's Hospital Radiology department. Your purpose is to provide clear and simple information to patients and their families about pediatric interventional radiology procedures.

CRITICAL INSTRUCTIONS:
1. You MUST base your answer EXCLUSIVELY on the information provided in the retrieved context below.
2. Do not use any of your own internal knowledge or information from outside this context.
3. If the context does not contain the information needed to answer the question, you MUST respond with:
   "I'm sorry, I don't have the specific information to answer that question. It's a very good question, and I recommend you ask one of the nurses or your doctor. Would you like me to provide the contact number for the IR nurse coordinator?"
4. You are strictly forbidden from providing any form of medical advice, diagnosis, treatment recommendations, or interpretation of a patient's personal medical situation.
5. Your role is purely educational.
6. Your tone must always be empathetic, reassuring, and easy to understand.
7. Use simple language and avoid complex medical jargon.
8. The user may ask questions in English or Traditional Chinese. You must generate your response in the same language as the user's original query.

Question: {question}

Context: {context}

IMPORTANT DISCLAIMER:
Every response you provide must end with the following disclaimer:
"Please remember, this information is for educational purposes only and is not a substitute for professional medical advice. Always discuss any specific medical questions or concerns with your doctor or nurse."

(Chinese version: "請記住，此資訊僅供教育目的，不能代替專業醫療建議。請務必與您的醫生或護士討論任何具體的醫療問題或疑慮。")"""


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
    if orchestrator_llm is None:
        # Use qwen2.5:8b for orchestration (supports tool calling)
        orchestrator_llm = get_langchain_llm(
            provider="ollama",
            model=settings.ollama_orchestrator_model
        )
        logger.info(f"Using orchestrator LLM: {settings.ollama_orchestrator_model}")

    # Get answer LLM (for final medical answer generation)
    if answer_llm is None:
        # Use medgemma for final answers (medical domain fine-tuned)
        answer_llm = get_langchain_llm(
            provider="ollama",
            model=settings.ollama_chat_model  # medgemma
        )
        logger.info(f"Using answer LLM: {settings.ollama_chat_model}")

    # Use orchestrator_llm for grading if not specified
    if grader_llm is None:
        grader_llm = orchestrator_llm

    # Legacy support: if llm is provided, use it as orchestrator
    if llm is not None and orchestrator_llm is None:
        orchestrator_llm = llm

    # Get tools if not provided
    if tools is None:
        # Import retriever to pass to tools
        from src.retriever import AdvancedRetriever

        # Create retriever with LLM to ensure SelfQueryRetriever always runs
        retriever_llm = get_langchain_llm(provider="ollama", model=settings.ollama_orchestrator_model)
        retriever = AdvancedRetriever(vector_store, llm=retriever_llm)
        logger.info("Created AdvancedRetriever with SelfQueryRetriever for structured queries")

        # Pass retriever to tools so SelfQueryRetriever is always used
        tools = get_knowledge_base_tools(vector_store, retriever=retriever)
        logger.info(f"Initialized {len(tools)} tools for agent with SelfQueryRetriever")

    # Convert tools to retriever tool format if needed
    retriever_tool = tools[0] if tools else None

    # Node 1: Generate query or respond (uses orchestrator_llm with tool calling)
    def generate_query_or_respond(state: MessagesState):
        """Call the model to generate a response. It will decide to retrieve using tools or respond directly."""
        try:
            logger.info("=== Node: generate_query_or_respond ===")
            logger.info(f"State messages count: {len(state.get('messages', []))}")

            # Bind tools to orchestrator LLM if supported
            if hasattr(orchestrator_llm, 'bind_tools'):
                try:
                    response = orchestrator_llm.bind_tools(tools).invoke(state["messages"])
                    logger.info(f"Generated response (with tools): {type(response).__name__}")
                    if hasattr(response, 'content'):
                        logger.info(f"Response content preview: {response.content[:200]}...")
                    if hasattr(response, 'tool_calls') and response.tool_calls:
                        logger.info(f"Tool calls made: {len(response.tool_calls)}")
                        for tc in response.tool_calls:
                            logger.info(f"  - Tool: {tc.get('name', 'unknown')}, Args: {tc.get('args', {})}")
                    return {"messages": [response]}
                except Exception as e:
                    logger.warning(f"bind_tools failed: {e}, trying without tools")
                    # Fallback: try ReAct-style prompting
                    response = orchestrator_llm.invoke(state["messages"])
                    logger.info(f"Generated response (without tools): {type(response).__name__}")
                    if hasattr(response, 'content'):
                        logger.info(f"Response content preview: {response.content[:200]}...")
                    return {"messages": [response]}
            else:
                # For models without bind_tools, use ReAct-style prompting
                logger.warning("Orchestrator LLM doesn't support bind_tools, using ReAct-style")
                response = orchestrator_llm.invoke(state["messages"])
                logger.info(f"Generated response (ReAct-style): {type(response).__name__}")
                if hasattr(response, 'content'):
                    logger.info(f"Response content preview: {response.content[:200]}...")
                return {"messages": [response]}
        except Exception as e:
            logger.error(f"Error in generate_query_or_respond: {e}")
            logger.exception(e)
            # Fallback: just respond without tools
            response = orchestrator_llm.invoke(state["messages"])
            return {"messages": [response]}

    # Node 2: Grade documents
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
                    question = msg.content if hasattr(msg, 'content') else msg.get('content', '')
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
                        original_question = msg.content if hasattr(msg, 'content') else msg.get('content', '')
                        break
                # Return original question to proceed to answer generation (will be routed to generate_answer)
                return {"messages": [HumanMessage(content=original_question)]}

            # Extract original question
            question = ""
            for msg in messages:
                if isinstance(msg, HumanMessage) or (isinstance(msg, dict) and msg.get('role') == 'user'):
                    question = msg.content if hasattr(msg, 'content') else msg.get('content', '')
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
    def generate_answer(state: MessagesState):
        """Generate final answer based on retrieved context."""
        try:
            messages = state["messages"]

            # Extract question
            question = ""
            for msg in messages:
                if isinstance(msg, HumanMessage) or (isinstance(msg, dict) and msg.get('role') == 'user'):
                    question = msg.content if hasattr(msg, 'content') else msg.get('content', '')
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

            # Ensure response is an AIMessage
            if isinstance(response, AIMessage):
                logger.info(f"Generated answer (length: {len(response.content)} chars)")
                logger.info(f"Answer preview: {response.content[:200]}...")
                return {"messages": [response]}
            elif hasattr(response, 'content'):
                # Convert to AIMessage if needed
                ai_msg = AIMessage(content=response.content)
                logger.info(f"Generated answer (length: {len(ai_msg.content)} chars)")
                logger.info(f"Answer preview: {ai_msg.content[:200]}...")
                return {"messages": [ai_msg]}
            else:
                logger.warning(f"Unexpected response type: {type(response)}, converting to string")
                return {"messages": [AIMessage(content=str(response))]}
        except Exception as e:
            logger.error(f"Error in generate_answer: {e}")
            logger.exception(e)
            error_msg = "I'm sorry, I encountered an error while generating a response. Please try again."
            return {"messages": [AIMessage(content=error_msg)]}

    # Build the graph
    workflow = StateGraph(MessagesState)

    # Add nodes
    workflow.add_node("generate_query_or_respond", generate_query_or_respond)
    workflow.add_node("retrieve", ToolNode(tools))
    workflow.add_node("rewrite_question", rewrite_question)
    workflow.add_node("generate_answer", generate_answer)

    # Add edges
    workflow.add_edge(START, "generate_query_or_respond")

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

