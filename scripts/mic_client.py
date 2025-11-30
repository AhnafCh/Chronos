import asyncio
import websockets
import pyaudio
import sys

# --- CONFIGURATION ---
# These must match the Deepgram settings in asr.py
CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# File to save the bot's response
OUTPUT_FILE = "bot_response.mp3"

async def send_mic_audio(websocket, stream):
    print("🎤  Microphone Live! Speak now... (say 'Hello')")
    try:
        while True:
            # Read raw audio data from microphone
            data = stream.read(CHUNK, exception_on_overflow=False)
            # Send raw bytes to server
            await websocket.send(data)
            # Small sleep to allow context switch
            await asyncio.sleep(0.001) 
    except Exception as e:
        print(f"Mic Error: {e}")

async def receive_audio(websocket):
    print(f"🎧  Listening for response... (Saving to {OUTPUT_FILE})")
    
    # Open file in binary write mode
    with open(OUTPUT_FILE, "wb") as f:
        try:
            while True:
                # Receive MP3 chunks from server
                audio_chunk = await websocket.recv()
                
                if isinstance(audio_chunk, str):
                    print(f"Server Message: {audio_chunk}")
                else:
                    print(f"   < Received audio chunk: {len(audio_chunk)} bytes")
                    f.write(audio_chunk)
                    # Flush to ensure data is written immediately
                    f.flush()
                    
        except websockets.exceptions.ConnectionClosed:
            print("Server connection closed.")

async def run():
    uri = "ws://localhost:8000/ws/chat"
    
    # Setup PyAudio (Microphone)
    p = pyaudio.PyAudio()
    
    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
    except OSError as e:
        print("❌ Could not open microphone. Check your default audio device.")
        print(e)
        return

    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected! Press Ctrl+C to stop.")
            
            # Run send and receive loops in parallel
            await asyncio.gather(
                send_mic_audio(websocket, stream),
                receive_audio(websocket)
            )
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Connection Error: {e}")
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        p.terminate()

if __name__ == "__main__":
    asyncio.run(run())