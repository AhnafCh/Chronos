import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Chronos Voice Agent", layout="wide")

st.title("🎙️ Chronos Voice RAG Agent")
st.markdown("This client connects directly to your local **FastAPI WebSocket** (`ws://localhost:8026/ws/chat`).")

# --- CSS STYLING ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
</style>
""", unsafe_allow_html=True)

# --- JAVASCRIPT CLIENT ---
html_code = """
<!DOCTYPE html>
<html>
<head>
    <title>Chronos Client</title>
    <style>
        body { font-family: sans-serif; margin: 0; padding: 0; }
        .container { padding: 20px; border: 1px solid #ddd; border-radius: 10px; text-align: center; }
        .controls { margin-bottom: 20px; }
        .btn { padding: 15px 32px; font-size: 16px; border: none; border-radius: 5px; cursor: pointer; color: white; margin: 5px; }
        .btn-start { background-color: #4CAF50; }
        .btn-stop { background-color: #f44336; }
        .btn:disabled { background-color: #ccc; cursor: not-allowed; }
        
        /* Chat Box Styling */
        #chat-box {
            height: 300px;
            overflow-y: auto;
            border: 1px solid #eee;
            border-radius: 5px;
            padding: 10px;
            background-color: #000000;
            text-align: left;
            margin-top: 15px;
            display: flex;
            flex-direction: column;
        }
        .message {
            margin: 5px 0;
            padding: 8px 12px;
            border-radius: 15px;
            max-width: 80%;
            word-wrap: break-word;
        }
        .user {
            align-self: flex-end;
            background-color: #DCF8C6;
            color: #000;
        }
        .bot {
            align-self: flex-start;
            background-color: #E8E8E8;
            color: #000;
        }
        .status { font-weight: bold; color: gray; }
    </style>
</head>
<body>
    <div class="container">
        <h3>Status: <span id="status" class="status">Disconnected</span></h3>
        
        <div class="controls">
            <button id="startBtn" class="btn btn-start">📞 Start Call</button>
            <button id="stopBtn" class="btn btn-stop" disabled>🛑 End Call</button>
        </div>

        <!-- Chat Transcript Area -->
        <div id="chat-box">
            <div style="text-align: center; color: #888; font-size: 0.9em;">
                <i>Transcript will appear here...</i>
            </div>
        </div>
    </div>

    <script>
        let socket;
        let audioContext;
        let processor;
        let input;
        let globalStream;
        
        let audioQueue = [];
        let isPlaying = false;

        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const statusSpan = document.getElementById('status');
        const chatBox = document.getElementById('chat-box');

        function appendMessage(role, text) {
            const div = document.createElement('div');
            div.className = `message ${role === 'user' ? 'user' : 'bot'}`;
            div.innerText = text;
            chatBox.appendChild(div);
            // Auto-scroll to bottom
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        async function playQueue() {
            if (isPlaying || audioQueue.length === 0) return;
            isPlaying = true;

            const audioBlob = audioQueue.shift();
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);

            audio.onended = () => {
                isPlaying = false;
                playQueue();
            };
            
            try {
                await audio.play();
            } catch (e) {
                console.error("Playback error:", e);
                isPlaying = false;
            }
        }

        startBtn.onclick = async () => {
            // Connect to WebSocket
            socket = new WebSocket("ws://localhost:8026/ws/chat");
            
            // IMPORTANT: We do NOT set binaryType to 'arraybuffer' immediately here
            // because we need to detect strings vs binary automatically.
            // Most browsers handle mixed types fine by default.

            socket.onopen = () => {
                statusSpan.innerText = "Connected";
                statusSpan.style.color = "green";
                startBtn.disabled = true;
                stopBtn.disabled = false;
                chatBox.innerHTML = ""; // Clear previous chat
                startAudio();
            };

            socket.onmessage = (event) => {
                const data = event.data;

                // 1. Handle TEXT (JSON Transcript)
                if (typeof data === "string") {
                    try {
                        const msg = JSON.parse(data);
                        if (msg.type === "conversation_item") {
                            appendMessage(msg.role, msg.content);
                        }
                    } catch (e) {
                        console.error("Error parsing JSON:", e);
                    }
                } 
                // 2. Handle BINARY (Audio Blob)
                else if (data instanceof Blob) {
                    audioQueue.push(data);
                    playQueue();
                }
            };

            socket.onclose = () => {
                statusSpan.innerText = "Disconnected";
                statusSpan.style.color = "gray";
                stopAudio();
                startBtn.disabled = false;
                stopBtn.disabled = true;
            };
        };

        stopBtn.onclick = () => {
            if (socket) socket.close();
            stopAudio();
        };

        async function startAudio() {
            try {
                audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                globalStream = stream;
                input = audioContext.createMediaStreamSource(stream);
                processor = audioContext.createScriptProcessor(4096, 1, 1);

                input.connect(processor);
                processor.connect(audioContext.destination);

                processor.onaudioprocess = (e) => {
                    if (socket && socket.readyState === WebSocket.OPEN) {
                        const inputData = e.inputBuffer.getChannelData(0);
                        const buffer = new ArrayBuffer(inputData.length * 2);
                        const view = new DataView(buffer);
                        for (let i = 0; i < inputData.length; i++) {
                            let s = Math.max(-1, Math.min(1, inputData[i]));
                            view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
                        }
                        socket.send(buffer);
                    }
                };
            } catch (e) {
                alert("Microphone Error: " + e.message);
            }
        }

        function stopAudio() {
            if (processor) { processor.disconnect(); processor = null; }
            if (input) { input.disconnect(); input = null; }
            if (globalStream) { globalStream.getTracks().forEach(track => track.stop()); globalStream = null; }
            if (audioContext) { audioContext.close(); audioContext = null; }
        }
    </script>
</body>
</html>
"""

components.html(html_code, height=600)