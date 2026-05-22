import os
import time
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore

load_dotenv()

# Constants
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "multipdf-rag")
EMBEDDING_MODEL = "models/gemini-embedding-001" 
# Use Gemini 3.1 Pro for the main LLM execution in the agent
LLM_MODEL = "models/gemini-3.1-pro-preview" 

def init_pinecone_index():
    """Ensure Pinecone index exists, create if it doesn't"""
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("PINECONE_API_KEY no configurado, omitiendo inicialización de índice.")
        return
    
    pc = Pinecone(api_key=api_key)
    
    if INDEX_NAME not in pc.list_indexes().names():
        print(f"Creando índice de Pinecone: {INDEX_NAME}...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=768, # Dimensión para GoogleGenerativeAIEmbeddings
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1" # Region por defecto
            )
        )
        while not pc.describe_index(INDEX_NAME).status['ready']:
            time.sleep(1)
        print("Índice creado exitosamente.")
    else:
        print(f"El índice {INDEX_NAME} ya existe.")

def get_embeddings():
    return GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)

def ingest_local_data():
    """Lee PDFs de la carpeta local 'data' y los carga en Pinecone. 
    Preparado para ser adaptado a storage en la nube en el futuro."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    loader = PyPDFDirectoryLoader(DATA_DIR)
    documents = loader.load()
    
    if not documents:
        return {"status": "No se encontraron documentos en el directorio local."}
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )
    docs = text_splitter.split_documents(documents)
    
    embeddings = get_embeddings()
    PineconeVectorStore.from_documents(docs, embeddings, index_name=INDEX_NAME)
    
    return {"status": f"Se ingirieron exitosamente {len(documents)} documentos en {len(docs)} fragmentos."}

def get_vectorstore():
    embeddings = get_embeddings()
    return PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
