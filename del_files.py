import os
import shutil 
from dotenv import load_dotenv
load_dotenv()


class DelFiles:
    def __init__(self):
        pass 
    def delete_files(self, file_path):
        for root, dirs, files in os.walk(file_path):
            for file in files:
                if file.startswith("._"):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        print(f"Deleted file: {file_path}")
                    except Exception as e:
                        print(f"Error deleting file {file_path}: {e}")
