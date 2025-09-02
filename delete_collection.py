from langchain_chroma import Chroma
from dotenv import load_dotenv
import os
load_dotenv()

persist_dir = os.getenv("PERSISTENT_DIR")
vdb = Chroma(persist_directory=persist_dir)
client = vdb._client
client.delete_collection("Sem_6-multiprocessing_test_copy")
for collection in client.list_collections():    
    print(f"Collection Name: {collection.name}, ID: {collection.id}, Document Count: {collection.count()}")
