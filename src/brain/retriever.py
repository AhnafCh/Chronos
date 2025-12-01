import os
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from src.core.config import settings

# Ensure environment variable is set for the library
os.environ["PINECONE_API_KEY"] = settings.PINECONE_API_KEY # type: ignore

def get_retriever():
    """
    Creates a Pinecone Retriever connected to our index.
    """
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small", 
        api_key=settings.OPENAI_API_KEY # type: ignore
    )
    
    vectorstore = PineconeVectorStore(
        index_name=settings.PINECONE_INDEX_NAME,
        embedding=embeddings,
        pinecone_api_key=settings.PINECONE_API_KEY # type: ignore
    )
    
    # Return top 2 results to keep latency low
    return vectorstore.as_retriever(search_kwargs={"k": 2})

# Singleton instance
retriever = get_retriever()