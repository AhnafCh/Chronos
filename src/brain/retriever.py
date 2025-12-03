import os
from typing import Optional
from functools import lru_cache
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from src.core.config import settings
from src.core import control

# Ensure environment variable is set for the library
os.environ["PINECONE_API_KEY"] = settings.PINECONE_API_KEY # type: ignore

@lru_cache(maxsize=1)
def _get_embeddings() -> OpenAIEmbeddings:
    """Get or create cached embeddings instance (thread-safe via lru_cache)"""
    return OpenAIEmbeddings(
        model=control.RAG_EMBEDDING_MODEL, 
        api_key=settings.OPENAI_API_KEY # type: ignore
    )

@lru_cache(maxsize=1)
def _get_vectorstore() -> PineconeVectorStore:
    """Get or create cached vectorstore instance (thread-safe via lru_cache)"""
    return PineconeVectorStore(
        index_name=settings.PINECONE_INDEX_NAME,
        embedding=_get_embeddings(),
        pinecone_api_key=settings.PINECONE_API_KEY # type: ignore
    )

def clear_retriever_cache() -> None:
    """Clear cached embeddings and vectorstore (useful for credential rotation)"""
    _get_vectorstore.cache_clear()
    _get_embeddings.cache_clear()

def get_retriever(user_uuid: Optional[str] = None):
    """
    Creates a Pinecone Retriever connected to our index.
    Uses control.py settings for embedding model and top_k.
    Reuses cached embeddings and vectorstore for performance.
    
    Args:
        user_uuid: Optional UUID to filter documents by user. 
                   If provided, only retrieves documents uploaded by this user.
    """
    vectorstore = _get_vectorstore()
    
    # Build search kwargs with optional user filter
    search_kwargs: dict = {"k": control.RAG_TOP_K}
    if user_uuid:
        search_kwargs["filter"] = {"user_uuid": user_uuid}
    
    return vectorstore.as_retriever(search_kwargs=search_kwargs)