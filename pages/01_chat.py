import streamlit as st
import requests
from database.vector_db import VectorDB, VectorManager
from rag_pipeline.create_rag import RAGPipeline
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

st.set_page_config(
    page_title="Chat Interface",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark mode chat interface styling
st.markdown("""
<style>
/* Hide default sidebar */
section[data-testid="stSidebar"] {
    display: none !important;
}

/* Global dark theme */
.stApp {
    background: #0f172a;
    color: #e2e8f0;
}

/* Remove all white backgrounds */
.main .block-container {
    background: transparent !important;
    padding-top: 2rem;
}

/* Navigation button styling */
.stButton > button {
    background: #1e293b !important;
    color: #e2e8f0 !important;
    border: 1px solid #334155 !important;
    padding: 0.5rem 1rem !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    background: #334155 !important;
    border-color: #3b82f6 !important;
    color: #f1f5f9 !important;
}

/* Message styling */
.user-message {
    background: #1e3a8a !important;
    color: white !important;
    padding: 1rem !important;
    border-radius: 12px 12px 4px 12px !important;
    margin: 0.5rem 0 0.5rem auto !important;
    max-width: 80% !important;
    box-shadow: 0 2px 8px rgba(30, 58, 138, 0.3) !important;
}

.assistant-message {
    background: #1e293b !important;
    color: #e2e8f0 !important;
    padding: 1rem !important;
    border-radius: 12px 12px 12px 4px !important;
    margin: 0.5rem auto 0.5rem 0 !important;
    max-width: 80% !important;
    border: 1px solid #334155 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
}

/* Selectbox styling */
.stSelectbox > div > div {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}

.stSelectbox > div > div > div {
    color: #e2e8f0 !important;
}

.stSelectbox label {
    color: #f1f5f9 !important;
}

/* Text area styling */
.stTextArea > div > div > textarea {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    font-size: 16px !important;
}

.stTextArea > div > div > textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 1px #3b82f6 !important;
}

.stTextArea label {
    color: #f1f5f9 !important;
    font-weight: 600 !important;
}

/* Collection info */
.collection-info {
    background: #064e3b !important;
    border: 1px solid #065f46 !important;
    border-radius: 8px !important;
    padding: 1rem !important;
    margin: 1rem 0 !important;
    color: #10b981 !important;
}

/* Form styling */
div[data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
}

/* Chat form button styling */
.stForm button[type="submit"] {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
    color: white !important;
    border: none !important;
    padding: 0.75rem 2rem !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

.stForm button[type="submit"]:hover {
    background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
    transform: translateY(-1px) !important;
}

/* Text color overrides */
h1, h2, h3, h4, h5, h6 {
    color: #f1f5f9 !important;
}

p {
    color: #cbd5e1 !important;
}

/* Warning and info styling */
div[data-testid="stAlert"] {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #e2e8f0 !important;
}

/* Spinner styling */
div[data-testid="stSpinner"] {
    color: #3b82f6 !important;
}
</style>
""", unsafe_allow_html=True)

def get_source_directory_for_collection(manager, collection_name):
    """Fetch the source_directory metadata for a collection."""
    try:
        collection = manager.vector_db._client.get_collection(name=collection_name)
        metadata = getattr(collection, "metadata", {})
        return metadata.get("source_directory")
    except Exception as e:
        st.error(f"Could not fetch source directory for collection '{collection_name}': {e}")
        return None

# Initialize database
try:
    vector_db = VectorDB(
        rag_dir=os.getenv("RAG_DIR"),
        persist_directory=os.getenv("PERSISTENT_DIR"),
        embeddings_model=os.getenv("EMBEDDINGS_MODEL"),
    )
    vector_manager = VectorManager(vector_db)
    collections = vector_manager.list_collections()
except Exception as e:
    st.error(f"Database Error: {str(e)}")
    collections = []

# Initialize session state
if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = {}
if "current_collection" not in st.session_state:
    st.session_state.current_collection = None

# Header
st.title("💬 Chat Interface")
st.markdown("*Engage in intelligent conversations with your document collections*")

# Navigation buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🏠 Home"):
        st.switch_page("main_streamlit.py")
with col2:
    if st.button("➕ Create Collection"):
        st.switch_page("pages/02_create_rag_folder.py")
with col3:
    if st.button("📊 Database Stats"):
        st.switch_page("pages/03_database_stats.py")

st.markdown("---")

if not collections:
    st.warning("📁 No collections found. Create one first!")
    if st.button("➕ Create Collection", type="primary"):
        st.switch_page("pages/02_create_rag_folder.py")
    st.stop()

# Collection Selection
selected_collection = st.selectbox(
    "📂 Select a Collection to Chat With:",
    [""] + collections,
    index=0,
    format_func=lambda x: "Choose a collection..." if x == "" else f"📄 {x}",
    key="collection_selector"
)

if selected_collection:
    st.session_state.current_collection = selected_collection
    
    # Display collection info
    st.markdown(f"""
    <div class="collection-info">
        <strong>📁 Active Collection:</strong> <code>{selected_collection}</code>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize chat history for current collection
    if selected_collection not in st.session_state.chat_histories:
        st.session_state.chat_histories[selected_collection] = []
    
    # Get RAG pipeline
    rag_pipeline = None
    source_dir = get_source_directory_for_collection(vector_manager, selected_collection)
    if source_dir:
        try:
            with st.spinner("📄 Loading collection..."):
                rag_pipeline = RAGPipeline(
                    rag_dir=source_dir,
                    persist_dir=os.getenv("PERSISTENT_DIR"),
                    embeddings_model=os.getenv("EMBEDDINGS_MODEL"),
                    llm_model=os.getenv("LLM_MODEL"),
                )
        except Exception as e:
            st.error(f"❌ Error loading collection: {str(e)}")
    
    # Chat interface
    current_messages = st.session_state.chat_histories[selected_collection]
    
    # Display chat history
    st.markdown("### 💬 Conversation")
    
    if not current_messages:
        st.info("👋 Ready to chat! Ask me anything about your documents.")
    
    # Create a container for messages
    chat_container = st.container()
    
    with chat_container:
        for i, message in enumerate(current_messages):
            if message["role"] == "user":
                st.markdown(f"""
                <div class="user-message">
                    <strong>You:</strong><br>
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="assistant-message">
                    <strong>Assistant:</strong><br>
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)
    
    # Chat input at the bottom
    st.markdown("### 💭 Ask a question:")
    
    # Use form for better UX
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Message",
            height=100,
            placeholder="Ask me anything about your documents...",
            key="user_input"
        )
        
        col1, col2 = st.columns([1, 5])
        with col1:
            send_clicked = st.form_submit_button("Send", disabled=not user_input.strip())
        with col2:
            if st.form_submit_button("🗑️ Clear Chat"):
                st.session_state.chat_histories[selected_collection] = []
                st.rerun()
    
    # Handle message sending
    if send_clicked and rag_pipeline and user_input.strip():
        # Add user message
        current_messages.append({"role": "user", "content": user_input})
        
        # Generate response
        with st.spinner("🤔 Thinking..."):
            try:
                response = rag_pipeline.ask_detailed(user_input)
                answer = response.get("answer", "I couldn't generate an answer.")
                current_messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                error_msg = f"❌ Sorry, I encountered an error: {str(e)}"
                current_messages.append({"role": "assistant", "content": error_msg})
        
        st.rerun()

else:
    st.info("👆 Please select a collection to start chatting.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; padding: 1rem; border-top: 1px solid #334155;">
    <strong>Universal RAG System</strong> • Built with Streamlit, Ollama & ChromaDB
</div>
""", unsafe_allow_html=True)