import os
import asyncio
import urllib.parse
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import google.auth
from google import genai
from google.genai import types

load_dotenv()

# Configuration
DB_PASS = os.environ.get("live_db_pass")
PROJECT_ID = "ygofilutzgdtuuwjtahp"

async def seed_data():
    if not DB_PASS:
        print("❌ live_db_pass not found.")
        return

    # 1. Initialize Google GenAI Client with explicit Vertex AI scopes
    # The 'invalid_scope' error is often fixed by providing the correct scope
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    credentials, project = google.auth.default(scopes=scopes)
    
    client = genai.Client(
        vertexai=True,
        project="betterai",
        location="us-central1",
        credentials=credentials
    )

    # 2. Setup Direct SQL Engine
    encoded_pass = urllib.parse.quote_plus(DB_PASS)
    db_url = f"postgresql://postgres.{PROJECT_ID}:{encoded_pass}@aws-1-us-east-2.pooler.supabase.com:5432/postgres"
    engine = create_engine(db_url)
    
    # 3. Load and Split Data
    with open("backend/seed_data.md", "r") as f:
        content = f.read()

    sections = content.split("## ")[1:]
    
    # In Vertex AI, we use the model ID directly
    MODEL_NAME = "text-embedding-004"
    
    print(f"Embedding {len(sections)} documents using Vertex AI ({MODEL_NAME})...")
    
    docs_to_insert = []
    for section in sections:
        lines = section.split("\n", 1)
        if len(lines) < 2: continue
        title, text_content = lines
        
        # Generate embedding
        response = client.models.embed_content(
            model=MODEL_NAME,
            contents=text_content.strip(),
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        )
        
        vector = response.embeddings[0].values
        
        docs_to_insert.append({
            "content": text_content.strip(),
            "metadata": {"category": title.strip()},
            "embedding": vector
        })

    print(f"Inserting {len(docs_to_insert)} documents directly via SQL...")

    try:
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE front_desk_knowledge;"))
            
            for doc in docs_to_insert:
                vector_str = "[" + ",".join(map(str, doc["embedding"])) + "]"
                conn.execute(
                    text("INSERT INTO front_desk_knowledge (content, metadata, embedding) VALUES (:c, :m, :v)"),
                    {"c": doc["content"], "m": json.dumps(doc["metadata"]), "v": vector_str}
                )
        print("✅ Seeding completed successfully.")
    except Exception as e:
        print(f"❌ Seeding failed: {e}")

if __name__ == "__main__":
    asyncio.run(seed_data())
