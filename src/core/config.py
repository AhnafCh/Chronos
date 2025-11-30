from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "Chronos"
    DEBUG: bool = True
    
    # AI Providers
    OPENAI_API_KEY: str | None = None
    DEEPGRAM_API_KEY: str | None = None
    ELEVENLABS_API_KEY: str | None = None
    PINECONE_API_KEY: str | None = None

    # Infrastructure
    REDIS_URL: str = "redis://localhost:6379"

    # Audio Settings
    INPUT_SAMPLE_RATE: int = 16000  # Standard for Speech to Text
    OUTPUT_SAMPLE_RATE: int = 24000 # Good quality for TTS

    # THIS SECTION FIXES THE ERROR
    # It tells Pydantic: "If you see a variable in .env that isn't listed above, just ignore it."
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore" 
    )

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()