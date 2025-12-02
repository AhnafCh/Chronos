import asyncio
import logging
import re
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
        # Queue for passing text from ASR -> LLM with input type info
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
        Input Actor: Listens to WebSocket and handles:
        - Raw audio bytes → ASR
        - Text JSON messages → Directly to transcription queue
        """
        try:
            while True:
                # Check message type
                message = await self.websocket.receive()
                
                # Handle text messages (chat input)
                if "text" in message:
                    import json
                    try:
                        data = json.loads(message["text"])
                        if data.get("type") == "text":
                            # Bypass ASR, send text directly to brain with input_type marker
                            await self.transcription_queue.put({
                                "text": data.get("content", ""),
                                "input_type": "text"
                            })
                    except json.JSONDecodeError:
                        logger.warning("Received invalid JSON text message")
                
                # Handle binary messages (audio input)
                elif "bytes" in message:
                    # Send immediately to Deepgram (Fire and Forget)
                    await self.asr.process(message["bytes"])
                    
        except WebSocketDisconnect:
            raise # Let the main loop handle the disconnect
        except Exception as e:
            logger.error(f"Error receiving data: {e}")
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
            queue_item = await self.transcription_queue.get()
            
            # Handle both old string format and new dict format
            if isinstance(queue_item, dict):
                transcript = queue_item.get("text", "")
                input_type = queue_item.get("input_type", "voice")
            else:
                # Legacy: if it's just a string, assume it's from voice
                transcript = queue_item
                input_type = "voice"
            
            if not transcript:
                continue

            logger.info(f"User said: {transcript} (input_type: {input_type})")
            
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
            
            # 4. Synthesize & Stream (TTS) - Only if input was voice
            async for sentence in sentence_generator:
                logger.info(f"Speaking: {sentence}")

                # Send Bot Text to Frontend immediately
                await self.websocket.send_json({
                    "type": "conversation_item",
                    "role": "assistant",
                    "content": sentence
                })
                
                # Only generate and send audio if the input was voice
                if input_type == "voice":
                    # PARALLEL PROCESSING: Start TTS immediately and stream as chunks arrive
                    # This reduces perceived latency - audio starts playing sooner
                    async for audio_chunk in self.tts.speak(sentence):
                        if audio_chunk:
                            await self.websocket.send_bytes(audio_chunk)

    async def text_chunker(self, chunks: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        """
        Aggregates tokens into full sentences to optimize TTS audio quality.
        Handles emails, URLs, abbreviations, and decimals intelligently.
        """
        buffer = ""
        
        # Pattern to match sentence-ending punctuation that's NOT part of:
        # - Email addresses (word@word.word)
        # - URLs (http://example.com or www.example.com)
        # - Common abbreviations (Dr., Mr., Mrs., Ms., etc.)
        # - Decimals (3.14)
        # - File extensions (.txt, .pdf)
        sentence_end_pattern = re.compile(
            r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s+'
            r'|(?<=\?)\s+'
            r'|(?<=!)\s+'
            r'|(?<=:)\s+(?=[A-Z])'  # Colon followed by capital letter
            r'|(?<=;)\s+'
        )
        
        async for text in chunks:
            buffer += text
            
            # Look for sentence boundaries
            matches = list(sentence_end_pattern.finditer(buffer))
            
            if matches:
                # Get the position of the last match
                last_match = matches[-1]
                sentence_end_pos = last_match.start()
                
                # Extract the complete sentence(s)
                sentence = buffer[:sentence_end_pos].strip()
                buffer = buffer[sentence_end_pos:].strip()
                
                if sentence:
                    yield sentence

        # Yield any remaining content
        if buffer.strip():
            yield buffer.strip()