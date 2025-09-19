import streamlit as st
import requests
from database.vector_db import VectorDB, VectorManager
from rag_pipeline.create_rag import RAGPipeline
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

st.set_page_config(
    page_title="Universal RAG Chat", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------- Custom CSS for ChatGPT-like styling ----------------------
st.markdown("""
<style>
/* Main app styling */
.main > div {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Hide Streamlit menu and footer for cleaner look */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Sidebar styling */
.css-1d391kg {
    background-color: #f7f7f8;
    border-right: 1px solid #e5e7eb;
}

/* Custom sidebar sections */
.sidebar-section {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border: 1px solid #e5e7eb;
}

.sidebar-header {
    font-size: 1.1rem;
    font-weight: 600;
    color: #374151;
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #e5e7eb;
}

/* Button styling */
.stButton > button {
    background: linear-gradient(90deg, #10b981, #059669);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-weight: 500;
    transition: all 0.2s;
}

.stButton > button:hover {
    background: linear-gradient(90deg, #059669, #047857);
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

/* Input styling */
.stTextInput > div > div > input {
    border-radius: 6px;
    border: 1px solid #d1d5db;
    padding: 0.75rem;
}

.stSelectbox > div > div > div {
    border-radius: 6px;
}

/* Chat message styling improvements */
.stChatMessage {
    margin: 1rem 0;
}

.stChatMessage > div {
    background-color: transparent;
}

/* Status indicators */
.status-success { color: #10b981; font-weight: 500; }
.status-warning { color: #f59e0b; font-weight: 500; }
.status-error { color: #ef4444; font-weight: 500; }

/* Main title */
.main-title {
    text-align: center;
    color: #1f2937;
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.subtitle {
    text-align: center;
    color: #6b7280;
    font-size: 1.1rem;
    margin-bottom: 2rem;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 3rem 2rem;
    background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
    border-radius: 12px;
    border: 1px dashed #d1d5db;
    margin: 2rem 0;
}

.empty-state-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.empty-state-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #374151;
    margin-bottom: 0.5rem;
}

.empty-state-description {
    color: #6b7280;
    font-size: 0.95rem;
    line-height: 1.5;
}

/* Collection info card */
.collection-info {
    background: linear-gradient(90deg, #f0f9ff, #e0f2fe);
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
    border-left: 4px solid #0ea5e9;
    font-weight: 500;
}

/* Loading animation improvements */
.stSpinner > div {
    border-color: #10b981 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------- Helper Functions ----------------------
@st.cache_data(ttl=30)
def categorize_models():
    """Categorize models into LLMs and embedding models with caching"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        data = response.json()

        llms, embedding_models = [], []
        embedding_keywords = [
            "embed", "embedding", "mxbai-embed", "nomic-embed",
            "all-minilm", "arctic-embed", "snowflake-arctic-embed"
        ]

        for model in data["models"]:
            model_name = model["model"].lower()
            is_embedding = any(k in model_name for k in embedding_keywords)
            if is_embedding:
                embedding_models.append(model)
            else:
                llms.append(model)

        return [m["model"] for m in llms], [m["model"] for m in embedding_models]

    except Exception as e:
        st.sidebar.error(f"⚠️ Cannot connect to Ollama: {str(e)}")
        return [], []

def get_source_directory_for_collection(manager, collection_name):
    """Fetch the source_directory metadata for a collection."""
    try:
        collection = manager.vector_db._client.get_collection(name=collection_name)
        metadata = getattr(collection, "metadata", {})
        return metadata.get("source_directory")
    except Exception as e:
        st.error(f"Could not fetch source directory for collection '{collection_name}': {e}")
        return None

def slugify_path(path_str: str) -> str:
    """Convert path to a clean collection name"""
    p = Path(path_str).expanduser().resolve()
    parts = p.parts[-2:] if len(p.parts) >= 2 else p.parts[-1:]
    base = "_".join(parts)
    return "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in base).lower()

# ---------------------- Session State Initialization ----------------------
if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = {}
if "current_collection" not in st.session_state:
    st.session_state.current_collection = None
if "rag_pipelines" not in st.session_state:
    st.session_state.rag_pipelines = {}

# ---------------------- Sidebar ----------------------
with st.sidebar:
    st.markdown('<div class="sidebar-header">📁 Collections</div>', unsafe_allow_html=True)
    
    # Initialize database connection
    try:
        vector_db = VectorDB(
            rag_dir=os.getenv("RAG_DIR"),
            persist_directory=os.getenv("PERSISTENT_DIR"),
            embeddings_model=os.getenv("EMBEDDINGS_MODEL"),
        )
        vector_manager = VectorManager(vector_db)
        collections = vector_manager.list_collections()
        llms, embeddings = categorize_models()
        
        if not collections:
            st.info("📝 No collections yet. Create one below!")
        
    except Exception as e:
        st.error(f"❌ Database Error: {str(e)}")
        collections = []
    
    # Collection Selection
    selected_collection = st.selectbox(
        "Choose a collection:",
        ["-- None --"] + collections,
        index=0 if not st.session_state.current_collection else 
              (collections.index(st.session_state.current_collection) + 1 
               if st.session_state.current_collection in collections else 0),
        key="collection_selector"
    )
    
    # Update current collection
    if selected_collection != "-- None --" and selected_collection != st.session_state.current_collection:
        st.session_state.current_collection = selected_collection
        st.rerun()
    elif selected_collection == "-- None --":
        st.session_state.current_collection = None
    
    st.markdown("---")
    
    # Create New Collection Section
    st.markdown('<div class="sidebar-header">➕ Create New Collection</div>', unsafe_allow_html=True)
    
    with st.form("create_collection_form", clear_on_submit=False):
        folder_path = st.text_input(
            "📂 Document Folder Path",
            placeholder="e.g., /path/to/your/documents",
            help="Path to folder containing PDF, TXT, or DOCX files"
        )
        
        if llms and embeddings:
            col1, col2 = st.columns(2)
            with col1:
                selected_llm = st.selectbox("🤖 LLM", llms, index=0 if llms else None)
            with col2:
                selected_embedding = st.selectbox("🔗 Embedding", embeddings, index=0 if embeddings else None)
            
            create_button = st.form_submit_button("🚀 Create Collection", type="primary")
            
            if create_button and folder_path:
                folder_path_obj = Path(folder_path)
                
                if not folder_path_obj.exists():
                    st.error("📂 Folder doesn't exist!")
                elif not any(folder_path_obj.glob("*")):
                    st.warning("📄 Folder is empty!")
                else:
                    collection_name = slugify_path(folder_path)
                    
                    if collection_name in collections:
                        st.warning("⚠️ Collection already exists!")
                    else:
                        with st.spinner("🔄 Creating collection..."):
                            try:
                                rag_pipeline = RAGPipeline(
                                    rag_dir=folder_path,
                                    persist_dir=os.getenv("PERSISTENT_DIR"),
                                    embeddings_model=selected_embedding,
                                    llm_model=selected_llm,
                                )
                                
                                st.session_state.rag_pipelines[collection_name] = rag_pipeline
                                st.session_state.current_collection = collection_name
                                st.session_state.chat_histories[collection_name] = []
                                
                                st.success("✅ Collection created successfully!")
                                st.balloons()
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ No Ollama models found. Please install models first.")
            st.form_submit_button("🚀 Create Collection", disabled=True)
    
    # Collection Management
    if st.session_state.current_collection:
        st.markdown("---")
        st.markdown('<div class="sidebar-header">🛠️ Tools</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", help="Clear chat history"):
                if st.session_state.current_collection in st.session_state.chat_histories:
                    st.session_state.chat_histories[st.session_state.current_collection] = []
                st.success("🧹 Cleared!")
                st.rerun()
        
        with col2:
            if st.button("📊 Stats", help="View collection stats"):
                st.switch_page("pages/database_stats.py") 

# ---------------------- Main Chat Interface ----------------------

# Title
st.markdown('<h1 class="main-title">💬 Universal RAG Chat</h1>', unsafe_allow_html=True)

if not st.session_state.current_collection:
    # Empty State
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">🤖</div>
        <div class="empty-state-title">Welcome to Universal RAG Chat!</div>
        <div class="empty-state-description">
            Get started by selecting an existing collection or creating a new one from your documents.<br>
            I can help you chat with your PDFs, text files, and Word documents using advanced AI.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick start guide
    with st.expander("📖 Quick Start Guide", expanded=True):
        st.markdown("""
        **How to get started:**
        
        1. **📂 Prepare Documents**: Put your PDF, TXT, or DOCX files in a folder
        2. **➕ Create Collection**: Use the sidebar form to create a new collection  
        3. **💬 Start Chatting**: Ask questions about your documents!
        
        **Tips:**
        - Supported formats: PDF, TXT, DOCX
        - Each collection has separate chat history
        - Use descriptive folder names
        """)

else:
    # Show current collection
    st.markdown(f"""
    <div class="collection-info">
        <strong>📁 Current Collection:</strong> <code>{st.session_state.current_collection}</code>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize chat history for current collection
    if st.session_state.current_collection not in st.session_state.chat_histories:
        st.session_state.chat_histories[st.session_state.current_collection] = []
    
    # Get or create RAG pipeline
    rag_pipeline = None
    if st.session_state.current_collection in st.session_state.rag_pipelines:
        rag_pipeline = st.session_state.rag_pipelines[st.session_state.current_collection]
    else:
        # Load existing collection
        source_dir = get_source_directory_for_collection(vector_manager, st.session_state.current_collection)
        if source_dir:
            try:
                with st.spinner("🔄 Loading collection..."):
                    rag_pipeline = RAGPipeline(
                        rag_dir=source_dir,
                        persist_dir=os.getenv("PERSISTENT_DIR"),
                        embeddings_model=os.getenv("EMBEDDINGS_MODEL"),
                        llm_model=os.getenv("LLM_MODEL"),
                    )
                    st.session_state.rag_pipelines[st.session_state.current_collection] = rag_pipeline
            except Exception as e:
                st.error(f"❌ Error loading collection: {str(e)}")
        else:
            st.error("❌ Could not load collection directory.")
    
    # Display chat history using Streamlit's chat components
    current_messages = st.session_state.chat_histories[st.session_state.current_collection]
    
    if not current_messages:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; color: #6b7280;">
            <h3>👋 Ready to chat!</h3>
            <p>Ask me anything about your documents. I'll search through them to find relevant information.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Render chat messages using Streamlit's chat components
    for message in current_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input - this automatically clears after submission
    if prompt := st.chat_input("💭 Ask me anything about your documents..."):
        if rag_pipeline:
            # Add user message
            current_messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate AI response
            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking..."):
                    try:
                        response = rag_pipeline.ask_detailed(prompt)
                        
                        answer = response.get("answer", "I couldn't generate an answer.")
                        sources = response.get("source_documents", [])
                        
                        # Display answer
                        st.markdown(answer)
                        
                        # Show source info
                        if sources:
                            st.caption(f"📄 *Answer based on {len(sources)} source document(s)*")
                            
                            # Optional: Show sources in expander
                            with st.expander("🔍 View Sources", expanded=False):
                                for i, doc in enumerate(sources[:3]):  # Show top 3
                                    st.markdown(f"**Source {i+1}:**")
                                    content = doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content
                                    st.markdown(f"> {content}")
                                    if hasattr(doc, 'metadata') and doc.metadata:
                                        st.caption(f"📄 From: {doc.metadata.get('source', 'Unknown')}")
                                    if i < len(sources) - 1:
                                        st.divider()
                        
                        # Add assistant message to history
                        current_messages.append({"role": "assistant", "content": answer})
                        
                    except Exception as e:
                        error_msg = f"❌ Sorry, I encountered an error: {str(e)}"
                        st.error(error_msg)
                        current_messages.append({"role": "assistant", "content": error_msg})
        else:
            st.error("❌ No RAG pipeline available. Please check your collection.")

# ---------------------- Footer ----------------------
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #6b7280; font-size: 0.9rem; padding: 1rem;">
        🚀 <strong>Universal RAG Chat</strong> - Powered by Ollama & ChromaDB
    </div>
    """, 
    unsafe_allow_html=True
)
