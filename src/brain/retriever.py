import os
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from src.core.config import settings
from src.core import control

# Ensure environment variable is set for the library
os.environ["PINECONE_API_KEY"] = settings.PINECONE_API_KEY # type: ignore

def get_retriever():
    """
    Creates a Pinecone Retriever connected to our index.
    Uses control.py settings for embedding model and top_k.
    """
    embeddings = OpenAIEmbeddings(
        model=control.RAG_EMBEDDING_MODEL, 
        api_key=settings.OPENAI_API_KEY # type: ignore
    )
    
    vectorstore = PineconeVectorStore(
        index_name=settings.PINECONE_INDEX_NAME,
        embedding=embeddings,
        pinecone_api_key=settings.PINECONE_API_KEY # type: ignore
    )
    
    # Use control.py setting for number of documents to retrieve
    return vectorstore.as_retriever(search_kwargs={"k": control.RAG_TOP_K})

# Singleton instance
retriever = get_retriever()