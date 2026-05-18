import os
import asyncio
import urllib.parse
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import google.auth
from google import genai
from google.genai import types
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

# Configuration
DB_PASS = os.environ.get("live_db_pass")
PROJECT_ID = "ygofilutzgdtuuwjtahp"
PDF_FILE = "2019-division-of-child-and-family-development-family-handbook-final.pdf"
MD_FILE = "backend/seed_data.md"

async def seed_data():
    if not DB_PASS:
        print("❌ live_db_pass not found.")
        return

    # 1. Initialize Google GenAI Client with explicit Vertex AI scopes
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
    
    # 3. Choose Data Source
    docs_to_insert = []
    MODEL_NAME = "gemini-embedding-001"

    if os.path.exists(PDF_FILE):
        print(f"📄 Parsing PDF: {PDF_FILE}")
        reader = PdfReader(PDF_FILE)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            length_function=len,
        )
        chunks = text_splitter.split_text(full_text)
        print(f"📊 Split PDF into {len(chunks)} chunks.")

        print(f"Embedding {len(chunks)} chunks using Vertex AI ({MODEL_NAME})...")
        for i, chunk in enumerate(chunks):
            # Generate embedding
            response = client.models.embed_content(
                model=MODEL_NAME,
                contents=chunk,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
            )
            vector = response.embeddings[0].values
            docs_to_insert.append({
                "content": chunk,
                "metadata": {"source": PDF_FILE, "chunk": i},
                "embedding": vector
            })
    else:
        print(f"📝 PDF not found. Falling back to MD: {MD_FILE}")
        with open(MD_FILE, "r") as f:
            content = f.read()
        sections = content.split("## ")[1:]
        print(f"Embedding {len(sections)} sections from MD...")
        for section in sections:
            lines = section.split("\n", 1)
            if len(lines) < 2: continue
            title, text_content = lines
            response = client.models.embed_content(
                model=MODEL_NAME,
                contents=text_content.strip(),
                config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
            )
            vector = response.embeddings[0].values
            docs_to_insert.append({
                "content": text_content.strip(),
                "metadata": {"category": title.strip(), "source": MD_FILE},
                "embedding": vector
            })

    # 4. Insert into Database
    if not docs_to_insert:
        print("⚠️ No documents to insert.")
        return

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
