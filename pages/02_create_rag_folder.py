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
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.creation-form {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    margin: 1rem 0;
}

.collection-card {
    background: white;
    padding: 1.5rem;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    margin: 0.5rem 0;
}

.progress-container {
    background: #f8fafc;
    padding: 2rem;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
    margin: 1rem 0;
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
        st.warning(f"⚠️ Cannot connect to Ollama: {str(e)}")
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
    st.error(f"❌ Database Error: {str(e)}")
    collections = []

# Header
st.title("➕ Create RAG Collection")
st.markdown("*Transform your document folders into intelligent, searchable collections*")

# Collection Creation Form
st.markdown('<div class="creation-form">', unsafe_allow_html=True)
st.subheader("📂 Create New Collection")

with st.form("create_collection_form", clear_on_submit=False):
    col1, col2 = st.columns([2, 1])
    
    with col1:
        folder_path = st.text_input(
            "📁 Document Folder Path",
            placeholder="e.g., /path/to/your/documents",
            help="Enter the full path to your folder containing PDF, TXT, or DOCX files"
        )
    
    with col2:
        if folder_path:
            suggested_name = slugify_path(folder_path)
            st.text_input("📝 Collection Name", value=suggested_name, disabled=True)
    
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
                    st.markdown('<div class="progress-container">', unsafe_allow_html=True)
                    st.subheader("🔄 Creating Collection...")
                    
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
                        
                        status_text.text("✅ Processing documents...")
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

st.markdown('</div>', unsafe_allow_html=True)

# Existing Collections
st.subheader("📁 Existing Collections")

if collections:
    for collection in collections:
        try:
            stats = vector_manager.collection_stats(collection)
            doc_count = stats.get("total_docs", 0)
            chunk_count = stats.get("total_chunks", 0)
            
            st.markdown(f"""
            <div class="collection-card">
                <h4>📄 {collection}</h4>
                <p><strong>Documents:</strong> {doc_count} | <strong>Chunks:</strong> {chunk_count}</p>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception:
            st.markdown(f"""
            <div class="collection-card">
                <h4>📄 {collection}</h4>
                <p style="color: #ef4444;">Error loading stats</p>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("📝 No collections yet. Create your first one above!")

# Navigation
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🏠 Home"):
        st.switch_page("main.py")
with col2:
    if st.button("💬 Chat Interface"):
        st.switch_page("pages/01_chat.py")
with col3:
    if st.button("📊 Database Stats"):
        st.switch_page("pages/03_database_stats.py")
