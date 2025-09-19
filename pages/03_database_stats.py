import streamlit as st
from database.vector_db import VectorDB, VectorManager
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(
    page_title="Vector DB Dashboard", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark mode dashboard styling
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

/* Stats cards styling */
div[data-testid="metric-container"] {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important;
    transition: all 0.3s ease !important;
}

div[data-testid="metric-container"]:hover {
    background: #334155 !important;
    transform: translateY(-4px) !important;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4) !important;
}

/* Metric styling */
div[data-testid="metric-container"] > div > div {
    color: #3b82f6 !important;
}

div[data-testid="metric-container"] label {
    color: #cbd5e1 !important;
}

/* Expander styling */
div[data-testid="stExpander"] {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 12px !important;
    margin: 1rem 0 !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
}

div[data-testid="stExpander"] summary {
    background: #1e293b !important;
    color: #f1f5f9 !important;
    padding: 1rem !important;
    border-radius: 12px !important;
}

div[data-testid="stExpander"] summary:hover {
    background: #334155 !important;
}

div[data-testid="stExpander"] > div > div {
    background: #1e293b !important;
    border-top: 1px solid #334155 !important;
    padding: 1.5rem !important;
}

/* Button styling */
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

/* Delete button styling */
button[kind="secondary"]:has-text("Delete") {
    background: #450a0a !important;
    color: #ef4444 !important;
    border: 1px solid #b91c1c !important;
}

button[kind="secondary"]:has-text("Delete"):hover {
    background: #7f1d1d !important;
    border-color: #ef4444 !important;
    color: white !important;
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

/* Danger zone styling */
.danger-zone {
    background: #450a0a !important;
    border: 1px solid #7f1d1d !important;
    border-radius: 8px !important;
    padding: 1rem !important;
    margin-top: 1rem !important;
}

.danger-zone h5 {
    color: #ef4444 !important;
}

.danger-zone p {
    color: #fca5a5 !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize DB and Manager
try:
    vdb = VectorDB(
        rag_dir=os.getenv('RAG_DIR'), 
        persist_directory=os.getenv('PERSISTENT_DIR'), 
        embeddings_model=os.getenv('EMBEDDINGS_MODEL')
    )
    manager = VectorManager(vdb)
    db_stats = manager.database_stats()
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.stop()

# Header
st.title("Vector DB Dashboard")
st.markdown("*Monitor your collections, view statistics, and manage your knowledge base*")

# Navigation buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Home", key="nav_home"):
        st.switch_page("main_streamlit.py")
with col2:
    if st.button("Chat Interface", key="nav_chat"):
        st.switch_page("pages/01_chat.py")
with col3:
    if st.button("Create Collection", key="nav_create"):
        st.switch_page("pages/02_create_rag_folder.py")

st.markdown("---")

# Database Stats
st.subheader("Database Statistics")

total_docs = sum(col["total_docs"] for col in db_stats["all_collections"].values())
total_chunks = sum(col["total_chunks"] for col in db_stats["all_collections"].values())

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Collections", db_stats["total_collections"])

with col2:
    st.metric("Documents", f"{total_docs:,}")

with col3:
    st.metric("Chunks", f"{total_chunks:,}")

# Collection Details
st.markdown("---")
st.subheader("Collection Details")

collections = db_stats["all_collections"]

if not collections:
    st.info("No collections found. Create your first collection to get started!")
    if st.button("Create Collection", type="primary"):
        st.switch_page("pages/02_create_rag_folder.py")
else:
    for collection_name, stats in collections.items():
        with st.expander(f"📄 {collection_name}"):
            # Collection stats
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Documents", stats['total_docs'])
            with col2:
                st.metric("Chunks", f"{stats['total_chunks']:,}")
            with col3:
                docs = stats['total_docs']
                chunks = stats['total_chunks']
                avg_chunks = round(chunks / docs, 1) if docs > 0 else 0
                st.metric("Avg Chunks/Doc", avg_chunks)
            
            # Document types
            doc_types = stats.get("doc_types", {})
            if doc_types:
                st.write("**Document Types:**")
                for doc_type, count in doc_types.items():
                    percentage = (count / chunks * 100) if chunks > 0 else 0
                    st.write(f"• **{doc_type.upper()}**: {count} chunks ({percentage:.1f}%)")
            else:
                st.write("No document type information available")

            # Delete Collection Button
            st.markdown('<div class="danger-zone">', unsafe_allow_html=True)
            st.markdown("##### ⚠️ Danger Zone")
            st.markdown("Permanently delete this collection and all its data.")
            
            delete_key = f"delete_{collection_name}"
            confirm_key = f"confirm_delete_{collection_name}"
            
            if st.button(f"🗑️ Delete {collection_name}", key=delete_key):
                if st.session_state.get(confirm_key):
                    try:
                        result = manager.delete_collection(collection_name)
                        if "success" in result:
                            st.success(f"Collection '{collection_name}' deleted!")
                            st.session_state.pop(confirm_key, None)
                            st.rerun()
                        else:
                            st.error(result.get("error", "Unknown error"))
                    except Exception as e:
                        st.error(f"Error deleting collection: {e}")
                else:
                    st.session_state[confirm_key] = True
                    st.warning(f"⚠️ Click the delete button again to confirm deletion of '{collection_name}'")
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; padding: 2rem; border-top: 1px solid #334155;">
    <strong>Universal RAG System</strong> • Built with Streamlit, Ollama & ChromaDB
</div>
""", unsafe_allow_html=True)