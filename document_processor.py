from langchain.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from custom_pdf_processor import CustomPDFProcessor
from langchain.text_splitter import RecursiveCharacterTextSplitter
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

    def create_documents(self) -> List[Document]:
        file_paths = self.get_doc_paths()
        documents = []
        for file_path in file_paths:
            file_name, extension = os.path.splitext(os.path.basename(file_path))
            extension = extension.lower()

            if extension in self.valid_ext:
                if extension == ".pdf":
                    try: 
                        loader = CustomPDFProcessor(file_path)
                        text = loader.extract_text()
                        doc = Document(page_content=text, metadata={
                            'source': file_name,
                            'doc_name': file_name,
                            'doc_type': 'pdf',
                            'file_size': Path(file_path).stat().st_size
                        })
                        documents.append(doc)
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
                        documents.extend(loaded_docs)
                    
                if extension == ".docx":
                    loader = Docx2txtLoader(file_path)
                    loaded_docs = loader.load()
                    for doc in loaded_docs:
                        doc.metadata.update({
                            'source': file_name,
                            'file_name': file_name,
                            'file_type': 'pdf',
                            'file_size': Path(file_path).stat().st_size
                        })
                    documents.extend(loaded_docs)

                if extension == ".txt":
                    loader = TextLoader(file_path, encoding = 'utf-8')
                    loaded_docs = loader.load()
                    for doc in loaded_docs:
                        doc.metadata.update({
                            'source': file_name,
                            'file_name': file_name,
                            'file_type': 'pdf',
                            'file_size': Path(file_path).stat().st_size
                        })
                    documents.extend(loaded_docs)
        return documents

    def chunk_docs(self):
        documents = self.create_documents()
        chunks = self.text_splitter.split_documents(documents)
        return chunks