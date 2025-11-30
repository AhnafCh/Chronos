import asyncio
import websockets

async def test_audio_loop():
    uri = "ws://localhost:8000/ws/chat"
    async with websockets.connect(uri) as websocket:
        print("Connected to Chronos")
        
        # Simulate sending 5 chunks of "audio" (random bytes)
        for i in range(5):
            dummy_audio = b'\x99' * 1024 # Fake audio chunk
            print(f"Sending chunk {i}...")
            await websocket.send(dummy_audio)
            await asyncio.sleep(0.5)

            # Listen for response (Echo)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                print(f"Received audio back: {len(response)} bytes")
            except asyncio.TimeoutError:
                print("No response yet...")

if __name__ == "__main__":
    asyncio.run(test_audio_loop())