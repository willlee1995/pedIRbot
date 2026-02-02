"""Interactive chat interface for testing the RAG system."""
from src.rag_pipeline import RAGPipeline
from src.llm import get_llm_provider
from src.retriever import HybridRetriever
from src.vector_store import VectorStore
from src.embeddings import get_embedding_model
from src.conversation_memory import ConversationMemory
from config import settings
from loguru import logger
import sys
from pathlib import Path

# Add current directory to path FIRST (before other imports)
sys.path.insert(0, str(Path(__file__).parent))

# isort: off  - Don't reorder imports below this line
# isort: on


def main():
    """Run interactive chat interface."""
    print("=" * 60)
    print("PedIR RAG Chatbot - Interactive Testing Interface")
    print("=" * 60)
    print(f"Embedding Provider: {settings.embedding_provider}")
    print(f"LLM Provider: {settings.llm_provider}")
    print("=" * 60)
    print()

    # Parse command line args for verbose mode
    import argparse
    parser = argparse.ArgumentParser(description="Interactive RAG chat interface")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed document information")
    args = parser.parse_args()

    show_details = args.verbose

    # Initialize RAG system
    print("Initializing RAG system...")
    try:
        embedding_model = get_embedding_model()
        vector_store = VectorStore(embedding_model)
        retriever = HybridRetriever(vector_store)
        llm_provider = get_llm_provider()
        rag_pipeline = RAGPipeline(retriever, llm_provider)

        stats = vector_store.get_stats()
        print(f"✓ Vector store loaded: {stats['total_documents']} documents")
        
        # Initialize conversation memory
        memory = ConversationMemory(max_turns=10)
        print(f"✓ Conversation memory initialized (session: {memory.session_id})")
        print()
    except Exception as e:
        print(f"✗ Error initializing RAG system: {e}")
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

            result = rag_pipeline.generate_response(
                query=query,
                include_sources=True
            )

            print(result['response'])

            # Add assistant response to memory
            memory.add_assistant_message(
                result['response'],
                sources=result.get('sources'),
                safety_info=result.get('safety_assessment')
            )

            # Show sources
            if result.get('sources'):
                if show_details:
                    # Detailed view
                    print(f"\n{'='*60}")
                    print(f"📚 MATCHED DOCUMENTS ({len(result['sources'])} total)")
                    print(f"{'='*60}")

                    for i, source in enumerate(result['sources'], 1):
                        score = source.get('score', 0)

                        # Score indicator
                        if score >= 0.7:
                            score_indicator = "✅"
                        elif score >= 0.5:
                            score_indicator = "⚠️"
                        else:
                            score_indicator = "❌"

                        print(f"\n📄 Document {i} {score_indicator}")
                        print(f"{'─'*60}")
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

                    print(f"\n{'='*60}")
                else:
                    # Compact view
                    print(f"\n[Sources: {len(result['sources'])} documents]")
                    for i, source in enumerate(result['sources'][:5], 1):
                        score = source.get('score', 0)
                        score_icon = "✅" if score >= 0.7 else "⚠️" if score >= 0.5 else "❌"
                        print(f"  {i}. {source['source_org']} - {source['filename']} (score: {score:.3f}) {score_icon}")

            print()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}\n")
            continue


if __name__ == "__main__":
    main()
