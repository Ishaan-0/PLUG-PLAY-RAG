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
        self.client = vector_db._client
        self.embedding_func = vector_db.embedding_func
        self.persist_directory = vector_db.persist_directory

    def list_collections(self):
        """Return all collection names"""
        try:
            collections = self.client.list_collections()
            return [collection.name for collection in collections]
        except Exception as e:
            return [f"Error listing collections: {str(e)}"]

    def collection_stats(self, collection_name):
        """Return stats for a specific collection using direct ChromaDB access"""
        try:
            # Get the collection directly from the client
            collection = self.client.get_collection(name=collection_name)
            
            # Get all documents from this collection
            result = collection.get()
            
            if not result or 'ids' not in result:
                return {
                    "collection_name": collection_name,
                    "total_docs": 0,
                    "doc_types": {},
                    "total_chunks": 0
                }
            
            ids = result['ids']
            metadatas = result.get('metadatas', [])
            
            # Count document types and unique sources
            doc_types = {}
            unique_sources = set()
            
            for metadata in metadatas:
                if metadata:
                    # Count doc types
                    doc_type = metadata.get("doc_type", "unknown")
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                    
                    # Track unique source documents
                    source = metadata.get('source', 'unknown')
                    unique_sources.add(source)
            
            return {
                "collection_name": collection_name,
                "total_docs": len(unique_sources),
                "doc_types": doc_types,
                "total_chunks": len(ids)
            }
            
        except Exception as e:
            return {
                "collection_name": collection_name,
                "error": f"Failed to get collection stats: {str(e)}"
            }

    def get_all_documents_from_collection(self, collection_name):
        """Get all documents and their metadata from a specific collection"""
        try:
            collection = self.client.get_collection(name=collection_name)
            result = collection.get()
            
            if not result:
                return {"collection_name": collection_name, "documents": [], "total": 0}
            
            # Organize the results
            documents = []
            ids = result.get('ids', [])
            documents_text = result.get('documents', [])
            metadatas = result.get('metadatas', [])
            
            for i, doc_id in enumerate(ids):
                doc_data = {
                    "id": doc_id,
                    "content": documents_text[i] if i < len(documents_text) else "",
                    "metadata": metadatas[i] if i < len(metadatas) else {}
                }
                documents.append(doc_data)
            
            return {
                "collection_name": collection_name,
                "documents": documents,
                "total": len(documents)
            }
            
        except Exception as e:
            return {
                "collection_name": collection_name,
                "error": f"Failed to get documents: {str(e)}"
            }

    def database_stats(self):
        """Return stats for the entire DB"""
        try:
            collections = self.list_collections()
            
            all_collection_stats = {}
            total_docs = 0
            total_chunks = 0
            
            for collection_name in collections:
                if isinstance(collection_name, str):  # Skip error messages
                    stats = self.collection_stats(collection_name)
                    all_collection_stats[collection_name] = stats
                    
                    if 'error' not in stats:
                        total_docs += stats.get('total_docs', 0)
                        total_chunks += stats.get('total_chunks', 0)
            
            return {
                "total_collections": len([c for c in collections if isinstance(c, str)]),
                "total_docs_across_all": total_docs,
                "total_chunks_across_all": total_chunks,
                "current_collection": self.vector_db.collection_name,
                "all_collections": all_collection_stats
            }
            
        except Exception as e:
            return {"error": f"Failed to get database stats: {str(e)}"}

    def search_in_collection(self, collection_name, query, k=5):
        """Search for similar documents in a specific collection"""
        try:
            from langchain.vectorstores import Chroma
            
            # Create temporary Chroma instance for this collection
            temp_chroma = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding_func,
                collection_name=collection_name,
                client=self.client
            )
            
            results = temp_chroma.similarity_search(query, k=k)
            
            return {
                "collection_name": collection_name,
                "query": query,
                "results": [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc in results
                ]
            }
            
        except Exception as e:
            return {
                "collection_name": collection_name,
                "error": f"Failed to search collection: {str(e)}"
            }

    def delete_collection(self, collection_name):
        """Delete entire collection from DB"""
        try:
            self.client.delete_collection(name=collection_name)
            return {"success": f"Collection '{collection_name}' deleted successfully"}
        except Exception as e:
            return {"error": f"Failed to delete collection '{collection_name}': {str(e)}"}
