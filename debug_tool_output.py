import sys
import os
import re
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from src.agentic_rag import create_agentic_rag_graph
from src.vector_store import VectorStore
from src.embeddings import get_embedding_model
from langchain_core.messages import HumanMessage, ToolMessage

def debug_tool_output():
    print("Initializing...")
    embedding_model = get_embedding_model()
    vector_store = VectorStore(embedding_model=embedding_model)
    rag_graph = create_agentic_rag_graph(vector_store=vector_store)

    state = rag_graph.invoke({"messages": [HumanMessage(content="what is picc")]})

    print("\n=== ANALYZING TOOL MESSAGES ===")
    for i, msg in enumerate(state['messages']):
        msg_type = type(msg).__name__
        print(f"\n[{i}] {msg_type}")

        if isinstance(msg, ToolMessage) or msg_type == 'ToolMessage':
            content = msg.content if hasattr(msg, 'content') else str(msg)
            print(f"Tool name: {getattr(msg, 'name', 'N/A')}")
            print(f"\n--- FULL TOOL OUTPUT ---")
            print(content[:2000])
            print("--- END ---")

            # Test regex
            doc_pattern = r'\[Document \d+\] Source: ([^|]+) \| Region: ([^|]+) \| Category: ([^|]+) \| ([^(]+) \(Relevance: ([\d.]+)\)'
            matches = re.findall(doc_pattern, content)
            print(f"\nRegex matches found: {len(matches)}")
            for j, m in enumerate(matches):
                print(f"  Match {j}: {m}")

if __name__ == "__main__":
    debug_tool_output()
