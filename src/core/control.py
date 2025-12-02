"""
Control Panel
=========================
"""

from typing import Literal

# ============================================================================
# Server Configuration
# ============================================================================

# Server Host
# "0.0.0.0" = listen on all interfaces, "127.0.0.1" = localhost only
SERVER_HOST: str = "0.0.0.0"

# Server Port
SERVER_PORT: int = 8026

# API Base URL for clients (used by frontend)
# Use localhost for local development, or your domain for production
API_BASE_URL: str = f"http://localhost:{SERVER_PORT}"

# WebSocket Base URL for clients
WS_BASE_URL: str = f"ws://localhost:{SERVER_PORT}"

# ============================================================================
# LLM (Language Model) Settings
# ============================================================================

# Model Selection
# Options: Open AI text generation models
LLM_MODEL: str = "gpt-4o-mini"

# Temperature (0.0 = deterministic, 2.0 = very creative)
# Lower = more focused, Higher = more creative/random
LLM_TEMPERATURE: float = 0.7

# Max Tokens to Generate
# Controls response length. Higher = longer responses, higher cost
LLM_MAX_TOKENS: int = 1000

# ============================================================================
# ASR (Speech-to-Text) Settings - Deepgram
# ============================================================================

# Model Selection
# Options: "nova-2" (fastest), "nova", "enhanced", "base"
ASR_MODEL: str = "nova-2"

# Language
ASR_LANGUAGE: str = "en-US"

# Smart Formatting (adds punctuation, capitalization)
ASR_SMART_FORMAT: bool = True

# Input Audio Format
ASR_ENCODING: str = "linear16"
ASR_CHANNELS: int = 1
ASR_SAMPLE_RATE: int = 16000

# End-of-Speech Detection (in milliseconds)
# How long to wait after silence before considering speech ended
# Lower = faster responses but may cut off speech
# Higher = more complete phrases but slower responses
ASR_ENDPOINTING_MS: int = 1000

# Keepalive (prevents timeout after 10s of silence)
ASR_KEEPALIVE: bool = True

# ============================================================================
# TTS (Text-to-Speech) Settings - OpenAI
# ============================================================================

# Model Selection
# Options: "tts-1" (fastest), "tts-1-hd" (higher quality, slower)
TTS_MODEL: str = "tts-1"

# Voice Selection
# Options: "alloy", "echo", "fable", "onyx", "nova", "shimmer"
TTS_VOICE: str = "alloy"

# Response Format
# Options: "pcm" (lowest latency), "mp3", "opus", "aac", "flac", "wav"
TTS_RESPONSE_FORMAT: str = "pcm"

# Speech Speed (0.25 to 4.0)
# 1.0 = normal, <1.0 = slower, >1.0 = faster
TTS_SPEED: float = 1.1

# Audio Output Settings (for PCM format)
TTS_OUTPUT_SAMPLE_RATE: int = 24000
TTS_OUTPUT_CHANNELS: int = 1
TTS_OUTPUT_BITS_PER_SAMPLE: int = 16

# Audio Chunk Size (bytes)
# Smaller = more frequent updates, Higher = fewer network calls
TTS_CHUNK_SIZE: int = 2048

# TTS Streaming Buffer Size (bytes)
# Controls buffering before sending audio chunks to client
# Smaller = lower latency but may cause audio breakup
# Larger = smoother audio but slightly higher latency
# Recommended: 4096-16384 for good balance
TTS_BUFFER_SIZE: int = 19000

# ============================================================================
# RAG (Retrieval-Augmented Generation) Settings - Pinecone
# ============================================================================

# Embedding Model
# Options: "text-embedding-3-small" (faster), "text-embedding-3-large" (better quality)
RAG_EMBEDDING_MODEL: str = "text-embedding-3-small"

# Number of Documents to Retrieve
# Lower = faster, less context; Higher = more context, slower
RAG_TOP_K: int = 2

# Similarity Threshold (0.0 to 1.0)
# Higher = only very similar docs, Lower = more diverse results
RAG_SIMILARITY_THRESHOLD: float = 0.7

# ============================================================================
# WebSocket & Connection Settings
# ============================================================================

# Audio Input Buffer Size (bytes)
# How much audio data to accumulate before sending to ASR
WS_AUDIO_BUFFER_SIZE: int = 4096

# Ping Interval (seconds)
# How often to send keepalive pings to maintain connection
WS_PING_INTERVAL: int = 30

# Connection Timeout (seconds)
WS_CONNECTION_TIMEOUT: int = 300

# ============================================================================
# Text Processing & Buffering
# ============================================================================

# Sentence Chunking for TTS
# Whether to buffer LLM tokens into complete sentences before TTS
# True = better audio quality, slight delay
# False = faster but may sound choppy
ENABLE_SENTENCE_BUFFERING: bool = True

# ============================================================================
# Response Quality vs Speed Trade-offs
# ============================================================================

# Parallel TTS Processing
# Start playing audio while still generating text
# True = lowest latency, False = wait for full text before audio
PARALLEL_TTS_PROCESSING: bool = True

# ============================================================================
# Performance Monitoring
# ============================================================================

# Token Usage Logging
# Track input/output tokens for cost analysis
ENABLE_TOKEN_LOGGING: bool = True

# Detailed Performance Logging
# Log timing for each component (ASR, LLM, TTS)
ENABLE_PERFORMANCE_LOGGING: bool = False

# Log Level for Voice Pipeline
# Options: "DEBUG", "INFO", "WARNING", "ERROR"
VOICE_PIPELINE_LOG_LEVEL: str = "INFO"

# ============================================================================
# Advanced Settings (Use with caution)
# ============================================================================

# ASR Interim Results
# Show partial transcripts while user is still speaking
ASR_INTERIM_RESULTS: bool = False

# VAD (Voice Activity Detection) Sensitivity
# How sensitive to detect speech vs silence
# Options: "low", "medium", "high"
VAD_SENSITIVITY: Literal["low", "medium", "high"] = "medium"

# ============================================================================
# Helper Functions
# ============================================================================

def get_all_settings() -> dict:
    """Return all current settings as a dictionary."""
    return {k: v for k, v in globals().items() if k.isupper() and not k.startswith('_')}

def print_current_config():
    """Print current configuration in a readable format."""
    print("\n" + "="*70)
    print("CHRONOS PERFORMANCE CONFIGURATION")
    print("="*70)
    
    settings = get_all_settings()
    categories = {
        "LLM": [k for k in settings if k.startswith("LLM_")],
        "ASR": [k for k in settings if k.startswith("ASR_")],
        "TTS": [k for k in settings if k.startswith("TTS_")],
        "RAG": [k for k in settings if k.startswith("RAG_")],
        "WebSocket": [k for k in settings if k.startswith("WS_")],
        "Other": [k for k in settings if not any(k.startswith(p) for p in ["LLM_", "ASR_", "TTS_", "RAG_", "WS_"])]
    }
    
    for category, keys in categories.items():
        if keys:
            print(f"\n{category} Settings:")
            print("-" * 70)
            for key in sorted(keys):
                print(f"  {key:40} = {settings[key]}")
    
    print("\n" + "="*70 + "\n")


# Run this to see current config
if __name__ == "__main__":
    print_current_config()
