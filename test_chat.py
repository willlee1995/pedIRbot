"""Interactive chat interface for testing the RAG system."""
from src.rag_pipeline import RAGPipeline
from src.retriever import AdvancedRetriever
from src.vector_store import VectorStore
from src.embeddings import get_embedding_model
<<<<<<< HEAD
from src.conversation_memory import ConversationMemory
=======
from src.llm import get_langchain_llm
>>>>>>> 1aad27fcdfa1290f77fcf297c7601ea5fed7f3f2
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
<<<<<<< HEAD
        
        # Initialize conversation memory
        memory = ConversationMemory(max_turns=10)
        print(f"✓ Conversation memory initialized (session: {memory.session_id})")
=======
        print(f"✓ LangChain Agent initialized")
>>>>>>> 1aad27fcdfa1290f77fcf297c7601ea5fed7f3f2
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
    print("  'history' - Show conversation history")
    print("  'clear' - Clear conversation memory")
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

            if query.lower() == 'history':
                mem_stats = memory.get_stats()
                print(f"\n📝 Conversation History (Session: {mem_stats['session_id']})")
                print(f"   Total turns: {mem_stats['total_turns']}")
                if mem_stats['total_turns'] > 0:
                    print("   Recent exchanges:")
                    for turn in list(memory.history)[-6:]:
                        role_icon = "👤" if turn.role == "user" else "🤖"
                        content_preview = turn.content[:80] + "..." if len(turn.content) > 80 else turn.content
                        print(f"   {role_icon} {content_preview}")
                print()
                continue

            if query.lower() == 'clear':
                memory.clear()
                print("\n🗑️  Conversation memory cleared.")
                print()
                continue

            # Check if this is a follow-up question
            is_follow_up = memory.is_follow_up_question(query)
            if is_follow_up:
                enhanced_query = memory.enhance_query_with_context(query)
                if enhanced_query != query:
                    print(f"   (Detected follow-up question, adding context...)")
                    query = enhanced_query

            # Add user message to memory
            memory.add_user_message(query)

            # Generate response
            print("\nPedIR-Bot: ", end="", flush=True)

            # Trace the test chat query with LangSmith
            result = _process_test_query(rag_pipeline, query)

            print(result['response'])

<<<<<<< HEAD
            # Add assistant response to memory
            memory.add_assistant_message(
                result['response'],
                sources=result.get('sources'),
                safety_info=result.get('safety_assessment')
            )

            # Show sources
=======
            # Display total round trip time
            if 'total_time' in result:
                total_time = result['total_time']
                print(f"\n{'─'*60}")
                print(f"⏱️  Total Round Trip Time: {total_time:.2f} seconds")
                print(f"{'─'*60}")

            # Show sources (from agent intermediate steps)
>>>>>>> 1aad27fcdfa1290f77fcf297c7601ea5fed7f3f2
            if result.get('sources'):
                if show_details:
                    # Detailed view
                    print(f"\n{'='*60}")
                    print(f"📚 SOURCES USED BY AGENT ({len(result['sources'])} total)")
                    print(f"{'='*60}")

                    for i, source in enumerate(result['sources'], 1):
                        print(f"\n📄 Source {i}")
                        print(f"{'─'*60}")
<<<<<<< HEAD
                        print(f"File:     {source['filename']}")
                        print(f"Source:   {source['source_org']}")
                        print(f"Score:    {score:.4f} {score_indicator}")
                        print(f"Length:   {len(source.get('content', ''))} characters")

                        # Show chunk content preview
                        content = source.get('content', '')
                        if content:
                            preview_len = 10000
                            print(f"\nContent preview:")
                            if len(content) > preview_len:
                                print(f"{content[:preview_len]}...")
                            else:
                                print(content)
=======
                        if isinstance(source, dict):
                            tool_name = source.get('tool', 'Unknown')
                            output_preview = source.get('output', '')[:200]
                            print(f"Tool: {tool_name}")
                            print(f"Output preview: {output_preview}...")
                        else:
                            print(f"Source: {source}")
>>>>>>> 1aad27fcdfa1290f77fcf297c7601ea5fed7f3f2

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
