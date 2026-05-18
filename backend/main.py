import os
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import urllib.parse
from sqlalchemy import create_engine, text
from google import genai
from google.genai import types
import google.auth
from dotenv import load_dotenv
import json
import traceback

load_dotenv()

app = FastAPI(title="Brightwheel AI Front Desk PoC")

# --- Configuration & Initialization ---
DB_PASS = os.environ.get("live_db_pass")
PROJECT_ID = "ygofilutzgdtuuwjtahp"

# Direct DB URL
encoded_pass = urllib.parse.quote_plus(DB_PASS) if DB_PASS else ""
DB_URL = f"postgresql://postgres.{PROJECT_ID}:{encoded_pass}@aws-1-us-east-2.pooler.supabase.com:5432/postgres"
db_engine = create_engine(DB_URL)

# Initialize Google GenAI Client (Vertex AI mode)
try:
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    genai_client = genai.Client(
        vertexai=True,
        project="betterai",
        location="us-central1",
        credentials=credentials
    )
except Exception as e:
    print(f"FAILED TO INITIALIZE GENAI CLIENT: {e}")
    traceback.print_exc()

# Model Names
EMBEDDING_MODEL = "gemini-embedding-001"
CHAT_MODEL = "gemini-2.0-flash-lite-001" 

# In-memory session store
SESSION_HISTORY_STORE = {}

# --- Schemas ---
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default-session"

# --- Utilities ---
def log_interaction(question: str, answer: str, needs_review: bool):
    try:
        with db_engine.begin() as conn:
            query = text("""
                INSERT INTO front_desk_logs (question, answer, needs_review)
                VALUES (:q, :a, :r)
            """)
            conn.execute(query, {"q": question, "a": answer, "r": needs_review})
    except Exception as e:
        print(f"Failed to log interaction: {e}")
        traceback.print_exc()

def get_relevant_context(query: str, k: int = 2):
    try:
        # Generate embedding
        response = genai_client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=query,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        )
        vector = response.embeddings[0].values
        vector_str = "[" + ",".join(map(str, vector)) + "]"
        
        # Manual similarity search via SQL
        with db_engine.connect() as conn:
            query_sql = text("""
                SELECT content FROM front_desk_knowledge
                ORDER BY embedding <=> :v::vector
                LIMIT :k
            """)
            result = conn.execute(query_sql, {"v": vector_str, "k": k})
            rows = result.fetchall()
            return "\n".join([row[0] for row in rows])
    except Exception as e:
        print(f"Retrieval error: {e}")
        traceback.print_exc()
        return ""

# --- Endpoints ---
@app.post("/api/parent/chat")
async def handle_parent_chat(req: ChatRequest, background_tasks: BackgroundTasks):
    try:
        # 1. Retrieval
        context = get_relevant_context(req.message)

        # 2. History Retrieval
        history = SESSION_HISTORY_STORE.get(req.session_id, [])
        
        # 3. Build Prompt
        contents = []
        system_instruction = f"""You are 'Sunny', the AI Front Desk assistant for Sunshine Early Learning.
Your job is to give busy parents fast, deeply polite, and highly accurate answers.

CRITICAL INSTRUCTIONS:
- Only answer using the Grounding Knowledge Matrix provided below.
- If the answer is not present, or if it involves sensitive personal info, say exactly: 'I want to make sure you get the exact right answer for that. Let me loop in our center director right now to assist you directly.'
- Keep answers strictly under 3 sentences.

Grounding Knowledge Matrix:
{context}"""

        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part(text=msg["text"])]))
        
        contents.append(types.Content(role="user", parts=[types.Part(text=req.message)]))

        # 4. Generate Response
        response = genai_client.models.generate_content(
            model=CHAT_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0
            )
        )
        ai_answer = response.text

        # 5. Update History
        history.append({"role": "user", "text": req.message})
        history.append({"role": "model", "text": ai_answer})
        SESSION_HISTORY_STORE[req.session_id] = history[-6:]

        # 6. Escalation Logic
        needs_review = "center director" in ai_answer.lower() or not context

        # 7. Async Logging
        background_tasks.add_task(log_interaction, req.message, ai_answer, needs_review)

        return {"answer": ai_answer, "needs_review": needs_review}
    except Exception as e:
        print(f"ERROR IN CHAT ENDPOINT: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
