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
        await self.asr.start(self.transcription_queue)

        # 2. Start Independent Tasks
        receive_task = asyncio.create_task(self.receive_audio())
        process_task = asyncio.create_task(self.run_brain())

        try:
            # 3. Keep connection alive
            await asyncio.gather(receive_task, process_task)
        except WebSocketDisconnect:
            logger.info("Client disconnected gracefully")
        except Exception as e:
            logger.error(f"Connection error: {e}")
        finally:
            # --- START: TOKEN USAGE LOGGING ---
            try:
                # We ask the LLM service for the accumulated stats
                stats = self.llm.get_usage_stats()
                # We safely get the thread_id if available
                session_id = getattr(self.llm, 'thread_id', 'unknown')
                
                logger.info("--- CALL SUMMARY ---")
                logger.info(f"Session ID: {session_id}")
                logger.info(f"Token Usage: {stats}")
                logger.info("--------------------")
            except Exception as e:
                logger.warning(f"Could not log token stats: {e}")
            # --- END: TOKEN USAGE LOGGING ---

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
            
            # Send User Text to Frontend
            await self.websocket.send_json({
                "type": "conversation_item",
                "role": "user",
                "content": transcript
            })

            # 2. Generate Tokens (LLM)
            token_generator = self.llm.generate_response(transcript)
            
            # 3. Buffer Tokens into Sentences (Better TTS quality)
            sentence_generator = self.text_chunker(token_generator)
            
            # 4. Synthesize & Stream (TTS)
            async for sentence in sentence_generator:
                logger.info(f"Speaking: {sentence}")

                # Send Bot Text to Frontend
                await self.websocket.send_json({
                    "type": "conversation_item",
                    "role": "assistant",
                    "content": sentence
                })
                
                # --- FIX FOR SMOOTH AUDIO ---
                # Instead of sending tiny chunks, we collect the whole sentence 
                # audio and send it as one playable blob.
                full_sentence_audio = bytearray()
                
                async for audio_chunk in self.tts.speak(sentence):
                    full_sentence_audio.extend(audio_chunk)
                
                # Send the complete sentence audio at once
                if len(full_sentence_audio) > 0:
                    await self.websocket.send_bytes(full_sentence_audio)
                # ----------------------------

    async def text_chunker(self, chunks: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        """
        Aggregates tokens into full sentences to optimize TTS audio quality.
        """
        buffer = ""
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
                sentence = buffer[:last_punc_index+1]
                buffer = buffer[last_punc_index+1:]
                
                sentence = sentence.strip()
                if sentence:
                    yield sentence

        if buffer.strip():
            yield buffer.strip()