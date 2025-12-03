from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "Chronos"
    DEBUG: bool = False
    
    # AI Providers
    OPENAI_API_KEY: str | None = None
    DEEPGRAM_API_KEY: str | None = None
    ELEVENLABS_API_KEY: str | None = None

    # Vector Store
    PINECONE_API_KEY: str | None = None
    PINECONE_INDEX_NAME: str = "chronos-index"

    # Caching
    # REDIS_URL: str = "redis://localhost:6379"

    # Database
    DATABASE_URL: str | None = None
    
    # Authentication
    JWT_SECRET: str | None = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Audio Settings
    INPUT_SAMPLE_RATE: int = 16000  # Standard for Speech to Text
    OUTPUT_SAMPLE_RATE: int = 24000 # Good quality for TTS

    # Ignore unused env vars
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore" 
    )

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()