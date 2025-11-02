"""LangChain-based retrieval system with SelfQueryRetriever and Reranker."""
from typing import List, Dict, Any, Optional
import functools
from loguru import logger

# LangChain imports - ContextualCompressionRetriever location in LangChain 1.0+
try:
    # LangChain 1.0+ - try the main retrievers module first
    from langchain_community.retrievers.contextual_compression import ContextualCompressionRetriever
except ImportError:
    try:
        # Alternative path for LangChain 1.0
        from langchain.retrievers.contextual_compression import ContextualCompressionRetriever
    except ImportError:
        try:
            # LangChain 0.2.x path
            from langchain.retrievers import ContextualCompressionRetriever
        except ImportError:
            # If all imports fail, make it optional (expected in LangChain 1.0)
            logger.debug("ContextualCompressionRetriever not available. Reranking will be disabled.")
            ContextualCompressionRetriever = None

# SelfQueryRetriever imports - try multiple paths
try:
    # LangChain 1.0+ - try langchain_community first
    from langchain_community.retrievers.self_query.base import SelfQueryRetriever
except ImportError:
    try:
        from langchain_community.retrievers.self_query import SelfQueryRetriever
    except ImportError:
        try:
            # Try langchain.retrievers path
            from langchain.retrievers.self_query.base import SelfQueryRetriever
        except ImportError:
            # If all fail, make it optional (expected in LangChain 1.0 - not needed for agentic RAG pattern)
            logger.debug("SelfQueryRetriever not available. Using direct vector store search (LangChain 1.0 pattern).")
            SelfQueryRetriever = None
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from loguru import logger

from src.vector_store import VectorStore
from config import settings

# Try different import paths for CrossEncoderReranker
try:
    from langchain_community.cross_encoders import CrossEncoderReranker
except ImportError:
    try:
        from langchain_core.retrievers.document_compressors import CrossEncoderReranker
    except ImportError:
        try:
            from langchain.retrievers.document_compressors import CrossEncoderReranker
        except ImportError:
            logger.debug("CrossEncoderReranker not available, reranking will be disabled")
            CrossEncoderReranker = None

# Import custom Qwen3 reranker
try:
    from src.qwen3_reranker import Qwen3Reranker
    QWEN3_RERANKER_AVAILABLE = True
except ImportError as e:
    QWEN3_RERANKER_AVAILABLE = False
    logger.debug(f"Qwen3Reranker not available: {e}")
except Exception as e:
    QWEN3_RERANKER_AVAILABLE = False
    logger.warning(f"Qwen3Reranker import error: {e}")


class AdvancedRetriever:
    """Advanced retriever using LangChain SelfQueryRetriever and Reranker."""

    def __init__(
        self,
        vector_store: VectorStore,
        llm: Optional[BaseChatModel] = None,
        use_reranker: bool = None,
        reranker_model: str = None,
    ):
        """
        Initialize advanced retriever.

        Args:
            vector_store: VectorStore instance
            llm: LLM for SelfQueryRetriever (for query parsing)
            use_reranker: Whether to use reranker (default from settings)
            reranker_model: Reranker model name (default from settings)
        """
        self.vector_store = vector_store
        self.use_reranker = use_reranker if use_reranker is not None else settings.use_reranker
        self.reranker_model = reranker_model or settings.reranker_model

        # Get base retriever from vector store
        # In LangChain 1.0+, retrievers are created via as_retriever()
        try:
            base_retriever = vector_store.as_retriever(
                search_kwargs={"k": settings.reranker_top_k if self.use_reranker else settings.top_k_retrieval}
            )
        except Exception as e:
            logger.warning(f"Error creating retriever: {e}, will use direct vector store search")
            base_retriever = None

        # Setup SelfQueryRetriever if LLM is provided
        if llm:
            # Define metadata fields for filtering with enhanced structure
            metadata_field_info = [
                {
                    "name": "source_org",
                    "description": "The source organization (HKCH, SickKids, SIR, HKSIR, CIRSE)",
                    "type": "string",
                },
                {
                    "name": "filename",
                    "description": "The name of the source file",
                    "type": "string",
                },
                {
                    "name": "region",
                    "description": "The region: 'Hong Kong' (for HKCH and HKSIR sources) or 'Non-Hong Kong' (for other sources)",
                    "type": "string",
                },
                {
                    "name": "procedure_category",
                    "description": "The procedure category: 'Venous Access', 'Angiogram Related', 'Embolization Related', 'Biopsy Related', 'Pain Injection Relief Related', or 'Other'",
                    "type": "string",
                },
                {
                    "name": "procedure_type",
                    "description": "The type of procedure (PICC, angioplasty, stent, biopsy, drainage, ablation, etc.)",
                    "type": "string",
                },
                {
                    "name": "related_procedures",
                    "description": "List of related procedures mentioned in the document (e.g., ['PICC insertion', 'catheter placement'])",
                    "type": "list[string]",
                },
                {
                    "name": "category",
                    "description": "The phase of care: 'pre-operative' (before procedure), 'perioperative' (during procedure), 'post-operative' (after procedure), or 'general' (overview/general information)",
                    "type": "string",
                },
                {
                    "name": "keywords",
                    "description": "Important medical keywords or terms extracted from the document (e.g., ['insertion', 'removal', 'complications', 'care'])",
                    "type": "list[string]",
                },
            ]

            document_contents = "Information about pediatric interventional radiology procedures, including procedures, care instructions, complications, and patient education materials."

            if SelfQueryRetriever is None:
                logger.debug("SelfQueryRetriever not available. Using base retriever (LangChain 1.0 pattern).")
                self.retriever = base_retriever if base_retriever is not None else vector_store.vectorstore.as_retriever()
            else:
                try:
                    self.retriever = SelfQueryRetriever.from_llm(
                        llm=llm,
                        vectorstore=vector_store.vectorstore,
                        document_contents=document_contents,
                        metadata_field_info=metadata_field_info,
                        verbose=True,
                    )
                    logger.info("Initialized SelfQueryRetriever with enhanced metadata fields (related_procedures, category, keywords)")

                    # Store reference to SelfQueryRetriever before it might be wrapped
                    self_query_retriever = self.retriever

                    # Wrap the _get_relevant_documents method to log structured query
                    original_method = self_query_retriever._get_relevant_documents

                    @functools.wraps(original_method)
                    def wrapped_get_relevant_documents(query: str, *, run_manager=None):
                        """Wrapper to intercept and log structured query during retrieval."""
                        try:
                            # Access the query_constructor (which is a RunnableBinding)
                            query_constructor = self_query_retriever.query_constructor

                            # Prepare input for query_constructor (SelfQueryRetriever passes a dict with 'query')
                            input_data = {"query": query}

                            # Invoke query_constructor to get structured query
                            try:
                                structured_query = query_constructor.invoke(input_data)

                                # Log the structured query
                                logger.info("=" * 80)
                                logger.info("STRUCTURED QUERY OUTPUT:")
                                logger.info(f"Original Query: {query}")
                                logger.info(f"✅ Parsed Query Text: {structured_query.query if hasattr(structured_query, 'query') else 'N/A'}")
                                logger.info(f"✅ Metadata Filters: {structured_query.filter if hasattr(structured_query, 'filter') else 'N/A'}")
                                logger.info(f"✅ Limit: {structured_query.limit if hasattr(structured_query, 'limit') else 'N/A'}")

                                # Show filter details if available
                                if hasattr(structured_query, 'filter') and structured_query.filter:
                                    logger.info("Filter Details:")
                                    import json
                                    try:
                                        if hasattr(structured_query.filter, 'dict'):
                                            filter_dict = structured_query.filter.dict()
                                        elif hasattr(structured_query.filter, 'model_dump'):
                                            filter_dict = structured_query.filter.model_dump()
                                        elif hasattr(structured_query.filter, '__dict__'):
                                            filter_dict = structured_query.filter.__dict__
                                        else:
                                            filter_dict = structured_query.filter

                                        filter_str = json.dumps(filter_dict, indent=2, default=str)
                                        logger.info(filter_str)
                                    except Exception:
                                        logger.info(f"Filter (as string): {str(structured_query.filter)}")
                                else:
                                    logger.info("⚠️  No metadata filters extracted")
                                logger.info("=" * 80)
                            except Exception as e:
                                # If query construction fails, log warning but continue
                                logger.warning(f"Failed to log structured query: {e}")
                                logger.debug(f"Error type: {type(e).__name__}")

                            # Call the original method to perform actual retrieval
                            return original_method(query, run_manager=run_manager)
                        except Exception as e:
                            logger.error(f"Error in wrapped_get_relevant_documents: {e}")
                            logger.exception(e)
                            # Re-raise to let the original error handling work
                            raise

                    # Replace the method
                    self_query_retriever._get_relevant_documents = wrapped_get_relevant_documents

                    # Store reference to SelfQueryRetriever for use when wrapped in ContextualCompressionRetriever
                    self._self_query_retriever = self_query_retriever

                except Exception as e:
                    logger.warning(f"Failed to initialize SelfQueryRetriever: {e}. Using base retriever.")
                    logger.exception(e)
                    self.retriever = base_retriever if base_retriever is not None else vector_store.vectorstore.as_retriever()
        else:
            logger.info("No LLM provided, using base retriever without SelfQuery")
            self.retriever = base_retriever if base_retriever is not None else vector_store.vectorstore.as_retriever()

        # Setup reranker if enabled
        if self.use_reranker:
            reranker = None

            # Try Qwen3 reranker first (preferred)
            if QWEN3_RERANKER_AVAILABLE:
                try:
                    reranker = Qwen3Reranker(
                        model_name="Qwen/Qwen3-Reranker-0.6B",
                        top_n=settings.top_k_reranker,
                    )
                    logger.info("Initialized Qwen3 Reranker")
                except Exception as e:
                    logger.warning(f"Failed to initialize Qwen3 Reranker: {e}")
                    logger.exception(e)
                    # Note: CrossEncoderReranker requires BaseCrossEncoder instance, not a string
                    # So we skip it and just disable reranking if Qwen3 fails
                    reranker = None

            # Use reranker if successfully initialized
            if reranker is not None and ContextualCompressionRetriever is not None:
                try:
                    self.retriever = ContextualCompressionRetriever(
                        base_compressor=reranker,
                        base_retriever=self.retriever,
                    )
                    logger.info(f"Reranker enabled (top_n: {settings.top_k_reranker})")
                except Exception as e:
                    logger.warning(f"Failed to setup reranker: {e}. Using retriever without reranking.")
                    logger.exception(e)
                    self.use_reranker = False
            else:
                if ContextualCompressionRetriever is None:
                    logger.debug("ContextualCompressionRetriever not available, disabling reranking")
                else:
                    logger.debug("No reranker available, disabling reranking")
                self.use_reranker = False

        logger.info(f"Initialized AdvancedRetriever (reranker: {self.use_reranker})")

    def retrieve(
        self,
                 query: str,
                 k: int = None,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform retrieval with optional reranking.

        Args:
            query: Query text
            k: Number of results to return (default from settings)
            filter_dict: Optional metadata filter (used if SelfQueryRetriever not available)

        Returns:
            List of results with content, metadata, and scores
        """
        k = k or settings.top_k_retrieval

        logger.debug(f"Retrieving documents for query: {query[:50]}...")

        # Use LangChain retriever
        if filter_dict and (SelfQueryRetriever is None or not isinstance(self.retriever, SelfQueryRetriever)):
            # If filter_dict provided but not using SelfQueryRetriever, use direct search
            results = self.vector_store.similarity_search(
                query=query,
                k=k,
                filter_dict=filter_dict
            )
        else:
            # Use LangChain retriever
            # The structured query logging is now handled by the wrapper in __init__
            # Try get_relevant_documents first (LangChain < 1.0), then invoke (LangChain 1.0+)
            try:
                if hasattr(self.retriever, 'get_relevant_documents'):
                    docs = self.retriever.get_relevant_documents(query)
                elif hasattr(self.retriever, 'invoke'):
                    # LangChain 1.0+ uses invoke method
                    docs = self.retriever.invoke(query)
                else:
                    # Fallback: use vector store directly
                    logger.warning("Retriever doesn't have get_relevant_documents or invoke, using vector store directly")
                    results = self.vector_store.similarity_search(query=query, k=k, filter_dict=filter_dict)
                    return results
            except Exception as e:
                logger.warning(f"Error using retriever: {e}, falling back to direct vector store search")
                logger.exception(e)
                results = self.vector_store.similarity_search(query=query, k=k, filter_dict=filter_dict)
                return results

            # Convert LangChain Documents to our format
            results = []
            for doc in docs[:k]:
                # Extract score if available
                score = getattr(doc, 'score', None)
                if score is None:
                    score = 0.8  # Default score if not available

                results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': score,
                    'id': doc.metadata.get('chunk_id', doc.metadata.get('id', ''))
                })

        logger.info(f"Retrieved {len(results)} documents")
        return results

    def rebuild_index(self):
        """Rebuild the retriever index (placeholder for future implementation)."""
        logger.info("Rebuilding retriever index...")
        # Note: LangChain retrievers automatically use the updated vector store
        pass
