from create_rag import RAGPipeline
import os 
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    rag_dir = os.getenv("RAG_DIR")
    persistent_dir = os.getenv("PERSISTENT_DIR")
    embeddings_model = os.getenv("EMBEDDINGS_MODEL")
    llm_model = os.getenv("LLM_MODEL")
    rag_pipeline = RAGPipeline(
        rag_dir=rag_dir,    
        persist_dir=persistent_dir,
        embeddings_model=embeddings_model,
        llm_model=llm_model
    )
    print("RAG Pipeline is set up and ready to use!")
    
    
    while True: 
        print('-' * 50)
        query = input("\nEnter your question (or type 'exit' to quit): ")
        if query.lower() == 'exit':
            print("Exiting the RAG system. Goodbye!")
            break
        
        response = rag_pipeline.ask_detailed(query)
        source = response['source_documents']
        answer = response['answer']
        print(f"\nANSWER: \n{answer}\n\n")