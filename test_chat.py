"""Interactive chat interface for testing the RAG system."""
from src.rag_pipeline import RAGPipeline
from src.retriever import AdvancedRetriever
from src.vector_store import VectorStore
from src.embeddings import get_embedding_model
from src.llm import get_langchain_llm
from config import settings
from loguru import logger
import sys
from pathlib import Path

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

# Add current directory to path FIRST (before other imports)
sys.path.insert(0, str(Path(__file__).parent))

# isort: off  - Don't reorder imports below this line
# isort: on


@traceable(name="test_chat_query", metadata={"component": "test_chat", "interface": "interactive"})
def _process_test_query(rag_pipeline: RAGPipeline, query: str) -> dict:
    """
    Process a query from the test chat interface with LangSmith tracing.

    Args:
        rag_pipeline: RAGPipeline instance
        query: User query string

    Returns:
        Result dictionary with response and metadata
    """
    return rag_pipeline.generate_response(
        query=query,
        include_sources=True
    )


def main():
    """Run interactive chat interface."""
    print("=" * 60)
    print("PedIR RAG Chatbot - Interactive Testing Interface")
    print("=" * 60)
    print(f"Embedding Provider: {settings.embedding_provider}")
    print(f"LLM Provider: {settings.llm_provider}")
    print(f"Using LangChain Agent Architecture")
    print("=" * 60)
    print()

    # Parse command line args for verbose mode
    import argparse
    parser = argparse.ArgumentParser(description="Interactive RAG chat interface")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed document information")
    parser.add_argument("--agent-verbose", action="store_true", help="Show agent intermediate steps")
    args = parser.parse_args()

    show_details = args.verbose

    # Enable agent verbose mode if requested
    if args.agent_verbose:
        settings.agent_verbose = True

    # Initialize RAG system
    print("Initializing RAG system...")
    try:
        embedding_model = get_embedding_model()
        vector_store = VectorStore(embedding_model)

        # Initialize retriever (optional, for direct retrieval)
        retriever = AdvancedRetriever(vector_store, llm=get_langchain_llm())

        # Initialize RAG pipeline with agent
        rag_pipeline = RAGPipeline(vector_store, retriever=retriever)

        stats = vector_store.get_stats()
        print(f"✓ Vector store loaded: {stats['total_documents']} documents")
        print(f"✓ LangChain Agent initialized")
        print()
    except Exception as e:
        print(f"✗ Error initializing RAG system: {e}")
        logger.exception(e)
        return

    # Interactive loop
    print("Chat interface ready!")
    print("Commands:")
    print("  'quit' - Exit")
    print("  'stats' - Show vector store statistics")
    print("  'details' - Toggle detailed document display")
    print("  'verbose' - Same as 'details'")
    print("-" * 60)
    print()

    while True:
        try:
            # Get user input
            query = input("You: ").strip()

            if not query:
                continue

            # Handle special commands
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break

            if query.lower() == 'stats':
                stats = vector_store.get_stats()
                print(f"\nVector Store Stats:")
                print(f"  Collection: {stats['collection_name']}")
                print(f"  Documents: {stats['total_documents']}")
                print(f"  Directory: {stats['persist_directory']}")
                print()
                continue

            if query.lower() in ['details', 'verbose']:
                show_details = not show_details
                print(f"\nDetailed document display: {'ON ✅' if show_details else 'OFF ❌'}")
                print()
                continue

            # Generate response
            print("\nPedIR-Bot: ", end="", flush=True)

            # Trace the test chat query with LangSmith
            result = _process_test_query(rag_pipeline, query)

            print(result['response'])

            # Display total round trip time
            if 'total_time' in result:
                total_time = result['total_time']
                print(f"\n{'─'*60}")
                print(f"⏱️  Total Round Trip Time: {total_time:.2f} seconds")
                print(f"{'─'*60}")

            # Show sources (from agent intermediate steps)
            if result.get('sources'):
                if show_details:
                    # Detailed view
                    print(f"\n{'='*60}")
                    print(f"📚 SOURCES USED BY AGENT ({len(result['sources'])} total)")
                    print(f"{'='*60}")

                    for i, source in enumerate(result['sources'], 1):
                        print(f"\n📄 Source {i}")
                        print(f"{'─'*60}")
                        if isinstance(source, dict):
                            tool_name = source.get('tool', 'Unknown')
                            output_preview = source.get('output', '')[:200]
                            print(f"Tool: {tool_name}")
                            print(f"Output preview: {output_preview}...")
                        else:
                            print(f"Source: {source}")

                    print(f"\n{'='*60}")
                else:
                    # Compact view
                    print(f"\n[Sources: {len(result['sources'])} used by agent]")
                    for i, source in enumerate(result['sources'][:5], 1):
                        if isinstance(source, dict):
                            tool = source.get('tool', 'Unknown')
                            print(f"  {i}. Tool: {tool}")

            print()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}\n")
            logger.exception(e)
            continue


if __name__ == "__main__":
    main()
