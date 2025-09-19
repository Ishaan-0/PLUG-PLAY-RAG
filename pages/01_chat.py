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
    layout="wide"
)

# Custom CSS for chat interface
st.markdown("""
<style>
.chat-container {
    height: 60vh;
    overflow-y: auto;
    padding: 1rem;
    background: white;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
    margin-bottom: 1rem;
}

.user-message {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 0.75rem 1rem;
    border-radius: 18px 18px 4px 18px;
    margin: 0.5rem 0 0.5rem auto;
    max-width: 70%;
    word-wrap: break-word;
    text-align: right;
}

.assistant-message {
    background: #f8fafc;
    color: #1a202c;
    padding: 0.75rem 1rem;
    border-radius: 18px 18px 18px 4px;
    margin: 0.5rem auto 0.5rem 0;
    max-width: 70%;
    word-wrap: break-word;
    border: 1px solid #e2e8f0;
    text-align: left;
}

.collection-info {
    background: linear-gradient(90deg, #f0f9ff, #e0f2fe);
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #0ea5e9;
    margin-bottom: 1rem;
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
    st.error(f"❌ Database Error: {str(e)}")
    collections = []

# Initialize session state
if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = {}
if "current_collection" not in st.session_state:
    st.session_state.current_collection = None

# Header
st.title("💬 Chat Interface")
st.markdown("*Engage in intelligent conversations with your document collections*")

if not collections:
    st.warning("📝 No collections found. Create one first!")
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
            with st.spinner("🔄 Loading collection..."):
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
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    if not current_messages:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; color: #64748b;">
            <h4>👋 Ready to chat!</h4>
            <p>Ask me anything about your documents.</p>
        </div>
        """, unsafe_allow_html=True)
    
    for message in current_messages:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">💬 {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="assistant-message">🤖 {message["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input
    col1, col2 = st.columns([6, 1])
    with col1:
        user_input = st.text_input(
            "",
            key="user_input",
            placeholder="💭 Ask me anything about your documents...",
            label_visibility="collapsed"
        )
    with col2:
        send_clicked = st.button("Send", type="primary", disabled=not user_input.strip())
    
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
    
    # Chat management
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_histories[selected_collection] = []
            st.success("🧹 Chat history cleared!")
            st.rerun()
    
    with col2:
        if st.button("📊 View Collection Stats"):
            st.switch_page("pages/03_database_stats.py")

else:
    st.info("👆 Please select a collection to start chatting.")

# Navigation
st.markdown("---")
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
