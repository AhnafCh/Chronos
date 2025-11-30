import pkg_resources
import deepgram
import sys

print("--- DEBUG INFO ---")
try:
    version = pkg_resources.get_distribution("deepgram-sdk").version
    print(f"Deepgram SDK Version: {version}")
except:
    print("Could not detect version.")

print(f"Deepgram Location: {deepgram.__file__}")

print("\n--- ATTEMPTING IMPORTS ---")

# Check 1: Top Level
if "LiveTranscriptionEvents" in dir(deepgram):
    print("✅ Found at: deepgram.LiveTranscriptionEvents")
else:
    print("❌ Not at top level")

# Check 2: Clients Module
try:
    from deepgram.clients.live.v1 import LiveTranscriptionEvents
    print("✅ Found at: deepgram.clients.live.v1.LiveTranscriptionEvents")
except ImportError:
    print("❌ Not at deepgram.clients.live.v1")

# Check 3: Enums Module
try:
    from deepgram.enums import LiveTranscriptionEvents
    print("✅ Found at: deepgram.enums.LiveTranscriptionEvents")
except ImportError:
    print("❌ Not at deepgram.enums")

# Check 4: Inspecting internal structure
try:
    import deepgram.clients.live.enums
    print("🔍 Inspecting deepgram.clients.live.enums...")
    print(dir(deepgram.clients.live.enums))
except ImportError:
    print("❌ Could not import deepgram.clients.live.enums")

print("------------------")