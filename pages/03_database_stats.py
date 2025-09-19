import streamlit as st
from database.vector_db import VectorDB, VectorManager
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="Vector DB Dashboard", layout="wide")

# Custom CSS for stats
st.markdown("""
<style>
.stats-card {
    background: white;
    padding: 1.5rem;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    text-align: center;
}

.stats-number {
    font-size: 2rem;
    font-weight: bold;
    color: #667eea;
}

.danger-zone {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
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
except Exception as e:
    st.error(f"❌ Database connection error: {e}")
    st.stop()

st.title("📊 Vector DB Dashboard")

# Database Stats Section
st.header("Database Stats")
db_stats = manager.database_stats()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="stats-card">
        <div class="stats-number">{db_stats["total_collections"]}</div>
        <div>Collections</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    total_docs = sum(col["total_docs"] for col in db_stats["all_collections"].values())
    st.markdown(f"""
    <div class="stats-card">
        <div class="stats-number">{total_docs:,}</div>
        <div>Documents</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    total_chunks = sum(col["total_chunks"] for col in db_stats["all_collections"].values())
    st.markdown(f"""
    <div class="stats-card">
        <div class="stats-number">{total_chunks:,}</div>
        <div>Chunks</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Collection-wise Details
st.header("Collection-wise Details")

collections = db_stats["all_collections"]
for collection_name, stats in collections.items():
    with st.expander(f"📁 {collection_name}"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Documents", stats['total_docs'])
        with col2:
            st.metric("Chunks", stats['total_chunks'])
        with col3:
            docs = stats['total_docs']
            chunks = stats['total_chunks']
            avg_chunks = round(chunks / docs, 1) if docs > 0 else 0
            st.metric("Avg Chunks/Doc", avg_chunks)
        
        st.write("**Document Types:**")
        doc_types = stats.get("doc_types", {})
        if doc_types:
            for doc_type, count in doc_types.items():
                percentage = (count / chunks * 100) if chunks > 0 else 0
                st.write(f"**{doc_type.upper()}**: {count} chunks ({percentage:.1f}%)")
        else:
            st.write("No document type information available")

        # Delete Collection Button
        st.markdown('<div class="danger-zone">', unsafe_allow_html=True)
        st.write("**Danger Zone**")
        
        if st.button(f"🗑️ Delete {collection_name}", key=f"delete_{collection_name}"):
            if st.session_state.get(f"confirm_delete_{collection_name}"):
                try:
                    result = manager.delete_collection(collection_name)
                    if "success" in result:
                        st.success(f"Collection '{collection_name}' deleted!")
                        st.session_state.pop(f"confirm_delete_{collection_name}", None)
                        st.rerun()
                    else:
                        st.error(result.get("error", "Unknown error"))
                except Exception as e:
                    st.error(f"Error deleting collection: {e}")
            else:
                st.session_state[f"confirm_delete_{collection_name}"] = True
                st.warning(f"⚠️ Click again to confirm deletion of '{collection_name}'")
        
        st.markdown('</div>', unsafe_allow_html=True)

# Navigation
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🏠 Home"):
        st.switch_page("main_streamlit.py")
with col2:
    if st.button("💬 Chat Interface"):
        st.switch_page("pages/01_chat.py")
with col3:
    if st.button("➕ Create Collection"):
        st.switch_page("pages/02_create_rag_folder.py")
