import streamlit as st
import streamlit.components.v1 as components
import uuid
import requests
import sys
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import control
from auth_utils import init_auth_state, is_authenticated, get_auth_headers
from auth_components import render_auth_page, render_user_menu

st.set_page_config(page_title="Chronos AI", layout="centered")

# --- CONFIG ---
# Use configuration from control.py
WS_URL = f"{control.WS_BASE_URL}/ws/chat"
API_URL = control.API_BASE_URL

# Initialize authentication state
init_auth_state()

# Check if user is authenticated
if not is_authenticated():
    # Show login/register page
    render_auth_page()
    st.stop()

# Initialize session ID for authenticated users
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# --- SIDEBAR: File Upload ---
with st.sidebar:
    st.header("📤 Upload Documents")
    st.markdown("Upload files to enhance the AI's knowledge base")
    
    uploaded_files = st.file_uploader(
        "Choose files",
        type=["pdf", "txt", "md", "docx"],
        accept_multiple_files=True,
        help="Supported formats: PDF, TXT, MD, DOCX"
    )
    
    if st.button("🚀 Ingest Files", type="primary", disabled=not uploaded_files):
        if uploaded_files:
            with st.spinner("Processing and ingesting files..."):
                try:
                    # Prepare files for upload
                    files = [("files", (file.name, file.getvalue(), file.type)) for file in uploaded_files]
                    
                    # Upload to API with authentication headers
                    response = requests.post(
                        f"{API_URL}/api/upload/batch", 
                        files=files,
                        headers=get_auth_headers()
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ Successfully ingested {result['total_documents_ingested']} documents!")
                        
                        # Show details
                        with st.expander("📋 Details"):
                            for file_result in result['files']:
                                status_icon = "✅" if file_result['status'] == 'processed' else "❌"
                                st.write(f"{status_icon} **{file_result['filename']}**: {file_result.get('documents_extracted', 'N/A')} docs")
                    else:
                        error_detail = response.json().get('detail', 'Unknown error')
                        st.error(f"❌ Upload failed: {error_detail}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to server. Is it running on port 8026?")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    st.divider()
    st.caption("💡 Files are automatically processed and stored in the vector database")
    
    # Render user menu at the bottom of sidebar
    render_user_menu()

st.title("🤖 Chronos Unified Agent")

# Build WebSocket URL with authentication token
access_token = st.session_state.get("access_token", "")
ws_url_with_auth = f"{WS_URL}?session_id={st.session_state.session_id}"
if access_token:
    ws_url_with_auth += f"&token={access_token}"

# We pass the Session ID, URL, and Token to the JavaScript
js_code = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: "Source Sans Pro", sans-serif; margin: 0; padding: 0; }}
        
        /* Chat Container */
        #chat-container {{
            display: flex;
            flex-direction: column;
            height: 500px;
            border: 1px solid #ddd;
            border-radius: 12px;
            background: #fff;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}

        /* History Area */
        #history {{
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #fafafa;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        /* Message Bubbles */
        .bubble {{
            max-width: 80%;
            padding: 10px 14px;
            border-radius: 14px;
            font-size: 15px;
            line-height: 1.4;
            position: relative;
        }}
        .user {{
            align-self: flex-end;
            background-color: #007bff;
            color: white;
            border-bottom-right-radius: 2px;
        }}
        .assistant {{
            align-self: flex-start;
            background-color: #e9ecef;
            color: #333;
            border-bottom-left-radius: 2px;
        }}

        /* Input Area */
        #input-area {{
            padding: 15px;
            background: #fff;
            border-top: 1px solid #eee;
            display: flex;
            gap: 10px;
            align-items: center;
        }}

        input[type="text"] {{
            flex: 1;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 25px;
            outline: none;
            font-size: 15px;
        }}
        input[type="text"]:focus {{ border-color: #007bff; }}

        /* Buttons */
        .btn-icon {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            transition: all 0.2s;
        }}
        
        #micBtn {{ background: #f8f9fa; color: #333; border: 1px solid #ddd; }}
        #micBtn.active {{ background: #ff4b4b; color: white; border-color: #ff4b4b; animation: pulse 1.5s infinite; }}
        
        #sendBtn {{ background: #007bff; color: white; }}
        #sendBtn:hover {{ background: #0056b3; }}

        @keyframes pulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.4); }}
            70% {{ box-shadow: 0 0 0 10px rgba(255, 75, 75, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(255, 75, 75, 0); }}
        }}

        #status {{ font-size: 11px; color: #999; text-align: center; padding: 5px; }}
    </style>
</head>
<body>

    <div id="chat-container">
        <div id="status">Connecting...</div>
        <div id="history">
            <div style="text-align:center; color:#ccc; margin-top:20px;">start conversation...</div>
        </div>
        
        <div id="input-area">
            <button id="micBtn" class="btn-icon">🎙️</button>
            <input type="text" id="textInput" placeholder="Type a message..." disabled />
            <button id="sendBtn" class="btn-icon">➤</button>
        </div>
    </div>

    <script>
        const SESSION_ID = "{st.session_state.session_id}";
        const WS_URL = "{ws_url_with_auth}";
        
        // DOM Elements
        const historyDiv = document.getElementById('history');
        const textInput = document.getElementById('textInput');
        const sendBtn = document.getElementById('sendBtn');
        const micBtn = document.getElementById('micBtn');
        const statusDiv = document.getElementById('status');

        // State
        let socket;
        let audioContext, processor, input, globalStream;
        let isMicActive = false;
        let audioQueue = [];
        let isPlaying = false;

        // --- 1. WebSocket Logic ---
        function connect() {{
            socket = new WebSocket(WS_URL);
            
            socket.onopen = () => {{
                statusDiv.innerText = "Connected";
                textInput.disabled = false;
                textInput.focus();
            }};

            socket.onmessage = (event) => {{
                const data = event.data;
                
                // Handle Audio
                if (data instanceof Blob) {{
                    audioQueue.push(data);
                    playQueue();
                }} 
                // Handle JSON (Text Chat)
                else if (typeof data === "string") {{
                    try {{
                        const msg = JSON.parse(data);
                        if (msg.type === "conversation_item") {{
                            addBubble(msg.role, msg.content);
                        }}
                    }} catch (e) {{ console.error(e); }}
                }}
            }};

            socket.onclose = () => {{
                statusDiv.innerText = "Disconnected. Refresh to reconnect.";
                textInput.disabled = true;
                stopMic();
            }};
        }}

        // --- 2. Chat UI Logic ---
        function addBubble(role, text) {{
            // Remove placeholder
            if (historyDiv.innerText.includes("start conversation")) historyDiv.innerHTML = "";
            
            const div = document.createElement('div');
            div.className = `bubble ${{role}}`;
            div.innerText = text;
            historyDiv.appendChild(div);
            historyDiv.scrollTop = historyDiv.scrollHeight;
        }}

        function sendText() {{
            const text = textInput.value.trim();
            if (!text || socket.readyState !== WebSocket.OPEN) return;
            
            // Send JSON frame
            socket.send(JSON.stringify({{ type: "text", content: text }}));
            textInput.value = "";
        }}

        // Event Listeners for Text
        sendBtn.onclick = sendText;
        textInput.onkeypress = (e) => {{ if (e.key === 'Enter') sendText(); }};

        // --- 3. Audio Logic ---
        micBtn.onclick = () => {{
            if (!isMicActive) startMic();
            else stopMic();
        }};

        async function startMic() {{
            try {{
                audioContext = new (window.AudioContext || window.webkitAudioContext)({{ sampleRate: 16000 }});
                const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                globalStream = stream;
                input = audioContext.createMediaStreamSource(stream);
                processor = audioContext.createScriptProcessor(4096, 1, 1);
                input.connect(processor);
                processor.connect(audioContext.destination);

                processor.onaudioprocess = (e) => {{
                    if (socket && socket.readyState === WebSocket.OPEN) {{
                        const inputData = e.inputBuffer.getChannelData(0);
                        const buffer = new ArrayBuffer(inputData.length * 2);
                        const view = new DataView(buffer);
                        for (let i = 0; i < inputData.length; i++) {{
                            let s = Math.max(-1, Math.min(1, inputData[i]));
                            view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
                        }}
                        socket.send(buffer);
                    }}
                }};
                
                isMicActive = true;
                micBtn.classList.add("active");
                statusDiv.innerText = "Listening...";
                
            }} catch (e) {{ alert("Mic Error: " + e.message); }}
        }}

        function stopMic() {{
            if (processor) processor.disconnect();
            if (input) input.disconnect();
            if (globalStream) globalStream.getTracks().forEach(t => t.stop());
            if (audioContext) audioContext.close();
            
            isMicActive = false;
            micBtn.classList.remove("active");
            statusDiv.innerText = "Connected";
        }}

        async function playQueue() {{
            if (isPlaying || audioQueue.length === 0) return;
            isPlaying = true;
            const audioBlob = audioQueue.shift();
            const audio = new Audio(URL.createObjectURL(audioBlob));
            audio.onended = () => {{ isPlaying = false; playQueue(); }};
            await audio.play();
        }}

        // Init
        connect();

    </script>
</body>
</html>
"""

# Render the Unified Interface
components.html(js_code, height=600)