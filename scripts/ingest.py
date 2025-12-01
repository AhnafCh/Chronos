import os
import sys

# Allow importing from src
sys.path.append(os.getcwd())

from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from src.core.config import settings

def ingest_data():
    print("--- 1. Loading Knowledge ---")
    text_content = """
    Chronos Voice AI Pricing:
    - Basic Plan: $29/month. Includes 5 hours of talk time.
    - Pro Plan: $99/month. Includes 20 hours of talk time and custom voices.
    - Enterprise: Contact sales. Includes unlimited talk time and on-premise deployment.
    
    Refund Policy:
    We offer a 30-day money-back guarantee if you are not satisfied with the latency.
    
    Support Hours:
    Our support team is available Monday to Friday, 9 AM to 5 PM EST.
    """
    
    docs = [Document(page_content=text_content, metadata={"source": "pricing_sheet"})]

    print("--- 2. Creating Embeddings ---")
    # FIX: Pass the API key explicitly here
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=settings.OPENAI_API_KEY # type: ignore
    )

    print(f"--- 3. Uploading to Pinecone ({settings.PINECONE_INDEX_NAME}) ---")
    # To be safe, we set the env var for this process:
    os.environ["PINECONE_API_KEY"] = settings.PINECONE_API_KEY # type: ignore
    
    PineconeVectorStore.from_documents(
        docs, 
        embeddings, 
        index_name=settings.PINECONE_INDEX_NAME
    )
    
    print("✅ Success! The bot now knows the pricing.")

if __name__ == "__main__":
    ingest_data()