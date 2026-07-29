import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from google import genai

app = FastAPI(title="AI Agent Chat")

# Setup Gemini Client
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

class QueryRequest(BaseModel):
    prompt: str

# 1. API Endpoint for message processing
@app.post("/run")
def run_agent(request: QueryRequest):
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is missing.")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=request.prompt
        )
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Beautiful User Interface for Clients
@app.get("/", response_class=HTMLResponse)
def serve_chat_ui():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Agent Assistant</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            body { background-color: #f4f6f8; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .chat-container { width: 100%; max-width: 600px; height: 80vh; background: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); display: flex; flex-direction: column; overflow: hidden; }
            .chat-header { background: #2563eb; color: white; padding: 16px; font-weight: bold; font-size: 1.2rem; text-align: center; }
            .chat-box { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
            .message { max-width: 80%; padding: 12px 16px; border-radius: 18px; font-size: 0.95rem; line-height: 1.4; white-space: pre-wrap; }
            .user-msg { background-color: #2563eb; color: white; align-self: flex-end; border-bottom-right-radius: 4px; }
            .bot-msg { background-color: #e5e7eb; color: #1f2937; align-self: flex-start; border-bottom-left-radius: 4px; }
            .input-area { display: flex; padding: 12px; background: #fff; border-top: 1px solid #e5e7eb; gap: 8px; }
            input { flex: 1; padding: 12px 16px; border: 1px solid #d1d5db; border-radius: 24px; outline: none; font-size: 1rem; }
            input:focus { border-color: #2563eb; }
            button { background: #2563eb; color: white; border: none; padding: 0 20px; border-radius: 24px; font-weight: bold; cursor: pointer; transition: background 0.2s; }
            button:hover { background: #1d4ed8; }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">🤖 AI Agent Assistant</div>
            <div class="chat-box" id="chatBox">
                <div class="message bot-msg">Hello! How can I help you today?</div>
            </div>
            <div class="input-area">
                <input type="text" id="userInput" placeholder="Type your prompt here..." onkeypress="if(event.key === 'Enter') sendMessage()">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>

        <script>
            async function sendMessage() {
                const inputEl = document.getElementById('userInput');
                const chatBox = document.getElementById('chatBox');
                const prompt = inputEl.value.trim();

                if (!prompt) return;

                // Add User Message
                chatBox.innerHTML += `<div class="message user-msg">${prompt}</div>`;
                inputEl.value = '';
                chatBox.scrollTop = chatBox.scrollHeight;

                // Add Thinking Placeholder
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'message bot-msg';
                loadingDiv.innerText = 'Thinking...';
                chatBox.appendChild(loadingDiv);
                chatBox.scrollTop = chatBox.scrollHeight;

                try {
                    const res = await fetch('/run', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ prompt: prompt })
                    });
                    const data = await res.json();
                    loadingDiv.innerText = data.response || "Error getting response.";
                } catch (err) {
                    loadingDiv.innerText = "Error connecting to AI service.";
                }
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        </script>
    </body>
    </html>
    """