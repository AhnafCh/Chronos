# Chronos Streamlit Frontend

This directory contains the Streamlit-based web interface for the Chronos AI assistant with integrated authentication.

## Files

- **`app.py`** - Main Streamlit application with chat interface and file upload functionality
- **`auth_utils.py`** - Authentication utilities (login, register, token management, session state)
- **`auth_components.py`** - Reusable UI components for login and registration forms

## Features

### 🔐 Authentication
- **User Registration** with email validation and strong password requirements:
  - Minimum 8 characters
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 number
- **User Login** with JWT token-based authentication
- **Session Management** - Tokens stored in Streamlit session state
- **Protected Routes** - Users must authenticate before accessing the chat interface

### 💬 Chat Interface
- **Voice Chat** - Click the microphone button to speak with the AI
- **Text Chat** - Type messages directly in the input field
- **Real-time Audio Streaming** - Hear responses as they're generated
- **Conversation History** - See all messages in a clean bubble interface

### 📤 File Upload & Ingestion
- Upload multiple documents (PDF, TXT, MD, DOCX)
- Files are automatically processed and stored in the vector database
- Authenticated API calls ensure secure file uploads
- Visual feedback on ingestion progress and results

## Configuration

The Streamlit app automatically uses configuration from `src/core/control.py`:
- **Server Host/Port** - `SERVER_HOST` and `SERVER_PORT` (default: 0.0.0.0:8026)
- **API URLs** - `API_BASE_URL` and `WS_BASE_URL` automatically constructed

To change the server port or URLs, edit `src/core/control.py` instead of hardcoding values.

## Running the Application

### Prerequisites
1. Backend server must be running (configured in `src/core/control.py`):
   ```bash
   python -m src.main
   ```

2. Database must be initialized (PostgreSQL running on localhost:5432)

3. Environment variables must be configured (see `.env` in project root)

### Start Streamlit
```bash
streamlit run streamlit/app.py
```

The application will open in your browser at `http://localhost:8501`

## Usage Flow

1. **First Time Users**
   - Navigate to the "Register" tab
   - Enter email and password (meeting strength requirements)
   - Click "Register"
   - Switch to "Login" tab

2. **Returning Users**
   - Enter credentials on "Login" tab
   - Click "Login"
   - Access granted to chat interface

3. **Chat & Upload**
   - Use the voice button or text input to interact with the AI
   - Upload documents via the sidebar
   - Logout using the button in the sidebar

## Authentication Flow

```
User → Streamlit → FastAPI Backend
              ↓
        JWT Token Generated
              ↓
        Stored in Session State
              ↓
    Passed to WebSocket & API Calls
              ↓
        Backend Validates Token
              ↓
        User ID Linked to Session
```

## API Endpoints Used

- `POST /api/auth/register` - Create new user account
- `POST /api/auth/login` - Login and receive JWT token
- `GET /api/auth/me` - Get current user details
- `POST /api/upload/batch` - Upload and ingest documents
- `WS /ws/chat?session_id=<id>&token=<jwt>` - WebSocket for real-time chat

## Security Features

- JWT tokens with configurable expiration (default: 60 minutes)
- Password hashing with bcrypt
- Token validation on every WebSocket connection
- Session-based authentication state management
- Secure password input fields

## Troubleshooting

**"Cannot connect to server"**
- Ensure backend is running: `python -m src.main`
- Check that the configured port is available (see `SERVER_PORT` in `src/core/control.py`)
- Verify `API_BASE_URL` and `WS_BASE_URL` in `src/core/control.py` match your setup

**"Login failed"**
- Verify credentials are correct
- Check database connection
- Ensure JWT_SECRET is set in `.env`

**"Upload failed"**
- Verify you're logged in
- Check file format is supported
- Ensure backend has write permissions for temp_uploads/

## Development Notes

- Authentication state persists across page refreshes (Streamlit session state)
- Tokens are automatically included in all authenticated API requests
- WebSocket connections pass the JWT token as a query parameter
- User ID is linked to session logs in the database for analytics
