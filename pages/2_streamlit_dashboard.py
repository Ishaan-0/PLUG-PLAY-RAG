import streamlit as st
from database.vector_db import VectorDB, VectorManager
from dotenv import load_dotenv
import os 

load_dotenv()

# --- Initialize DB and Manager ---
vdb = VectorDB(rag_dir = os.getenv('RAG_DIR'), 
               persist_directory= os.getenv('PERSISTENT_DIR'), 
               embeddings_model=os.getenv('EMBEDDINGS_MODEL'))
manager = VectorManager(vdb)

collections_list = manager.list_collections()

st.set_page_config(page_title="Vector DB Dashboard", layout="wide")
st.title("📊 Vector DB Dashboard")

# --- Database Stats Section ---
st.header("Database Stats")
db_stats = manager.database_stats()

st.metric("Total Collections", db_stats["total_collections"])
total_docs = db_stats["total_docs_across_all"]
st.metric("Total Documents", total_docs)
total_chunks = db_stats["total_chunks_across_all"]
st.metric("Total Chunks", total_chunks)

st.markdown("---")

# --- Collection-wise Details ---
st.header("Collection-wise Details")

collections = db_stats["all_collections"]
for collection_name, stats in collections.items():
    with st.expander(f"📁 {collection_name}"):
        st.write(f"**Documents:** {stats['total_docs']}")
        st.write(f"**Total Chunks:** {stats['total_chunks']}")
        st.write("**Document Types:**")
        st.json(stats["doc_types"])

        # --- Delete Collection Button ---
        if st.button(f"Delete {collection_name}"):
            manager.delete_collection(collection_name)
            st.success(f"Collection '{collection_name}' deleted!")
            st.rerun()
