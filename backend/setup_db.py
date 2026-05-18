import os
import urllib.parse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def run_schema():
    print("--- Executing Schema Setup ---")
    db_pass = os.environ.get("live_db_pass")
    project_id = "ygofilutzgdtuuwjtahp"
    
    if not db_pass:
        print("❌ live_db_pass not found.")
        return

    encoded_pass = urllib.parse.quote_plus(db_pass)
    db_url = f"postgresql://postgres.{project_id}:{encoded_pass}@aws-1-us-east-2.pooler.supabase.com:5432/postgres"
    
    engine = create_engine(db_url)
    
    with open("backend/schema.sql", "r") as f:
        schema_sql = f.read()

    # Split by semicolon to execute statements individually if needed, 
    # but SQLAlchemy can often handle blocks. We'll use a transaction.
    try:
        with engine.begin() as conn:
            # We need to execute the extension separately if it fails in a block
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            
            # For POC, drop existing table to update dimensions
            conn.execute(text("DROP TABLE IF EXISTS front_desk_knowledge CASCADE;"))
            
            # Execute the rest of the schema
            # SQLAlchemy's execute(text(...)) handles the multi-line string
            conn.execute(text(schema_sql))
            print("✅ Schema executed successfully.")
    except Exception as e:
        print(f"❌ Schema execution failed: {e}")

if __name__ == "__main__":
    run_schema()
