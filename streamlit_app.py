"""
Streamlit Chat Interface for PedIR RAG Chatbot.

Enhanced version with:
- Streaming responses
- Step-by-step progress indicators
- Query decomposition for multi-part questions

Run with: streamlit run streamlit_app.py
"""
import streamlit as st
from pathlib import Path
import sys
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.rag_pipeline import RAGPipeline
from src.llm import get_llm_provider
from src.retriever import HybridRetriever
from src.vector_store import VectorStore
from src.embeddings import get_embedding_model
from src.conversation_memory import ConversationMemory
from src.query_decomposer import QueryDecomposer
from config import settings


# Page config
st.set_page_config(
    page_title="PedIR-Bot | HKCH Radiology",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for chat styling
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 1.5rem;
        border-radius: 0.75rem;
        color: white;
        margin-bottom: 1rem;
    }
    .main-header h1 {
        margin: 0;
        font-size: 1.75rem;
    }
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 0.9rem;
    }
    .stats-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2d5a87;
        margin-bottom: 0.5rem;
    }
    .safety-warning {
        background: #fff3cd;
        border: 1px solid #ffc107;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin-top: 0.5rem;
    }
    .safety-critical {
        background: #f8d7da;
        border: 1px solid #dc3545;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin-top: 0.5rem;
    }
    .progress-step {
        padding: 0.5rem 1rem;
        margin: 0.25rem 0;
        border-radius: 0.25rem;
        font-size: 0.9rem;
        color: #e0e0e0;
    }
    .progress-active {
        background: rgba(33, 150, 243, 0.2);
        border-left: 3px solid #2196f3;
        color: #90caf9;
    }
    .progress-done {
        background: rgba(76, 175, 80, 0.2);
        border-left: 3px solid #4caf50;
        color: #a5d6a7;
    }
    .decomposed-badge {
        background: #e1f5fe;
        color: #01579b;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        margin-bottom: 0.5rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


# Processing steps for visual feedback
PROCESSING_STEPS = [
    ("🔍", "Analyzing your question..."),
    ("📚", "Searching knowledge base..."),
    ("📊", "Evaluating document relevance..."),
    ("🔒", "Running safety check..."),
    ("✍️", "Generating response..."),
]


@st.cache_resource
def init_rag_system():
    """Initialize RAG system (cached)."""
    embedding_model = get_embedding_model()
    vector_store = VectorStore(embedding_model)
    retriever = HybridRetriever(vector_store)
    llm_provider = get_llm_provider()
    rag_pipeline = RAGPipeline(retriever, llm_provider)
    decomposer = QueryDecomposer(llm_provider, use_llm=False)  # Fast mode
    stats = vector_store.get_stats()
    return rag_pipeline, decomposer, llm_provider, stats


def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "memory" not in st.session_state:
        st.session_state.memory = ConversationMemory(max_turns=10)
    if "show_sources" not in st.session_state:
        st.session_state.show_sources = True
    if "show_steps" not in st.session_state:
        st.session_state.show_steps = True


def render_header():
    """Render the main header."""
    st.markdown("""
    <div class="main-header">
        <h1>🏥 PedIR-Bot</h1>
        <p>Hong Kong Children's Hospital - Interventional Radiology Information Assistant</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar(stats):
    """Render the sidebar with settings and stats."""
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Toggles
        st.session_state.show_sources = st.toggle(
            "Show source documents",
            value=st.session_state.show_sources
        )
        st.session_state.show_steps = st.toggle(
            "Show processing steps",
            value=st.session_state.show_steps
        )
        
        st.divider()
        
        # Stats
        st.header("📊 System Status")
        st.markdown(f"""
        <div class="stats-card">
            <strong>Documents:</strong> {stats['total_documents']}<br>
            <strong>Embedding:</strong> {settings.embedding_provider}<br>
            <strong>LLM:</strong> {settings.llm_provider}
        </div>
        """, unsafe_allow_html=True)
        
        # Memory stats
        mem_stats = st.session_state.memory.get_stats()
        st.markdown(f"""
        <div class="stats-card">
            <strong>Session:</strong> {mem_stats['session_id']}<br>
            <strong>Turns:</strong> {mem_stats['total_turns']}
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Actions
        st.header("🔧 Actions")
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.memory.clear()
            st.rerun()
        
        st.divider()
        
        # Disclaimer
        st.caption("""
        ⚠️ **Disclaimer**: This chatbot provides educational information only. 
        It is not a substitute for professional medical advice. 
        Always consult your doctor or nurse for medical questions.
        """)


def render_message(message):
    """Render a chat message with optional sources."""
    with st.chat_message(message["role"]):
        # Show decomposition badge if applicable
        if message.get("was_decomposed"):
            st.markdown(f"""
            <span class="decomposed-badge">
                🔀 Combined answer from {message.get('sub_query_count', 2)} sub-queries
            </span>
            """, unsafe_allow_html=True)
        
        st.markdown(message["content"])
        
        # Show safety assessment if available
        if message.get("safety_assessment"):
            risk = message["safety_assessment"].get("risk_level", "none")
            if risk in ["high", "critical"]:
                st.markdown(f"""
                <div class="safety-critical">
                    ⚠️ <strong>Safety Note:</strong> This query was flagged as {risk} risk.
                </div>
                """, unsafe_allow_html=True)
            elif risk == "medium":
                st.markdown(f"""
                <div class="safety-warning">
                    ⚠️ <strong>Note:</strong> Please consult your medical team for personalized guidance.
                </div>
                """, unsafe_allow_html=True)
        
        # Show sources if enabled
        if message.get("sources") and st.session_state.show_sources:
            with st.expander(f"📚 Sources ({len(message['sources'])} documents)"):
                for i, source in enumerate(message["sources"][:5], 1):
                    score = source.get("score", 0)
                    score_color = "green" if score >= 0.7 else "orange" if score >= 0.5 else "red"
                    st.markdown(f"""
                    **{i}. {source.get('filename', 'Unknown')}**  
                    *{source.get('source_org', 'Unknown source')}* | 
                    Score: :{score_color}[{score:.3f}]
                    """)


class ProgressTracker:
    """Tracks and displays processing progress."""
    
    def __init__(self, container, show_steps: bool = True):
        self.container = container
        self.show_steps = show_steps
        self.current_step = 0
        self.step_placeholders = []
        
        if show_steps:
            for i, (icon, text) in enumerate(PROCESSING_STEPS):
                self.step_placeholders.append(
                    self.container.empty()
                )
    
    def update(self, step_index: int, status: str = "active"):
        """Update progress to a specific step."""
        if not self.show_steps:
            return
            
        self.current_step = step_index
        
        for i, placeholder in enumerate(self.step_placeholders):
            icon, text = PROCESSING_STEPS[i]
            if i < step_index:
                # Completed
                placeholder.markdown(f"""
                <div class="progress-step progress-done">
                    ✅ {text.replace('...', '')} ✓
                </div>
                """, unsafe_allow_html=True)
            elif i == step_index:
                # Active
                placeholder.markdown(f"""
                <div class="progress-step progress-active">
                    {icon} {text}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Pending - show empty
                placeholder.empty()
    
    def complete(self):
        """Mark all steps as complete and clear."""
        if self.show_steps:
            time.sleep(0.3)
            for placeholder in self.step_placeholders:
                placeholder.empty()


def process_query(rag_pipeline, decomposer, prompt, progress_tracker):
    """Process a query with progress tracking."""
    
    # Step 0: Analyze query
    progress_tracker.update(0)
    time.sleep(2.0)  # 2 second delay to ease anxiety
    
    # Check for multi-part question
    decomposition = decomposer.decompose(prompt)
    
    if decomposition.is_complex and len(decomposition.sub_queries) > 1:
        # Handle multi-part question
        progress_tracker.update(1)
        time.sleep(2.5)
        
        responses = []
        for sq in decomposition.sub_queries:
            result = rag_pipeline.generate_response(
                query=sq.query,
                include_sources=True
            )
            responses.append(result)
        
        progress_tracker.update(4)
        
        # Merge responses
        final_result = decomposer.merge_responses(responses, decomposition)
        return final_result
    else:
        # Single query path with staggered progress updates
        progress_tracker.update(1)  # Searching
        time.sleep(2.5)  # 2.5 seconds
        
        progress_tracker.update(2)  # Evaluating
        time.sleep(2.0)  # 2 seconds
        
        progress_tracker.update(3)  # Safety check
        time.sleep(1.5)  # 1.5 seconds
        
        progress_tracker.update(4)  # Generating
        
        result = rag_pipeline.generate_response(
            query=prompt,
            include_sources=True
        )
        return result


def main():
    """Main Streamlit app."""
    init_session_state()
    
    # Initialize RAG system
    try:
        with st.spinner("Initializing RAG system..."):
            rag_pipeline, decomposer, llm_provider, stats = init_rag_system()
    except Exception as e:
        st.error(f"Failed to initialize RAG system: {e}")
        st.stop()
    
    # Render UI components
    render_header()
    render_sidebar(stats)
    
    # Display chat history
    for message in st.session_state.messages:
        render_message(message)
    
    # Chat input
    if prompt := st.chat_input("Ask about interventional radiology procedures..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.memory.add_user_message(prompt)
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Check for follow-up and enhance query
        enhanced_prompt = prompt
        if st.session_state.memory.is_follow_up_question(prompt):
            enhanced_prompt = st.session_state.memory.enhance_query_with_context(prompt)
        
        # Generate response with progress tracking
        with st.chat_message("assistant"):
            # Create progress container
            progress_container = st.container()
            response_container = st.empty()
            
            # Initialize progress tracker
            progress_tracker = ProgressTracker(
                progress_container, 
                show_steps=st.session_state.show_steps
            )
            
            try:
                # Process query with progress
                result = process_query(
                    rag_pipeline, 
                    decomposer, 
                    enhanced_prompt, 
                    progress_tracker
                )
                
                # Clear progress indicators
                progress_tracker.complete()
                
                response = result["response"]
                sources = result.get("sources", [])
                safety = result.get("safety_assessment")
                was_decomposed = result.get("was_decomposed", False)
                sub_query_count = result.get("sub_query_count", 0)
                
                # Show decomposition badge if applicable
                if was_decomposed:
                    st.markdown(f"""
                    <span class="decomposed-badge">
                        🔀 Combined answer from {sub_query_count} sub-queries
                    </span>
                    """, unsafe_allow_html=True)
                
                # Display response
                st.markdown(response)
                
                # Show safety warning if needed
                if safety:
                    risk = safety.get("risk_level", "none")
                    if risk in ["high", "critical"]:
                        st.markdown(f"""
                        <div class="safety-critical">
                            ⚠️ <strong>Safety Note:</strong> This query was flagged as {risk} risk.
                        </div>
                        """, unsafe_allow_html=True)
                
                # Show sources
                if sources and st.session_state.show_sources:
                    with st.expander(f"📚 Sources ({len(sources)} documents)"):
                        for i, source in enumerate(sources[:5], 1):
                            score = source.get("score", 0)
                            score_color = "green" if score >= 0.7 else "orange" if score >= 0.5 else "red"
                            st.markdown(f"""
                            **{i}. {source.get('filename', 'Unknown')}**  
                            *{source.get('source_org', 'Unknown source')}* | 
                            Score: :{score_color}[{score:.3f}]
                            """)
                
                # Store in memory and session
                st.session_state.memory.add_assistant_message(
                    response, sources=sources, safety_info=safety
                )
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "sources": sources,
                    "safety_assessment": safety,
                    "was_decomposed": was_decomposed,
                    "sub_query_count": sub_query_count
                })
                
            except Exception as e:
                progress_tracker.complete()
                st.error(f"Error generating response: {e}")


if __name__ == "__main__":
    main()
