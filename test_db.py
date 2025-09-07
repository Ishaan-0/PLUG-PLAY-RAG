from database.vector_db import VectorDB
from dotenv import load_dotenv
import os

load_dotenv()

vdb = VectorDB(rag_dir = os.getenv('RAG_DIR'), persist_directory= os.getenv('PERSISTENT_DIR'), embeddings_model=os.getenv('EMBEDDINGS_MODEL'))

for collection_name in vdb.list_all_collections():
    doc = vdb.get_document(collection_name)
    print('----------------------')
    print('\n')