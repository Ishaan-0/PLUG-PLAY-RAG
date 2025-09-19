import streamlit as st
import requests
from database.vector_db import VectorDB, VectorManager
from rag_pipeline.create_rag import RAGPipeline
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

st.set_page_config(
    page_title="Create RAG Collection",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark mode styling
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

/* Form container styling */
div[data-testid="stForm"] {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 16px !important;
    padding: 2rem !important;
    margin: 1rem 0 !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important;
}

/* Input styling */
.stTextInput > div > div > input {
    background: #0f172a !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    padding: 0.75rem !important;
}

.stTextInput > div > div > input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 1px #3b82f6 !important;
}

.stTextInput label {
    color: #f1f5f9 !important;
    font-weight: 600 !important;
}

/* Selectbox styling */
.stSelectbox > div > div {
    background: #0f172a !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}

.stSelectbox > div > div > div {
    color: #e2e8f0 !important;
}

.stSelectbox label {
    color: #f1f5f9 !important;
    font-weight: 600 !important;
}

/* Button styling */
.stButton > button {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
    color: white !important;
    border: none !important;
    padding: 0.8rem 2rem !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4) !important;
}

/* Form submit button */
.stForm button[type="submit"] {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    color: white !important;
    border: none !important;
    padding: 1rem 3rem !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
}

.stForm button[type="submit"]:hover {
    background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
    transform: translateY(-2px) !important;
}

/* Collection cards */
.collection-card {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    padding: 1.5rem !important;
    border-radius: 12px !important;
    margin: 1rem 0 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
}

.collection-card:hover {
    background: #334155 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
}

/* Progress styling */
.progress-container {
    background: #064e3b !important;
    border: 1px solid #065f46 !important;
    border-radius: 12px !important;
    padding: 2rem !important;
    margin: 1rem 0 !important;
    color: #10b981 !important;
}

.stProgress .stProgress-bar {
    background: #10b981 !important;
}

/* Text styling */
h1, h2, h3, h4, h5, h6 {
    color: #f1f5f9 !important;
}

p {
    color: #cbd5e1 !important;
}

/* Alert styling */
div[data-testid="stAlert"] {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #e2e8f0 !important;
}

/* Success alert */
div[data-testid="stAlert"][data-baseweb="notification"][kind="success"] {
    background: #064e3b !important;
    border: 1px solid #065f46 !important;
    color: #10b981 !important;
}

/* Warning alert */
div[data-testid="stAlert"][data-baseweb="notification"][kind="warning"] {
    background: #451a03 !important;
    border: 1px solid #92400e !important;
    color: #f59e0b !important;
}

/* Error alert */
div[data-testid="stAlert"][data-baseweb="notification"][kind="error"] {
    background: #450a0a !important;
    border: 1px solid #b91c1c !important;
    color: #ef4444 !important;
}

/* Info alert */
div[data-testid="stAlert"][data-baseweb="notification"][kind="info"] {
    background: #0c2340 !important;
    border: 1px solid #1e40af !important;
    color: #3b82f6 !important;
}

/* Spinner styling */
div[data-testid="stSpinner"] {
    color: #3b82f6 !important;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=30)
def categorize_models():
    """Get available models from Ollama"""
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
                embedding_models.append(model["model"])
            else:
                llms.append(model["model"])

        return sorted(llms), sorted(embedding_models)

    except Exception as e:
        st.warning(f"Cannot connect to Ollama: {str(e)}")
        return [], []

def slugify_path(path_str: str) -> str:
    """Convert path to a clean collection name"""
    p = Path(path_str).expanduser().resolve()
    parts = p.parts[-2:] if len(p.parts) >= 2 else p.parts[-1:]
    base = "_".join(parts)
    return "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in base).lower()

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

# Header
st.title("Create RAG Collection")
st.markdown("*Transform your document folders into intelligent, searchable collections*")

# Navigation buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Home"):
        st.switch_page("main_streamlit.py")
with col2:
    if st.button("Chat Interface"):
        st.switch_page("pages/01_chat.py")
with col3:
    if st.button("Database Stats"):
        st.switch_page("pages/03_database_stats.py")

st.markdown("---")

# Collection Creation Form
st.subheader("Create New Collection")

with st.form("create_collection_form", clear_on_submit=False):
    col1, col2 = st.columns([3, 1])
    
    with col1:
        folder_path = st.text_input(
            "Document Folder Path",
            placeholder="e.g., /path/to/your/documents",
            help="Enter the full path to your folder containing PDF, TXT, or DOCX files"
        )
    
    with col2:
        if folder_path:
            suggested_name = slugify_path(folder_path)
            st.text_input("Collection Name", value=suggested_name, disabled=True)
    
    # Model Selection
    llms, embeddings = categorize_models()
    
    if llms and embeddings:
        col1, col2 = st.columns(2)
        
        with col1:
            selected_llm = st.selectbox(
                "🤖 LLM Model",
                llms,
                index=0,
                help="Language model for generating responses"
            )
        
        with col2:
            selected_embedding = st.selectbox(
                "🔗 Embedding Model",
                embeddings,
                index=0,
                help="Model for creating document embeddings"
            )
        
        create_button = st.form_submit_button("🚀 Create Collection", type="primary")
        
        if create_button and folder_path:
            folder_path_obj = Path(folder_path).expanduser().resolve()
            
            if not folder_path_obj.exists():
                st.error("📂 Folder doesn't exist!")
            elif not any(folder_path_obj.glob("*.pdf")) and not any(folder_path_obj.glob("*.txt")) and not any(folder_path_obj.glob("*.docx")):
                st.warning("📄 No supported files found! (PDF, TXT, DOCX)")
            else:
                collection_name = slugify_path(folder_path)
                
                if collection_name in collections:
                    st.warning("⚠️ Collection already exists!")
                else:
                    # Create collection with progress tracking
                    with st.container():
                        st.markdown('<div class="progress-container">', unsafe_allow_html=True)
                        st.markdown("#### 🔄 Creating Collection...")
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        try:
                            status_text.text("📄 Initializing document processor...")
                            progress_bar.progress(20)
                            
                            status_text.text("🗃️ Setting up vector database...")
                            progress_bar.progress(40)
                            
                            status_text.text("🤖 Loading AI models...")
                            progress_bar.progress(60)
                            
                            rag_pipeline = RAGPipeline(
                                rag_dir=str(folder_path_obj),
                                persist_dir=os.getenv("PERSISTENT_DIR"),
                                embeddings_model=selected_embedding,
                                llm_model=selected_llm,
                            )
                            
                            status_text.text("✨ Processing documents...")
                            progress_bar.progress(80)
                            
                            progress_bar.progress(100)
                            status_text.text("🎉 Collection created successfully!")
                            
                            st.balloons()
                            st.success(f"✅ Collection '{collection_name}' created successfully!")
                            
                            if st.button("💬 Start Chatting with This Collection"):
                                st.switch_page("pages/01_chat.py")
                            
                        except Exception as e:
                            st.error(f"❌ Error creating collection: {str(e)}")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        st.warning("⚠️ No Ollama models found. Please install models first.")
        st.info("💡 Run `ollama pull llama3.2:1b` and `ollama pull nomic-embed-text` to get started.")
        st.form_submit_button("🚀 Create Collection", disabled=True)

# Existing Collections
st.markdown("---")
st.subheader("📚 Existing Collections")

if collections:
    # Display collections in a simple list format
    for collection in collections:
        try:
            stats = vector_manager.collection_stats(collection)
            doc_count = stats.get("total_docs", 0)
            chunk_count = stats.get("total_chunks", 0)
            
            st.markdown(f"""
            <div class="collection-card">
                <h4 style="color: #f1f5f9; margin: 0 0 0.5rem 0;">📄 {collection}</h4>
                <p style="color: #94a3b8; margin: 0; font-size: 0.9rem;">
                    <strong>Documents:</strong> {doc_count} | <strong>Chunks:</strong> {chunk_count:,}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception:
            st.markdown(f"""
            <div class="collection-card">
                <h4 style="color: #f1f5f9; margin: 0 0 0.5rem 0;">📄 {collection}</h4>
                <p style="color: #ef4444; margin: 0; font-size: 0.9rem;">Error loading stats</p>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("📁 No collections yet. Create your first collection using the form above!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; padding: 2rem; border-top: 1px solid #334155;">
    <strong>Universal RAG System</strong> • Built with Streamlit, Ollama & ChromaDB
</div>
""", unsafe_allow_html=True)