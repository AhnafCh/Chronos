import asyncio
import logging
from typing import AsyncGenerator
from fastapi import WebSocket, WebSocketDisconnect
from src.core.interfaces import ASRInterface, LLMInterface, TTSInterface

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self, websocket: WebSocket, asr: ASRInterface, llm: LLMInterface, tts: TTSInterface):
        self.websocket = websocket
        self.asr = asr
        self.llm = llm
        self.tts = tts
        # Queue for passing text from ASR -> LLM
        self.transcription_queue = asyncio.Queue()

    async def connect(self):
        await self.websocket.accept()
        logger.info("Client connected")

        # 1. Start ASR Background Connection
        # This sets up the Deepgram websocket and tells it to write to our queue
        await self.asr.start(self.transcription_queue)

        # 2. Start Independent Tasks
        # Task A: Listen to Client Audio (The Ear)
        receive_task = asyncio.create_task(self.receive_audio())
        # Task B: Process Transcripts (The Brain & Mouth)
        process_task = asyncio.create_task(self.run_brain())

        try:
            # 3. Keep connection alive
            # If either task fails/finishes, we exit
            await asyncio.gather(receive_task, process_task)
        except WebSocketDisconnect:
            logger.info("Client disconnected gracefully")
        except Exception as e:
            logger.error(f"Connection error: {e}")
        finally:
            # Cleanup on exit
            await self.asr.stop()
            logger.info("Connection resources cleaned up")

    async def receive_audio(self):
        """
        Input Actor: Listens to WebSocket and pushes raw bytes to ASR.
        """
        try:
            while True:
                # Expecting raw PCM bytes from client
                data = await self.websocket.receive_bytes()
                # Send immediately to Deepgram (Fire and Forget)
                await self.asr.process(data)
        except WebSocketDisconnect:
            raise # Let the main loop handle the disconnect
        except Exception as e:
            logger.error(f"Error receiving audio: {e}")
            raise

    async def run_brain(self):
        """
        Brain & Output Actor:
        1. Waits for Text from ASR Queue
        2. Sends to LLM
        3. Buffers Tokens into Sentences
        4. Sends to TTS
        5. Streams Audio back to Client
        """
        while True:
            # 1. Wait for a final transcript from ASR
            transcript = await self.transcription_queue.get()
            
            if not transcript:
                continue

            logger.info(f"User said: {transcript}")

            # 2. Generate Tokens (LLM)
            # We use the Interface method: generate_response
            token_generator = self.llm.generate_response(transcript)
            
            # 3. Buffer Tokens into Sentences (Better TTS quality)
            sentence_generator = self.text_chunker(token_generator)
            
            # 4. Synthesize & Stream (TTS)
            async for sentence in sentence_generator:
                logger.info(f"Speaking: {sentence}")
                
                # Stream audio chunks from TTS
                async for audio_chunk in self.tts.speak(sentence):
                    # 5. Send back to User immediately
                    await self.websocket.send_bytes(audio_chunk)

    async def text_chunker(self, chunks: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        """
        Aggregates tokens into full sentences to optimize TTS audio quality.
        Does not wait for the whole response; yields as soon as a sentence is ready.
        """
        buffer = ""
        # Punctuation that marks the end of a sentence
        punctuation = {".", "?", "!", ":", ";"}
        
        async for text in chunks:
            buffer += text
            
            # Check for punctuation
            last_punc_index = -1
            for p in punctuation:
                idx = buffer.rfind(p)
                if idx > last_punc_index:
                    last_punc_index = idx
            
            if last_punc_index != -1:
                # We found a complete sentence
                sentence = buffer[:last_punc_index+1]
                buffer = buffer[last_punc_index+1:]
                
                # Clean up and yield
                sentence = sentence.strip()
                if sentence:
                    yield sentence

        # Yield remaining buffer if any (the last sentence might miss punctuation)
        if buffer.strip():
            yield buffer.strip()