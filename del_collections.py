import chromadb 
import datetime
import os 
from dotenv import load_dotenv
load_dotenv()

client = chromadb.PersistentClient(os.getenv('PERSISTENT_DIR'))

collections = client.list_collections()
'''if collections:
    for collection in collections:
        print(f"Collection Name: {collection.name}, Document Count: {collection.count()}")
else:    
    print("NO COLLECTIONS IN THIS DB")'''
    
rag_dir = os.getenv('RAG_DIR')
parent_dir = os.path.dirname(rag_dir).split('/')[-1]
print(f"Parent Dir: {parent_dir}")
current_dir = os.path.basename(rag_dir)
print(f"Current Dir: {current_dir}")
collection_name = '_'.join(parent_dir.split()) + "-" + '_'.join(os.path.basename(rag_dir).split())
print(f"Collection Name: {collection_name}")
collection_metadata = {
    "description": f"RAG collection for documents from {rag_dir}",
    "source_directory": rag_dir,
    "embeddings_model": os.getenv('EMBEDDINGS_MODEL'),
    "created_at": str(datetime.datetime.now()),
    "version": "1.0"
}
#print(f"COLLECTION METADATA:\n{collection_metadata}\n")

try:
    collection = client.get_collection(name=collection_name)
    print(f"Collection '{collection_name}' already exists")
except Exception:
    collection = client.create_collection(
        name=collection_name,
        metadata=collection_metadata
    )
    print(f"Created new collection '{collection_name}' with metadata")