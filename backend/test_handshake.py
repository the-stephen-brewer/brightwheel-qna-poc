import os
import urllib.parse
from sqlalchemy import create_engine
from supabase import create_client as create_supabase_client
from dotenv import load_dotenv

load_dotenv()

def test_connections():
    print("--- Testing Handshake ---")
    
    # 1. Test Supabase Client (REST)
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if supabase_url and supabase_key:
        try:
            client = create_supabase_client(supabase_url, supabase_key)
            # We expect this might fail if 'users' table doesn't exist yet, 
            # but it confirms the client can reach the API.
            try:
                res = client.table("users").select("count", count="exact").execute()
                print(f"✅ Supabase REST connection successful. User count: {res.count}")
            except Exception as e:
                if "PGRST205" in str(e):
                    print("✅ Supabase REST reachable (Table 'users' not yet created, which is expected).")
                else:
                    print(f"❌ Supabase REST query failed: {e}")
        except Exception as e:
            print(f"❌ Supabase REST client initialization failed: {e}")
    else:
        print("⚠️ Supabase credentials missing.")

    # 2. Test SQL Connection (PostgreSQL)
    db_pass = os.environ.get("live_db_pass")
    
    if db_pass:
        try:
            project_id = "ygofilutzgdtuuwjtahp"
            encoded_pass = urllib.parse.quote_plus(db_pass)
            # Using the exact host and port provided by the user
            db_url = f"postgresql://postgres.{project_id}:{encoded_pass}@aws-1-us-east-2.pooler.supabase.com:5432/postgres"
            engine = create_engine(db_url)
            with engine.connect() as conn:
                print("✅ Supabase SQL (PostgreSQL) connection successful.")
        except Exception as e:
            print(f"❌ Supabase SQL connection failed: {e}")
    else:
        print("⚠️ Database password (live_db_pass) missing.")

    # 3. Test Gemini API (Check environment variable)
    google_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if google_creds:
        if os.path.exists(google_creds):
            print(f"✅ Gemini Credentials found at: {google_creds}")
        else:
            print(f"❌ Gemini Credentials file not found at: {google_creds}")
    else:
        print("⚠️ GOOGLE_APPLICATION_CREDENTIALS missing.")

if __name__ == "__main__":
    test_connections()
