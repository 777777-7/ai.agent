import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from google import genai
from google.genai import types

app = FastAPI(title="E-Commerce AI Shopping Assistant")

# Initialize Gemini Client
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

# 🛒 1. MOCK PRODUCT CATALOG DATABASE
PRODUCTS = [
    {"id": 1, "name": "Wireless Noise-Canceling Headphones", "category": "Electronics", "price": 120.00, "description": "High-quality wireless headphones with active noise cancellation and 30h battery life."},
    {"id": 2, "name": "Smart Fitness Watch", "category": "Electronics", "price": 85.00, "description": "Tracks heart rate, sleep, steps, and sports activities with a waterproof design."},
    {"id": 3, "name": "Ergonomic Office Chair", "category": "Furniture", "price": 199.99, "description": "Breathable mesh chair with adjustable lumbar support and headrest."},
    {"id": 4, "name": "Minimalist Leather Backpack", "category": "Fashion", "price": 65.00, "description": "Sleek water-resistant leather backpack fitting laptops up to 15 inches."},
    {"id": 5, "name": "Organic Stainless Steel Water Bottle", "category": "Home & Kitchen", "price": 25.00, "description": "Keeps drinks cold for 24 hours or hot for 12 hours. BPA-free."}
]

class QueryRequest(BaseModel):
    prompt: str

@app.post("/run")
def run_agent(request: QueryRequest):
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY environment variable is not configured.")
    
    try:
        # Search catalog for simple keyword matches to provide context
        search_terms = request.prompt.lower().split()
        matched_products = [
            p for p in PRODUCTS 
            if any(term in p["name"].lower() or term in p["category"].lower() or term in p["description"].lower() for term in search_terms)
        ]
        
        # If no specific matches found, supply full catalog context
        catalog_context = matched_products if matched_products else PRODUCTS

        # Construct System Prompt & Instructions
        system_instruction = (
            "You are a friendly, enthusiastic, and helpful AI Shopping Assistant for our store. "
            "Your job is to help customers find products, answer questions about items, and recommend products based on their needs.\n"
            "Here is the product catalog available in store:\n"
            f"{catalog_context}\n\n"
            "Guidelines:\n"
            "- Always state product names clearly alongside their exact prices.\n"
            "- If a customer asks about items we don't carry, politely let them know and recommend the closest alternative from the catalog.\n"
            "- Keep answers concise, clear, and easy to read."
        )

        # Call Gemini API with System Persona
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=request.prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7
            )
        )
        return {"response": response.text}
    except Exception as e:
        print(f"❌ Execution Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
def serve_chat_ui():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Shopping Assistant</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; }
            body { background: #f3f4f6; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .chat-container { width: 100%; max-width: 600px; height: 85vh; background: #fff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); display: flex; flex-direction: column; overflow: hidden; }
            .chat-header { background: #059669; color: white; padding: 16px; font-weight: bold; font-size: 1.2rem; text-align: center; }
            .chat-box { flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
            .message { max-width: 80%; padding: 12px 16px; border-radius: 18px; font-size: 0.95rem; line-height: 1.4; white-space: pre-wrap; }
            .user-msg { background-color: #059669; color: white; align-self: flex-end; border-bottom-right-radius: 4px; }
            .bot-msg { background-color: #e5e7eb; color: #1f2937; align-self: flex-start; border-bottom-left-radius: 4px; }
            .input-area { display: flex; padding: 12px; background: #fff; border-top: 1px solid #e5e7eb; gap: 8px; }
            input { flex: 1; padding: 12px 16px; border: 1px solid #d1d5db; border-radius: 24px; outline: none; font-size: 1rem; }
            button { background: #059669; color: white; border: none; padding: 0 20px; border-radius: 24px; font-weight: bold; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">🛍️ Store Assistant</div>
            <div class="chat-box" id="chatBox">
                <div class="message bot-msg">Hi there! Welcome to our store. How can I help you find what you're looking for today?</div>
            </div>
            <div class="input-area">
                <input type="text" id="userInput" placeholder="Ask for headphones, backpacks, chairs..." onkeypress="if(event.key === 'Enter') sendMessage()">
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
                const userDiv = document.createElement('div');
                userDiv.className = 'message user-msg';
                userDiv.textContent = prompt;
                chatBox.appendChild(userDiv);
                inputEl.value = '';
                chatBox.scrollTop = chatBox.scrollHeight;

                // Add Bot Loading Message
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'message bot-msg';
                loadingDiv.textContent = 'Searching store...';
                chatBox.appendChild(loadingDiv);
                chatBox.scrollTop = chatBox.scrollHeight;

                try {
                    const res = await fetch('/run', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ prompt: prompt })
                    });
                    const data = await res.json();
                    if (res.ok) {
                        loadingDiv.textContent = data.response;
                    } else {
                        loadingDiv.textContent = "Error: " + (data.detail || "Unable to retrieve products.");
                    }
                } catch (err) {
                    loadingDiv.textContent = "Error connecting to store assistant server.";
                }
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        </script>
    </body>
    </html>
    """