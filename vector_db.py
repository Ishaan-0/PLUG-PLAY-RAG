from langchain.vectorstores import Chroma
from langchain_ollama.embeddings import OllamaEmbeddings
import chromadb
import os
import datetime
from typing import Optional, Dict, Any, List

class VectorDB(Chroma):
    
    def __init__(self, rag_dir: str, persist_directory: str, embeddings_model: str):
        self.persist_directory = persist_directory
        self.rag_dir = rag_dir
        self.embeddings_model = embeddings_model
        
        # Create embedding function
        self.embedding_func = OllamaEmbeddings(
            model=self.embeddings_model,
            base_url="http://localhost:11434"
        )
        
        # Generate unique collection name from directory structure
        parent_dir = os.path.dirname(self.rag_dir).split('/')[-1]
        self.collection_name = '_'.join(parent_dir.split()) + "-" + '_'.join(os.path.basename(self.rag_dir).split())
        collection_metadata = {
            "description": f"RAG collection for documents from {rag_dir}",
            "source_directory": rag_dir,
            "embeddings_model": embeddings_model,
            "created_at": str(datetime.datetime.now()),
            "version": "1.0"
        }

        client = chromadb.PersistentClient(path=self.persist_directory)
        
        try:
            collection = client.get_collection(name=self.collection_name)
            print(f"Collection '{self.collection_name}' already exists")
        except Exception:
            collection = client.create_collection(
                name=self.collection_name,
                metadata=collection_metadata
            )
            print(f"Created new collection '{self.collection_name}' with metadata")
        
        # Initialize parent Chroma class
        super().__init__(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_func,
            collection_name=self.collection_name,
            client=client
        )

    def get_collection_metadata(self) -> Dict[str, Any]:
        try:
            collection = self._collection
            metadata = collection.metadata if hasattr(collection, 'metadata') else {}
            return {
                "collection_name": self.collection_name,
                "metadata": metadata
            }
        except Exception as e:
            return {"error": f"Failed to get collection metadata: {str(e)}"}

    def get_db_info(self) -> Dict[str, Any]:
        try:
            client = self._client
            collections = client.list_collections()
            
            current_collection = self._collection
            current_collection_count = current_collection.count() if current_collection else 0
            
            db_info = {
                "database_info": {
                    "persist_directory": self.persist_directory,
                    "embeddings_model": self.embeddings_model,
                    "rag_directory": self.rag_dir,
                    "base_url": "http://localhost:11434"
                },
                "current_collection": {
                    "name": self.collection_name,
                    "document_count": current_collection_count,
                    "embedding_function": str(type(self.embedding_func).__name__)
                },
                "total_collections": len(collections),
                "all_collections": []
            }
            
            for collection in collections:
                try:
                    collection_info = {
                        "name": collection.name,
                        "id": collection.id,
                        "document_count": collection.count(),
                        "metadata": collection.metadata if hasattr(collection, 'metadata') else None
                    }
                    db_info["all_collections"].append(collection_info)
                except Exception as e:
                    db_info["all_collections"].append({
                        "name": collection.name,
                        "error": str(e)
                    })
            
            return db_info
            
        except Exception as e:
            return {
                "error": f"Failed to get database info: {str(e)}",
                "current_collection_name": getattr(self, 'collection_name', 'unknown'),
                "persist_directory": getattr(self, 'persist_directory', 'unknown')
            }

    def list_all_collections(self) -> List[str]:
        """Get list of all collection names."""
        try:
            client = self._client
            collections = client.list_collections()
            return [collection.name for collection in collections]
        except Exception as e:
            return [f"Error listing collections: {str(e)}"]
        
# vector_db.py
class VectorManager:
    def __init__(self, vector_db):
        """
        vector_db: Instance of existing VectorDB class
        """
        self.vector_db = vector_db

    def list_collections(self):
        """Return all collection names"""
        return self.vector_db.list_all_collections()

    def collection_stats(self, collection_name):
        """Return stats for a single collection"""
        docs = self.vector_db.get_documents(collection_name)
        return {
            "total_docs": len(docs),
            "doc_types": self._get_doc_types(docs),
            "total_chunks": sum(d["chunk_count"] for d in docs)
        }

    def database_stats(self):
        """Return stats for the entire DB"""
        collections = self.list_collections()
        stats = {c: self.collection_stats(c) for c in collections}
        return {
            "total_collections": len(collections),
            "collections": stats
        }

    def _get_doc_types(self, docs):
        """Helper to count doc types"""
        types = {}
        for d in docs:
            t = d.get("doc_type", "unknown")
            types[t] = types.get(t, 0) + 1
        return types

    def delete_collection(self, collection_name):
        """Delete entire collection from DB"""
        return self.vector_db.delete_collection(collection_name)
