from abc import ABC, abstractmethod
import asyncio
from typing import AsyncGenerator 

class ASRInterface(ABC):
    @abstractmethod
    async def start(self, output_queue: asyncio.Queue):
        pass

    @abstractmethod
    async def process(self, audio_chunk: bytes):
        pass

    @abstractmethod
    async def stop(self):
        pass

class LLMInterface(ABC):
    @abstractmethod
    # FIX: Use AsyncGenerator, not asyncio.AsyncGenerator
    async def generate_response(self, query: str) -> AsyncGenerator[str, None]:
        yield "abstract_yield"
    
    @abstractmethod
    def get_usage_stats(self) -> dict:
        pass

class TTSInterface(ABC):
    @abstractmethod
    # FIX: Use AsyncGenerator, not asyncio.AsyncGenerator
    async def speak(self, text: str) -> AsyncGenerator[bytes, None]:
        yield b"abstract_yield"