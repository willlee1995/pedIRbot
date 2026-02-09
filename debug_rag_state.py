import sys
import os
import asyncio
from dotenv import load_dotenv

# Add project root to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from src.agentic_rag import create_agentic_rag_graph
from src.vector_store import VectorStore
from src.embeddings import get_embedding_model
from src.llm import get_langchain_llm
from langchain_core.messages import HumanMessage

def debug_rag():
    print("Initializing components...")
    embedding_model = get_embedding_model()
    vector_store = VectorStore(embedding_model=embedding_model)

    # Create graph
    rag_graph = create_agentic_rag_graph(
        vector_store=vector_store,
    )

    question = "what is picc"
    print(f"\nrunning query: {question}")

    # Invoke graph
    state = rag_graph.invoke({"messages": [HumanMessage(content=question)]})

    print("\n=== FINAL STATE MESSAGES ===")
    for i, msg in enumerate(state['messages']):
        print(f"\n[Message {i}] Type: {type(msg).__name__}")
        if hasattr(msg, 'name'):
            print(f"Name: {msg.name}")
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            print(f"Tool Calls: {msg.tool_calls}")

        content = msg.content
        print(f"Content (preview): {str(content)[:500]}...")

        # If it's a ToolMessage, let's see why regex might fail
        if type(msg).__name__ == 'ToolMessage':
            print("--- TOOL CONTENT DIUMP ---")
            print(content)
            print("--------------------------")

            # Test regex match
            import re
            # Regex from rag_pipeline.py
            doc_pattern = r'\[Document \d+\] Source: ([^|]+) \| Region: ([^|]+) \| Category: ([^|]+) \| ([^(]+) \(Relevance: ([\d.]+)\)'
            matches = re.findall(doc_pattern, str(content))
            print(f"Regex matches: {matches}")

    print("\n=== END DEBUG ===")

if __name__ == "__main__":
    debug_rag()
