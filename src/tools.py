"""LangChain tools for knowledge base querying."""
from typing import List, Dict, Any, Optional

from langchain_core.tools import tool
from langchain_core.documents import Document
from loguru import logger

from src.vector_store import VectorStore
from src.retriever import AdvancedRetriever
from config import settings


@tool
def search_knowledge_base(
    query: str,
    top_k: int = 5,
    source_org: Optional[str] = None,
    procedure_type: Optional[str] = None
) -> str:
    """
    Search the knowledge base for relevant information about pediatric interventional radiology.

    Args:
        query: The search query
        top_k: Number of results to return (default: 5)
        source_org: Optional filter by source organization (HKCH, SickKids, SIR, HKSIR, CIRSE)
        procedure_type: Optional filter by procedure type

    Returns:
        Formatted string with retrieved documents and their sources
    """
    logger.info(f"Searching knowledge base with query: {query[:100]}...")

    # This will be injected by the agent setup
    vector_store: Optional[VectorStore] = None

    # Build filter dict
    filter_dict = {}
    if source_org:
        filter_dict['source_org'] = source_org
    if procedure_type:
        filter_dict['procedure_type'] = procedure_type

    # Perform search
    results = vector_store.similarity_search(
        query=query,
        k=top_k,
        filter_dict=filter_dict if filter_dict else None
    )

    if not results:
        return "No relevant information found in the knowledge base."

    # Format results
    formatted_results = []
    for i, result in enumerate(results, 1):
        source_org = result['metadata'].get('source_org', 'Unknown')
        filename = result['metadata'].get('filename', 'Unknown')
        score = result.get('score', 0)

        formatted_results.append(
            f"[Document {i}] Source: {source_org} - {filename} (Relevance: {score:.3f})\n"
            f"{result['content'][:500]}...\n"
        )

    return "\n---\n".join(formatted_results)


@tool
def search_by_metadata(
    query: str,
    source_org: str,
    top_k: int = 3
) -> str:
    """
    Search the knowledge base filtered by source organization.

    Args:
        query: The search query
        source_org: Source organization to filter by (HKCH, SickKids, SIR, HKSIR, CIRSE)
        top_k: Number of results to return

    Returns:
        Formatted string with retrieved documents from the specified source
    """
    logger.info(f"Searching {source_org} knowledge base for: {query[:100]}...")

    vector_store: Optional[VectorStore] = None

    results = vector_store.similarity_search(
        query=query,
        k=top_k,
        filter_dict={'source_org': source_org}
    )

    if not results:
        return f"No relevant information found from {source_org}."

    formatted_results = []
    for i, result in enumerate(results, 1):
        filename = result['metadata'].get('filename', 'Unknown')
        score = result.get('score', 0)

        formatted_results.append(
            f"[{source_org} Document {i}] {filename} (Relevance: {score:.3f})\n"
            f"{result['content'][:500]}...\n"
        )

    return "\n---\n".join(formatted_results)


def get_knowledge_base_tools(vector_store: VectorStore, retriever: Optional[AdvancedRetriever] = None) -> List:
    """
    Get list of LangChain tools for knowledge base querying.

    If retriever is provided, use it to ensure SelfQueryRetriever always runs.
    Otherwise, fall back to direct vector store search.

    Args:
        vector_store: VectorStore instance to use for search (fallback)
        retriever: AdvancedRetriever instance with SelfQueryRetriever (preferred)

    Returns:
        List of LangChain tools
    """
    # Inject retriever/vector_store into tool functions using closure
    def make_search_tool(vs: VectorStore, ret: Optional[AdvancedRetriever] = None):
        @tool
        def search_kb(query: str, top_k: int = 5, source_org: Optional[str] = None) -> str:
            """Search the knowledge base for relevant information about pediatric interventional radiology.

            This tool uses SelfQueryRetriever to structure queries with metadata filters.
            The query will be automatically parsed to extract:
            - procedure_type (e.g., PICC, angioplasty)
            - category (pre-operative, perioperative, post-operative, general)
            - related_procedures
            - keywords

            Args:
                query: The search query (will be structured automatically)
                top_k: Number of results to return (default: 5)
                source_org: Optional filter by source organization (HKCH, SickKids, SIR, HKSIR, CIRSE)
            """
            logger.info(f"Structuring query with SelfQueryRetriever: {query[:100]}...")

            # Use AdvancedRetriever if available (will use SelfQueryRetriever)
            if ret is not None:
                logger.info("Using AdvancedRetriever with SelfQueryRetriever for structured query")
                logger.info(f"🔍 Input Query: {query}")
                # Build filter dict for explicit filters (SelfQueryRetriever will handle query parsing)
                filter_dict = {'source_org': source_org} if source_org else None
                try:
                    results = ret.retrieve(query=query, k=top_k, filter_dict=filter_dict)
                except Exception as e:
                    logger.error(f"Error in AdvancedRetriever.retrieve: {e}")
                    logger.exception(e)
                    # Fallback to direct vector store search
                    logger.warning("Falling back to direct vector store search due to retriever error")
                    filter_dict = {'source_org': source_org} if source_org else None
                    results = vs.similarity_search(query=query, k=top_k, filter_dict=filter_dict)
            else:
                # Fallback to direct vector store search
                logger.warning("AdvancedRetriever not available, using direct vector store search")
                filter_dict = {'source_org': source_org} if source_org else None
                results = vs.similarity_search(query=query, k=top_k, filter_dict=filter_dict)

            if not results:
                return "No relevant information found in the knowledge base."

            formatted = []
            for i, r in enumerate(results, 1):
                org = r['metadata'].get('source_org', 'Unknown')
                filename = r['metadata'].get('filename', 'Unknown')
                score = r.get('score', 0)
                formatted.append(
                    f"[Document {i}] Source: {org} - {filename} (Relevance: {score:.3f})\n{r['content'][:500]}...\n"
                )
            return "\n---\n".join(formatted)

        return search_kb

    # Create tools with retriever/vector_store bound
    tools = [
        make_search_tool(vector_store, retriever),
    ]

    return tools

