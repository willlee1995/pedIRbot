"""Interactive chat interface for testing the RAG system."""
from src.rag_pipeline import RAGPipeline
from src.llm import get_llm_provider
from src.retriever import HybridRetriever
from src.vector_store import VectorStore
from src.embeddings import get_embedding_model
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
        print()
    except Exception as e:
        print(f"✗ Error initializing RAG system: {e}")
        return

    # Interactive loop
    print("Chat interface ready! (Type 'quit' to exit, 'stats' for info)")
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

            # Generate response
            print("\nPedIR-Bot: ", end="", flush=True)

            result = rag_pipeline.generate_response(
                query=query,
                include_sources=True
            )

            print(result['response'])

            # Show sources
            if result.get('sources'):
                print(f"\n[Sources: {len(result['sources'])} documents]")
                for i, source in enumerate(result['sources'][:3], 1):
                    print(
                        f"  {i}. {source['source_org']} - {source['filename']} (score: {source['score']:.3f})")

            print()

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n✗ Error: {e}\n")
            continue


if __name__ == "__main__":
    main()
