from database.vector_db import VectorDB
from typing import List, Dict, Optional
from langchain.schema import Document
class Retriever:
    def __init__(self, vectordb: VectorDB, search_kwargs: Optional[Dict] = None):
        self.vectordb = vectordb
        self.search_kwargs = search_kwargs or {'k': 5}
        self.retriever = self.vectordb.as_retriever(search_kwargs=self.search_kwargs)
    
    def get_retriever(self):
        return self.retriever
    
    def search(self, query: str, k: Optional[int] = None) -> List[Document]:
        if k is not None:
            self.retriever = self.vectordb.as_retriever(search_kwargs={'k': k})
        return self.retriever.get_relevant_documents(query)
    
    def update_search_params(self, **kwargs):
        self.search_kwargs.update(kwargs)
        self.retriever = self.vectordb.as_retriever(search_kwargs=self.search_kwargs)