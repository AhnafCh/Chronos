import asyncio
from typing import AsyncGenerator
from src.core.interfaces import ASRInterface, LLMInterface, TTSInterface

class MockASR(ASRInterface):
    async def transcribe(self, audio_chunk: bytes) -> str:
        # Simulate processing time
        await asyncio.sleep(0.05) 
        # For testing, we assume every chunk containing data is "Ping"
        if len(audio_chunk) > 0:
            return "Ping"
        return ""

class MockLLM(LLMInterface):
    async def generate(self, prompt: str) -> AsyncGenerator[str, None]:
        # Simulate thinking
        await asyncio.sleep(0.1)
        response = f"Echo: {prompt}"
        for word in response.split():
            yield word + " "
            await asyncio.sleep(0.05) # Simulate streaming latency

class MockTTS(TTSInterface):
    async def synthesize(self, text: str) -> AsyncGenerator[bytes, None]:
        # Return dummy bytes (noise) representing audio
        # In reality, this would be MP3/PCM data
        yield b'\x00\x01\x02'