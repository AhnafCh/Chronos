import asyncio
from typing import AsyncGenerator
from openai import AsyncOpenAI
from src.core.interfaces import TTSInterface
from src.core.config import settings

class OpenAITTS(TTSInterface):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def speak(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        Stream audio bytes from OpenAI TTS-1 using the streaming wrapper.
        """
        if not text:
            return

        try:
            # Using 'with_streaming_response' to get a true async stream
            async with self.client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice="onyx",
                input=text,
                response_format="mp3"
            ) as response:
                # response.iter_bytes() is an async iterator here
                async for chunk in response.iter_bytes(chunk_size=4096):
                    if chunk:
                        yield chunk

        except Exception as e:
            print(f"TTS Error: {e}")