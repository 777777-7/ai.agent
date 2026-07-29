import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai

# 1. This variable MUST be named "app"
app = FastAPI(title="Gemini AI Agent")

# 2. Setup Gemini Client using environment variable
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

class QueryRequest(BaseModel):
    prompt: str

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Agent service is running"}

@app.post("/run")
def run_agent(request: QueryRequest):
    if not client:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured.")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=request.prompt
        )
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    