import os
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

from google.oauth2 import service_account

load_dotenv()

app = FastAPI(title="Brightwheel AI Front Desk PoC")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration & Initialization ---
DB_PASS = os.environ.get("live_db_pass")
PROJECT_ID = "ygofilutzgdtuuwjtahp"

# Direct DB URL
encoded_pass = urllib.parse.quote_plus(DB_PASS) if DB_PASS else ""
DB_URL = f"postgresql://postgres.{PROJECT_ID}:{encoded_pass}@aws-1-us-east-2.pooler.supabase.com:5432/postgres"
db_engine = create_engine(DB_URL)

# Initialize Google GenAI Client (Vertex AI mode)
try:
    # Check for raw JSON string in environment first
    json_creds = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if json_creds:
        import json
        info = json.loads(json_creds)
        credentials = service_account.Credentials.from_service_account_info(
            info, 
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
    else:
        # Fallback to default OIDC / Application Default Credentials
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
#CHAT_MODEL = "gemini-2.0-flash-lite-001"
CHAT_MODEL = "gemini-2.5-flash"

# In-memory session store
SESSION_HISTORY_STORE = {}

# --- Schemas ---
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default-session"

class FeedbackRequest(BaseModel):
    log_id: str
    feedback: str # 'thumbs_up', 'thumbs_down'

# --- Utilities ---
def log_interaction(question: str, answer: str, needs_review: bool, metadata: dict = None):
    try:
        with db_engine.begin() as conn:
            query = text("""
                INSERT INTO front_desk_logs (question, answer, needs_review, metadata)
                VALUES (:q, :a, :r, :m)
                RETURNING id
            """)
            result = conn.execute(query, {
                "q": question, 
                "a": answer, 
                "r": needs_review, 
                "m": json.dumps(metadata) if metadata else None
            })
            return result.fetchone()[0]
    except Exception as e:
        print(f"Failed to log interaction: {e}")
        traceback.print_exc()
        return None
def get_relevant_context(query: str, k: int = 6):
    try:
        # 1. Query Expansion: Generate a few variations to catch different terms (e.g. 'rest' vs 'nap')
        # We'll use a very fast internal prompt for this
        expansion_response = genai_client.models.generate_content(
            model=CHAT_MODEL,
            contents=f"Generate 3 short search terms related to this question to help find the answer in a handbook: '{query}'. Output only the terms separated by commas.",
            config=types.GenerateContentConfig(temperature=0.0)
        )
        search_queries = [query] + [q.strip() for q in expansion_response.text.split(",")]

        all_rows = []
        seen_content = set()

        # 2. Search for each variation
        for q in search_queries[:3]: # Limit to 3 queries for speed
            response = genai_client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=q,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
            )
            vector = response.embeddings[0].values
            vector_str = "[" + ",".join(map(str, vector)) + "]"

            with db_engine.connect() as conn:
                query_sql = text("""
                    SELECT content, metadata->>'category' as cat FROM front_desk_knowledge
                    ORDER BY embedding <=> CAST(:v AS vector)
                    LIMIT :k
                """)
                result = conn.execute(query_sql, {"v": vector_str, "k": k})
                for row in result:
                    if row[0] not in seen_content:
                        # Prepend category for better LLM grounding
                        all_rows.append(f"[{row[1]}] {row[0]}")
                        seen_content.add(row[0])

        return "\n\n".join(all_rows[:k]) # Return top K unique results
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
        with open("backend/reminders.json", "r") as f:
            reminders = json.load(f)
        
        # Check if we should include a reminder (once every 3 days)
        # For POC, we'll check the database for the last reminder sent to this session
        include_reminder = False
        reminder_text = ""
        try:
            with db_engine.connect() as conn:
                res = conn.execute(text("""
                    SELECT created_at FROM front_desk_logs 
                    WHERE metadata->>'session_id' = :sid AND metadata->>'type' = 'reminder'
                    ORDER BY created_at DESC LIMIT 1
                """), {"sid": req.session_id})
                last_reminder_row = res.fetchone()
                
                from datetime import datetime, timedelta
                now = datetime.now()
                
                if not last_reminder_row:
                    include_reminder = True
                else:
                    last_dt = last_reminder_row[0]
                    # Ensure both are naive or both are aware for comparison
                    if last_dt.tzinfo:
                        delta = datetime.now(last_dt.tzinfo) - last_dt
                    else:
                        delta = now - last_dt
                    
                    if delta > timedelta(days=3):
                        include_reminder = True

                if include_reminder:
                    now_str = now.strftime("%Y-%m-%d")
                    upcoming = [r for r in reminders if r["date"] >= now_str]
                    if upcoming:
                        r = upcoming[0]
                        reminder_text = f"REMINDER: {r['event']} on {r['date']}. {r['details']}"
                        print(f"DEBUG: Including reminder for session {req.session_id}: {r['event']}")
        except Exception as e:
            print(f"Reminder check error: {e}")

        system_instruction = f"""You are 'Sunny', the AI Front Desk assistant for Sunshine Early Learning.
Your job is to give busy parents fast, deeply polite, and highly accurate answers.

CRITICAL INSTRUCTIONS:
- Answer using the Grounding Knowledge Matrix provided below. 
- BE HOLISTIC: If the user asks a question, try to provide other relevant details from the matrix that might be helpful.
- IF A 'REMINDER' IS PRESENT BELOW: You MUST include it at the very end of your response, starting with a polite transition like "Also, just a quick reminder..." or "By the way, don't forget...".
- If the answer is not present, or if it involves sensitive personal info, say exactly: 'I want to make sure you get the exact right answer for that. Let me loop in our center director right now to assist you directly.'
- Keep answers helpful but concise (under 5 sentences).

Grounding Knowledge Matrix:
{context}

{reminder_text}"""

        contents = []
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
        log_meta = {"session_id": req.session_id}
        if include_reminder and reminder_text:
            log_meta["type"] = "reminder"
            
        log_id = log_interaction(req.message, ai_answer, needs_review, metadata=log_meta)

        return {
            "answer": ai_answer, 
            "needs_review": needs_review, 
            "log_id": str(log_id) if log_id else None
        }
    except Exception as e:
        print(f"ERROR IN CHAT ENDPOINT: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/knowledge")
async def get_knowledge():
    try:
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT id, content, metadata FROM front_desk_knowledge ORDER BY id DESC"))
            return [{"id": row[0], "content": row[1], "metadata": row[2]} for row in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/logs")
async def get_logs(filter_type: Optional[str] = None):
    try:
        query_str = "SELECT id, question, answer, feedback, needs_review, created_at FROM front_desk_logs"
        if filter_type == "alerts":
            query_str += " WHERE feedback = 'thumbs_down'"
        elif filter_type == "escalations":
            query_str += " WHERE needs_review = TRUE"
        
        query_str += " ORDER BY created_at DESC"
        
        with db_engine.connect() as conn:
            result = conn.execute(text(query_str))
            rows = result.fetchall()
            return [{
                "id": str(row[0]),
                "question": row[1],
                "answer": row[2],
                "feedback": row[3],
                "needs_review": row[4],
                "created_at": row[5]
            } for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/trends")
async def get_trends():
    try:
        with db_engine.connect() as conn:
            total = conn.execute(text("SELECT count(*) FROM front_desk_logs")).scalar() or 0
            resolved = conn.execute(text("SELECT count(*) FROM front_desk_logs WHERE needs_review = FALSE")).scalar() or 0
            
            # Simple category trend based on the last few inquiries
            # In a real app we'd use semantic clustering, here we'll just show the most frequent categories from our new knowledge base
            top_cats_query = conn.execute(text("""
                SELECT metadata->>'category' as cat, count(*) as count 
                FROM front_desk_knowledge
                GROUP BY cat ORDER BY count DESC LIMIT 1
            """))
            top_cat = top_cats_query.fetchone()
            
            # Get some sample questions
            samples_query = conn.execute(text("SELECT question FROM front_desk_logs ORDER BY created_at DESC LIMIT 3"))
            samples = [row[0] for row in samples_query]
            if not samples:
                samples = ["What is the fever policy?", "When is nap time?", "Do I need to bring sunscreen?"]

            return {
                "total_inquiries": total,
                "resolution_rate": (resolved / total * 100) if total > 0 else 100,
                "top_categories": [{"name": top_cat[0] if top_cat else "General Policies", "count": total}],
                "sample_questions": samples
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/resolve")
async def resolve_ticket(req: FeedbackRequest):
    try:
        with db_engine.begin() as conn:
            conn.execute(
                text("UPDATE front_desk_logs SET needs_review = FALSE WHERE id = CAST(:id AS uuid)"),
                {"id": req.log_id}
            )
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feedback")
async def handle_feedback(req: FeedbackRequest):
    try:
        with db_engine.begin() as conn:
            conn.execute(
                text("UPDATE front_desk_logs SET feedback = :f WHERE id = CAST(:id AS uuid)"),
                {"f": req.feedback, "id": req.log_id}
            )
        return {"status": "ok"}
    except Exception as e:
        print(f"Feedback error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
