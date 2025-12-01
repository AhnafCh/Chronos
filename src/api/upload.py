# src/api/upload.py
import os
import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader,
)
from src.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Ensure Pinecone API key is set
os.environ["PINECONE_API_KEY"] = settings.PINECONE_API_KEY # type: ignore

def get_embeddings():
    """Get OpenAI embeddings instance"""
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=settings.OPENAI_API_KEY # type: ignore
    )

async def process_file(file: UploadFile) -> List[Document]:
    """
    Process uploaded file and extract documents
    Supports: PDF, TXT, MD, DOCX
    """
    # Create temp directory if it doesn't exist
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Save file temporarily
    file_path = os.path.join(temp_dir, file.filename)
    
    try:
        # Write uploaded file to disk
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Determine file type and load accordingly
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension == ".pdf":
            loader = PyPDFLoader(file_path)
        elif file_extension == ".txt":
            loader = TextLoader(file_path, encoding="utf-8")
        elif file_extension == ".md":
            loader = UnstructuredMarkdownLoader(file_path)
        elif file_extension in [".docx", ".doc"]:
            loader = Docx2txtLoader(file_path)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}. Supported: .pdf, .txt, .md, .docx"
            )
        
        # Load and split documents
        documents = loader.load()
        
        # Add metadata
        for doc in documents:
            doc.metadata["source"] = file.filename
            doc.metadata["file_type"] = file_extension
        
        return documents
    
    finally:
        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)

async def ingest_to_pinecone(documents: List[Document]) -> int:
    """
    Ingest documents into Pinecone vector store
    Returns number of documents ingested
    """
    embeddings = get_embeddings()
    
    PineconeVectorStore.from_documents(
        documents,
        embeddings,
        index_name=settings.PINECONE_INDEX_NAME
    )
    
    return len(documents)

@router.post("/upload", tags=["Upload"])
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file and automatically ingest it into Pinecone vector store.
    
    Supported file types: PDF, TXT, MD, DOCX
    """
    try:
        logger.info(f"📤 Received file: {file.filename}")
        
        # Validate Pinecone configuration
        if not settings.PINECONE_API_KEY or not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="Missing PINECONE_API_KEY or OPENAI_API_KEY in configuration"
            )
        
        # Process the file
        logger.info(f"📄 Processing file: {file.filename}")
        documents = await process_file(file)
        
        if not documents:
            raise HTTPException(
                status_code=400,
                detail="No content could be extracted from the file"
            )
        
        logger.info(f"📝 Extracted {len(documents)} document(s)")
        
        # Ingest to Pinecone
        logger.info(f"🚀 Ingesting to Pinecone index: {settings.PINECONE_INDEX_NAME}")
        num_ingested = await ingest_to_pinecone(documents)
        
        logger.info(f"✅ Successfully ingested {num_ingested} document(s)")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": f"File '{file.filename}' successfully uploaded and ingested",
                "filename": file.filename,
                "documents_processed": num_ingested,
                "index": settings.PINECONE_INDEX_NAME
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing file: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

@router.post("/upload/batch", tags=["Upload"])
async def upload_files_batch(files: List[UploadFile] = File(...)):
    """
    Upload multiple files and automatically ingest them into Pinecone vector store.
    
    Supported file types: PDF, TXT, MD, DOCX
    """
    try:
        logger.info(f"📤 Received {len(files)} file(s)")
        
        # Validate Pinecone configuration
        if not settings.PINECONE_API_KEY or not settings.OPENAI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="Missing PINECONE_API_KEY or OPENAI_API_KEY in configuration"
            )
        
        all_documents = []
        file_results = []
        
        # Process all files
        for file in files:
            try:
                logger.info(f"📄 Processing file: {file.filename}")
                documents = await process_file(file)
                all_documents.extend(documents)
                
                file_results.append({
                    "filename": file.filename,
                    "status": "processed",
                    "documents_extracted": len(documents)
                })
            except Exception as e:
                logger.error(f"❌ Error processing {file.filename}: {e}")
                file_results.append({
                    "filename": file.filename,
                    "status": "failed",
                    "error": str(e)
                })
        
        if not all_documents:
            raise HTTPException(
                status_code=400,
                detail="No content could be extracted from any files"
            )
        
        # Ingest all documents to Pinecone
        logger.info(f"🚀 Ingesting {len(all_documents)} document(s) to Pinecone")
        num_ingested = await ingest_to_pinecone(all_documents)
        
        logger.info(f"✅ Successfully ingested {num_ingested} document(s)")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": f"Successfully processed {len(files)} file(s)",
                "total_documents_ingested": num_ingested,
                "index": settings.PINECONE_INDEX_NAME,
                "files": file_results
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing files: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing files: {str(e)}"
        )
