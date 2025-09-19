import streamlit as st
import ollama
import requests
from database.vector_db import VectorDB, VectorManager
from rag_pipeline.create_rag import RAGPipeline
import os
from dotenv import load_dotenv

load_dotenv()


def get_source_directory_for_collection(manager, collection_name):
    """Fetch the source_directory metadata for a collection."""
    try:
        collection = manager.vector_db._client.get_collection(name=collection_name)
        metadata = getattr(collection, "metadata", {})
        return metadata.get("source_directory")
    except Exception as e:
        print(f"Could not fetch source directory for collection '{collection_name}': {e}")
        return None


vector_db = VectorDB(
    rag_dir=os.getenv("RAG_DIR"),
    persist_directory=os.getenv("PERSISTENT_DIR"),
    embeddings_model=os.getenv("EMBEDDINGS_MODEL"),
)
vector_manager = VectorManager(vector_db)
collections = vector_manager.list_collections()
print("Available collections:", collections)



