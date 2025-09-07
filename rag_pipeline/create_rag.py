from database.vector_db import VectorDB
from database.document_processor import DocumentProcessor
from database.retriever import Retriever
from langchain.chains import RetrievalQA
from langchain_ollama import ChatOllama
from langchain.schema import Document
from typing import List, Dict, Any, Optional

class RAGPipeline:
    def __init__(self, rag_dir: str, persist_dir: str, embeddings_model: str, 
                 llm_model: str):
        self.rag_dir = rag_dir
        self.persist_dir = persist_dir
        self.embeddings_model = embeddings_model
        self.llm_model_name = llm_model
        
        # Initialize LLM
        self.llm_model = ChatOllama(
            model=llm_model,
            base_url="http://localhost:11434"
        )
        
        # Initialize components
        self.document_processor = None
        self.vectordb = None
        self.retriever = None
        self.qa_chain = None
        
        # Setup pipeline
        self._setup_pipeline()
    
    def _setup_pipeline(self):
        """Setup the complete RAG pipeline."""
        print("🚀 Initializing RAG Pipeline...")
        
        # Step 1: Initialize document processor
        print("📄 Step 1: Initializing document processor...")
        self.document_processor = DocumentProcessor(self.rag_dir)
        
        # Step 2: Initialize vector database
        print("🗃️  Step 2: Initializing vector database...")
        self.vectordb = VectorDB(
            rag_dir=self.rag_dir,
            persist_directory=self.persist_dir,
            embeddings_model=self.embeddings_model,
        )
        
        # Step 3: Check if database needs population
        print("📊 Step 3: Checking database status...")
        self._populate_database_if_needed()
        
        # Step 4: Initialize retriever
        print("🔍 Step 4: Initializing retriever...")
        self.retriever = Retriever(self.vectordb)
        
        # Step 5: Initialize QA chain
        print("🤖 Step 5: Initializing QA chain...")
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm_model,
            chain_type="stuff",
            retriever=self.retriever.get_retriever(),
            return_source_documents=True
        )
        
        print("✅ RAG Pipeline initialization complete!")
    
    def _populate_database_if_needed(self):
        try:
            db_info = self.vectordb.get_db_info()
            current_count = db_info.get('current_collection', {}).get('document_count', 0)
            
            if current_count == 0:
                print("📥 Database is empty. Processing and adding documents...")
                chunks = self.document_processor.chunk_docs()
                if chunks:
                    self.vectordb.add_documents(chunks)
                    print(f"✅ Added {len(chunks)} chunks to database")
                else:
                    print("⚠️  No documents found to add")
            else:
                print(f"✅ Database already contains {current_count} documents")
                
        except Exception as e:
            print(f"❌ Error populating database: {str(e)}")
    
    def ask(self, question: str) -> str:
        try:
            result = self.qa_chain({"query": question})
            return result.get('result', 'No answer generated')
        except Exception as e:
            return f"Error: {str(e)}"
    
    def ask_detailed(self, question: str) -> Dict[str, Any]:
        try:
            result = self.qa_chain({"query": question})
            return {
                "question": question,
                "answer": result.get('result', 'No answer generated'),
                "source_documents": result.get('source_documents', []),
                "num_sources": len(result.get('source_documents', []))
            }
        except Exception as e:
            return {
                "question": question,
                "error": f"Failed to generate result: {str(e)}",
                "answer": "",
                "source_documents": [],
                "num_sources": 0
            }
    
    def search_documents(self, query: str, k: int = 5) -> List[Document]:
        return self.retriever.search(query, k=k)
    
    def update_retrieval_params(self, k: int):
        self.retriever.update_search_params(k=k)
        self.qa_chain.retriever = self.retriever.get_retriever()
        print(f"✅ Updated retriever to return top {k} documents")
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        try:
            db_info = self.vectordb.get_db_info()
            return {
                "pipeline_config": {
                    "rag_directory": self.rag_dir,
                    "persist_directory": self.persist_dir,
                    "embeddings_model": self.embeddings_model,
                    "llm_model": self.llm_model_name,
                    "retrieval_k": self.retriever.search_kwargs.get('k', 5)
                },
                "database_info": db_info,
                "collection_metadata": self.vectordb.get_collection_metadata(),
                "status": "ready"
            }
        except Exception as e:
            return {"error": f"Failed to get pipeline info: {str(e)}"}
    
    def add_documents(self, documents: List[Document]) -> bool:
        try:
            self.vectordb.add_documents(documents)
            print(f"✅ Added {len(documents)} documents to database")
            return True
        except Exception as e:
            print(f"❌ Error adding documents: {str(e)}")
            return False
    
    def refresh_documents(self):
        try:
            print("🔄 Refreshing documents...")
            chunks = self.document_processor.chunk_docs()
            if chunks:
                # Note: This adds new chunks. In production, you might want to 
                # clear existing ones first or implement update logic
                self.vectordb.add_documents(chunks)
                print(f"✅ Refreshed with {len(chunks)} chunks")
            else:
                print("⚠️  No documents found during refresh")
        except Exception as e:
            print(f"❌ Error refreshing documents: {str(e)}")