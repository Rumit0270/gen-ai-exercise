import os
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_google_community import GoogleDriveLoader
from langchain_community.document_loaders import ConfluenceLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()

# OpenAI API configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL= os.environ.get("EMBEDDING_MODEL")

# Confluence API configuration
CONFLUENCE_API_TOKEN= os.environ.get("CONFLUENCE_API_TOKEN")
CODE_OF_CONDUCT_URL= os.environ.get("CODE_OF_CONDUCT_URL")
CONFLUENCE_USERNAME= os.environ.get("CONFLUENCE_USERNAME")
CONFLUENCE_BASE_URL= os.environ.get("CONFLUENCE_BASE_URL")

# Google Cloud configuration
ANTI_HARASSMENT_FILE_ID= os.environ.get("ANTI_HARASSMENT_FILE_ID")
NOMINATION_GUIDELINE_DOC_ID= os.environ.get("NOMINATION_GUIDELINE_DOC_ID")


def load_documents():
    """
    Load the documents for the Code of Conduct, Nomination Guidelines, and Anti-Harassment Policy.
    """
    
    documents = []
    
    # Load Confluence document (Code of Conduct)
    try:
        page_id = CODE_OF_CONDUCT_URL.split('/pages/')[1].split('/')[0]
        
        confluence_loader = ConfluenceLoader(
            url=CONFLUENCE_BASE_URL,
            username=CONFLUENCE_USERNAME,
            api_key=CONFLUENCE_API_TOKEN,
            page_ids=[page_id]
        )
        
        confluence_docs = confluence_loader.load()
        documents.extend(confluence_docs)
        print(f"Loaded Confluence document: {len(confluence_docs)} pages")
        
    except Exception as e:
        print(f"Confluence loading failed: {e}")
    
    # Load docs from Google Drive (Nomination Guidelines and Anti-Harassment Policy)
    # Note: This was not working for me.
    try:
        google_loader = GoogleDriveLoader(
            document_ids=[
                ANTI_HARASSMENT_FILE_ID,
                NOMINATION_GUIDELINE_DOC_ID
            ],
            service_account_key=os.path.join(os.path.dirname(__file__), '..', 'google_credentials.json'),
        )
        google_docs = google_loader.load()
        documents.extend(google_docs)
        print(f"Loaded Google Drive documents: {len(google_docs)} files")
    except Exception as loader_error:
        print(f"GoogleDriveLoader failed: {loader_error}")
        
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        import tempfile
        import requests
        from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
        
        try:
            doc_ids = [
                ANTI_HARASSMENT_FILE_ID,
                NOMINATION_GUIDELINE_DOC_ID
            ]
        
            # Assuming service account is saved in google_credentials.json
            credentials_path = os.path.join(os.path.dirname(__file__), '..', 'google_credentials.json')
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=[
                    'https://www.googleapis.com/auth/drive.readonly',
                    'https://www.googleapis.com/auth/drive.file'
                ]
            )
            
            service = build('drive', 'v3', credentials=credentials)
            
            # Try to download and load each document manually
            for doc_id in doc_ids:
                try:
                    # Get file metadata
                    file_info = service.files().get(fileId=doc_id).execute()
                    file_name = file_info.get('name', 'unknown')
                    mime_type = file_info.get('mimeType', '')
                    
                    if 'pdf' in mime_type:
                        # For PDF files
                        request = service.files().get_media(fileId=doc_id)
                        file_content = request.execute()
                        
                        # Save to temporary file and load with PyPDFLoader
                        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                            temp_file.write(file_content)
                            temp_path = temp_file.name
                        
                        try:
                            pdf_loader = PyPDFLoader(temp_path)
                            pdf_docs = pdf_loader.load()
                            
                            for doc in pdf_docs:
                                doc.metadata.update({
                                    'title': file_name,
                                    'id': doc_id,
                                    'source': 'google_drive_manual',
                                    'mime_type': mime_type
                                })
                            
                            documents.extend(pdf_docs)
                            print(f"Manually loaded PDF: {file_name}")
                            
                        finally:
                            os.unlink(temp_path)
                            
                    elif 'wordprocessingml' in mime_type or 'document' in mime_type:
                        # For Word documents
                        request = service.files().get_media(fileId=doc_id)
                        file_content = request.execute()
                        
                        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
                            temp_file.write(file_content)
                            temp_path = temp_file.name
                        
                        try:
                            docx_loader = Docx2txtLoader(temp_path)
                            docx_docs = docx_loader.load()
                            
                            for doc in docx_docs:
                                doc.metadata.update({
                                    'title': file_name,
                                    'id': doc_id,
                                    'source': 'google_drive_manual',
                                    'mime_type': mime_type
                                })
                            
                            documents.extend(docx_docs)
                            print(f"Manually loaded DOCX: {file_name}")
                            
                        finally:
                            os.unlink(temp_path)
                        
                except Exception as e:
                    print(f"Failed to manually load {doc_id}: {e}")
                    continue
        
        except Exception as manual_error:
            print(f"Manual loading failed: {manual_error}")
        
    return documents

def chunk_documents(documents):
    """Split documents into manageable chunks"""
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    
    chunks = text_splitter.split_documents(documents)
    return chunks

def add_chunks_to_vector_db(chunks):
    """Add chunks to the vector database"""
    
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name="rag_exercise",
        persist_directory="./chroma_data"  
    )

    vector_store.add_documents(chunks)
    
    return vector_store


def main():
    documents = load_documents()
    chunks = chunk_documents(documents)  
    add_chunks_to_vector_db(chunks)

if __name__ == "__main__":
    main()

    
