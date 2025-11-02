"""LangChain tools for knowledge base querying."""
from typing import List, Dict, Any, Optional

from langchain_core.tools import tool
from langchain_core.documents import Document
from loguru import logger

from src.vector_store import VectorStore
from src.retriever import AdvancedRetriever
from config import settings

# Try to import create_retriever_tool from langchain_classic (LangChain 1.0 pattern)
try:
    from langchain_classic.tools.retriever import create_retriever_tool
    CREATE_RETRIEVER_TOOL_AVAILABLE = True
except ImportError:
    CREATE_RETRIEVER_TOOL_AVAILABLE = False
    logger.debug("langchain_classic.tools.retriever.create_retriever_tool not available")


@tool
def search_knowledge_base(
    query: str,
    top_k: int = 5,
    source_org: Optional[str] = None,
    procedure_type: Optional[str] = None,
    region: Optional[str] = None,
    procedure_category: Optional[str] = None
) -> str:
    """
    Search the knowledge base for relevant information about pediatric interventional radiology.

    Args:
        query: The search query
        top_k: Number of results to return (default: 5)
        source_org: Optional filter by source organization (HKCH, SickKids, SIR, HKSIR, CIRSE)
        procedure_type: Optional filter by procedure type
        region: Optional filter by region ('Hong Kong' or 'Non-Hong Kong')
        procedure_category: Optional filter by procedure category ('Venous Access', 'Angiogram Related', 'Embolization Related', 'Biopsy Related', 'Pain Injection Relief Related', 'Other')

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
    if region:
        filter_dict['region'] = region
    if procedure_category:
        filter_dict['procedure_category'] = procedure_category

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
        metadata = result.get('metadata', {})
        source_org = metadata.get('source_org', 'Unknown')
        filename = metadata.get('filename', 'Unknown')
        region = metadata.get('region', 'Not categorized')
        procedure_category = metadata.get('procedure_category', 'Not categorized')
        score = result.get('score', 0)

        # Log metadata for each document
        logger.info(f"📄 Document {i} Metadata:")
        logger.info(f"   Region: {region}")
        logger.info(f"   Procedure Category: {procedure_category}")
        logger.info(f"   Source Org: {source_org}")
        logger.info(f"   Filename: {filename}")
        logger.info(f"   Score: {score:.3f}")

        # Warn if metadata is missing (documents may need re-ingestion)
        if region == 'Not categorized' or procedure_category == 'Not categorized':
            logger.warning(f"⚠️  Document {i} is missing categorization metadata. Documents may need to be re-ingested with: python scripts/ingest_documents.py KB/md --reset")

        formatted_results.append(
            f"[Document {i}] Source: {source_org} | Region: {region} | Category: {procedure_category} | {filename} (Relevance: {score:.3f})\n"
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

    Follows LangChain 1.0 agentic RAG pattern from:
    https://docs.langchain.com/oss/python/langgraph/agentic-rag

    Args:
        vector_store: VectorStore instance to use for search
        retriever: AdvancedRetriever instance (optional, for compatibility)

    Returns:
        List of LangChain tools
    """
    # Try to use create_retriever_tool from langchain_classic (LangChain 1.0 pattern)
    if CREATE_RETRIEVER_TOOL_AVAILABLE:
        try:
            # Create a simple retriever from vector store (LangChain 1.0 pattern)
            base_retriever = vector_store.as_retriever(
                search_kwargs={"k": settings.top_k_retrieval}
            )

            # Use create_retriever_tool if available (simpler, follows tutorial)
            # Mark as fallback - prefer SQL tools
            retriever_tool = create_retriever_tool(
                base_retriever,
                "search_kb",
                "[FALLBACK] Semantic search for information. PREFER using SQL tools (search_documents_sql, get_document_by_id) for full document context. Only use this when you need semantic similarity search or don't know metadata filters.",
            )
            logger.info("Created retriever tool using langchain_classic.create_retriever_tool (marked as fallback)")
            return [retriever_tool]
        except Exception as e:
            logger.warning(f"Failed to use create_retriever_tool: {e}, falling back to custom tool")
            logger.exception(e)

    # Fallback: Create custom tool with metadata filtering support
    def make_search_tool(vs: VectorStore):
        @tool
        def search_kb(query: str, top_k: int = 5, source_org: Optional[str] = None, region: Optional[str] = None, procedure_category: Optional[str] = None) -> str:
            """[FALLBACK] Semantic search in the knowledge base for relevant information.

            **PREFER using SQL tools (search_documents_sql, get_document_by_id) instead** - they provide
            full document context without scattered information. Only use this tool when:
            1. You don't know specific metadata filters (source_org, region, category)
            2. You need to find documents by semantic similarity to natural language query
            3. SQL search didn't return relevant results

            This tool returns chunks (partial content). If you find relevant chunks, extract the document_id
            from metadata and use get_document_by_id() to fetch the full document for complete context.

            Args:
                query: The search query text (semantic similarity search)
                top_k: Number of results to return (default: 5)
                source_org: Optional filter by source organization
                region: Optional filter by region
                procedure_category: Optional filter by procedure category
            """
            logger.info(f"🔍 Searching knowledge base with query: {query[:100]}...")

            # Build filter dict for metadata filtering
            filter_dict = {}
            if source_org:
                filter_dict['source_org'] = source_org
                logger.info(f"📋 Filter by Source Org: {source_org}")
            if region:
                filter_dict['region'] = region
                logger.info(f"🌍 Filter by Region: {region}")
            if procedure_category:
                filter_dict['procedure_category'] = procedure_category
                logger.info(f"🏷️  Filter by Procedure Category: {procedure_category}")

            filter_dict = filter_dict if filter_dict else None
            if filter_dict:
                logger.info(f"📋 Active Filters: {filter_dict}")

            # Use direct vector store search with filters
            try:
                results = vs.similarity_search(query=query, k=top_k, filter_dict=filter_dict)
            except Exception as e:
                logger.error(f"Error in vector store search: {e}")
                logger.exception(e)
                return "Error searching the knowledge base. Please try again."

            if not results:
                return "No relevant information found in the knowledge base."

            formatted = []
            for i, r in enumerate(results, 1):
                metadata = r.get('metadata', {})
                org = metadata.get('source_org', 'Unknown')
                filename = metadata.get('filename', 'Unknown')
                region_val = metadata.get('region', 'Not categorized')
                procedure_category_val = metadata.get('procedure_category', 'Not categorized')
                score = r.get('score', 0)

                # Log metadata for each document
                logger.info(f"📄 Document {i} Metadata:")
                logger.info(f"   Region: {region_val}")
                logger.info(f"   Procedure Category: {procedure_category_val}")
                logger.info(f"   Source Org: {org}")
                logger.info(f"   Filename: {filename}")
                logger.info(f"   Score: {score:.3f}")

                # Warn if metadata is missing
                if region_val == 'Not categorized' or procedure_category_val == 'Not categorized':
                    logger.warning(f"⚠️  Document {i} is missing categorization metadata")

                formatted.append(
                    f"[Document {i}] Source: {org} | Region: {region_val} | Category: {procedure_category_val} | {filename} (Relevance: {score:.3f})\n{r['content'][:500]}...\n"
                )
            return "\n---\n".join(formatted)

        return search_kb

    # Create tools with vector_store bound
    tools = [
        make_search_tool(vector_store),
    ]
    logger.info(f"Created {len(tools)} custom knowledge base tool(s)")

    return tools

