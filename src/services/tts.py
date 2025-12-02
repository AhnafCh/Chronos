import asyncio
import struct
from typing import AsyncGenerator
from openai import AsyncOpenAI
from src.core.interfaces import TTSInterface
from src.core.config import settings

class OpenAITTS(TTSInterface):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    def create_wav_header(self, data_size: int, sample_rate: int = 24000, channels: int = 1, bits_per_sample: int = 16) -> bytes:
        """
        Create a WAV header for PCM audio data.
        OpenAI TTS PCM format is: 24kHz, 16-bit, mono
        """
        byte_rate = sample_rate * channels * bits_per_sample // 8
        block_align = channels * bits_per_sample // 8
        
        header = struct.pack('<4sI4s', b'RIFF', data_size + 36, b'WAVE')
        header += struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, channels, sample_rate, byte_rate, block_align, bits_per_sample)
        header += struct.pack('<4sI', b'data', data_size)
        
        return header

    async def speak(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        Stream audio bytes from OpenAI TTS-1 with WAV headers for browser playback.
        """
        if not text:
            return

        try:
            # Collect all PCM chunks first
            pcm_chunks = []
            
            async with self.client.audio.speech.with_streaming_response.create(
                model="tts-1",  # Fastest model
                voice="alloy",  # Fast, natural voice
                input=text,
                response_format="pcm",  # Lower latency than mp3
                speed=1.1  # Slightly faster speech for reduced latency
            ) as response:
                async for chunk in response.iter_bytes(chunk_size=2048):
                    if chunk:
                        pcm_chunks.append(chunk)
            
            # Combine all PCM data and add WAV header
            if pcm_chunks:
                pcm_data = b''.join(pcm_chunks)
                wav_header = self.create_wav_header(len(pcm_data))
                wav_audio = wav_header + pcm_data
                
                # Yield the complete WAV file as one chunk
                # (Browser needs complete WAV file to play)
                yield wav_audio

        except Exception as e:
            print(f"TTS Error: {e}")