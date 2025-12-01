# 🤖 Chronos - Voice RAG Orchestrator

A production-ready voice AI assistant with real-time conversation capabilities, RAG (Retrieval-Augmented Generation), and document ingestion features.

## ✨ Features

- 🎙️ **Real-time Voice Conversation**: WebSocket-based voice interaction with streaming audio
- 💬 **Text Chat**: Traditional text-based conversations
- 📚 **RAG Integration**: Retrieval-Augmented Generation using Pinecone vector database
- 📤 **Document Upload**: Automatic ingestion of PDF, TXT, MD, and DOCX files
- 🎨 **Streamlit UI**: Interactive web interface for conversations and file uploads
- ⚡ **Fast & Scalable**: Built with FastAPI and async Python

## 📋 Prerequisites

- **Python**: 3.11 or 3.12 (not 3.13+)
- **Poetry**: For dependency management
- **API Keys**:
  - OpenAI API key
  - Pinecone API key
  - Deepgram API key (for voice features)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Chronos
```

### 2. Install Poetry (if not installed)

```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -
```

### 3. Install Dependencies

```bash
poetry install
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```env
# App Configuration
APP_NAME=Chronos
DEBUG=true

# AI Services
OPENAI_API_KEY=your_openai_key_here
DEEPGRAM_API_KEY=your_deepgram_key_here

# Vector Store
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_INDEX_NAME=chronos-index

# Audio Settings (optional)
INPUT_SAMPLE_RATE=16000
OUTPUT_SAMPLE_RATE=24000
```

### 5. Set Up Pinecone Index

1. Create a Pinecone account at [pinecone.io](https://www.pinecone.io)
2. Create a new index named `chronos-index` (or match your `.env` setting)
3. Use dimension: **1536** (for OpenAI text-embedding-3-small)
4. Choose your preferred cloud provider and region

### 6. Ingest Initial Knowledge Base

Run the ingestion script to populate your vector database:

```bash
poetry run python scripts/ingest.py
```

### 7. Start the Backend Server

```bash
poetry run python src/main.py
```

The server will start on `http://localhost:8026`

### 8. Start the Streamlit UI (Optional)

In a new terminal:

```bash
poetry run streamlit run streamlit/app.py
```

The UI will open at `http://localhost:8501`

## 📖 Usage

### Using the Streamlit UI

1. Open `http://localhost:8501` in your browser
2. **Chat**: Use the text input or microphone button for voice chat
3. **Upload Documents**: Use the sidebar to upload and ingest documents into the knowledge base

### Using the API Directly

#### Health Check
```bash
curl http://localhost:8026/
```

#### Upload Single File
```bash
curl.exe -X POST "http://localhost:8026/api/upload" -F "file=@document.pdf"
```

#### Upload Multiple Files
```bash
curl.exe -X POST "http://localhost:8026/api/upload/batch" ^
  -F "files=@doc1.pdf" ^
  -F "files=@doc2.txt" ^
  -F "files=@doc3.md"
```

#### WebSocket Chat
Connect to `ws://localhost:8026/ws/chat?session_id=YOUR_SESSION_ID`

### Using the Test Scripts

#### Test File Upload
```bash
poetry run python scripts/test_upload.py document.pdf

# Multiple files
poetry run python scripts/test_upload.py doc1.pdf doc2.txt doc3.md
```

#### Test WebSocket Client
```bash
poetry run python scripts/test_client.py
```

## 📁 Project Structure

```
Chronos/
├── src/
│   ├── main.py              # FastAPI application entry point
│   ├── api/
│   │   ├── websocket.py     # WebSocket endpoint for chat
│   │   └── upload.py        # File upload endpoints
│   ├── brain/
│   │   ├── graph.py         # LangGraph workflow
│   │   ├── retriever.py     # Pinecone retriever
│   │   └── state.py         # State management
│   ├── core/
│   │   ├── config.py        # Configuration & settings
│   │   └── logger.py        # Logging setup
│   ├── domain/
│   │   └── models.py        # Data models
│   └── services/
│       ├── asr.py           # Speech-to-Text (Deepgram)
│       ├── llm.py           # LLM integration
│       └── tts.py           # Text-to-Speech (ElevenLabs)
├── streamlit/
│   └── app.py               # Streamlit web interface
├── scripts/
│   ├── ingest.py            # Initial data ingestion
│   ├── test_upload.py       # Test upload endpoint
│   └── test_client.py       # WebSocket test client
├── tests/                   # Unit tests
├── pyproject.toml           # Poetry dependencies
├── .env                     # Environment variables (create this)
└── README.md                # This file
```

## 🔧 Configuration

### Supported File Types for Upload
- **PDF** (`.pdf`)
- **Text** (`.txt`)
- **Markdown** (`.md`)
- **Word Documents** (`.docx`, `.doc`)

### Audio Settings
- Input sample rate: 16000 Hz (for ASR)
- Output sample rate: 24000 Hz (for TTS)

### Vector Store
- Uses Pinecone for vector storage
- OpenAI embeddings (text-embedding-3-small)
- Top-k retrieval: 2 documents

## 🛠️ Development

### Run Tests
```bash
poetry run pytest
```

### Run with Auto-reload
```bash
poetry run python src/main.py
```
The server will automatically reload on code changes.

### View API Documentation
Open `http://localhost:8026/docs` for interactive Swagger UI

## 📚 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/api/upload` | Upload single file |
| POST | `/api/upload/batch` | Upload multiple files |
| WS | `/ws/chat` | WebSocket chat endpoint |

## 🐛 Troubleshooting

### Port Already in Use
Change the port in `src/main.py`:
```python
uvicorn.run("src.main:app", host="0.0.0.0", port=8026)
```

### Poetry Installation Issues
```bash
# Clear cache
poetry cache clear . --all

# Reinstall
poetry install --no-cache
```

### Python Version Issues
Ensure you're using Python 3.11 or 3.12:
```bash
python --version
poetry env use python3.11
```

### Missing Dependencies
```bash
poetry install
```
