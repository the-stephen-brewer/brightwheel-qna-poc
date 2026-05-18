import os
import asyncio
import urllib.parse
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import google.auth
from google import genai
from google.genai import types
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

load_dotenv()

# Configuration
DB_PASS = os.environ.get("live_db_pass")
PROJECT_ID = "ygofilutzgdtuuwjtahp"
MD_FILE = "backend/handbook.md"

async def seed_data():
    if not DB_PASS:
        print("❌ live_db_pass not found.")
        return

    # 1. Initialize Google GenAI Client
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
    
    # 3. Load Markdown
    if not os.path.exists(MD_FILE):
        print(f"❌ {MD_FILE} not found. Please run convert_pdf.py first.")
        return

    with open(MD_FILE, "r") as f:
        md_content = f.read()

    # Strip markdown code blocks if Gemini wrapped it
    if md_content.startswith("```markdown"):
        md_content = md_content.replace("```markdown", "").replace("```", "").strip()

    # 4. Split by Headers
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    md_header_splits = markdown_splitter.split_text(md_content)
    
    # Further split into smaller chunks if needed (increased size to keep schedules together)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
    splits = text_splitter.split_documents(md_header_splits)
    
    print(f"📊 Split Markdown into {len(splits)} chunks.")

    docs_to_insert = []
    MODEL_NAME = "gemini-embedding-001"

    print(f"Embedding {len(splits)} chunks...")
    for i, split in enumerate(splits):
        # Extract category from headers (prioritize most specific/closest header)
        category = split.metadata.get("Header 3") or split.metadata.get("Header 2") or split.metadata.get("Header 1") or "General"
        
        # Generate embedding
        response = client.models.embed_content(
            model=MODEL_NAME,
            contents=split.page_content,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        )
        vector = response.embeddings[0].values
        
        docs_to_insert.append({
            "content": split.page_content,
            "metadata": {"category": category, "source": "handbook.pdf", "chunk": i},
            "embedding": vector
        })

    # 5. Insert into Database
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
