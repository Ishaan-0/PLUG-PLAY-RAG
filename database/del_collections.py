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
    
    
#client.delete_collection('Documents-Resume')
#print("DELETED COLLECTION")
print( collections)