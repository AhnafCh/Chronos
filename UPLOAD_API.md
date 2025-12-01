# File Upload & Auto-Ingestion Feature

## Overview
The upload endpoint allows you to automatically ingest documents into Pinecone vector store for RAG capabilities.

## Endpoints

### Single File Upload
**POST** `/api/upload`

Upload a single file and automatically ingest it into Pinecone.

**Supported File Types:**
- PDF (`.pdf`)
- Text (`.txt`)
- Markdown (`.md`)
- Word Documents (`.docx`, `.doc`)

**Example using cURL:**
```bash
curl -X POST "http://localhost:8026/api/upload" \
  -F "file=@/path/to/document.pdf"
```

**Example using Python:**
```python
import requests

with open("document.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post("http://localhost:8026/api/upload", files=files)
    print(response.json())
```

**Response:**
```json
{
  "status": "success",
  "message": "File 'document.pdf' successfully uploaded and ingested",
  "filename": "document.pdf",
  "documents_processed": 5,
  "index": "chronos-index"
}
```

---

### Batch File Upload
**POST** `/api/upload/batch`

Upload multiple files at once and ingest them into Pinecone.

**Example using cURL:**
```bash
curl -X POST "http://localhost:8026/api/upload/batch" \
  -F "files=@/path/to/doc1.pdf" \
  -F "files=@/path/to/doc2.txt" \
  -F "files=@/path/to/doc3.md"
```

**Example using Python:**
```python
import requests

files = [
    ("files", open("doc1.pdf", "rb")),
    ("files", open("doc2.txt", "rb")),
    ("files", open("doc3.md", "rb"))
]

response = requests.post("http://localhost:8026/api/upload/batch", files=files)
print(response.json())

# Close files
for _, f in files:
    f.close()
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully processed 3 file(s)",
  "total_documents_ingested": 12,
  "index": "chronos-index",
  "files": [
    {
      "filename": "doc1.pdf",
      "status": "processed",
      "documents_extracted": 5
    },
    {
      "filename": "doc2.txt",
      "status": "processed",
      "documents_extracted": 1
    },
    {
      "filename": "doc3.md",
      "status": "processed",
      "documents_extracted": 6
    }
  ]
}
```

---

## Testing

Use the provided test script:

```bash
# Single file
python scripts/test_upload.py document.pdf

# Multiple files
python scripts/test_upload.py doc1.pdf doc2.txt doc3.md
```

---

## Installation

The required dependencies are included in `pyproject.toml`. Install them with:

```bash
poetry install
```

Or manually install:
```bash
pip install langchain-pinecone langchain-community pypdf python-docx unstructured python-multipart
```

---

## Configuration

Ensure your `.env` file contains:
```env
OPENAI_API_KEY=your_openai_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=chronos-index
```

---

## How It Works

1. **File Upload**: Client sends file via multipart/form-data
2. **Processing**: File is saved temporarily and parsed using appropriate loader
3. **Document Extraction**: Content is split into documents with metadata
4. **Embedding**: Documents are converted to embeddings using OpenAI
5. **Storage**: Embeddings are stored in Pinecone vector database
6. **Cleanup**: Temporary files are removed
7. **Response**: Success status with ingestion details

---

## Error Handling

- **Unsupported File Type**: Returns 400 error
- **Missing API Keys**: Returns 500 error with configuration message
- **Processing Error**: Returns 500 error with detailed message
- **No Content Extracted**: Returns 400 error

---

## Interactive API Documentation

Visit `http://localhost:8026/docs` after starting the server to see the interactive Swagger UI with all endpoints.
