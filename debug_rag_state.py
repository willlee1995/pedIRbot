import sys
import os
from dotenv import load_dotenv

# Add project root to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from src.rag_pipeline import RAGPipeline
from src.vector_store import VectorStore
from src.embeddings import get_embedding_model
from src.conversation_memory import ConversationMemory
from loguru import logger

def debug_rag_pipeline():
    print("Initializing components...")
    embedding_model = get_embedding_model()
    vector_store = VectorStore(embedding_model=embedding_model)

    # Initialize RAG pipeline
    rag_pipeline = RAGPipeline(vector_store)

    # Initialize memory
    memory = ConversationMemory(max_turns=10)

    # Sequence of queries to reproduce the issue
    queries = [
        "What is PICC",
        "Can you further explain?",
        "What is a kidney biopsy"
    ]

    for i, query in enumerate(queries):
        print(f"\n\n{'='*50}")
        print(f"Round {i+1}: {query}")
        print(f"{'='*50}")

        # Check follow-up
        if memory.is_follow_up_question(query):
            enhanced_query = memory.enhance_query_with_context(query)
            if enhanced_query != query:
                print(f"Enhanced query: {enhanced_query}")
                query = enhanced_query

        memory.add_user_message(query)

        # Generate response
        result = rag_pipeline.generate_response(query=query, include_sources=True)
        response = result['response']

        print(f"\nResponse:\n{response}")

        # Extract sources for memory context
        # Extract sources for memory context.
        # Note: RAGPipeline returns source_documents as a list of dicts, NOT Document objects.
        source_docs = result.get('source_documents', [])

        # Extract filenames from source dicts
        memory_sources = []
        for doc in source_docs:
            if isinstance(doc, dict):
                memory_sources.append({"filename": doc.get('filename', 'unknown')})
            else:
                # Fallback if it is a Document object (unlikely with current pipeline)
                memory_sources.append({"filename": getattr(doc, 'metadata', {}).get('filename', 'unknown')})

        memory.add_assistant_message(response, sources=memory_sources)

if __name__ == "__main__":
    # Configure logger to show info
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    debug_rag_pipeline()
