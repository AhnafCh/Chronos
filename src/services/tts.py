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
            # tts-1 is optimized for speed (lower latency than tts-1-hd)
            # alloy voice is fast and natural
            # pcm16 has lower overhead than mp3 for streaming
            async with self.client.audio.speech.with_streaming_response.create(
                model="tts-1",  # Fastest model
                voice="alloy",  # Fast, natural voice
                input=text,
                response_format="pcm",  # Lower latency than mp3
                speed=1.1  # Slightly faster speech for reduced latency
            ) as response:
                # Smaller chunks for lower latency
                async for chunk in response.iter_bytes(chunk_size=2048):
                    if chunk:
                        yield chunk

        except Exception as e:
            print(f"TTS Error: {e}")