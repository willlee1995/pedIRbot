"""LangChain tools for knowledge base querying using LEANN."""
from typing import List, Dict, Any, Optional

from langchain_core.tools import tool
from loguru import logger

from src.vector_store_leann import LEANNVectorStore
from config import settings

# Try to import create_retriever_tool from langchain_classic (LangChain 1.0 pattern)
try:
    from langchain_classic.tools.retriever import create_retriever_tool
    CREATE_RETRIEVER_TOOL_AVAILABLE = True
except ImportError:
    CREATE_RETRIEVER_TOOL_AVAILABLE = False
    logger.debug("langchain_classic.tools.retriever.create_retriever_tool not available")


@tool
def search_knowledge_base_leann(
    query: str,
    top_k: int = 5,
    source_org: Optional[str] = None,
    procedure_type: Optional[str] = None,
    region: Optional[str] = None,
    procedure_category: Optional[str] = None
) -> str:
    """
    Search the knowledge base using LEANN for relevant information about pediatric interventional radiology.

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
    logger.info(f"Searching LEANN knowledge base with query: {query[:100]}...")

    # This will be injected by the agent setup
    vector_store: Optional[LEANNVectorStore] = None

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
            logger.warning(f"⚠️  Document {i} is missing categorization metadata. Documents may need to be re-ingested with: python scripts/ingest_documents_leann.py KB/md --reset")

        formatted_results.append(
            f"[Document {i}] Source: {source_org} | Region: {region} | Category: {procedure_category} | {filename} (Relevance: {score:.3f})\n"
            f"{result['content'][:500]}...\n"
        )

    return "\n---\n".join(formatted_results)


@tool
def search_by_metadata_leann(
    query: str,
    source_org: str,
    top_k: int = 3
) -> str:
    """
    Search the LEANN knowledge base filtered by source organization.

    Args:
        query: The search query
        source_org: Source organization to filter by (HKCH, SickKids, SIR, HKSIR, CIRSE)
        top_k: Number of results to return

    Returns:
        Formatted string with retrieved documents from the specified source
    """
    logger.info(f"Searching {source_org} LEANN knowledge base for: {query[:100]}...")

    vector_store: Optional[LEANNVectorStore] = None

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


def get_knowledge_base_tools_leann(vector_store: LEANNVectorStore, retriever: Optional[Any] = None) -> List:
    """
    Get list of LangChain tools for knowledge base querying using LEANN.

    Args:
        vector_store: LEANNVectorStore instance to use for search
        retriever: Retriever instance (optional, for compatibility)

    Returns:
        List of LangChain tools
    """
    # Try to use create_retriever_tool from langchain_classic (LangChain 1.0 pattern)
    if CREATE_RETRIEVER_TOOL_AVAILABLE:
        try:
            # Create a simple retriever from LEANN vector store
            base_retriever = vector_store.as_retriever(
                search_kwargs={"k": settings.top_k_retrieval}
            )

            # Use create_retriever_tool if available
            retriever_tool = create_retriever_tool(
                base_retriever,
                "search_kb_leann",
                "[LEANN] Semantic search for information using LEANN vector index. Provides efficient storage and fast retrieval.",
            )
            logger.info("Created LEANN retriever tool using langchain_classic.create_retriever_tool")
            return [retriever_tool]
        except Exception as e:
            logger.warning(f"Failed to use create_retriever_tool: {e}, falling back to custom tool")
            logger.exception(e)

    # Fallback: Create custom tool with metadata filtering support
    def make_search_tool(vs: LEANNVectorStore):
        @tool
        def search_kb_leann(query: str, top_k: int = 5, source_org: Optional[str] = None, region: Optional[str] = None, procedure_category: Optional[str] = None) -> str:
            """Semantic search in the knowledge base using LEANN for relevant information.

            LEANN provides 97% storage savings while maintaining fast, accurate retrieval.

            Args:
                query: The search query text (semantic similarity search)
                top_k: Number of results to return (default: 5)
                source_org: Optional filter by source organization
                region: Optional filter by region
                procedure_category: Optional filter by procedure category
            """
            logger.info(f"🔍 Searching LEANN knowledge base with query: {query[:100]}...")

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

            # Use LEANN vector store search with filters
            try:
                results = vs.similarity_search(query=query, k=top_k, filter_dict=filter_dict)
            except Exception as e:
                logger.error(f"Error in LEANN vector store search: {e}")
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

        return search_kb_leann

    # Create tools with vector_store bound
    tools = [
        make_search_tool(vector_store),
    ]
    logger.info(f"Created {len(tools)} custom LEANN knowledge base tool(s)")

    return tools



