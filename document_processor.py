from langchain.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from custom_pdf_processor import CustomPDFProcessor
from langchain.text_splitter import RecursiveCharacterTextSplitter
from concurrent.futures import ProcessPoolExecutor, as_completed
from langchain.schema import Document
import os
from pathlib import Path
from typing import List

class DocumentProcessor:
    def __init__(self, parent_dir: str):
        self.parent_dir = parent_dir
        self.valid_ext = [".pdf", ".txt", ".docx"]
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    def get_doc_paths(self) -> List[str]:
        all_files = []
        for root, dirs, files in os.walk(self.parent_dir):
            for file in files:
                print(f"FILE NAME: {file}")
                all_files.append(os.path.join(root, file))
        return all_files
    
    def process_pdf(self, file_path: str) -> List[Document]:
        file_name, _ = os.path.splitext(os.path.basename(file_path))
        try: 
            loader = CustomPDFProcessor(file_path)
            text = loader.extract_text()
            doc = Document(page_content=text, metadata={
                'source': file_name,
                'doc_name': file_name,
                'doc_type': 'pdf',
                'file_size': Path(file_path).stat().st_size
            })
            return [doc]
        except:
            loader = PyPDFLoader(file_path)
            loaded_docs = loader.load()
            for doc in loaded_docs:
                doc.metadata.update({
                    'source': file_name,
                    'file_name': file_name,
                    'file_type': 'pdf',
                    'file_size': Path(file_path).stat().st_size
                })
            return loaded_docs
        
    def process_docx(self, file_path: str) -> List[Document]:
        file_name, _ = os.path.splitext(os.path.basename(file_path))
        loader = Docx2txtLoader(file_path)
        loaded_docs = loader.load()
        for doc in loaded_docs:
            doc.metadata.update({
                'source': file_name,
                'file_name': file_name,
                'file_type': 'docx',
                'file_size': Path(file_path).stat().st_size
            })
        return loaded_docs
    
    def process_txt(self, file_path: str) -> List[Document]:
        file_name, _ = os.path.splitext(os.path.basename(file_path))
        loader = TextLoader(file_path, encoding = 'utf-8')
        loaded_docs = loader.load()
        for doc in loaded_docs:
            doc.metadata.update({
                'source': file_name,
                'file_name': file_name,
                'file_type': 'txt',
                'file_size': Path(file_path).stat().st_size
            })
        return loaded_docs

    def create_documents(self) -> List[Document]:
        file_paths = self.get_doc_paths()
        documents = []

        processor_map = {
            ".pdf": self.process_pdf,
            ".docx": self.process_docx,
            ".txt": self.process_txt
        }

        with ProcessPoolExecutor() as executor:
            future_to_file = {
                executor.submit(processor_map[os.path.splitext(fp)[1].lower()], fp): fp
                for fp in file_paths if os.path.splitext(fp)[1].lower() in processor_map
            }

            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    docs = future.result()
                    documents.extend(docs)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

        return documents

    def chunk_docs(self):
        documents = self.create_documents()
        chunks = self.text_splitter.split_documents(documents)
        return chunks