import asyncio
import struct
import logging
import time
from typing import AsyncGenerator
from openai import AsyncOpenAI
from src.core.interfaces import TTSInterface
from src.core.config import settings
from src.core import control

logger = logging.getLogger(__name__)

class OpenAITTS(TTSInterface):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    def create_wav_header(self, data_size: int, sample_rate: int | None = None, channels: int | None = None, bits_per_sample: int | None = None) -> bytes:
        """
        Create a WAV header for PCM audio data.
        OpenAI TTS PCM format is: 24kHz, 16-bit, mono
        """
        # Use control.py settings as defaults
        sample_rate = sample_rate or control.TTS_OUTPUT_SAMPLE_RATE
        channels = channels or control.TTS_OUTPUT_CHANNELS
        bits_per_sample = bits_per_sample or control.TTS_OUTPUT_BITS_PER_SAMPLE
        byte_rate = sample_rate * channels * bits_per_sample // 8
        block_align = channels * bits_per_sample // 8
        
        header = struct.pack('<4sI4s', b'RIFF', data_size + 36, b'WAVE')
        header += struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, channels, sample_rate, byte_rate, block_align, bits_per_sample)
        header += struct.pack('<4sI', b'data', data_size)
        
        return header

    async def speak(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        Stream audio with optimized buffering - balance between latency and quality.
        Uses configurable buffer size to prevent audio breakup while keeping latency low.
        
        Performance metrics are logged when ENABLE_PERFORMANCE_LOGGING is enabled.
        """
        if not text:
            return

        start_time = time.time()
        first_chunk_time = None
        total_bytes = 0
        chunks_sent = 0
        
        try:
            # Use mp3 format for better streaming support
            # Buffer chunks to ensure complete mp3 frames for smooth playback
            buffer = b''
            buffer_size = control.TTS_BUFFER_SIZE
            
            if control.ENABLE_PERFORMANCE_LOGGING:
                logger.debug(f"TTS: Starting synthesis for {len(text)} characters")
                logger.debug(f"TTS: Buffer size: {buffer_size} bytes, Chunk size: {control.TTS_CHUNK_SIZE} bytes")
            
            async with self.client.audio.speech.with_streaming_response.create(
                model=control.TTS_MODEL,
                voice=control.TTS_VOICE,
                input=text,
                response_format="mp3",
                speed=control.TTS_SPEED
            ) as response:
                async for chunk in response.iter_bytes(chunk_size=control.TTS_CHUNK_SIZE):
                    if chunk:
                        buffer += chunk
                        
                        # Send buffer when it reaches optimal size
                        if len(buffer) >= buffer_size:
                            if first_chunk_time is None:
                                first_chunk_time = time.time()
                                if control.ENABLE_PERFORMANCE_LOGGING:
                                    latency = (first_chunk_time - start_time) * 1000
                                    logger.debug(f"TTS: First chunk latency: {latency:.1f}ms")
                            
                            yield buffer
                            total_bytes += len(buffer)
                            chunks_sent += 1
                            buffer = b''
                
                # Send any remaining data
                if buffer:
                    if first_chunk_time is None:
                        first_chunk_time = time.time()
                    yield buffer
                    total_bytes += len(buffer)
                    chunks_sent += 1
            
            # Log performance metrics
            if control.ENABLE_PERFORMANCE_LOGGING:
                total_time = (time.time() - start_time) * 1000
                logger.debug(f"TTS: Complete - {total_bytes} bytes in {chunks_sent} chunks, {total_time:.1f}ms total")
                if chunks_sent > 0:
                    logger.debug(f"TTS: Avg chunk size: {total_bytes / chunks_sent:.0f} bytes")

        except Exception as e:
            logger.error(f"TTS Error: {e}")
            if control.ENABLE_PERFORMANCE_LOGGING:
                logger.debug(f"TTS: Failed after {(time.time() - start_time) * 1000:.1f}ms")