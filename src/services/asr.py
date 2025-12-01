import asyncio
import logging
from typing import Optional

# 1. Keep the imports that we know work for your version
from deepgram.client import DeepgramClient
from deepgram.clients.live.v1 import LiveOptions
from deepgram import LiveTranscriptionEvents

from src.core.interfaces import ASRInterface
from src.core.config import settings

logger = logging.getLogger(__name__)

class DeepgramASR(ASRInterface):
    def __init__(self):
        try:
            self.client = DeepgramClient(settings.DEEPGRAM_API_KEY) # type: ignore
        except Exception as e:
            logger.error(f"Failed to initialize Deepgram Client: {e}")
            raise

        self.dg_connection = None
        self.queue: Optional[asyncio.Queue] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None  # Store the main loop here

    async def start(self, output_queue: asyncio.Queue):
        self.queue = output_queue
        
        # 1. CAPTURE THE MAIN LOOP
        # We need this to schedule tasks from Deepgram's background thread
        self.loop = asyncio.get_running_loop()
        
        try:
            self.dg_connection = self.client.listen.live.v("1") # type: ignore
        except AttributeError:
            logger.error("Deepgram Client configuration error.")
            return

        # 2. Define Event Handlers
        def on_message(self_dg, result, **kwargs):
            try:
                sentence = result.channel.alternatives[0].transcript
                
                if len(sentence) > 0 and result.is_final:
                    if self.queue is not None and self.loop is not None:
                        logger.info(f"ASR Transcript: {sentence}")
                        
                        # FIX: Use self.loop (Main Loop) instead of get_running_loop()
                        asyncio.run_coroutine_threadsafe(
                            self.queue.put(sentence), 
                            self.loop
                        )
            except Exception as e:
                logger.error(f"Error in Deepgram Callback: {e}")

        def on_error(self_dg, error, **kwargs):
            logger.error(f"Deepgram Error: {error}")

        if self.dg_connection:
            self.dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            self.dg_connection.on(LiveTranscriptionEvents.Error, on_error)

        try:
            options = LiveOptions(
                model="nova-2",
                language="en-US",
                smart_format=True,
                encoding="linear16", 
                channels=1,
                sample_rate=16000,
                endpointing="1000", # milliseconds of silence to consider end of speech
            )
            
            if self.dg_connection.start(options) is False:
                logger.error("Failed to start Deepgram connection")
                return

            logger.info("Deepgram Live Connection Started")
        
        except Exception as e:
            logger.error(f"Failed to configure Deepgram options: {e}")

    async def process(self, audio_chunk: bytes):
        if self.dg_connection:
            self.dg_connection.send(audio_chunk)

    async def stop(self):
        if self.dg_connection:
            self.dg_connection.finish()
            self.dg_connection = None
            logger.info("Deepgram Connection Closed")